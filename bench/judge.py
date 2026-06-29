"""Pairwise LLM-as-judge for writing tasks.

Method (from the blueprint): compare the candidate answer against a frozen
baseline, two-game position swap to cancel position bias, average win/tie/loss.

Judge backend:
  * If ANTHROPIC_API_KEY is set -> use a strong Claude judge (recommended;
    different family from every local contestant).
  * Else -> use a local Ollama judge model (set in config/judge.json).
Never let a model judge its own family: run.py skips those pairs.
"""
import json
import os
import re
import urllib.request

from . import ollama_client

FAMILIES = ["qwen", "gemma", "mistral", "magistral", "devstral", "codestral",
            "llama", "deepseek", "phi", "glm", "gpt-oss", "seed", "minicpm", "lfm"]


def family_of(tag):
    t = tag.lower()
    for fam in FAMILIES:
        if fam in t:
            return fam
    return t.split(":")[0]


def same_family(a, b):
    return family_of(a) == family_of(b)


_SYS = ("You are an impartial writing evaluator. Compare two answers (A and B) to "
        "the same prompt against the given rubric. Judge quality only — ignore length "
        "and which is listed first. Respond with one short reason, then a final line "
        "exactly: 'Verdict: A' or 'Verdict: B' or 'Verdict: tie'.")


def _judge_prompt(task, ans_a, ans_b):
    return (f"PROMPT:\n{task['prompt']}\n\nRUBRIC:\n{task.get('rubric', 'overall quality')}\n\n"
            f"ANSWER A:\n{ans_a}\n\nANSWER B:\n{ans_b}\n\n"
            "Which answer better satisfies the rubric?")


def _ask_anthropic(messages_text, model="claude-sonnet-4-6"):
    key = os.environ["ANTHROPIC_API_KEY"]
    body = json.dumps({
        "model": model,
        "max_tokens": 512,
        "system": _SYS,
        "messages": [{"role": "user", "content": messages_text}],
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=body,
        headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read())
    return "".join(b.get("text", "") for b in data.get("content", []))


def _ask(judge_model, prompt):
    if os.environ.get("ANTHROPIC_API_KEY"):
        return _ask_anthropic(prompt)
    text, _ = ollama_client.chat(
        judge_model,
        [{"role": "system", "content": _SYS}, {"role": "user", "content": prompt}],
        temperature=0.0, num_predict=400, think=False)
    return text


def _verdict(text):
    m = re.search(r"verdict\s*[:\-]?\s*(A|B|tie)", text, re.IGNORECASE)
    return m.group(1).lower() if m else "tie"


def judge_pairwise(judge_model, task, candidate):
    """Returns dict {score: 0..1, detail}. score = candidate win-rate over 2 games."""
    baseline = task["baseline"]
    # Game 1: candidate=A, baseline=B
    v1 = _verdict(_ask(judge_model, _judge_prompt(task, candidate, baseline)))
    # Game 2: swap — baseline=A, candidate=B
    v2 = _verdict(_ask(judge_model, _judge_prompt(task, baseline, candidate)))

    def pts(v, cand_is_a):
        if v == "tie":
            return 0.5
        cand_won = (v == "a") if cand_is_a else (v == "b")
        return 1.0 if cand_won else 0.0

    score = (pts(v1, True) + pts(v2, False)) / 2.0
    return {"score": score, "detail": f"g1={v1} g2={v2} -> {score}",
            "judge": "claude" if os.environ.get("ANTHROPIC_API_KEY") else judge_model}
