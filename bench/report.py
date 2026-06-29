"""Aggregate per-task records into a leaderboard and render markdown + JSON."""
import json
import statistics


def aggregate(records, speed, weights):
    """records: list of {model, category, task_id, score(None ok), ...}
    Returns {model: {cat: mean, ...}, 'overall':x, 'n':n, 'speed':{...}}}."""
    models = {}
    for r in records:
        models.setdefault(r["model"], []).append(r)

    summary = {}
    for model, recs in models.items():
        by_cat = {}
        for r in recs:
            if r.get("score") is None:
                continue
            by_cat.setdefault(r["category"], []).append(r["score"])
        cat_scores = {c: round(statistics.mean(v), 4) for c, v in by_cat.items() if v}
        # weighted overall, renormalized over categories that actually have scores
        present = {c: weights.get(c, 0) for c in cat_scores}
        wsum = sum(present.values()) or 1.0
        overall = sum(cat_scores[c] * present[c] for c in cat_scores) / wsum
        summary[model] = {
            "categories": cat_scores,
            "overall": round(overall, 4),
            "n_scored": sum(len(v) for v in by_cat.values()),
            "speed": speed.get(model, {}),
        }
    return summary


CATS_ORDER = ["coding", "reasoning", "agentic", "writing", "instruction", "longcontext"]


def _fmt(x):
    return "—" if x is None else f"{x*100:4.1f}"


def render_markdown(summary, meta, weights):
    ranked = sorted(summary.items(), key=lambda kv: kv[1]["overall"], reverse=True)
    lines = []
    lines.append(f"# Local LLM Benchmark — Results\n")
    lines.append(f"- **Host:** {meta.get('host')}")
    lines.append(f"- **Runtime:** {meta.get('runtime')}")
    lines.append(f"- **Date:** {meta.get('date')}")
    lines.append(f"- **Context window:** {meta.get('ctx')} tokens · **decode temp:** {meta.get('temp')}")
    lines.append(f"- **Judge:** {meta.get('judge')}")
    lines.append(f"- **Tasks/model:** {meta.get('n_tasks')}\n")

    wstr = " · ".join(f"{c} {weights.get(c,0):.2f}" for c in CATS_ORDER)
    lines.append(f"**Category weights:** {wstr}\n")

    # capability leaderboard
    head = ["Rank", "Model", "**Overall**"] + [c[:5] for c in CATS_ORDER]
    lines.append("## Capability (scores are % ; — = not run/scored)\n")
    lines.append("| " + " | ".join(head) + " |")
    lines.append("|" + "|".join(["---"] * len(head)) + "|")
    for i, (model, s) in enumerate(ranked, 1):
        row = [str(i), f"`{model}`", f"**{s['overall']*100:.1f}**"]
        for c in CATS_ORDER:
            row.append(_fmt(s["categories"].get(c)))
        lines.append("| " + " | ".join(row) + " |")

    # performance table
    lines.append("\n## Performance\n")
    ph = ["Model", "Decode tok/s (mean±sd)", "Prefill tok/s", "Cold load (s)", "Resident RAM (GB)"]
    lines.append("| " + " | ".join(ph) + " |")
    lines.append("|" + "|".join(["---"] * len(ph)) + "|")
    for model, s in ranked:
        sp = s.get("speed") or {}
        d = sp.get("decode_tps") or {}
        p = sp.get("prefill_tps") or {}
        dstr = f"{d.get('mean','—')}±{d.get('stdev','')}" if d else "—"
        pstr = f"{p.get('mean','—')}" if p else "—"
        lines.append(f"| `{model}` | {dstr} | {pstr} | {sp.get('cold_load_s','—')} | {sp.get('resident_gb','—')} |")

    lines.append("\n> Capability and performance are reported separately by design — never collapse them. "
                 "All rows share the same quant tier, context length, runtime, and hardware. "
                 "Decode = generation throughput; prefill measured separately (MLX-backend prefill on M4 "
                 "may trail llama.cpp+FlashAttention). Cold-load excluded from throughput.\n")
    return "\n".join(lines)


def save(summary, meta, weights, records, md_path, json_path):
    with open(md_path, "w") as f:
        f.write(render_markdown(summary, meta, weights))
    with open(json_path, "w") as f:
        json.dump({"meta": meta, "weights": weights, "summary": summary,
                   "records": records}, f, indent=2)
