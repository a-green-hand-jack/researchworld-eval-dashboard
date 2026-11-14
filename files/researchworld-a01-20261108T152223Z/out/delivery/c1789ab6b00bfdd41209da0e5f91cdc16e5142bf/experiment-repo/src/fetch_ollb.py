"""Download the Open LLM Leaderboard `contents` parquet at the pinned dataset commit and print its SHA-256.
Usage: python3 src/fetch_ollb.py OUTDIR
"""
import hashlib, sys, urllib.request, pathlib
SHA = "9c09a7cae43334062a82cb164f2ef255013dafa2"
URL = f"https://huggingface.co/datasets/open-llm-leaderboard/contents/resolve/{SHA}/data/train-00000-of-00001.parquet"
out = pathlib.Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
p = out / "train-00000-of-00001.parquet"
if not p.exists(): p.write_bytes(urllib.request.urlopen(URL, timeout=120).read())
print(p, hashlib.sha256(p.read_bytes()).hexdigest())
