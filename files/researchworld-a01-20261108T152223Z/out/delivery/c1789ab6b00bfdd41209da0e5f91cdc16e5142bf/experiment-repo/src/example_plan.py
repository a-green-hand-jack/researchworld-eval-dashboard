"""Example plans: the L1-minimising plan of one real target under several rules (what the rules ask to raise).
Usage: python3 src/example_plan.py DATASET RANK CAP RULES OUT [--eps 1e-3]
  RANK  rank of the target under the mean rule (the ranked-RANK model, ties by stable order)
Writes OUT (rule, task, old, new) and OUT-with-suffix _summary.csv (per rule: K, L1, rank of the target under every rule after the plan).
Plans are optimal but not unique: score rules use a canonical optimal plan (mean: largest headroom first = K-minimal;
median/min: the tasks with the smallest gap to the level tau+eps), rank rules return the MILP's plan.
Every plan is checked: cost equals the solver value and the target ends strictly first under its rule."""
import sys, pathlib, argparse
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from scipy.stats import rankdata
from mti import scorerules as sr, ordinal as od, data as dt

ap = argparse.ArgumentParser(); ap.add_argument("dataset"); ap.add_argument("rank", type=int); ap.add_argument("cap")
ap.add_argument("rules"); ap.add_argument("out"); ap.add_argument("--eps", type=float, default=1e-3)
a = ap.parse_args()
X, names, tasks, meta = dt.load(a.dataset); M, n = X.shape; eps = a.eps
order = np.argsort(-X.mean(axis=1), kind="stable"); i = int(order[a.rank - 1])
x = X[i]; cap = np.maximum(dt.make_cap(a.cap, X, i), x)

def plan_score(rule):
    vals = sr.RULES[rule][0](X); tau = np.delete(vals, i).max(); b = tau + eps
    y = x.copy()
    if rule == "mean":
        need = n * b - x.sum()
        for t in np.argsort(-(cap - x), kind="stable"):
            if need <= 1e-12: break
            d = min(cap[t] - x[t], need); y[t] += d; need -= d
        assert need <= 1e-9
    elif rule in ("median", "min"):
        m = (n + 1) // 2 if rule == "median" else n
        gap = np.where(cap >= b, np.maximum(0, b - x), np.inf)
        for t in np.argsort(gap, kind="stable")[:m]: y[t] = max(x[t], b)
    else: raise KeyError(rule)
    return y

def plan_ordinal(rule):
    L1 = od.MIN_INV[rule](X, i, cap, eps, "L1")
    pl = od.LAST["plan"]; y = x.copy()
    for t, l in pl.items(): y[t] = l
    assert abs((y - x).sum() - L1) < 1e-6
    return y

def values(rule, Y):
    if rule in sr.RULES: return sr.RULES[rule][0](Y)
    if rule == "borda": return od.borda_points(Y)
    if rule == "plurality":
        mx = Y.max(axis=0); ties = Y == mx; return (ties / ties.sum(axis=0)).sum(axis=1)
    if rule == "condorcet": return od.copeland_values(Y)
def rank_after(rule, Y): return int(rankdata(-values(rule, Y), method="min")[i])

rules = a.rules.split(","); rows, summ = [], []
for rule in rules:
    y = plan_score(rule) if rule in sr.RULES else plan_ordinal(rule)
    Y = X.copy(); Y[i] = y
    assert (y >= x - 1e-12).all() and (y <= cap + 1e-9).all()
    assert rank_after(rule, Y) == 1, (rule, rank_after(rule, Y))
    for t in np.where(y > x + 1e-12)[0]: rows.append(dict(rule=rule, task=tasks[t], old=x[t], new=y[t], gain=y[t] - x[t]))
    summ.append(dict(rule=rule, target=names[i], cap=a.cap, K=int((y > x + 1e-12).sum()), L1=float((y - x).sum()),
                     rank_before_rule=rank_after(rule, X), **{f"rank_after_{r}": rank_after(r, Y) for r in rules}))
out = pathlib.Path(a.out)
pd.DataFrame(rows).to_csv(out, index=False); pd.DataFrame(summ).to_csv(out.with_name(out.stem + "_summary.csv"), index=False)
print(pd.DataFrame(summ).to_string()); print(pd.DataFrame(rows).groupby("rule").size())
