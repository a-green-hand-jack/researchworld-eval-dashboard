"""E5 summaries from certs.npz: results/certificates_<cell>.csv (per instance), certificate_coverage.csv (pooled, cluster bootstrap over
seeds then instances) and fixed_budget_<group>.csv (fixed-budget comparator at the same pooled correct rate).
Sequential rule: a run stops at the first stage of the 7-stage schedule whose statistic <= delta (the run's set at that stage is delivered);
a run that never certifies is delivered at the last stage (x16) and is counted as uncertified, with the maximum cost."""
import argparse, glob, json, os, re
import numpy as np, pandas as pd
from shapaudit import cells
from shapaudit.certs import RULES, KS, STAGE_MULTS

ap = argparse.ArgumentParser(); ap.add_argument("--cells", nargs="+"); ap.add_argument("--out", default="results"); ap.add_argument("--nboot", type=int, default=2000)
ap.add_argument("--tag", default="certs"); a = ap.parse_args()
DELTAS = (0.2, 0.1, 0.05, 0.01)
rng = np.random.default_rng(1)

def stop_stats(z, rule, dl, ki):
    p = z[rule][:, :, :, ki]                                  # (n, R, S)
    cert = p <= dl
    anyc = cert.any(2)
    stop = np.where(anyc, cert.argmax(2), p.shape[2] - 1)      # first certified stage, else last
    cor = z["correct_split" if rule == "split" else "correct"][:, :, :, ki]
    ok = np.take_along_axis(cor, stop[..., None], 2)[..., 0]
    return anyc, stop, ok

rows, per_cell = [], {}
for c in a.cells:
    z = np.load(os.path.join(cells.WORK, "cells", c, f"{a.tag}.npz")); cost = z["cost"].astype(float)
    n, R, S, _ = z["naive"].shape; cr = []
    for rule in RULES:
        for dl in DELTAS:
            for ki, k in enumerate(KS):
                anyc, stop, ok = stop_stats(z, rule, dl, ki)
                co = cost[0][stop] if cost.ndim > 1 else cost[stop]
                cost_i = cost[0] if cost.ndim > 1 else cost
                co = cost_i[stop]
                for i in range(n):
                    nc = int(anyc[i].sum())
                    cr.append(dict(cell=c, rule=rule, delta=dl, k=k, inst=int(z["inst"][i]), R=R, n_certified=nc,
                                   n_correct_among_certified=int((ok[i] & anyc[i]).sum()), n_correct_delivered=int(ok[i].sum()),
                                   mean_stop_coalitions_certified=float(co[i][anyc[i]].mean()) if nc else np.nan, mean_cost_all=float(co[i].mean())))
    D = pd.DataFrame(cr); D.to_csv(f"{a.out}/certificates_{c}.csv", index=False); per_cell[c] = D
    # fixed budget: pooled correct rate per stage
    fx = []
    for ki, k in enumerate(KS):
        for s in range(S):
            fx.append(dict(cell=c, k=k, stage=s, mult=STAGE_MULTS[s], coalitions=float(cost_i[s]), pooled_correct=float(z["correct"][:, :, s, ki].mean())))
    pd.DataFrame(fx).to_csv(f"{a.out}/fixed_budget_{c}.csv", index=False)

def grp(c): return re.sub(r"_s\d+$", "", c)
A = pd.concat(per_cell.values(), ignore_index=True); A["group"] = A.cell.map(grp); A["seed"] = A.cell.str.extract(r"_s(\d+)$").astype(int)
def pooled(D):
    nc = D.n_certified.sum()
    return (D.n_correct_among_certified.sum() / nc) if nc else np.nan
out = []
for (g, rule, dl, k), D in A.groupby(["group", "rule", "delta", "k"]):
    est = pooled(D); bs = []
    seeds = D.seed.unique()
    byseed = {s: D[D.seed == s] for s in seeds}
    for _ in range(a.nboot):
        parts = []
        for s in rng.choice(seeds, len(seeds)):
            X = byseed[s]; parts.append(X.iloc[rng.integers(0, len(X), len(X))])
        v = pooled(pd.concat(parts)); 
        if np.isfinite(v): bs.append(v)
    lo, hi = (np.percentile(bs, 2.5), np.percentile(bs, 97.5)) if bs else (np.nan, np.nan)
    R_tot = D.R.sum()
    deliv = D.n_correct_delivered.sum() / R_tot
    verdict = "calibrated" if (np.isfinite(est) and hi >= 1 - dl) else ("n/a" if not np.isfinite(est) else "miscalibrated" if (est < 1 - dl - 0.02 and hi < 1 - dl) else "inconclusive")
    out.append(dict(group=g, rule=rule, delta=dl, k=k, n_inst=len(D), n_seeds=len(seeds), certified_share=D.n_certified.sum() / R_tot,
                    correct_given_certified=est, ci_lo=lo, ci_hi=hi, target=1 - dl, calibration=verdict, pooled_correct_delivered=deliv,
                    mean_cost_all=(D.mean_cost_all * D.R).sum() / R_tot))
FB = pd.concat([pd.read_csv(f"{a.out}/fixed_budget_{c}.csv") for c in a.cells]); FB["group"] = FB.cell.map(grp)
FB = FB.groupby(["group", "k", "stage"], as_index=False).agg(coalitions=("coalitions", "mean"), pooled_correct=("pooled_correct", "mean"))
FB.to_csv(f"{a.out}/fixed_budget_pooled.csv", index=False)
def cheapest(g, k, rate):
    H = FB[(FB.group == g) & (FB.k == k) & (FB.pooled_correct >= rate - 1e-9)]
    return float(H.coalitions.min()) if len(H) else np.nan
for o in out: o["fixed_cost_same_rate"] = cheapest(o["group"], o["k"], o["pooled_correct_delivered"])        # NaN: no fixed grid budget reaches the adaptive pooled rate
C = pd.DataFrame(out); C.to_csv(f"{a.out}/certificate_coverage.csv", index=False)
pd.set_option("display.width", 220); print(C[C.k == 3].round(3).to_string())
