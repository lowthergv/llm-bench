// Acoustic augmentation for the ASR benchmark — the recording-free stand-in for real dictation.
// Takes each clean speech clip in benchmark/asr-corpus/ and writes degraded variants that
// simulate the conditions an RBT actually dictates in:
//
//   <id>.noisy10.wav  pink "clinic" noise mixed at ~10 dB SNR (moderate background)
//   <id>.noisy5.wav   pink noise at ~5 dB SNR (loud room)
//   <id>.phone.wav    telephone band-limit (300–3400 Hz) + Opus 12k codec round-trip (phone mic)
//   <id>.reverb.wav   multi-tap room echo (reverberant therapy room)
//
// Plus a pure-noise no-speech clip (noise-3s) to test hallucination under noise, not just silence.
// SNR is hit by measuring each signal's mean volume (ffmpeg volumedetect) and gaining the noise.
//
// Usage: node benchmark/augment-asr-corpus.mjs   (run AFTER make-asr-corpus.mjs)

import { spawnSync, execFileSync } from "node:child_process";
import { readdirSync, readFileSync, writeFileSync, rmSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const CORPUS = join(__dirname, "asr-corpus");
const SR = 16000;

function ffrun(args) {
  const r = spawnSync("ffmpeg", ["-hide_banner", "-y", ...args], { encoding: "utf8", maxBuffer: 64 * 1024 * 1024 });
  const log = (r.stdout || "") + (r.stderr || "");
  if (r.status !== 0) throw new Error(`ffmpeg failed: ${args.join(" ")}\n${log.slice(-400)}`);
  return log;
}
function meanVolumeDb(wav) {
  const out = ffrun(["-i", wav, "-af", "volumedetect", "-f", "null", "-"]);
  const m = out.match(/mean_volume:\s*(-?[\d.]+)\s*dB/);
  return m ? parseFloat(m[1]) : -30;
}
function wavSeconds(wav) {
  const out = execFileSync("afinfo", [wav], { encoding: "utf8" });
  const m = out.match(/estimated duration:\s*([\d.]+)/);
  return m ? parseFloat(m[1]) : 3;
}
const pcm = (out) => ["-ar", String(SR), "-ac", "1", "-c:a", "pcm_s16le", out];

function pinkNoise(durSec, out) {
  ffrun(["-f", "lavfi", "-i", `anoisesrc=color=pink:duration=${durSec.toFixed(2)}:sample_rate=${SR}`, ...pcm(out)]);
}
function mixAtSnr(clean, snrDb, out) {
  const sv = meanVolumeDb(clean);
  const noise = out.replace(/\.wav$/, ".noisetmp.wav");
  pinkNoise(wavSeconds(clean), noise);
  const nv = meanVolumeDb(noise);
  const gain = sv - snrDb - nv; // dB to apply to noise so (signal - noise) ≈ snrDb
  ffrun([
    "-i", clean, "-i", noise,
    "-filter_complex", `[1:a]volume=${gain.toFixed(2)}dB[n];[0:a][n]amix=inputs=2:duration=first:normalize=0[o]`,
    "-map", "[o]", ...pcm(out),
  ]);
  rmSync(noise, { force: true });
}
function phone(clean, out) {
  const ogg = out.replace(/\.wav$/, ".codectmp.ogg");
  ffrun(["-i", clean, "-af", "highpass=f=300,lowpass=f=3400", "-c:a", "libopus", "-b:a", "12k", ogg]);
  ffrun(["-i", ogg, ...pcm(out)]);
  rmSync(ogg, { force: true });
}
function reverb(clean, out) {
  ffrun(["-i", clean, "-af", "aecho=0.8:0.9:40|70|110:0.4|0.3|0.2", ...pcm(out)]);
}

// speech clean clips = <id>.clean.wav whose <id>.txt is non-empty
const speech = readdirSync(CORPUS)
  .filter((f) => f.endsWith(".clean.wav"))
  .map((f) => f.replace(/\.clean\.wav$/, ""))
  .filter((id) => readFileSync(join(CORPUS, `${id}.txt`), "utf8").trim() !== "");

for (const id of speech) {
  const clean = join(CORPUS, `${id}.clean.wav`);
  mixAtSnr(clean, 10, join(CORPUS, `${id}.noisy10.wav`));
  mixAtSnr(clean, 5, join(CORPUS, `${id}.noisy5.wav`));
  phone(clean, join(CORPUS, `${id}.phone.wav`));
  reverb(clean, join(CORPUS, `${id}.reverb.wav`));
  console.log(`✓ ${id} → noisy10, noisy5, phone, reverb`);
}

// pure-noise no-speech clip (hallucination under noise)
writeFileSync(join(CORPUS, "noise-3s.txt"), "");
ffrun(["-f", "lavfi", "-i", `anoisesrc=color=pink:duration=3:sample_rate=${SR}`, "-af", "volume=-22dB", ...pcm(join(CORPUS, "noise-3s.noise.wav"))]);
console.log("✓ noise-3s.noise.wav (no-speech, pink noise)");

console.log(`\nAugmented corpus ready. Next: node benchmark/asr.mjs`);
