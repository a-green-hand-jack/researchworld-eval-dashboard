"""Fetch the per-model lm-eval result files of the OLLB `results` dataset (pinned commit) for the top-N models of the processed
leaderboard table (rank by the mean of the six normalised scores, same slice as `ollb_top500`), keep every file of every model, and
write one JSON of leaf-task accuracies per file.  Needs network.
Usage: python3 code/fetch_ollb_leaves.py OUTDIR [N=500]
Output: OUTDIR/files.csv (model, file, size, ok) and OUTDIR/leaves.jsonl (one line per file: model, file, the 'results' block reduced
to the metrics used)."""
import sys, json, time, hashlib, pathlib, urllib.request, urllib.error, urllib.parse, concurrent.futures as cf
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mti.data import load
C = "aa81ecc38fdc5708254b833923368970efdf5ef5"
BASE = "https://huggingface.co"
out = pathlib.Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
N = int(sys.argv[2]) if len(sys.argv) > 2 else 500
X, names, _, _ = load("ollb")
order = np.argsort(-X.mean(axis=1), kind="stable")[:N]
models = [names[i] for i in order]

def get(url, tries=8):
    for k in range(tries):
        try: return urllib.request.urlopen(url, timeout=90).read()
        except urllib.error.HTTPError as e:
            err = e; time.sleep(float(e.headers.get("Retry-After", 0) or 0) + 5 * (k + 1) if e.code == 429 else 1)     # the hub rate-limits: back off
        except Exception as e: err = e; time.sleep(1)
    raise err

def one(m):
    try:
        tree = json.loads(get(f"{BASE}/api/datasets/open-llm-leaderboard/results/tree/{C}/{urllib.parse.quote(m)}"))
        rows = []
        for f in tree:
            if not f["path"].endswith(".json"): continue
            raw = get(f"{BASE}/datasets/open-llm-leaderboard/results/resolve/{C}/{urllib.parse.quote(f['path'])}")
            r = json.loads(raw)["results"]
            keep = {k: {a: b for a, b in v.items() if "stderr" not in a and a != "alias"} for k, v in r.items()}
            rows.append({"model": m, "file": f["path"].split("/")[-1], "size": f["size"], "results": keep,
                         "_src": {"path": f["path"], "git_oid": f.get("oid"), "sha256_raw": hashlib.sha256(raw).hexdigest(), "bytes_raw": len(raw)}})
        return m, rows, None
    except Exception as e:
        return m, [], repr(e)

res = {}
with cf.ThreadPoolExecutor(4) as ex:
    for m, rows, err in ex.map(one, models): res[m] = (rows, err)
man = []
with open(out / "leaves.jsonl", "w") as fh:
    for m in models:
        for r in res[m][0]:
            src = r.pop("_src"); line = json.dumps(r)
            fh.write(line + "\n")
            man.append(dict(model=m, file=r["file"], path=src["path"], size_tree=r["size"], bytes_downloaded=src["bytes_raw"], git_oid=src["git_oid"],
                            sha256_raw_file=src["sha256_raw"], sha256_reduced_record=hashlib.sha256(line.encode()).hexdigest()))
pd.DataFrame(man).to_csv(out / "source_manifest.csv", index=False)       # every retrieved file, with the digest of the raw download and of its reduced record
print("leaves.jsonl sha256", hashlib.sha256(open(out / "leaves.jsonl", "rb").read()).hexdigest())
pd.DataFrame([{"model": m, "n_files": len(res[m][0]), "error": res[m][1]} for m in models]).to_csv(out / "files.csv", index=False)
print("models", len(models), "with no file", sum(1 for m in models if not res[m][0]), "errors", sum(1 for m in models if res[m][1]))
