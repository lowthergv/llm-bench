# Benchmark Plan — Best Local LLMs on a MacBook Pro M4 Pro (48GB)

A plan **and** a runnable harness for ranking local models on **coding, general
reasoning, writing, and agentic/tool-use**, plus the performance that decides
whether a model is usable day-to-day. Built and verified against live mid-2026
sources (the research pass even caught and dropped one fabricated model).

---

## 1. Objective & target hardware

Find the best *locally runnable* models for **your four use cases**, scored on
capability **and** speed, so you can pick a daily driver per task type.

| | |
|---|---|
| Machine | **Apple M4 Pro** — 14 CPU (10P/4E), **20-core GPU**, Metal 4 |
| Memory | **48 GB** unified → budget **~36–40 GB usable** (OS + weights + KV cache) |
| Bandwidth | ~273 GB/s — the dominant factor in local decode throughput |
| Disk | 1.4 TB free — model storage is not a constraint |
| Installed | Ollama 0.30.6, LM Studio, Python 3.14 + uv, Homebrew, Node |

**Memory rule:** budget MoE models by **total** params (all must be resident),
but their *speed* reflects **active** params. A 4-bit 30–35B fits with room for
8–16k context; ~70B only fits at aggressive quant with short context.

---

## 2. Runtime decision

**Primary: Ollama (HTTP API).** As of v0.19 (Mar 2026) Ollama's Metal path runs
on the **MLX backend**, so it gets most of MLX's Apple-Silicon decode advantage
while giving (a) trivial model management, (b) one-line model swaps, and
(c) **clean nanosecond timing** in every `/api/chat` response
(`prompt_eval_*` = prefill, `eval_*` = decode, `load_duration` = cold load).
That combination is why the harness standardizes on it — we can run *today*.

**Rigor upgrades (optional, documented):**
- **MLX (`mlx-lm`) direct** — peak decode throughput (~1.4–1.8× dense, up to ~3× MoE
  vs raw llama.cpp) and 7–13% less RAM; install via `uv pip install mlx-lm`.
- **`llama.cpp` (`llama-bench -fa 1`)** — the reproducible GGUF control with
  mean±stddev, and **better prefill/long-context** than MLX on M4 (no M5 Neural
  Accelerators here, so don't assume MLX wins prefill — measure it).

> Treat Ollama/LM Studio as *engines for convenience*, not lab-grade controls:
> they inject defaults (`num_ctx`, KV type, batch). The harness pins these
> explicitly. For a paper-grade number, re-run the top 2–3 models under
> `llama-bench` and `mlx_lm.generate --verbose`.

---

## 3. Model roster (verified to fit 48 GB)

Full table with tags/quants/RAM in [`config/models.json`](config/models.json).
Ranked benchmark roster (all Apache-2.0 unless noted):

| # | Model | Best at | Params | Quant | ~RAM | Ollama tag |
|---|-------|---------|--------|-------|------|-----------|
| 1 | **Qwen3.6-27B** | Coding (headline) | 27B dense | Q6_K | 25–30 | `qwen3.6:27b` |
| 2 | **Qwen3.6-35B-A3B** | Agentic/coding | 35B/3B MoE | Q4_K_M | 25–27 | `qwen3.6:35b-a3b` |
| 3 | **Qwen3-Coder-30B-A3B** | Coding (speed) | 30.5B/3.3B MoE | Q4_K_M | 22–25 | `qwen3-coder:30b` |
| 4 | **Devstral Small 2 24B** | Agentic coder | 24B dense | Q8_0/Q4 | 27/15 | `devstral-small-2:24b` |
| 5 | **gpt-oss-20b** | Reasoning+agentic (fast) | 20.9B/3.6B MoE | MXFP4 | 14–22 | `gpt-oss:20b` |
| 6 | **GLM-4.7-Flash** | Agentic (MIT) | 30B/3B MoE | Q4_K_M | 20–24 | `glm-4.7-flash` |
| 7 | **Seed-OSS-36B** | Long-ctx/agentic | 36B dense | Q4_K_M | 24–26 | `milkey/Seed-OSS-36B-Instruct:q4_K_M` |
| 8 | **Gemma 4 31B** | Writing (headline) | 30.7B dense | Q4_K_M | 22–24 | `gemma4:31b` |
| 9 | **Mistral Small 3.2 24B** | All-rounder/writing | 24B dense | Q5_K_M | 20–28 | `mistral-small3.2:24b` |
| 10 | **Phi-4-reasoning-plus** | Reasoning (MIT) | 14B dense | Q8_0 | 13–20 | `phi4-reasoning:plus` |
| 11 | **DeepSeek-R1-Distill-Qwen-32B** | Reasoning (MIT) | 32B dense | Q4_K_M | 22–26 | `deepseek-r1:32b` |

**Stretch / optional anchors:** Qwen3-Coder-Next 80B-A3B (Q3_K_XL ~36GB, at the
ceiling — llama.cpp/LM Studio, *not* default Ollama tags); Llama-3.3-70B
(IQ3/Q3_K_S only, ~7–9 tok/s); Codestral-22B (FIM only, **non-commercial MNPL**, 32K).

**Dropped:** GLM-4.5-Air (3-bit ~46GB busts the budget), Llama-3.3-70B@Q4 (43GB
> macOS GPU cap), and a *fabricated* "GLM-5.1-32B dense" (real GLM-5.1 is a 754B
MoE needing 200GB+).

---

## 4. Benchmark suite (~22 tasks now; designed to grow to ~64)

Original, privately-authored tasks (no public-leaderboard contamination),
~70% deterministic / ~30% judge-scored. Each category lives in
[`tasks/<cat>/tasks.jsonl`](tasks/) and is trivially extendable.

| Category | Weight | Tasks now | Scorer | What it measures |
|---|---|---|---|---|
| Coding | 0.25 | 4 | `pass@1` via sandboxed pytest | Correct functions against hidden tests |
| Reasoning/Math | 0.20 | 5 | numeric/MC exact-match | Word problems + science/logic MC |
| Agentic/Tool | 0.20 | 4 | tool-call + JSON-schema checks | Right tool+args, **knowing when NOT to call**, schema-valid JSON |
| Writing | 0.15 | 3 | LLM-judge, pairwise 2-game swap | Concision, tone, age-appropriate explanation |
| Instruction | 0.10 | 4 | programmatic constraint checks | IFEval-style verifiable constraints |
| Long-context | 0.10 | 2 | exact-match @16k ctx | Single-needle + multi-hop retrieval |

**Scaling to the full ~64:** add post-cutoff **LiveCodeBench** slices + **EvalPlus**
(coding), **MMLU-Pro/GPQA-Diamond/AIME-2025** (reasoning), **IFEval** (instruction),
**Arena-Hard-Auto** prompts (writing), **BFCL-v4** cases (agentic), **RULER/NoLiMa**
(long-context). Keep a never-published private half with a canary GUID.

> **Avoid as rankers** (saturated/contaminated): vanilla HumanEval, MBPP, MMLU,
> GSM8K, MATH-500, MT-Bench, plain needle-in-haystack. Use them only as a ~90%
> "qualification gate," never on the leaderboard.

---

## 5. Scoring

- Every category normalized to **0–1**; per-category = mean of its tasks.
- **Overall** = weighted mean (weights above), **renormalized** over categories
  that actually ran — so a skipped category doesn't zero you out.
- **Capability and performance are reported in separate tables — never merged.**
  Every row is tagged with quant, context length, runtime, hardware.
- **Decoding:** temp 0.0, fixed seed, identical across models, all logged.
  Reasoning is done **inline** (`think=false`) so a hidden-thinking channel can't
  silently eat the token budget (a bug we hit and fixed — see §7).

**Writing judge:** pairwise vs a *frozen baseline*, **two-game position swap** to
cancel order bias. Judge = a model from a **different family** than the contestant
(self-family pairs are auto-skipped). If `ANTHROPIC_API_KEY` is set, a **Claude
judge** is used (recommended — neutral to every local model); else a local judge
(`gpt-oss:20b`). **Calibrate the judge against ~20–30 human labels before trusting
absolute writing numbers.**

---

## 6. Performance measurement (Apple Silicon)

Per `{model × quant × context}` the harness records, from Ollama's timing fields:
- **Decode tok/s** (generation) — headline speed, mean±stddev over N≥3 reps.
- **Prefill tok/s** (prompt) — measured *separately* (MLX-backend prefill on M4
  can trail llama.cpp+FlashAttention).
- **Cold-load (s)** — captured once, **excluded** from throughput.
- **Resident RAM (GB)** — from `/api/ps` (`size_vram`).

**Protocol:** 1 discarded warm-up → N timed reps → mean±stddev. For lab-grade
numbers also run a **10-minute sustained** test (first-minute vs last-minute tok/s)
with `sudo powermetrics --samplers thermal,cpu_power,gpu_power` to flag thermal
throttling (MacBook Pro chassis drops ~10–20% after 5–15 min), and verify **zero
swap** (`vm_stat`) before timing.

---

## 7. Harness architecture & top risks

Layout and usage in [`README.md`](README.md). Pure standard-library Python
(no installs), Ollama over HTTP, JSONL tasks, pluggable scorers, raw outputs
persisted so writing can be **re-judged without re-running inference**.

**Risks the design controls for:** (1) MLX-4bit ≠ GGUF-Q4_K_M — report
bits/weight + resident size, not just the label; (2) no M5 accelerators →
measure prefill, don't assume; (3) cold-load leakage → isolated; (4) thermal
throttle → sustained test + powermetrics; (5) **swap death** → budget 36–40GB,
flag stretch models; (6) contamination → private tasks + post-cutoff slices;
(7) judge bias → different-family judge, two-game swap, human calibration;
(8) advertised≠effective context → test at real 8k/16k; (9) Ollama defaults →
pinned; (10) MoE memory vs speed accounting → total for RAM, active for speed.
