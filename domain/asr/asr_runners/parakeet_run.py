"""Parakeet-MLX runner for the ASR benchmark. Loads the model once, warms up, then times
steady-state inference per clip. Prints a single JSON object to stdout.
Invoked by benchmark/asr.mjs via: uv run --python 3.12 --with parakeet-mlx python <this> <wavs...>"""
import sys, json, time

MODEL = "mlx-community/parakeet-tdt-0.6b-v3"
wavs = sys.argv[1:]
try:
    from parakeet_mlx import from_pretrained
    t = time.time()
    model = from_pretrained(MODEL)
    _ = model.transcribe(wavs[0])  # warmup (graph build / first-run cost)
    load_ms = (time.time() - t) * 1000.0
    results = []
    for w in wavs:
        t0 = time.time()
        r = model.transcribe(w)
        results.append({"wav": w, "ms": (time.time() - t0) * 1000.0, "text": r.text})
    print(json.dumps({"model": MODEL, "load_ms": load_ms, "results": results}))
except Exception as e:
    print(json.dumps({"model": MODEL, "error": f"{type(e).__name__}: {e}"}))
