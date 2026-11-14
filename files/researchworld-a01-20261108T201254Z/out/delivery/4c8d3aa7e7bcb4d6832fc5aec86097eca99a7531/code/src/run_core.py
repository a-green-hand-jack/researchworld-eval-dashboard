"""Minimum targeted investment, all rules; writes a tidy CSV.
Usage: python3 src/run_core.py DATASET CAPS RULES TARGETS OUT [--eps 1e-3]
  CAPS  comma list (ceil,front0,front2,gain5,gain10,gain20,emp95,emp99)
  RULES comma list from mean,geomean,harmonic,pow-5,median,min,trimmed1,winvstd,wdir0..wdir19,borda,condorcet,plurality
  TARGETS 'all' | 'sample' (rank-stratified, seed 0) | 'top<k>'
"""
import sys, time, pathlib, argparse
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from scipy.stats import rankdata
from mti import scorerules as sr, ordinal as od, data as dt

ap = argparse.ArgumentParser(); ap.add_argument("dataset"); ap.add_argument("caps"); ap.add_argument("rules")
ap.add_argument("targets"); ap.add_argument("out"); ap.add_argument("--eps", type=float, default=1e-3)
ap.add_argument("--no-tie-levels", action="store_true", help="ordinal rules: target may only pass a rival by eps, not tie")
ap.add_argument("--seed", type=int, default=0); ap.add_argument("--nsample", type=int, default=150)
a = ap.parse_args()
if a.no_tie_levels: od.TIE_LEVELS = False
X, names, tasks, meta = dt.load(a.dataset); M, n = X.shape
rules = a.rules.split(","); caps = a.caps.split(",")

def score_rule(rule):
    """(value fn, L1, K) for score rules incl. weighted means: wdir<k> (Dirichlet(1) weights, seed 1000+k), winvstd (weights 1/std per task)."""
    if rule in sr.RULES: return sr.RULES[rule]
    if rule.startswith("wdir"): return sr.make_wmean(np.random.default_rng(1000 + int(rule[4:])).dirichlet(np.ones(n)))
    if rule == "winvstd": return sr.make_wmean(1 / X.std(axis=0, ddof=1))
    return None
SR = {r: score_rule(r) for r in rules}

def rule_values(rule):
    if SR.get(rule) is not None: return SR[rule][0](X)
    if rule.startswith("trimmed"): return sr.trimmed_v(X, int(rule[7:]))
    if rule == "borda": return od.borda_points(X)
    if rule == "plurality":
        mx = X.max(axis=0); ties = X == mx; return (ties / ties.sum(axis=0)).sum(axis=1)
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
            cap = dt.make_cap(cap_name, X, i); c0 = time.process_time()
            if SR[rule] is not None: out = sr.min_investment(SR[rule], X, i, cap, a.eps)
            elif rule.startswith("trimmed"):
                t = int(rule[7:]); v = sr.trimmed_v(X, t); tau = np.delete(v, i).max()
                out = {"gap": float(tau - v[i])}
                assert t == 1, "only t=1 has the fast exact MILP"
                out["L1"] = 0.0 if v[i] > tau else sr.trimmed1_milp(X[i], tau, cap, a.eps, "L1")
                out["K"] = 0 if v[i] > tau else sr.trimmed1_milp(X[i], tau, cap, a.eps, "K")
                out["Linf"] = sr.linf_bisect(lambda y: sr.trimmed_v(y, t), X[i], tau, cap, a.eps)
            else:
                out = od.min_investment_ordinal(rule, X, i, cap, a.eps)
            for m in ("L1", "K", "Linf"):          # explicit status for every measure: INF = proven infeasible, NaN = censored
                if m in out and f"{m}_status" not in out:
                    out[f"{m}_status"] = "censored" if np.isnan(out[m]) else ("infeasible" if np.isinf(out[m]) else "opt")
            st = [out[f"{m}_status"] for m in ("L1", "K", "Linf") if f"{m}_status" in out]
            rows.append(dict(dataset=a.dataset, cap=cap_name, rule=rule, target=names[i], target_idx=int(i),
                             rank_mean=int(mean_rank[i]), rank_rule=rank_of(rule)[i], eps=a.eps,
                             feasible=np.nan if out["L1_status"] == "censored" else int(out["L1_status"] != "infeasible"),
                             censored=int("censored" in st), cpu_s=time.process_time() - c0, **out))
        r_ = [r for r in rows if r["cap"] == cap_name and r["rule"] == rule]
        print(f"{cap_name} {rule} done {time.time()-t0:.0f}s wall; cpu {sum(r['cpu_s'] for r in r_):.0f}s over {len(r_)} targets; "
              f"censored {sum(r['censored'] for r in r_)}; infeasible {sum(r['feasible'] == 0 for r in r_)}", flush=True)
        pd.DataFrame(rows).to_csv(a.out, index=False)
pd.DataFrame(rows).to_csv(a.out, index=False)
