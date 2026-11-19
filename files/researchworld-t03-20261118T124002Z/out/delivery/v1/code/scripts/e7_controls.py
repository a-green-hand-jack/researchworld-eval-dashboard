"""E7 controls from the R=20 grids (no new runs).
S1 chance baseline: P(a uniformly random k-set equals the exact top-k set) = 1 / C(nvar, k), averaged over instances of the cell.
S5 global control: global importance g_j = mean over the first n instances of |phi_j|, with one independent run per instance (run r of every instance, r = 0..R-1);
 compare the global top-k set of each of the R sets of runs with the global top-k set of the exact phi*, and their mutual stability (Nogueira), against the mean
 single-instance r_k of the same instances. Writes results/e7_controls.csv.
usage: PYTHONPATH=. python3 scripts/e7_controls.py --cells CELL ..."""
import argparse, json, os
from math import comb
import numpy as np, pandas as pd
from shapaudit import cells, metrics as M

ap = argparse.ArgumentParser(); ap.add_argument("--cells", nargs="+", required=True); ap.add_argument("--out", default="results"); ap.add_argument("--tag", default="R20")
ap.add_argument("--ns", default="10,30,100"); a = ap.parse_args()
rows = []
for c in a.cells:
    cdir = os.path.join(cells.WORK, "cells", c)
    z = np.load(os.path.join(cdir, f"runs_{a.tag}.npz")); mz = np.load(os.path.join(cdir, "meta.npz"))
    inst = z["inst"]; ps = mz["phi_star"][inst]; nvar = z["nvar"]
    T = pd.read_csv(f"{a.out}/tidy_{c}_{a.tag}.csv")
    for k in (1, 3, 5):
        rows.append(dict(cell=c, arm="chance", budget="-", k=k, n_inst=len(inst), global_exact=np.nan, global_nog=np.nan, mean_instance_r=float(np.mean([1 / comb(int(v), k) if v >= k else 1.0 for v in nvar]))))
    for key in z.files:
        if not key.startswith("phi/"): continue
        _, arm, b = key.split("/")
        if z[f"cost/{arm}/{b}"].max() == 0 or b not in ("x1", "perm500", "x0.25", "x4"): continue
        ph = np.abs(z[key].astype(np.float64))                                  # (n, R, d)
        for n in (int(v) for v in a.ns.split(",")):
            if n > len(inst): continue
            g_star = np.abs(ps[:n]).mean(0); g_run = ph[:n].mean(0)              # (d,), (R, d)
            for k in (3, 5):
                tstar = M.topk_mask(g_star, k); T_run = M.topk_mask(g_run, k)
                ex = (T_run == tstar[None]).all(1).mean()
                nog = M.nogueira(T_run[None])[0] if hasattr(M, "nogueira") else np.nan
                r_inst = T[(T.arm == arm) & (T.budget == b) & (T.k == k) & (T.inst.isin(inst[:n]))].r.mean()
                rows.append(dict(cell=c, arm=arm, budget=b, k=k, n_inst=n, global_exact=float(ex), global_nog=float(nog), mean_instance_r=float(r_inst)))
D = pd.DataFrame(rows); D.to_csv(f"{a.out}/e7_controls.csv", index=False)
pd.set_option("display.width", 200)
print(D[(D.k == 3) & D.budget.isin(["x1", "perm500", "-"]) & D.n_inst.isin([30, 100])].groupby(["arm", "budget", "n_inst"])[["global_exact", "global_nog", "mean_instance_r"]].mean().round(3))
