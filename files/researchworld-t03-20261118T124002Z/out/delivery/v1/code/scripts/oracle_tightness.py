"""Oracle tightness of the E5 certificates on the R~200 subset: at stage s (x0.25, x1, x4 of the Covert-Lee schedule, the budgets of the R200 reruns)
the oracle certifies an instance iff r_k(x; B_s) >= 1 - delta, where r_k is the probability, over fresh Covert-Lee reruns, that the run's top-k set is
the exact one (R=200). A rule 'certifies by stage s' a run if its statistic is <= delta at some stage <= s (the sequential rule's first certified
stage). Compared: oracle share, rule's certified share overall, within the oracle-OK instances (power) and within the oracle-not-OK instances
(certifications the oracle would not have issued). Writes results/oracle_tightness.csv.
usage: PYTHONPATH=. python3 scripts/oracle_tightness.py --cells CELL ..."""
import argparse, os
import numpy as np, pandas as pd
from shapaudit import cells
from shapaudit.certs import RULES, KS, STAGE_MULTS

ap = argparse.ArgumentParser(); ap.add_argument("--cells", nargs="+", required=True); ap.add_argument("--out", default="results")
ap.add_argument("--tag", default="R200"); a = ap.parse_args()
DELTAS = (0.2, 0.1, 0.05)
STAGES = {"x0.25": 0, "x1": 2, "x4": 4}
rows = []
for c in a.cells:
    T = pd.read_csv(f"{a.out}/tidy_{c}_{a.tag}.csv"); T = T[T.arm == "covert_lee"]
    z = np.load(os.path.join(cells.WORK, "cells", c, "certs.npz")); inst = list(z["inst"])
    for k_i, k in enumerate(KS):
        for b, s in STAGES.items():
            r = T[(T.k == k) & (T.budget == b)].set_index("inst").r
            ids = [i for i in r.index if i in inst]
            ii = [inst.index(i) for i in ids]
            for dl in DELTAS:
                ok = np.array([r[i] >= 1 - dl for i in ids])
                for rule in RULES:
                    p = z[rule][ii][:, :, :s + 1, k_i]                         # (n, R, stages up to s)
                    share = (p <= dl).any(2).mean(1)                           # per-instance certified share over its R20 runs
                    rows.append(dict(cell=c, k=k, stage=b, coalitions=float(z["cost"].reshape(-1, len(STAGE_MULTS))[0][s]), delta=dl, rule=rule, n_inst=len(ids),
                                     oracle_share=ok.mean(), cert_share=share.mean(),
                                     cert_share_oracle_ok=share[ok].mean() if ok.any() else np.nan,
                                     cert_share_oracle_not_ok=share[~ok].mean() if (~ok).any() else np.nan,
                                     n_oracle_ok=int(ok.sum())))
D = pd.DataFrame(rows); D.to_csv(f"{a.out}/oracle_tightness.csv", index=False)
pd.set_option("display.width", 220)
print(D[(D.k == 3) & (D.delta == 0.1)].round(3).to_string())
