"""Download the Open LLM Leaderboard `contents` parquet at the pinned dataset revision and check its SHA-256 against the one recorded
when the data were first processed (data/processed/manifest.json).  Usage: python3 src/fetch_ollb.py OUT_PARQUET"""
import hashlib, sys, urllib.request, pathlib
REV = "9c09a7cae43334062a82cb164f2ef255013dafa2"
URL = f"https://huggingface.co/datasets/open-llm-leaderboard/contents/resolve/{REV}/data/train-00000-of-00001.parquet"
EXPECT = "f13a7061e63133bc8745d89f8c7a56148584940ede22d3b27e21cad1e078dca5"
out = pathlib.Path(sys.argv[1]); out.parent.mkdir(parents=True, exist_ok=True)
b = urllib.request.urlopen(URL, timeout=120).read(); h = hashlib.sha256(b).hexdigest(); out.write_bytes(b)
print(out, len(b), "bytes sha256", h, "OK" if h == EXPECT else f"MISMATCH (expected {EXPECT})")
sys.exit(0 if h == EXPECT else 1)
