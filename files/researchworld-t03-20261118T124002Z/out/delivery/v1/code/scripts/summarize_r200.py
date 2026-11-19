"""R~200 subset: per-instance r_k with Clopper-Pearson intervals (reruns R=200 at x0.25 / x1 / x4 and perm500), joined to the R=20 estimate of the same
instance, arm and budget. Also the agreement of the per-instance 'reliable at delta' call (r >= 1 - delta) between R=20 and R=200.
Writes results/r200_subset.csv (one row per cell, inst, arm, budget, k) and results/r200_agreement.csv (per cell, arm, budget, k, delta).
usage: PYTHONPATH=. python3 scripts/summarize_r200.py --cells CELL ..."""
import argparse
import numpy as np, pandas as pd
from shapaudit.metrics import clopper_pearson

ap = argparse.ArgumentParser(); ap.add_argument("--cells", nargs="+", required=True); ap.add_argument("--out", default="results"); a = ap.parse_args()
rows, agree = [], []
for c in a.cells:
    T2 = pd.read_csv(f"{a.out}/tidy_{c}_R200.csv"); T1 = pd.read_csv(f"{a.out}/tidy_{c}_R20.csv")
    keys = ["cell", "inst", "arm", "budget", "k"]
    J = T2[keys + ["r", "R", "gap", "z_true", "nvar", "d"]].merge(T1[keys + ["r"]], on=keys, suffixes=("_R200", "_R20"))
    nR = J.R.iloc[0]; J["x200"] = np.round(J.r_R200 * nR).astype(int)
    lohi = np.array([clopper_pearson(int(x), int(nR)) for x in J.x200])
    J["r200_lo"], J["r200_hi"] = lohi[:, 0], lohi[:, 1]
    J["r20_in_cp200"] = (J.r_R20 >= J.r200_lo - 1e-9) & (J.r_R20 <= J.r200_hi + 1e-9)
    rows.append(J.drop(columns="x200"))
    for (arm, b, k), H in J.groupby(["arm", "budget", "k"]):
        for dl in (0.05, 0.1):
            u, v = H.r_R20 >= 1 - dl, H.r_R200 >= 1 - dl
            agree.append(dict(cell=c, arm=arm, budget=b, k=k, delta=dl, n_inst=len(H), reliable_share_R20=u.mean(), reliable_share_R200=v.mean(),
                              call_agreement=(u == v).mean(), mean_abs_r_diff=(H.r_R20 - H.r_R200).abs().mean(), cp_cover_R20=H.r20_in_cp200.mean()))
pd.concat(rows).to_csv(f"{a.out}/r200_subset.csv", index=False); A = pd.DataFrame(agree); A.to_csv(f"{a.out}/r200_agreement.csv", index=False)
pd.set_option("display.width", 220)
print(A[(A.k == 3) & (A.delta == 0.1)].round(3).to_string())
