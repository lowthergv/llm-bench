// Generates the BASE (clean) ASR benchmark corpus into benchmark/asr-corpus/.
// For each SCRIPT: writes <id>.txt (reference) and <id>.clean.wav (16 kHz mono 16-bit PCM,
// synthesized with the macOS `say` voice/rate + `afconvert`). Also writes pure-silence clips.
// Then run `node benchmark/augment-asr-corpus.mjs` to add noisy/phone/reverb variants.
//
// Usage: node benchmark/make-asr-corpus.mjs
//
// NOTE: clean TTS is a stopgap for real dictation. augment-asr-corpus.mjs degrades these clips
// to simulate real acoustics (clinic noise, phone mic, reverb); see docs/voice-and-interview-plan.md §8.

import { execFileSync } from "node:child_process";
import { mkdirSync, writeFileSync, rmSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { SCRIPTS, SILENCE_CLIPS } from "./asr-data.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const CORPUS = join(__dirname, "asr-corpus");
const SAMPLE_RATE = 16000;

rmSync(CORPUS, { recursive: true, force: true });
mkdirSync(CORPUS, { recursive: true });

/** Synthesize text → 16 kHz mono PCM WAV via `say` (voice + rate) then `afconvert`. */
function synth(text, voice, rate, wavPath) {
  const aiff = wavPath.replace(/\.wav$/, ".aiff");
  const args = ["-r", String(rate), "-o", aiff, text];
  try {
    execFileSync("say", ["-v", voice, ...args]);
  } catch {
    execFileSync("say", args); // default voice fallback if `voice` isn't installed
  }
  execFileSync("afconvert", [aiff, wavPath, "-f", "WAVE", "-d", `LEI16@${SAMPLE_RATE}`, "-c", "1"]);
  rmSync(aiff, { force: true });
}

/** Write `seconds` of digital silence as a 16 kHz mono 16-bit PCM WAV. */
function silenceWav(seconds, wavPath) {
  const samples = SAMPLE_RATE * seconds;
  const dataLen = samples * 2;
  const buf = Buffer.alloc(44 + dataLen);
  buf.write("RIFF", 0);
  buf.writeUInt32LE(36 + dataLen, 4);
  buf.write("WAVE", 8);
  buf.write("fmt ", 12);
  buf.writeUInt32LE(16, 16);
  buf.writeUInt16LE(1, 20); // PCM
  buf.writeUInt16LE(1, 22); // channels
  buf.writeUInt32LE(SAMPLE_RATE, 24);
  buf.writeUInt32LE(SAMPLE_RATE * 2, 28);
  buf.writeUInt16LE(2, 32);
  buf.writeUInt16LE(16, 34);
  buf.write("data", 36);
  buf.writeUInt32LE(dataLen, 40);
  writeFileSync(wavPath, buf);
}

for (const s of SCRIPTS) {
  writeFileSync(join(CORPUS, `${s.id}.txt`), s.text + "\n");
  synth(s.text, s.voice, s.rate, join(CORPUS, `${s.id}.clean.wav`));
  console.log(`✓ ${s.id}.clean.wav (${s.voice} @ ${s.rate}wpm)`);
}

for (const sec of SILENCE_CLIPS) {
  const id = `silence-${sec}s`;
  writeFileSync(join(CORPUS, `${id}.txt`), ""); // empty reference → no-speech (phantom) clip
  silenceWav(sec, join(CORPUS, `${id}.clean.wav`));
  console.log(`✓ ${id}.clean.wav (silence)`);
}

console.log(`\nWrote base corpus to ${CORPUS}\nNext: node benchmark/augment-asr-corpus.mjs`);
