"""Label-permutation negative control: re-score the cached predictions against permuted gold labels (every configuration is then at chance,
true spread = 0) and measure the optimism the search procedure produces.  Compared with the optimism on the real labels."""
import sys; sys.path.insert(0, "/work/code")
import numpy as np, pandas as pd
from realdata import load_cache
from sel import *; from mc import trial_naive
cache = sys.argv[1] if len(sys.argv) > 1 else "/work/cache/q15"; nrep = int(sys.argv[2]) if len(sys.argv) > 2 else 400
lp, pos, ans, cat = load_cache(cache); N = lp.shape[0]
pred = lp.argmax(-1)
Yreal = (pred == ans[:, None]).astype(np.uint8)
rng = np.random.default_rng(5); rows = []
for n in (50, 100, 200, 400, 800):
    for algo, kw in [("rs", dict(B=8)), ("rs", dict(B=72)), ("sh", dict(B=72)), ("ca", {}), ("mipro", dict(B=40))]:
        for kind in ("real", "perm"):
            for r in range(nrep):
                if kind == "perm":
                    # permute gold labels among items with the same number of options (keeps the label marginal), then re-score
                    perm = np.arange(N)
                    nopt = np.isfinite(lp[:, 0, :]).sum(-1)
                    for k in np.unique(nopt):
                        idx = np.where(nopt == k)[0]; perm[idx] = rng.permutation(idx)
                    Y = (pred == ans[perm][:, None]).astype(np.uint8)
                else:
                    Y = Yreal
                out = trial_naive(Y, n, algo, kw, rng, wr=True)
                R, _, _, t = out["naive"]
                rows.append(dict(n=n, algo=algo, B=kw.get("B", 0), kind=kind, rep=r, report=R, truth=t))
    print(n, flush=True)
pd.DataFrame(rows).to_parquet("/work/results/permnull.parquet")
