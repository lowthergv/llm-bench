// On-device ASR benchmark for Tact's voice features (talk-to-type + interview).
// Mirrors run.mjs in spirit: runs jargon-dense clinical utterances through each candidate model
// on the box, across acoustic CONDITIONS (clean + degraded variants from augment-asr-corpus.mjs),
// then writes a markdown robustness scoreboard.
//
// Each backend is a tiny Python runner (benchmark/asr_runners/*.py) launched via `uv run` with a
// pinned Python 3.12. The runner loads the model ONCE and reports per-clip steady-state latency.
//
// Corpus files are named <id>.<condition>.wav with a shared <id>.txt reference (empty = no-speech).
// Scores: WER and ABA jargon error rate per condition, latency / xRealtime, and phantom words on
// no-speech clips (silence + pure noise) — the hallucination failure WER misses.
//
// Usage:  node benchmark/asr.mjs                 (default backends)
//         node benchmark/asr.mjs parakeet whisper
// Prereq: node benchmark/make-asr-corpus.mjs && node benchmark/augment-asr-corpus.mjs

import { execFileSync } from "node:child_process";
import { readFileSync, writeFileSync, readdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { JARGON } from "./asr-data.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const CORPUS = join(__dirname, "asr-corpus");
const RUNNERS = join(__dirname, "asr_runners");
const OUT = join(__dirname, "asr-results.md");

const BACKENDS = {
  parakeet: { label: "Parakeet TDT 0.6B v3 (mlx)", dep: "parakeet-mlx", script: "parakeet_run.py" },
  whisper: { label: "Whisper large-v3-turbo (mlx)", dep: "mlx-whisper", script: "whisper_run.py" },
  // Moonshine was rebranded to the `moonshine-voice` PyPI package — a ctypes C-API voice SDK
  // bundling only tiny-en; the old onnx pip package is gone. Not wired here on purpose:
  // footprint (Moonshine's only edge) is a non-issue on the 48 GB box, and Parakeet already
  // wins on accuracy, speed, and hallucination. To revisit, update moonshine_run.py for the
  // new SDK and run `node benchmark/asr.mjs moonshine` explicitly.
  moonshine: { label: "Moonshine (moonshine-voice)", dep: "moonshine-voice", script: "moonshine_run.py" },
};

const DEFAULT_BACKENDS = ["parakeet", "whisper"];
const selected = process.argv.slice(2).length ? process.argv.slice(2) : DEFAULT_BACKENDS;
const short = (s) => (s.length > 160 ? s.slice(0, 160) + "…" : s);

// condition display order + labels
const ORDER = ["clean", "reverb", "phone", "noisy10", "noisy5"];
const LABEL = { clean: "clean", reverb: "reverb", phone: "phone 12k", noisy10: "noise 10dB", noisy5: "noise 5dB" };

// ---------- corpus ----------
function wavSeconds(path) {
  const out = execFileSync("afinfo", [path], { encoding: "utf8" });
  const m = out.match(/estimated duration:\s*([\d.]+)/);
  return m ? parseFloat(m[1]) : 0;
}
const items = readdirSync(CORPUS)
  .filter((f) => f.endsWith(".wav"))
  .sort()
  .map((f) => {
    const base = f.replace(/\.wav$/, "");
    const parts = base.split(".");
    const cond = parts.pop();
    const id = parts.join(".");
    const ref = readFileSync(join(CORPUS, `${id}.txt`), "utf8").trim();
    return { id, cond, wav: join(CORPUS, f), ref, noSpeech: ref === "", seconds: wavSeconds(join(CORPUS, f)) };
  });
const speech = items.filter((i) => !i.noSpeech);
const noSpeech = items.filter((i) => i.noSpeech);
const conditions = [
  ...ORDER.filter((c) => speech.some((i) => i.cond === c)),
  ...[...new Set(speech.map((i) => i.cond))].filter((c) => !ORDER.includes(c)),
];

// ---------- scoring ----------
const normalize = (s) =>
  s.toLowerCase().replace(/[-/]/g, " ").replace(/[^a-z0-9\s']/g, " ").replace(/\s+/g, " ").trim();
const wordsOf = (s) => (normalize(s) ? normalize(s).split(" ") : []);

function werStats(ref, hyp) {
  const r = wordsOf(ref);
  const h = wordsOf(hyp);
  const d = Array.from({ length: r.length + 1 }, () => new Array(h.length + 1).fill(0));
  for (let i = 0; i <= r.length; i++) d[i][0] = i;
  for (let j = 0; j <= h.length; j++) d[0][j] = j;
  for (let i = 1; i <= r.length; i++)
    for (let j = 1; j <= h.length; j++) {
      const cost = r[i - 1] === h[j - 1] ? 0 : 1;
      d[i][j] = Math.min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cost);
    }
  return { errors: d[r.length][h.length], refLen: r.length };
}
const jnorm = (s) => " " + normalize(s) + " ";
function countOcc(hay, needle) {
  const n = " " + needle + " ";
  let i = 0,
    c = 0;
  while ((i = hay.indexOf(n, i)) !== -1) {
    c++;
    i += n.length - 1;
  }
  return c;
}
function jargonStats(ref, hyp) {
  const R = jnorm(ref);
  const H = jnorm(hyp);
  let correct = 0,
    total = 0;
  for (const term of JARGON) {
    const rc = countOcc(R, term);
    if (!rc) continue;
    total += rc;
    correct += Math.min(rc, countOcc(H, term));
  }
  return { correct, total };
}

// ---------- run a backend ----------
function runBackend(key) {
  const b = BACKENDS[key];
  const args = ["run", "--python", "3.12", "--with", b.dep, "python", join(RUNNERS, b.script), ...items.map((i) => i.wav)];
  const stdout = execFileSync("uv", args, { encoding: "utf8", maxBuffer: 64 * 1024 * 1024 });
  return JSON.parse(stdout.slice(stdout.indexOf("{"), stdout.lastIndexOf("}") + 1));
}

// ---------- main ----------
const pct = (x) => (x * 100).toFixed(1) + "%";
const reports = [];

for (const key of selected) {
  if (!BACKENDS[key]) {
    console.log(`skip unknown backend: ${key}`);
    continue;
  }
  process.stdout.write(`Running ${key} (${BACKENDS[key].label})... `);
  let parsed;
  try {
    parsed = runBackend(key);
  } catch (e) {
    const msg = short(e.message.split("\n")[0]);
    console.log(`FAILED: ${msg}`);
    reports.push({ key, error: msg });
    continue;
  }
  if (parsed.error) {
    console.log(`ERROR: ${parsed.error}`);
    reports.push({ key, error: short(parsed.error) });
    continue;
  }
  const byWav = Object.fromEntries(parsed.results.map((r) => [r.wav, r]));
  const cond = {}; // cond -> { err, ref, jc, jt, samples }
  let speechMs = 0,
    speechSec = 0,
    phantom = 0;
  for (const it of speech) {
    const hyp = byWav[it.wav]?.text ?? "";
    const w = werStats(it.ref, hyp);
    const j = jargonStats(it.ref, hyp);
    const c = (cond[it.cond] ??= { err: 0, ref: 0, jc: 0, jt: 0, samples: [] });
    c.err += w.errors;
    c.ref += w.refLen;
    c.jc += j.correct;
    c.jt += j.total;
    c.samples.push({ id: it.id, wer: w.errors / w.refLen, hyp });
    speechMs += byWav[it.wav]?.ms ?? 0;
    speechSec += it.seconds;
  }
  for (const it of noSpeech) phantom += wordsOf(byWav[it.wav]?.text ?? "").length;
  const r = {
    key,
    label: BACKENDS[key].label,
    model: parsed.model,
    loadMs: parsed.load_ms,
    cond,
    avgClipMs: speechMs / speech.length,
    xRealtime: speechSec / (speechMs / 1000),
    phantom,
  };
  reports.push(r);
  const werLine = conditions.map((c) => `${c}:${pct(r.cond[c] ? r.cond[c].err / r.cond[c].ref : 0)}`).join(" ");
  console.log(`${werLine} · ${r.avgClipMs.toFixed(0)}ms/clip · ${r.xRealtime.toFixed(1)}x · phantom ${phantom}`);
}

// ---------- write markdown ----------
const ok = reports.filter((r) => !r.error);
let md = `# Tact — on-device ASR benchmark (robustness)\n\n`;
md += `Corpus: ${speech.length / conditions.length} clinical scripts (jargon-dense, ${[...new Set(speech.map((i) => i.id))].length} speakers/accents) × ${conditions.length} acoustic conditions = ${speech.length} speech clips, plus ${noSpeech.length} no-speech clips, 16 kHz mono.\n\n`;
md += `Conditions: ${conditions.map((c) => `**${LABEL[c] ?? c}**`).join(", ")}. Degraded clips are synthetic (TTS + ffmpeg noise/codec/reverb) — a recording-free stand-in for real dictation; **rerun on human recordings before locking the choice** (docs/voice-and-interview-plan.md §8).\n\n`;

const condCell = (r, c) => (r.cond[c] ? pct(r.cond[c].err / r.cond[c].ref) : "—");
const jCell = (r, c) => (r.cond[c] && r.cond[c].jt ? pct(1 - r.cond[c].jc / r.cond[c].jt) : "—");

md += `### Word error rate by condition\n\n`;
md += `| Model | ${conditions.map((c) => LABEL[c] ?? c).join(" | ")} |\n`;
md += `|---|${conditions.map(() => "---").join("|")}|\n`;
for (const r of ok) md += `| ${r.label} | ${conditions.map((c) => condCell(r, c)).join(" | ")} |\n`;

md += `\n### Jargon error rate by condition\n\n`;
md += `| Model | ${conditions.map((c) => LABEL[c] ?? c).join(" | ")} |\n`;
md += `|---|${conditions.map(() => "---").join("|")}|\n`;
for (const r of ok) md += `| ${r.label} | ${conditions.map((c) => jCell(r, c)).join(" | ")} |\n`;

md += `\n### Speed & hallucination\n\n`;
md += `| Model | Latency/clip | xRealtime | Load | Phantom words (no-speech) |\n|---|---|---|---|---|\n`;
for (const r of ok)
  md += `| ${r.label} | ${r.avgClipMs.toFixed(0)} ms | ${r.xRealtime.toFixed(1)}x | ${(r.loadMs / 1000).toFixed(1)}s | ${r.phantom} |\n`;
for (const r of reports.filter((r) => r.error)) md += `| ${BACKENDS[r.key]?.label ?? r.key} | — | — | — | ⚠️ ${r.error} |\n`;

md += `\nLower WER / jargon-ER is better; higher xRealtime is faster; phantom should be 0.\n`;

// per-model transcripts on the hardest speech condition, to eyeball degradation
const hardest = conditions[conditions.length - 1];
for (const r of ok) {
  md += `\n---\n\n## ${r.label}\n\n\`${r.model}\` · load ${(r.loadMs / 1000).toFixed(1)}s · ${r.avgClipMs.toFixed(0)} ms/clip · ${r.xRealtime.toFixed(1)}x · phantom ${r.phantom}\n\n`;
  md += `Transcripts on **${LABEL[hardest] ?? hardest}** (hardest condition):\n\n`;
  for (const s of (r.cond[hardest]?.samples ?? [])) {
    md += `**${s.id}** — WER ${pct(s.wer)}\n\n> ${s.hyp.replace(/\n/g, " ")}\n\n`;
  }
}

writeFileSync(OUT, md);
console.log(`\nWrote ${OUT}`);
