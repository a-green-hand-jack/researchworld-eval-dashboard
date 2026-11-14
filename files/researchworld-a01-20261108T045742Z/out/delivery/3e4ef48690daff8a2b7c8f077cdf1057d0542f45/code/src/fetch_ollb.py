"""Download the Open LLM Leaderboard `contents` parquet at the pinned commit and print its SHA-256.
Usage: python3 src/fetch_ollb.py OUTDIR
Pinned: open-llm-leaderboard/contents @ 9c09a7cae43334062a82cb164f2ef255013dafa2 (last update 2025-03-20)
"""
import hashlib, sys, pathlib, urllib.request
URL = ("https://huggingface.co/datasets/open-llm-leaderboard/contents/resolve/"
       "9c09a7cae43334062a82cb164f2ef255013dafa2/data/train-00000-of-00001.parquet")
out = pathlib.Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
b = urllib.request.urlopen(URL, timeout=120).read()
(out / "train-00000-of-00001.parquet").write_bytes(b)
print("sha256", hashlib.sha256(b).hexdigest(), len(b), "bytes")
