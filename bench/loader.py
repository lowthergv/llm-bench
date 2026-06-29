"""Load suite + tasks, and turn each task into chat messages + decode options.

Prompt templates are kept here so they stay aligned with the scorers' parsers
(e.g. 'Final answer:' lines, JSON-only tool calls).
"""
import json
import os
import random
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_json(path):
    with open(os.path.join(ROOT, path) if not os.path.isabs(path) else path) as f:
        return json.load(f)


def load_jsonl(path):
    full = os.path.join(ROOT, path) if not os.path.isabs(path) else path
    out = []
    with open(full) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("//"):
                out.append(json.loads(line))
    return out


# ----------------------------- long-context generation -----------------------------

_FILLER = [
    "The quarterly logistics report noted that warehouse throughput remained stable.",
    "Maintenance crews inspected the cooling units on the third floor without incident.",
    "The committee postponed the vote on the cafeteria menu until the next session.",
    "Several interns completed the onboarding module ahead of the posted schedule.",
    "Annual rainfall in the northern district was slightly below the ten-year average.",
    "The archive migration moved roughly four terabytes of records to cold storage.",
    "A new ergonomic chair policy took effect across the east wing offices.",
    "The shuttle service adjusted its morning timetable by ten minutes.",
    "Procurement consolidated three vendor contracts into a single agreement.",
    "The garden volunteers planted native shrubs along the southern fence line.",
]


def build_longcontext(task, seed):
    rng = random.Random(seed + zlib.crc32(task["id"].encode()))
    gen = task["gen"]
    n = gen.get("filler", 120)
    lines = [rng.choice(_FILLER) for _ in range(n)]
    # insert the fact sentence(s) at random positions
    for sent in gen["facts"]:
        pos = rng.randint(n // 6, n - n // 6)
        lines.insert(pos, sent)
    body = "\n".join(f"- {ln}" for ln in lines)
    prompt = ("You are given a long internal document. Read it carefully and answer "
              "the question using only information stated in the document.\n\n"
              "<document>\n" + body + "\n</document>\n\n"
              "Question: " + task["question"] + "\n"
              "Answer with only the value, nothing else.")
    return prompt


# ----------------------------- per-type message builders -----------------------------

def build_messages(task, cat_cfg, defaults):
    t = task["type"]
    user = task.get("prompt", "")

    if task["category"] == "longcontext":
        user = build_longcontext(task, defaults.get("seed", 7))
    elif t == "numeric":
        user = user + "\n\nThink step by step, then end your reply with a line:\nFinal answer: <number>"
    elif t == "mc":
        choices = "\n".join(f"{k}. {v}" for k, v in task["choices"].items())
        user = (user + "\n\nOptions:\n" + choices +
                "\n\nThink step by step, then end with a line:\nFinal answer: <letter>")
    elif t == "code_function":
        user = (user + "\n\nReturn ONLY the complete function inside a single ```python "
                "code block. Do not include tests, examples, or explanation.")
    elif t == "tool_call":
        tools = json.dumps(task["tools"], indent=2)
        user = ("You are a tool-using agent. Available tools:\n" + tools +
                "\n\nUser request: " + user +
                "\n\nRespond with ONLY a single-line JSON object: "
                '{"tool": <tool name as string, or null if no tool fits>, '
                '"arguments": {<arg>: <value>, ...}}. No prose, no code fence.')
    elif t == "json_schema":
        user = (user + "\n\nRespond with ONLY a valid JSON object matching this schema "
                "(required keys and types):\n" + json.dumps(task["schema"]) +
                "\nNo prose, no markdown.")
    # ifeval, writing (judge_pairwise), exact(non-longcontext) use prompt as-is

    messages = []
    if task.get("system"):
        messages.append({"role": "system", "content": task["system"]})
    messages.append({"role": "user", "content": user})

    num_ctx = max(cat_cfg.get("num_ctx", defaults.get("num_ctx", 8192)),
                  task.get("min_ctx", 0))
    opts = {
        "num_ctx": num_ctx,
        "num_predict": task.get("max_tokens", cat_cfg.get("max_tokens", 1024)),
        "think": task.get("think", cat_cfg.get("think", False)),
        "temperature": defaults.get("temperature", 0.0),
        "seed": defaults.get("seed", 7),
    }
    return messages, opts


def load_suite(path, limit=None, only=None):
    """Returns (defaults, [(category, cat_cfg, [tasks])])."""
    suite = load_json(path)
    defaults = suite.get("defaults", {})
    cats = []
    for cat, cfg in suite["categories"].items():
        if only and cat not in only:
            continue
        tasks = load_jsonl(cfg["file"])
        for tk in tasks:
            tk.setdefault("category", cat)
        if limit:
            tasks = tasks[:limit]
        cats.append((cat, cfg, tasks))
    return defaults, cats
