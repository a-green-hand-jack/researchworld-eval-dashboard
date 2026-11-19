"""Download the per-model evaluation JSONs of open-llm-leaderboard/results (pinned commit) and keep the sub-task scores.
Usage: python3 src/fetch_ollb_results.py OUT_DIR     (needs network; ~10.5k small files, 32 threads)
Writes OUT_DIR/raw/<org>/<model>/<file>.json (full files) and OUT_DIR/MANIFEST.sha256.json (path -> sha256).
"""
import sys, json, hashlib, pathlib, urllib.request, urllib.parse, concurrent.futures as cf
SHA = "aa81ecc38fdc5708254b833923368970efdf5ef5"; REPO = "open-llm-leaderboard/results"
out = pathlib.Path(sys.argv[1]); (out / "raw").mkdir(parents=True, exist_ok=True)

def listing():
    url = f"https://huggingface.co/api/datasets/{REPO}/tree/{SHA}?recursive=true&expand=false&limit=1000"; files = []
    while url:
        r = urllib.request.urlopen(url, timeout=120); files += [e["path"] for e in json.load(r) if e["type"] == "file"]
        nxt = [p for p in (r.headers.get("Link") or "").split(",") if 'rel="next"' in p]
        url = nxt[0].split(";")[0].strip(" <>") if nxt else None
    return [f for f in files if f.endswith(".json")]

def get(path):
    dest = out / "raw" / path
    if dest.exists(): return path, hashlib.sha256(dest.read_bytes()).hexdigest()
    url = f"https://huggingface.co/datasets/{REPO}/resolve/{SHA}/" + urllib.parse.quote(path)
    for k in range(4):
        try:
            b = urllib.request.urlopen(url, timeout=60).read(); break
        except Exception as e:
            if k == 3: return path, None
    dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes(b); return path, hashlib.sha256(b).hexdigest()

files = listing(); print(len(files), "json files", flush=True)
with cf.ThreadPoolExecutor(32) as ex: man = dict(ex.map(get, files))
fail = [p for p, h in man.items() if h is None]; print("failed", len(fail), fail[:5])
json.dump({"commit": SHA, "files": man}, open(out / "MANIFEST.sha256.json", "w"))
