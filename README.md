# llm-bench — local LLM benchmark for MacBook Pro M4 (48GB)

Ranks local models on **coding, reasoning, writing, agentic/tool-use, instruction-
following, and long-context**, plus **speed** (decode/prefill tok/s, cold-load,
resident RAM). Pure standard-library Python — no `pip install` needed. Drives
**Ollama** over its HTTP API. Full rationale in [`PLAN.md`](PLAN.md).

## Requirements
- Ollama running (`ollama serve`; check: `curl localhost:11434/api/version`)
- Python 3.9+ (stdlib only)
- Models pulled via `ollama pull <tag>` (see [`config/models.json`](config/models.json))

## Quick start
```bash
cd llm-bench

# smoke test: 1 task/category on one model
python3 run.py --models gpt-oss:20b --limit 1 --reps 1

# full run on the current roster (skips models you haven't pulled)
python3 run.py --models-file config/run_roster.txt

# include writing (LLM-as-judge); pulls missing models first
python3 run.py --models-file config/run_roster.txt --judge --pull

# best writing judge: use Claude instead of a local model
export ANTHROPIC_API_KEY=sk-...
python3 run.py --models gpt-oss:20b,qwen3-coder:30b --judge
```
Reports (markdown + JSON) are written to `reports/`; full model outputs to
`store/raw_outputs/<model>/` so writing can be re-judged without re-inferring.

## Flags
| Flag | Meaning |
|---|---|
| `--models a,b` / `--models-file PATH` | models to test (Ollama tags) |
| `--suite PATH` | suite config (default `config/suite.json`) |
| `--only c1,c2` | restrict to categories |
| `--limit N` | cap tasks/category (smoke testing) |
| `--judge` / `--judge-model TAG` | enable writing judge / pick judge model |
| `--ctx N` | override context window |
| `--reps N` | speed-probe reps (default 3; `0` skips speed) |
| `--pull` | `ollama pull` any missing models first |

## Layout
```
config/   suite.json (weights, ctx, think), models.json (roster), judge.json, run_roster.txt
tasks/    <category>/tasks.jsonl  — add lines to extend; see types below
bench/    ollama_client.py · loader.py · scorers.py · judge.py · report.py
run.py    orchestrator CLI
store/    raw_outputs/<model>/<task>.txt
reports/  report_<ts>.md · results_<ts>.json
```

## Adding tasks
Append a JSON line to the right file. Supported `type`s and key fields:
- `code_function` — `prompt`, `tests` (python asserts), `timeout`
- `numeric` — `prompt`, `answer`, `tol`
- `mc` — `prompt`, `choices` {A:..}, `answer`
- `ifeval` — `prompt`, `constraints` [{type,...}] (max_words, exact_bullets,
  contains_times, no_commas, valid_json, json_keys_sorted, starts_with, ends_with, …)
- `tool_call` — `tools`, `prompt`, `expected` ({name,arguments} or `null` for should-not-call)
- `json_schema` — `prompt`, `schema` {required:[], types:{}}
- `exact` — `prompt` or long-context `gen` {filler, facts[]}, `question`, `answer`, `aliases`, `min_ctx`
- `judge_pairwise` (writing) — `prompt`, `rubric`, `baseline`

## Notes / limitations
- Coding tasks execute model-generated code in a temp dir with a timeout (no network);
  tasks are self-contained algorithmics. Review before running untrusted task files.
- The starter suite (~22 tasks) is intentionally small and skews easy for top models —
  it discriminates speed and the hard edges (JSON types, should-not-call, writing).
  Scale up with the public-set slices listed in `PLAN.md` §4 for finer capability ranking.
- For paper-grade speed, re-check the top models under `llama-bench`/`mlx_lm` (`PLAN.md` §2).
