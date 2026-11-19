"""Minimum targeted investment, all rules; writes a tidy CSV.
Usage: python3 code/run_core.py DATASET CAPS RULES TARGETS OUT [--eps 1e-3] [--shard i/k]
  CAPS  comma list (ceil,front0,front2,gain5,gain10,gain20,emp95,emp99)
  RULES comma list from mean,geomean,harmonic,median,min,trimmed1,borda,condorcet,plurality,copeland (copeland: M <= 600)
  TARGETS 'all' | 'sample' (rank-stratified, seed 0) | 'top<k>' | 'idx:3,17,...' (row indices)
  --time-limit S  MILP time limit per solve (default 120 s; a hit is censored NaN)
"""
import sys, time, pathlib, argparse
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from scipy.stats import rankdata
from mti import scorerules as sr, ordinal as od, data as dt

ap = argparse.ArgumentParser(); ap.add_argument("dataset"); ap.add_argument("caps"); ap.add_argument("rules")
ap.add_argument("targets"); ap.add_argument("out"); ap.add_argument("--eps", type=float, default=1e-3)
ap.add_argument("--shard", default="0/1", help="i/k: run targets i, i+k, ... (independent parallel jobs)")
ap.add_argument("--seed", type=int, default=0); ap.add_argument("--nsample", type=int, default=150)
ap.add_argument("--time-limit", type=float, default=None, help="MILP time limit in seconds per solve (default 120): for reruns of censored rows")
a = ap.parse_args()
X, names, tasks, meta = dt.load(a.dataset); M, n = X.shape
rules = a.rules.split(","); caps = a.caps.split(",")
if a.time_limit: od.TIME_LIMIT = a.time_limit

def rule_values(rule):
    if rule in sr.RULES: return sr.RULES[rule][0](X)
    if rule.startswith("trimmed"): return sr.trimmed_v(X, int(rule[7:]))
    if rule == "borda": return od.borda_points(X)
    if rule == "plurality":
        mx = X.max(axis=0); ties = X == mx; return (ties / ties.sum(axis=0)).sum(axis=1)
    if rule == "copeland": return od.copeland_scores(X) if M <= 600 else np.full(M, np.nan)
    if rule == "condorcet":   # Copeland score as the ranking proxy
        return np.array([sum(od.wins(X[j], X[k]).sum() > n / 2 for k in range(M) if k != j) +
                         0.5 * sum(od.wins(X[j], X[k]).sum() == n / 2 for k in range(M) if k != j) for j in range(M)]) if M <= 400 else np.full(M, np.nan)
rank_cache = {}
def rank_of(rule):
    if rule not in rank_cache:
        v = rule_values(rule); rank_cache[rule] = rankdata(-v, method="min") if not np.isnan(v).all() else np.full(M, np.nan)
    return rank_cache[rule]

mean_rank = rankdata(-X.mean(axis=1), method="min")
if a.targets == "all": targets = np.arange(M)
elif a.targets.startswith("idx:"): targets = np.array([int(v) for v in a.targets[4:].split(",")])
elif a.targets.startswith("top"): targets = np.argsort(mean_rank, kind="stable")[: int(a.targets[3:])]
else:
    rng = np.random.default_rng(a.seed); order = np.argsort(mean_rank, kind="stable")
    head = order[1:21]; tail = order[21:]
    if len(tail) > a.nsample:      # log-uniform in rank
        pos = np.unique(np.round(np.exp(np.linspace(np.log(1), np.log(len(tail)), a.nsample))).astype(int) - 1)
        tail = tail[pos]
    targets = np.concatenate([head, tail])

si, sk = map(int, a.shard.split("/")); targets = targets[si::sk]
rows = []; t0 = time.time()
for cap_name in caps:
    for rule in rules:
        for i in targets:
            cap = dt.make_cap(cap_name, X, i)
            if rule in sr.RULES: out = sr.min_investment(rule, X, i, cap, a.eps, measures=("L1", "K", "Linf", "L2"))
            elif rule.startswith("trimmed"):
                t = int(rule[7:]); v = sr.trimmed_v(X, t); tau = np.delete(v, i).max()
                out = {"gap": float(tau - v[i])}
                out["L1"] = 0.0 if v[i] > tau else sr.trimmed_L1_lp(X[i], tau, cap, a.eps, t)
                out["K"] = 0 if v[i] > tau else sr.trimmed_K_enum(X[i], tau, cap, a.eps, t)
                out["Linf"] = sr.linf_bisect(lambda y: sr.trimmed_v(y, t), X[i], tau, cap, a.eps)
            else:
                out = od.min_investment_ordinal(rule, X, i, cap, a.eps)
            rows.append(dict(dataset=a.dataset, cap=cap_name, rule=rule, target=names[i], target_idx=int(i),
                             rank_mean=int(mean_rank[i]), rank_rule=rank_of(rule)[i], **out))
            if len(rows) % 25 == 0: pd.DataFrame(rows).to_csv(a.out, index=False)      # partial results survive a stopped job
        print(f"{cap_name} {rule} done {time.time()-t0:.0f}s", flush=True)
        pd.DataFrame(rows).to_csv(a.out, index=False)
pd.DataFrame(rows).to_csv(a.out, index=False)
