"""Feasibility and baseline quantities per (cap, rule, target) -- no MILP.
Usage: python3 src/run_extra.py DATASET CAPS RULES TARGETS OUT [--eps 1e-3]
Per (rule, target): d_star (smallest uniform lift = Linf* at ceiling), min_front_margin, min_emp95_mult (smallest feasible cap parameters);
per cap: feasible (target first when every task is at its cap), lam_prop / L1_prop (headroom-proportional allocation baseline).
"""
import sys, time, pathlib, argparse
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mti import data as dt, feas
ap = argparse.ArgumentParser(); ap.add_argument("dataset"); ap.add_argument("caps"); ap.add_argument("rules")
ap.add_argument("targets"); ap.add_argument("out"); ap.add_argument("--eps", type=float, default=1e-3)
ap.add_argument("--seed", type=int, default=0); ap.add_argument("--nsample", type=int, default=150)
a = ap.parse_args()
X, names, tasks, meta = dt.load(a.dataset); M, n = X.shape
scale, top = dt._units(a.dataset); top = np.broadcast_to(top, (n,)).astype(float)
targets, mean_rank = dt.sample_targets(X, a.seed, a.nsample) if a.targets == "sample" else (np.arange(M), dt.sample_targets(X)[1])
caps = a.caps.split(","); rules = a.rules.split(",")
hq = None
if a.dataset.startswith("ollb") and a.dataset != "ollb_pct":
    hq = dt.empirical_gain_caps(95)[0] / scale
elif a.dataset == "helm": hq = np.full(n, max(dt.empirical_gain_caps(95)[0][dt.OLLB_TASKS.index("MMLU-PRO")], 0.0))   # same proxy as cap empm95
rows = []; t0 = time.time()
for rule in rules:
    for i in targets:
        riv = feas.Rival(X, i, rule, a.eps)
        ds = feas.uniform_lift(riv, top); mf = feas.min_front_margin(riv, top)
        me = feas.min_emp_multiplier(riv, top, hq) if hq is not None else np.nan
        for cap_name in caps:
            cap = dt.make_cap(cap_name, X, i, a.dataset)
            lam, L1p = feas.proportional_allocation(riv, cap)
            rows.append(dict(dataset=a.dataset, scale=dt.SCALE[a.dataset], cap=cap_name, rule=rule, target=names[i], target_idx=int(i),
                             rank_mean=int(mean_rank[i]), eps=a.eps, feasible=int(np.isfinite(lam)), d_star=ds, min_front_margin=mf,
                             min_emp95_mult=me, lam_prop=lam, L1_prop=L1p))
    print(f"{rule} done {time.time()-t0:.0f}s", flush=True); pd.DataFrame(rows).to_csv(a.out, index=False)
pd.DataFrame(rows).to_csv(a.out, index=False)
