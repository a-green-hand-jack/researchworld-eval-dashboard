"""How correlated is run-to-run noise across cells? (seeds are the same function of (instance, budget index, run) in every cell,
so cells of one dataset sample the same coalitions / permutation orders for the same instances.)

usage: python3 analysis/seed_correlation.py [raw_dir] [out_dir]
For each dataset, explainer, budget index and pair of models: Spearman rank correlation (robust to the occasional blow-up at small Kernel budgets), over (instance, run, attribute), of the run noise
phi[i,b,r,:] - mean_r phi[i,b,:,:]  between the two models.  Each noise vector is first divided by that instance's reference norm in its own
cell.  'null' = the same statistic with the run index permuted within instance in one model (no shared random numbers).
Also across datasets of equal d (ACS-Income vs GMSC, d = 10; attributes are unrelated, so the correlation is taken on the noise norm
over runs).  Writes tables/seed_correlation.csv.
"""
import glob, itertools, os, sys
import numpy as np, pandas as pd
from scipy.stats import spearmanr

raw = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "results", "raw")
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), "..", "results", "tables")
rng = np.random.RandomState(3)
cells = {}
for f in sorted(glob.glob(f"{raw}/*__ref.npz")):
    tag = os.path.basename(f)[:-len("__ref.npz")]
    if "_logit__" in tag:
        continue
    ds, m = tag.split("__"); cells.setdefault(ds, []).append(m)
res = []
for ds, ms in cells.items():
    for ex in ("kernel", "perm"):
        N = {}
        for m in ms:
            fk = f"{raw}/{ds}__{m}__{ex}.npz"
            if not os.path.exists(fk):
                continue
            phi = np.load(fk)["phi"]; ref = np.load(f"{raw}/{ds}__{m}__ref.npz")["ref"]
            N[m] = (phi - phi.mean(2, keepdims=True)) / np.linalg.norm(ref, axis=1)[:, None, None, None]
        for a, b in itertools.combinations(sorted(N), 2):
            for bi in range(N[a].shape[1]):
                x, y = N[a][:, bi].ravel(), N[b][:, bi].ravel()
                if x.std() < 1e-9 or y.std() < 1e-9:
                    continue            # exact (enumerated) budget: no run noise
                yp = N[b][:, bi].copy()
                for i in range(yp.shape[0]):
                    yp[i] = yp[i][rng.permutation(yp.shape[1])]
                res.append(dict(dataset=ds, explainer=ex, budget_idx=bi, model_a=a, model_b=b,
                                spearman=float(spearmanr(x, y)[0]), spearman_null=float(spearmanr(x, yp.ravel())[0])))
pd.DataFrame(res).to_csv(f"{out}/seed_correlation.csv", index=False)
print(len(res), "rows")
