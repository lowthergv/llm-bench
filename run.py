#!/usr/bin/env python3
"""Local-LLM benchmark orchestrator (Ollama primary runtime).

Usage:
  python3 run.py --models gpt-oss:20b,qwen3-coder:30b
  python3 run.py --models-file config/run_roster.txt --judge
  python3 run.py --models gpt-oss:20b --only coding,reasoning --limit 2   # smoke test

Flags:
  --models a,b,c        comma-separated Ollama tags to benchmark
  --models-file PATH    file with one tag per line (# comments ok)
  --suite PATH          suite config (default config/suite.json)
  --only c1,c2          restrict to these categories
  --limit N             cap tasks per category (smoke testing)
  --judge               enable LLM-as-judge scoring for writing
  --judge-model TAG     judge model (default from config/judge.json)
  --ctx N               override default context window
  --reps N              speed-probe repetitions (default 3); 0 = skip speed probe
  --pull                pull any missing models before running
  --out DIR             report output dir (default reports/)
"""
import argparse
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bench import ollama_client, scorers, judge, loader, report  # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))


def sanitize(tag):
    return tag.replace("/", "_").replace(":", "_")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--models", default="")
    p.add_argument("--models-file", default="")
    p.add_argument("--suite", default="config/suite.json")
    p.add_argument("--only", default="")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--judge", action="store_true")
    p.add_argument("--judge-model", default="")
    p.add_argument("--ctx", type=int, default=0)
    p.add_argument("--reps", type=int, default=3)
    p.add_argument("--pull", action="store_true")
    p.add_argument("--out", default="reports")
    return p.parse_args()


def resolve_models(args):
    models = []
    if args.models:
        models += [m.strip() for m in args.models.split(",") if m.strip()]
    if args.models_file:
        with open(os.path.join(ROOT, args.models_file)) as f:
            for line in f:
                line = line.split("#")[0].strip()
                if line:
                    models.append(line)
    return models


def main():
    args = parse_args()
    if not ollama_client.server_up():
        sys.exit("Ollama server not reachable at localhost:11434. Run: ollama serve")

    models = resolve_models(args)
    if not models:
        sys.exit("No models given. Use --models a,b or --models-file PATH.")

    only = set(c.strip() for c in args.only.split(",") if c.strip()) or None
    defaults, cats = loader.load_suite(args.suite, limit=(args.limit or None), only=only)
    if args.ctx:
        defaults["num_ctx"] = args.ctx
    weights = {c: cfg.get("weight", 0) for c, cfg, _ in cats}
    n_tasks = sum(len(tasks) for _, _, tasks in cats)

    judge_cfg = loader.load_json("config/judge.json")
    judge_model = args.judge_model or judge_cfg.get("local_judge", "gpt-oss:20b")

    raw_dir = os.path.join(ROOT, "store", "raw_outputs")
    records, speed = [], {}

    for model in models:
        if not ollama_client.have_model(model):
            if args.pull:
                print(f"[pull] {model} ...", flush=True)
                subprocess.run(["ollama", "pull", model], check=False)
            if not ollama_client.have_model(model):
                print(f"[skip] {model} not installed (use --pull or `ollama pull {model}`)")
                continue

        print(f"\n=== {model} ===", flush=True)
        if args.reps > 0:
            print("  speed probe ...", flush=True)
            try:
                speed[model] = ollama_client.speed_probe(model, reps=args.reps,
                                                         num_ctx=defaults.get("num_ctx", 8192))
                sp = speed[model]
                d = (sp.get("decode_tps") or {}).get("mean")
                print(f"  decode ~{d} tok/s · RAM {sp.get('resident_gb')} GB · "
                      f"cold-load {sp.get('cold_load_s')} s", flush=True)
            except Exception as e:
                print(f"  speed probe failed: {e}")
                speed[model] = {}

        for cat, cfg, tasks in cats:
            mdir = os.path.join(raw_dir, sanitize(model))
            os.makedirs(mdir, exist_ok=True)
            done = 0
            for task in tasks:
                messages, opts = loader.build_messages(task, cfg, defaults)
                t0 = time.time()
                try:
                    text, timing = ollama_client.chat(model, messages, **opts)
                except Exception as e:
                    records.append({"model": model, "category": cat,
                                    "task_id": task["id"], "type": task["type"],
                                    "score": 0.0, "detail": f"infer error: {e}"})
                    continue
                with open(os.path.join(mdir, f"{task['id']}.txt"), "w") as f:
                    f.write(text)

                if task["type"] == "judge_pairwise":
                    if not args.judge:
                        res = {"score": None, "detail": "writing not judged (pass --judge)"}
                    elif judge.same_family(judge_model, model):
                        res = {"score": None,
                               "detail": f"skipped: judge {judge_model} same family as {model}"}
                    else:
                        try:
                            res = judge.judge_pairwise(judge_model, task, text)
                        except Exception as e:
                            res = {"score": None, "detail": f"judge error: {e}"}
                else:
                    res = scorers.score(task, text)

                records.append({
                    "model": model, "category": cat, "task_id": task["id"],
                    "type": task["type"], "score": res["score"],
                    "detail": res.get("detail", ""),
                    "decode_tps": (timing or {}).get("decode_tps"),
                    "wall_s": round(time.time() - t0, 2),
                })
                done += 1
            scored = [r for r in records if r["model"] == model and r["category"] == cat
                      and r["score"] is not None]
            mean = sum(r["score"] for r in scored) / len(scored) if scored else None
            print(f"  {cat:12s} {done:2d} tasks · "
                  + (f"{mean*100:.1f}%" if mean is not None else "not scored"), flush=True)

    summary = report.aggregate(records, speed, weights)
    meta = {
        "host": "MacBook Pro M4 Pro · 48GB",
        "runtime": "Ollama 0.30.6 (MLX Metal backend)",
        "date": time.strftime("%Y-%m-%d %H:%M"),
        "ctx": defaults.get("num_ctx", 8192),
        "temp": defaults.get("temperature", 0.0),
        "judge": ("Claude API" if os.environ.get("ANTHROPIC_API_KEY")
                  else (judge_model if args.judge else "none (writing unscored)")),
        "n_tasks": n_tasks,
    }
    os.makedirs(os.path.join(ROOT, args.out), exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    md = os.path.join(ROOT, args.out, f"report_{ts}.md")
    js = os.path.join(ROOT, args.out, f"results_{ts}.json")
    report.save(summary, meta, weights, records, md, js)

    print("\n" + "=" * 60)
    print(report.render_markdown(summary, meta, weights))
    print("=" * 60)
    print(f"\nSaved: {md}\n       {js}")


if __name__ == "__main__":
    main()
