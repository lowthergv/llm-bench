"""Thin Ollama HTTP client with clean per-phase timing capture.

Ollama's /api/chat returns nanosecond timing fields:
  prompt_eval_count / prompt_eval_duration  -> prefill (prompt) throughput
  eval_count        / eval_duration         -> decode (generation) throughput
  load_duration                             -> cold model-load cost (kept separate)
"""
import json
import statistics
import time
import urllib.error
import urllib.request

HOST = "http://localhost:11434"


def _post(path, payload, timeout=900):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(HOST + path, data=data,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get(path, timeout=30):
    with urllib.request.urlopen(HOST + path, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def server_up():
    try:
        _get("/api/version", timeout=4)
        return True
    except Exception:
        return False


def have_model(tag):
    """True if `tag` is already pulled locally."""
    try:
        listed = _get("/api/tags").get("models", [])
    except Exception:
        return False
    names = {m.get("name") for m in listed}
    names |= {m.get("name", "").split(":")[0] for m in listed}
    return tag in names or (tag + ":latest") in names or tag.split(":")[0] in names


def _derive_timing(r):
    """Pull tok/s and latencies out of an Ollama response dict."""
    def tps(count, dur_ns):
        if not count or not dur_ns:
            return None
        return count / (dur_ns / 1e9)
    out = {
        "load_s": (r.get("load_duration") or 0) / 1e9,
        "prompt_tokens": r.get("prompt_eval_count"),
        "gen_tokens": r.get("eval_count"),
        "prefill_tps": tps(r.get("prompt_eval_count"), r.get("prompt_eval_duration")),
        "decode_tps": tps(r.get("eval_count"), r.get("eval_duration")),
        "total_s": (r.get("total_duration") or 0) / 1e9,
    }
    # TTFT (warm) ~ time spent in prefill; cold also includes load.
    pe = r.get("prompt_eval_duration") or 0
    out["ttft_s"] = pe / 1e9
    return out


def chat(model, messages, *, temperature=0.0, num_ctx=8192, seed=7,
         num_predict=1024, think=False, timeout=900):
    """One non-streamed chat turn. Returns (text, timing_dict)."""
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_ctx": num_ctx,
            "seed": seed,
            "num_predict": num_predict,
        },
    }
    if think is not None:
        payload["think"] = think
    try:
        r = _post("/api/chat", payload, timeout=timeout)
    except urllib.error.HTTPError as e:
        # Older servers / non-thinking models may reject "think"; retry once.
        if "think" in payload:
            payload.pop("think")
            r = _post("/api/chat", payload, timeout=timeout)
        else:
            raise e
    msg = r.get("message") or {}
    text = msg.get("content") or ""
    if not text.strip():  # thinking models may leave content empty; salvage the answer
        text = msg.get("thinking") or ""
    return text, _derive_timing(r)


def resident_gb(model):
    """Resident memory of a loaded model (GB), from /api/ps. None if not loaded."""
    try:
        for m in _get("/api/ps").get("models", []):
            if m.get("name") == model or m.get("name", "").split(":")[0] == model.split(":")[0]:
                vram = m.get("size_vram") or m.get("size") or 0
                return round(vram / (1024 ** 3), 2)
    except Exception:
        pass
    return None


def speed_probe(model, *, reps=3, num_predict=256, num_ctx=8192):
    """Dedicated throughput probe with a fixed prompt: 1 warm-up + `reps` timed runs."""
    prompt = ("Write a clear, self-contained 200-word explanation of how a "
              "hash map works, including collision handling.")
    msgs = [{"role": "user", "content": prompt}]
    # warm-up (loads model; discarded)
    _, warm = chat(model, msgs, num_predict=64, num_ctx=num_ctx)
    load_s = warm.get("load_s", 0.0)
    decode, prefill = [], []
    for _ in range(reps):
        _, t = chat(model, msgs, num_predict=num_predict, num_ctx=num_ctx)
        if t.get("decode_tps"):
            decode.append(t["decode_tps"])
        if t.get("prefill_tps"):
            prefill.append(t["prefill_tps"])
        time.sleep(0.2)
    def agg(xs):
        if not xs:
            return None
        return {
            "mean": round(statistics.mean(xs), 2),
            "stdev": round(statistics.stdev(xs), 2) if len(xs) > 1 else 0.0,
            "min": round(min(xs), 2),
            "max": round(max(xs), 2),
        }
    return {
        "cold_load_s": round(load_s, 2),
        "decode_tps": agg(decode),
        "prefill_tps": agg(prefill),
        "resident_gb": resident_gb(model),
        "reps": reps,
    }
