"""Download the pinned Open LLM Leaderboard `contents` parquet (commit 9c09a7cae43334062a82cb164f2ef255013dafa2, last updated 2025-03-20).
Usage: python3 src/fetch_ollb.py OUT_DIR   -> OUT_DIR/ollb_contents.parquet (sha256 recorded in data/processed/manifest.json)
"""
import sys, pathlib, urllib.request, hashlib
URL = ("https://huggingface.co/datasets/open-llm-leaderboard/contents/resolve/9c09a7cae43334062a82cb164f2ef255013dafa2/"
       "data/train-00000-of-00001.parquet")
out = pathlib.Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
b = urllib.request.urlopen(URL, timeout=120).read(); (out / "ollb_contents.parquet").write_bytes(b)
print("sha256", hashlib.sha256(b).hexdigest(), len(b), "bytes")
