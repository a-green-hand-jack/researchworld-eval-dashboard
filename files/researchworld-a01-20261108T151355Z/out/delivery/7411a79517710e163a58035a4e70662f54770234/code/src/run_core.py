"""Minimum targeted investment, all rules; writes a tidy CSV.
Usage: python3 src/run_core.py DATASET CAPS RULES TARGETS OUT [--eps 1e-3]
  CAPS  comma list (ceil,front0,front2,gain5,gain10,gain20,emp95,emp99)
  RULES comma list from mean,geomean,harmonic,median,min,trimmed1,borda,condorcet,plurality
  TARGETS 'all' | 'sample' (rank-stratified, seed 0) | 'top<k>'
"""
import sys, time, pathlib, argparse
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from scipy.stats import rankdata
from mti import scorerules as sr, ordinal as od, data as dt

ap = argparse.ArgumentParser(); ap.add_argument("dataset"); ap.add_argument("caps"); ap.add_argument("rules")
ap.add_argument("targets"); ap.add_argument("out"); ap.add_argument("--eps", type=float, default=1e-3)
ap.add_argument("--seed", type=int, default=0); ap.add_argument("--nsample", type=int, default=150)
a = ap.parse_args()
X, names, tasks, meta = dt.load(a.dataset); M, n = X.shape
rules = a.rules.split(","); caps = a.caps.split(",")

def rule_values(rule):
    if rule in sr.RULES: return sr.RULES[rule][0](X)
    if rule.startswith("trimmed"): return sr.trimmed_v(X, int(rule[7:]))
    if rule == "borda": return od.borda_points(X)
    if rule == "plurality":
        mx = X.max(axis=0); ties = X == mx; return (ties / ties.sum(axis=0)).sum(axis=1)
    if rule == "condorcet":   # Copeland score (pairwise task-majority wins, ties 1/2) = ranking proxy; vectorised in chunks
        out = np.zeros(M)
        for lo in range(0, M, 64):
            Xc = X[lo:lo + 64]
            W = (Xc[:, None, :] > X[None, :, :]).sum(-1) + 0.5 * (Xc[:, None, :] == X[None, :, :]).sum(-1)    # (c, M) pairwise task wins
            out[lo:lo + 64] = ((W > n / 2) + 0.5 * (W == n / 2)).sum(1) - 0.5 * 1.0          # self counts 1/2 on a tie with itself: remove
        return out
rank_cache = {}
def rank_of(rule):
    if rule not in rank_cache:
        v = rule_values(rule); rank_cache[rule] = rankdata(-v, method="min") if not np.isnan(v).all() else np.full(M, np.nan)
    return rank_cache[rule]

mean_rank = rankdata(-X.mean(axis=1), method="min")
if a.targets == "all": targets = np.arange(M)
elif a.targets.startswith("top"): targets = np.argsort(mean_rank, kind="stable")[: int(a.targets[3:])]
else:
    rng = np.random.default_rng(a.seed); order = np.argsort(mean_rank, kind="stable")
    head = order[1:21]; tail = order[21:]
    if len(tail) > a.nsample:      # log-uniform in rank
        pos = np.unique(np.round(np.exp(np.linspace(np.log(1), np.log(len(tail)), a.nsample))).astype(int) - 1)
        tail = tail[pos]
    targets = np.concatenate([head, tail])

rows = []; t0 = time.time()
for cap_name in caps:
    for rule in rules:
        for i in targets:
            cap = dt.make_cap(cap_name, X, i)
            if rule in sr.RULES: out = sr.min_investment(rule, X, i, cap, a.eps)
            elif rule.startswith("trimmed"):
                t = int(rule[7:]); v = sr.trimmed_v(X, t); tau = np.delete(v, i).max()
                out = {"gap": float(tau - v[i])}
                out["L1"] = 0.0 if v[i] > tau else sr.trimmed_L1_milp(X[i], tau, cap, a.eps, t)
                out["K"] = 0.0 if v[i] > tau else sr.trimmed_K_milp(X[i], tau, cap, a.eps, t)
                out["Linf"] = sr.linf_bisect(lambda y: sr.trimmed_v(y, t), X[i], tau, cap, a.eps)
            else:
                out = od.min_investment_ordinal(rule, X, i, cap, a.eps)
            fin = [out[k] for k in ("L1", "K", "Linf")]
            status = "censored" if any(np.isnan(v) for v in fin) else ("infeasible" if any(np.isinf(v) for v in fin) else "ok")
            rows.append(dict(dataset=a.dataset, cap=cap_name, rule=rule, target=names[i], target_idx=int(i),
                             rank_mean=int(mean_rank[i]), rank_rule=rank_of(rule)[i], **out,
                             feasible=(status == "ok"), status=status, seed=a.seed))
        print(f"{cap_name} {rule} done {time.time()-t0:.0f}s", flush=True)
        pd.DataFrame(rows).to_csv(a.out, index=False)
pd.DataFrame(rows).to_csv(a.out, index=False)
