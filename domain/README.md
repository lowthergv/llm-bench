# Domain evals — the measurements behind Tact

The top-level suite ranks local models on **general** capability (coding,
reasoning, agentic, writing, instruction-following, long-context) and speed.
This folder is the other half: the **task-specific** evals I ran to actually
choose the models that ship in [Tact](https://github.com/lowthergv/note-helper),
a local-first clinical-note tool for ABA clinics.

A general benchmark tells you which model is smartest. It doesn't tell you which
model writes a *defensible clinical note* or transcribes *clinic dictation*
without inventing words. These do.

All inputs are **synthetic** — no PHI. Sample notes are fictional; the ASR
corpus is TTS-generated, not real recordings.

## 1. Clinical-note quality — [`clinical-notes/`](clinical-notes/)

Which local model turns an RBT's shorthand into a note that matches the clinic's
template and **invents nothing**? Each candidate gets Tact's live system prompt
plus fictional sample cases, and the output is checked against the required
structure and a no-fabrication rule.

- Results: [`note-quality.md`](clinical-notes/note-quality.md) (1:1 direct service)
  and [`note-quality-group.md`](clinical-notes/note-quality-group.md) (social-skills group).
- The runner lives **inside the Tact repo** (`benchmark/run.mjs`) because it
  reads Tact's live prompt — testing a stale copy would be lying to yourself.

**Takeaway:** small models hallucinate structure and detail (a 350M model
dropped sections and added an unsupported "CBT was effective" claim);
`gemma4:e4b` held the format and stuck to the notes. That's why Tact defaults to
it.

## 2. On-device ASR for dictation — [`asr/`](asr/)

If clinicians dictate notes, which speech model runs on the box — fast, accurate
on ABA jargon, and **without hallucinating words into silence**? A runnable
benchmark over 8 jargon-dense clinical scripts × 5 acoustic conditions (clean,
reverb, phone, two noise levels), 16 kHz mono.

```bash
node domain/asr/make-asr-corpus.mjs      # TTS the clean corpus (macOS `say`)
node domain/asr/augment-asr-corpus.mjs   # add reverb / phone / noise variants
node domain/asr/asr.mjs                   # score each backend
```

**Result:** Parakeet TDT 0.6B beats Whisper large-v3-turbo across the board —
lower word-error and jargon-error rates, **3× faster** (68× vs 23× realtime),
and **0 phantom words on silent clips vs Whisper's 6**. For a tool that must not
fabricate, the hallucination column decided it.

| Model | WER (clean→noisy) | Jargon ER | Speed | Phantom words |
|---|---|---|---|---|
| Parakeet TDT 0.6B v3 | 4.4% → 8.0% | 9.1% → 13.6% | 68× realtime | **0** |
| Whisper large-v3-turbo | 4.4% → 6.8% | 9.1% → 13.6% | 23× realtime | 6 |

## 3. Concurrency — [`concurrency-results.md`](concurrency-results.md)

Can one Mac "box" serve a clinic? A quick load check of concurrent generations
on the on-device stack.
