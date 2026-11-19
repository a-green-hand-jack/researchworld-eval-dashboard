"""Random-allocation control: what does *targeting* buy?  For each target and rule the exact optimum (results/helm_main.csv: L1*, K*) is compared with
randomly allocated investment under the same cap:
  spread : weights w ~ Dirichlet(1,..,1) over all n tasks, raise y_t = x_t + min(h_t, s*B*w_t), unspent points (cap hit) redistributed proportionally
  ktasks : K* random tasks (K* = the optimum's number of tasks), equal split of s*B, capped likewise (leftover redistributed within the K* tasks)
  with B = L1* (the optimal total).  Reported per scheme: success_at_opt = share of draws that make the target strictly first at s=1 (same total points
  as the optimum); factor = smallest multiplier s >= 1 of the total budget at which the draw makes the target first (bisection; inf if even s -> caps
  saturated fails); factor_med, q25, q75 over draws and share_inf.
Usage: python3 src/run_random_control.py OUT [--draws 100] [--maxrank 21] [--seed 0]
"""
import sys, pathlib, argparse
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mti import scorerules as sr, ordinal as od, data as dt
ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("--draws", type=int, default=100)
ap.add_argument("--maxrank", type=int, default=21); ap.add_argument("--caps", default="ceil,gain10"); ap.add_argument("--minL1", type=float, default=0.05); ap.add_argument("--seed", type=int, default=0); a = ap.parse_args()
rng = np.random.default_rng(a.seed)
X, names, tasks, _ = dt.load("helm"); M, n = X.shape
H = pd.read_csv("results/helm_main.csv")
RULES = ["mean", "geomean", "harmonic", "median", "min", "borda", "condorcet", "plurality"]
def first(rule, i, y):
    if rule in sr.RULES:
        v = sr.RULES[rule][0](X); vo = np.delete(v, i).max(); return sr.RULES[rule][0](y) > vo
    Y = X.copy(); Y[i] = y; return od.FIRST[rule](Y) == i
def alloc(h, w, total):
    """add total points with weights w subject to headroom h (iterative redistribution)"""
    d = np.zeros_like(h); w = w.astype(float).copy(); rem = total
    for _ in range(60):
        act = (h - d > 1e-12) & (w > 0)
        if rem <= 1e-12 or not act.any(): break
        add = np.minimum(h - d, rem * w / w[act].sum() * act); d += add; rem -= add.sum()
    return d
q = lambda v, p: float(np.sort(v)[int(round(p * (len(v) - 1)))])      # quantile that tolerates inf
rows = []
base = H[(H.cap.isin(["ceil", "gain10"]))]
for cap_name in a.caps.split(","):
    for i in np.argsort(-X.mean(axis=1))[1:a.maxrank]:
        cap = np.maximum(dt.make_cap(cap_name, X, i), X[i]); h = cap - X[i]
        for rule in RULES:
            r = base[(base.cap == cap_name) & (base.rule == rule) & (base.target_idx == i)].iloc[0]
            if not np.isfinite(r.L1) or r.L1 < a.minL1: continue      # near-ties (L1* of a few eps) make the ratio meaningless
            B, K = r.L1, int(r.K)
            for scheme in ("spread", "ktasks"):
                fac = []
                for _ in range(a.draws):
                    if scheme == "spread": w = rng.dirichlet(np.ones(n)); hh = h
                    else:
                        sel = rng.choice(n, K, replace=False); w = np.zeros(n); w[sel] = 1.0; hh = h
                    f = lambda s: first(rule, i, X[i] + alloc(hh, w, s * B))
                    if f(1.0): fac.append(1.0); continue
                    cap_s = (h.sum() if scheme == "spread" else h[w > 0].sum()) / B       # budget at which every allowed task is saturated
                    if cap_s <= 1 or not f(cap_s): fac.append(np.inf); continue
                    lo, hi = 1.0, cap_s
                    for _ in range(14):
                        mid = (lo + hi) / 2
                        if f(mid): hi = mid
                        else: lo = mid
                    fac.append(hi)
                fac = np.array(fac); fin = np.isfinite(fac)
                rows.append(dict(cap=cap_name, rule=rule, target=names[i], target_idx=int(i), rank_mean=int(r.rank_mean), L1_opt=B, K_opt=K, scheme=scheme,
                                 draws=a.draws, success_at_opt=float((fac == 1.0).mean()), share_inf=float((~fin).mean()),
                                 factor_med=q(fac, .5), factor_q25=q(fac, .25), factor_q75=q(fac, .75)))
        print(cap_name, names[i], flush=True); pd.DataFrame(rows).to_csv(a.out, index=False)
pd.DataFrame(rows).to_csv(a.out, index=False)
