"""Download the pinned Open LLM Leaderboard `results` dataset (commit aa81ecc38fdc5708254b833923368970efdf5ef5): one JSON (~120 KB) per evaluation run,
10 509 files (~1.2 GB in total, NOT the ~14 MB quoted in the data notes), of which only the per-task `results`, `n-samples`, `model_name`, `date` are kept.
Usage: python3 src/fetch_ollb_results.py OUT_DIR  -> OUT_DIR/ollb_results_leaf.jsonl (one line per file: path, sha256 of the raw file, model_name, date,
  results (leaf and group entries), n_samples), resumable.  ~10.5k requests; 32 threads.
"""
import sys, pathlib, json, re, urllib.request, hashlib, threading
from concurrent.futures import ThreadPoolExecutor
C = "aa81ecc38fdc5708254b833923368970efdf5ef5"; H = {"User-Agent": "Mozilla/5.0"}
out = pathlib.Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True); fn = out / "ollb_results_leaf.jsonl"
done = {json.loads(l)["path"] for l in open(fn)} if fn.exists() else set()
url = f"https://huggingface.co/api/datasets/open-llm-leaderboard/results/tree/{C}?recursive=true&limit=1000"; paths = []
while url:
    r = urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=120)
    paths += [o["path"] for o in json.load(r) if o["path"].endswith(".json")]
    m = re.search(r'<([^>]+)>; rel="next"', r.headers.get("Link") or ""); url = m.group(1) if m else None
todo = [p for p in sorted(paths) if p not in done]; print(len(paths), "files,", len(todo), "to fetch", flush=True)
lock = threading.Lock(); f = open(fn, "a"); cnt = [0]
def get(p):
    for k in range(5):
        try:
            b = urllib.request.urlopen(urllib.request.Request(f"https://huggingface.co/datasets/open-llm-leaderboard/results/resolve/{C}/{p}", headers=H), timeout=90).read(); break
        except Exception as e:
            if k == 4: print("FAILED", p, e, flush=True); return
    j = json.loads(b)
    rec = dict(path=p, sha256=hashlib.sha256(b).hexdigest(), model_name=j.get("model_name"), date=j.get("date"), results=j.get("results"), n_samples=j.get("n-samples"))
    with lock:
        f.write(json.dumps(rec) + "\n"); cnt[0] += 1
        if cnt[0] % 500 == 0: f.flush(); print(cnt[0], flush=True)
with ThreadPoolExecutor(32) as ex: list(ex.map(get, todo))
f.close(); print("done", cnt[0])
