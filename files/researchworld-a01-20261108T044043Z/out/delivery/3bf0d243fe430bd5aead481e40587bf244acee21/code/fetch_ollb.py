"""Download the Open LLM Leaderboard `contents` parquet at the pinned dataset commit and verify its SHA-256.
Usage: python3 code/fetch_ollb.py OUT_DIR
"""
import hashlib, sys, urllib.request, pathlib
SHA = "9c09a7cae43334062a82cb164f2ef255013dafa2"
URL = f"https://huggingface.co/datasets/open-llm-leaderboard/contents/resolve/{SHA}/data/train-00000-of-00001.parquet"
EXPECT = "f13a7061e63133bc8745d89f8c7a56148584940ede22d3b27e21cad1e078dca5"
out = pathlib.Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
b = urllib.request.urlopen(URL, timeout=120).read()
h = hashlib.sha256(b).hexdigest()
assert h == EXPECT, f"checksum mismatch: {h}"
(out / "train-00000-of-00001.parquet").write_bytes(b); print("ok", h)
