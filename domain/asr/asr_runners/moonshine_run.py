"""Moonshine (ONNX) runner for the ASR benchmark. base model. Loads once, warms up, times
steady-state inference per clip.
Invoked via: uv run --python 3.12 --with moonshine-onnx python <this> <wavs...>"""
import sys, json, time

MODEL = "moonshine/base"
wavs = sys.argv[1:]
try:
    from moonshine_onnx import transcribe
    def text_of(out):
        if isinstance(out, (list, tuple)):
            return out[0] if out else ""
        return str(out)
    t = time.time()
    _ = transcribe(wavs[0], MODEL)  # warmup + model load
    load_ms = (time.time() - t) * 1000.0
    results = []
    for w in wavs:
        t0 = time.time()
        out = transcribe(w, MODEL)
        results.append({"wav": w, "ms": (time.time() - t0) * 1000.0, "text": text_of(out)})
    print(json.dumps({"model": MODEL, "load_ms": load_ms, "results": results}))
except Exception as e:
    print(json.dumps({"model": MODEL, "error": f"{type(e).__name__}: {e}"}))
