"""Deterministic scorers. Each returns dict: {score: 0..1, detail: str}.

Dispatch is by task["type"]:
  code_function  -> run extracted code against hidden tests (pass@1)
  numeric        -> tolerant numeric exact-match
  mc             -> multiple-choice letter match
  ifeval         -> programmatic constraint checks (fraction satisfied)
  tool_call      -> correct tool name + args, incl. "should-not-call"
  json_schema    -> schema-valid rate + required-field/type checks
  exact          -> answer string present (used by long-context)
Writing (judge_pairwise) is handled in judge.py, not here.
"""
import json
import os
import re
import subprocess
import tempfile

# ----------------------------- extraction helpers -----------------------------

def extract_code(text):
    m = re.search(r"```(?:python|py)?\s*\n(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1)
    return text


def _final_span(text):
    """Text after a 'final answer' marker, else the whole text."""
    m = re.search(r"final answer\s*[:\-]?\s*(.+)", text, re.IGNORECASE | re.DOTALL)
    return m.group(1) if m else text


def extract_number(text):
    span = _final_span(text)
    nums = re.findall(r"-?\d[\d,]*\.?\d*", span)
    if not nums:
        nums = re.findall(r"-?\d[\d,]*\.?\d*", text)
    if not nums:
        return None
    try:
        return float(nums[-1].replace(",", ""))
    except ValueError:
        return None


def extract_letter(text):
    span = _final_span(text)
    m = re.search(r"\b([A-J])\b", span)
    if not m:
        m = re.search(r"\b([A-J])\b", text[::-1])  # last letter fallback
        if m:
            return m.group(1)
    return m.group(1).upper() if m else None


def extract_json(text):
    m = re.search(r"```(?:json)?\s*\n(.*?)```", text, re.DOTALL | re.IGNORECASE)
    candidate = m.group(1) if m else text
    # try whole, then first balanced {...}
    for blob in (candidate, _first_balanced(candidate), _first_balanced(text)):
        if not blob:
            continue
        try:
            return json.loads(blob)
        except Exception:
            continue
    return None


def _first_balanced(text):
    start = text.find("{")
    if start < 0:
        return None
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return None


# ----------------------------- code execution -----------------------------

def score_code(task, output):
    code = extract_code(output)
    program = code + "\n\n" + task["tests"] + "\nprint('__OK__')\n"
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "sol.py")
        with open(path, "w") as f:
            f.write(program)
        try:
            r = subprocess.run(["python3", path], cwd=d, capture_output=True,
                               text=True, timeout=task.get("timeout", 15),
                               env={"PATH": os.environ.get("PATH", "")})
        except subprocess.TimeoutExpired:
            return {"score": 0.0, "detail": "timeout"}
        ok = r.returncode == 0 and "__OK__" in r.stdout
        err = (r.stderr or "").strip().splitlines()
        return {"score": 1.0 if ok else 0.0,
                "detail": "pass" if ok else ("fail: " + (err[-1] if err else "no output"))}


# ----------------------------- numeric / mc -----------------------------

def score_numeric(task, output):
    got = extract_number(output)
    if got is None:
        return {"score": 0.0, "detail": "no number parsed"}
    want = float(task["answer"])
    tol = float(task.get("tol", 1e-6))
    ok = abs(got - want) <= tol or (want != 0 and abs(got - want) / abs(want) <= 1e-4)
    return {"score": 1.0 if ok else 0.0, "detail": f"got {got} want {want}"}


def score_mc(task, output):
    got = extract_letter(output)
    want = str(task["answer"]).upper()
    return {"score": 1.0 if got == want else 0.0, "detail": f"got {got} want {want}"}


# ----------------------------- instruction following -----------------------------

def _words(text):
    return re.findall(r"\b[\w']+\b", text)


def _check_constraint(c, text):
    t = c["type"]
    if t == "max_words":
        return len(_words(text)) <= c["n"]
    if t == "min_words":
        return len(_words(text)) >= c["n"]
    if t == "exact_bullets":
        bullets = [ln for ln in text.splitlines() if re.match(r"\s*[-*•]\s+", ln)]
        return len(bullets) == c["n"]
    if t == "line_count":
        return len([ln for ln in text.splitlines() if ln.strip()]) == c["n"]
    if t == "contains_times":
        n = len(re.findall(r"\b" + re.escape(c["word"]) + r"\b", text, re.IGNORECASE))
        return n == c["n"]
    if t == "no_commas":
        return "," not in text
    if t == "valid_json":
        return extract_json(text) is not None
    if t == "json_keys_sorted":
        obj = extract_json(text)
        if not isinstance(obj, dict):
            return False
        keys = list(obj.keys())
        return keys == sorted(keys)
    if t == "starts_with":
        return text.strip().lower().startswith(c["text"].lower())
    if t == "ends_with":
        return text.strip().lower().endswith(c["text"].lower())
    if t == "contains":
        return c["text"].lower() in text.lower()
    if t == "regex":
        return re.search(c["pattern"], text) is not None
    return False


def score_ifeval(task, output):
    cons = task["constraints"]
    results = [(c, _check_constraint(c, output)) for c in cons]
    passed = sum(1 for _, ok in results if ok)
    failed = [c["type"] for c, ok in results if not ok]
    return {"score": passed / len(cons),
            "detail": f"{passed}/{len(cons)} ok" + (f"; failed: {failed}" if failed else "")}


# ----------------------------- agentic: tool call / json -----------------------------

def _norm(v):
    return str(v).strip().lower()


def score_tool_call(task, output):
    obj = extract_json(output)
    if not isinstance(obj, dict):
        return {"score": 0.0, "detail": "no JSON object"}
    tool = obj.get("tool", obj.get("name"))
    expected = task["expected"]
    if expected is None:  # should-NOT-call
        ok = tool in (None, "null", "none", "", False)
        return {"score": 1.0 if ok else 0.0,
                "detail": "correctly declined" if ok else f"called {tool} when none expected"}
    name_ok = _norm(tool) == _norm(expected["name"])
    args = obj.get("arguments", obj.get("args", {})) or {}
    want_args = expected.get("arguments", {})
    args_ok = all(_norm(args.get(k)) == _norm(v) for k, v in want_args.items())
    score = (0.5 if name_ok else 0.0) + (0.5 if (name_ok and args_ok) else 0.0)
    return {"score": score, "detail": f"name_ok={name_ok} args_ok={args_ok}"}


def score_json_schema(task, output):
    obj = extract_json(output)
    schema = task["schema"]
    checks, passed = [], 0
    checks.append(("valid_json", obj is not None and isinstance(obj, dict)))
    if isinstance(obj, dict):
        for k in schema.get("required", []):
            checks.append((f"has:{k}", k in obj))
        type_map = {"string": str, "number": (int, float), "integer": int,
                    "array": list, "object": dict, "boolean": bool}
        for k, ty in schema.get("types", {}).items():
            py = type_map.get(ty, object)
            checks.append((f"type:{k}", k in obj and isinstance(obj[k], py)
                           and not (ty != "boolean" and isinstance(obj[k], bool))))
    passed = sum(1 for _, ok in checks if ok)
    failed = [n for n, ok in checks if not ok]
    return {"score": passed / len(checks),
            "detail": f"{passed}/{len(checks)}" + (f"; failed {failed}" if failed else "")}


# ----------------------------- exact (long-context) -----------------------------

def score_exact(task, output):
    want = str(task["answer"]).strip().lower()
    hay = output.lower()
    aliases = [want] + [str(a).strip().lower() for a in task.get("aliases", [])]
    ok = any(a in hay for a in aliases)
    return {"score": 1.0 if ok else 0.0, "detail": f"answer '{task['answer']}' "
            + ("found" if ok else "not found")}


# ----------------------------- dispatch -----------------------------

_SCORERS = {
    "code_function": score_code,
    "numeric": score_numeric,
    "mc": score_mc,
    "ifeval": score_ifeval,
    "tool_call": score_tool_call,
    "json_schema": score_json_schema,
    "exact": score_exact,
}


def score(task, output):
    fn = _SCORERS.get(task["type"])
    if fn is None:
        return {"score": 0.0, "detail": f"no scorer for type {task['type']}"}
    try:
        return fn(task, output)
    except Exception as e:  # never let one bad task kill a run
        return {"score": 0.0, "detail": f"scorer error: {e}"}
