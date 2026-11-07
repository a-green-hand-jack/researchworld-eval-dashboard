"""Build the model x task score matrix from the pinned MTEB results checkout.
usage: build_mteb.py RESULTS_DIR OUT_CSV
Per model: the revision directory with most task files; per task: main_score (x100)
averaged over hf_subsets of the 'test' split (else validation/dev/train, first present)."""
import json, os, sys, numpy as np, pandas as pd
root, out = sys.argv[1], sys.argv[2]
SPLITS = ["test", "validation", "dev", "train"]
rows = {}
for model in sorted(os.listdir(root)):
    mdir = os.path.join(root, model)
    if not os.path.isdir(mdir): continue
    best = None
    for rev in os.listdir(mdir):
        if not os.path.isdir(os.path.join(mdir, rev)): continue
        files = [f for f in os.listdir(os.path.join(mdir, rev)) if f.endswith(".json") and f != "model_meta.json"]
        if best is None or len(files) > len(best[1]): best = (rev, files)
    if best is None: continue
    rev, files = best
    r = {}
    for f in files:
        try: d = json.load(open(os.path.join(mdir, rev, f)))
        except Exception: continue
        sc = d.get("scores", {})
        for s in SPLITS:
            if s in sc and sc[s]:
                v = [e["main_score"] for e in sc[s] if isinstance(e.get("main_score"), (int, float))]
                if v: r[d.get("task_name", f[:-5])] = 100 * float(np.mean(v)); break
    rows[model] = r
df = pd.DataFrame(rows).T
df.index.name = "model"
df.to_csv(out)
print(df.shape, "observed frac", df.notna().mean().mean())
