"""mlx-whisper runner (large-v3-turbo) for the ASR benchmark. Loads once (module caches the
model after the first call), warms up, then times steady-state inference per clip.
Invoked via: uv run --python 3.12 --with mlx-whisper python <this> <wavs...>"""
import sys, json, time

MODEL = "mlx-community/whisper-large-v3-turbo"
wavs = sys.argv[1:]
try:
    import mlx_whisper
    def tx(w):
        return mlx_whisper.transcribe(w, path_or_hf_repo=MODEL, language="en", verbose=False)
    t = time.time()
    _ = tx(wavs[0])  # warmup + model load
    load_ms = (time.time() - t) * 1000.0
    results = []
    for w in wavs:
        t0 = time.time()
        out = tx(w)
        results.append({"wav": w, "ms": (time.time() - t0) * 1000.0, "text": out.get("text", "")})
    print(json.dumps({"model": MODEL, "load_ms": load_ms, "results": results}))
except Exception as e:
    print(json.dumps({"model": MODEL, "error": f"{type(e).__name__}: {e}"}))
