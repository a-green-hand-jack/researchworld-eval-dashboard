"""Extract a model x task score matrix from the MTEB results repo (pinned commit).
Usage: python -I extract_mteb.py <results_dir> <out_dir>
For each (model, task): main_score of the test split (fallback validation, dev),
averaged over hf_subsets (x100). Tasks with several subsets: only the modal subset
signature across models is kept (others -> NaN) so that scores are comparable.
Per model only the revision directory with most task files is used."""
import sys, os, json, collections
import numpy as np, pandas as pd
res, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
SPLITS = ["test", "validation", "dev"]
recs = {}   # (model, task) -> (signature, score, split)
meta = {}
for m in sorted(os.listdir(res)):
    mp = os.path.join(res, m)
    if not os.path.isdir(mp): continue
    revs = [r for r in os.listdir(mp) if os.path.isdir(os.path.join(mp, r))]
    best = max(revs, key=lambda r: (len(os.listdir(os.path.join(mp, r))), r))
    d = os.path.join(mp, best)
    mm = os.path.join(d, "model_meta.json")
    if os.path.exists(mm):
        j = json.load(open(mm))
        meta[m] = dict(n_parameters=j.get("n_parameters"), release_date=j.get("release_date"),
                       embed_dim=j.get("embed_dim"), open_weights=j.get("open_weights"))
    for f in os.listdir(d):
        if f == "model_meta.json" or not f.endswith(".json"): continue
        try: j = json.load(open(os.path.join(d, f)))
        except Exception: continue
        if "scores" not in j: continue
        sc = j["scores"]
        sp = next((s for s in SPLITS if s in sc), None)
        if sp is None: continue
        ents = sc[sp]
        try:
            vals = [float(e["main_score"]) for e in ents]
        except Exception: continue
        sig = tuple(sorted(str(e.get("hf_subset", "default")) for e in ents))
        recs[(m, f[:-5])] = (sig, float(np.mean(vals)) * 100, sp)
# modal signature per task
bytask = collections.defaultdict(collections.Counter)
for (m, t), (sig, s, sp) in recs.items(): bytask[t][(sig, sp)] += 1
modal = {t: c.most_common(1)[0][0] for t, c in bytask.items()}
rows = [(m, t, s) for (m, t), (sig, s, sp) in recs.items() if (sig, sp) == modal[t]]
df = pd.DataFrame(rows, columns=["model", "task", "score"])
M = df.pivot(index="model", columns="task", values="score")
M.to_csv(os.path.join(out, "mteb_full_matrix.csv"))
pd.DataFrame(meta).T.to_csv(os.path.join(out, "mteb_model_meta.csv"))
print("matrix", M.shape, "obs", M.notna().sum().sum(), "density", M.notna().mean().mean())
