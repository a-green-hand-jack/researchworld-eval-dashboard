"""E5 (Tier C, appendix): exact optimum vs greedy vs naive developers.
usage: run_e5.py OUT.csv board [shard n_shards] [ntargets=30] [nsub=60]   board = helm | m39 (the same top-nsub sub-board as E6)
Per target, rule and per-task cap B in {5, 10, 20} points (unit = points, own leader):
  exact      SV.price depth objective (the cheapest plan under the cap);
  uniform    the smallest common boost u <= B (all tasks, clipped at the ceiling) making the target first;
  hardest    raise tasks in ascending order of the target's own score, each by min(B, headroom), the last one only as far as needed (bisection), until first;
  random     the same with a random task order (mean over 20 draws of: feasible share, depth, breadth);
  greedy     repeatedly raise the task whose full boost min(B, headroom) increases the rule score of the target most (ties: lowest score), last boost trimmed by bisection."""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, pandas as pd
from lbprice import rules as R_, solvers as SV
from lbprice.boards import load_helm, load_ollb
out, which = sys.argv[1], sys.argv[2]
shard, ns = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (0, 1)
ntar = int(sys.argv[5]) if len(sys.argv) > 5 else 30
nsub = int(sys.argv[6]) if len(sys.argv) > 6 else 60
RULES = ["mean", "zmean", "median", "min", "borda", "plurality", "copeland"]
b = load_helm() if which == "helm" else load_ollb("m39")
top = np.argsort(-b["official"], kind="stable")[:nsub]; S = b["S"][top]; names = [b["names"][i] for i in top]; sig = S.std(axis=0); m = S.shape[1]
kw_of = lambda rule: dict(sigma=sig) if rule == "zmean" else {}


def first(S2, t, rule):
    A = R_.scores(S2, rule, **kw_of(rule)).astype(float); a = A[t]; A[t] = -np.inf
    return bool(a > A.max()) if rule in R_.RANK_RULES else bool(a - A.max() >= SV.EPS_AGG - 1e-9)


def apply(t, delta):
    S2 = S.copy(); S2[t] = np.minimum(S2[t] + delta, 100.0); return S2


def sequential(t, rule, order, B):
    """boost tasks in `order` by min(B, headroom) until first; trim the last by bisection. Returns (feasible, depth, breadth)."""
    delta = np.zeros(m); head = 100.0 - S[t]
    if first(S, t, rule): return True, 0.0, 0
    for j in order:
        full = min(B, head[j])
        if full <= 0: continue
        delta[j] = full
        if first(apply(t, delta), t, rule):
            lo, hi = 0.0, full
            for _ in range(30):
                mid = 0.5 * (lo + hi); delta[j] = mid
                if first(apply(t, delta), t, rule): hi = mid
                else: lo = mid
            delta[j] = hi
            return True, float(delta.sum()), int((delta > 0).sum())
    return False, np.inf, m + 1


def greedy_order(t, rule, B):
    """sequential greedy: returns the order built step by step (recomputed after each boost)."""
    delta = np.zeros(m); head = 100.0 - S[t]; chosen = []; left = [j for j in range(m) if head[j] > 0]
    while left:
        base = R_.scores(apply(t, delta), rule, **kw_of(rule))[t]; best, bj = -np.inf, None
        for j in left:
            d2 = delta.copy(); d2[j] = min(B, head[j])
            g = R_.scores(apply(t, d2), rule, **kw_of(rule))[t] - base
            key = (g, -S[t, j])
            if bj is None or key > best: best, bj = key, j
        chosen.append(bj); delta[bj] = min(B, head[bj]); left.remove(bj)
        if first(apply(t, delta), t, rule): break
    return chosen + [j for j in range(m) if j not in chosen]


rows = []; t0 = time.time(); k = 0
for t in range(ntar):
    k += 1
    if (k - 1) % ns != shard: continue
    for rule in RULES:
        rng = np.random.default_rng([20260401, t, RULES.index(rule)])
        for B in (5.0, 10.0, 20.0):
            base = dict(board=which, target=t, model=names[t], rule=rule, B=B)
            pl = SV.price(rule, S, t, B, ceil=100.0, objective="depth", sigma=sig if rule == "zmean" else None, time_limit=30.0)
            rows.append(dict(base, developer="exact", feasible=bool(pl["feasible"]), depth=pl["depth"] if pl["feasible"] else np.nan, breadth=pl["breadth"] if pl["feasible"] else np.nan))
            head = 100.0 - S[t]
            def uni(u):
                return first(apply(t, np.minimum(u, head)), t, rule)
            if first(S, t, rule): ok, dep, br = True, 0.0, 0
            elif not uni(B): ok, dep, br = False, np.nan, np.nan
            else:
                lo, hi = 0.0, B
                for _ in range(40):
                    mid = 0.5 * (lo + hi)
                    if uni(mid): hi = mid
                    else: lo = mid
                ok, dep, br = True, float(np.minimum(hi, head).sum()), int((head > 0).sum())
            rows.append(dict(base, developer="uniform", feasible=ok, depth=dep, breadth=br))
            for name, order in (("hardest", list(np.argsort(S[t], kind="stable"))), ("greedy", None)):
                if order is None: order = greedy_order(t, rule, B)
                ok, dep, br = sequential(t, rule, order, B)
                rows.append(dict(base, developer=name, feasible=ok, depth=dep if ok else np.nan, breadth=br if ok else np.nan))
            res = [sequential(t, rule, list(rng.permutation(m)), B) for _ in range(20)]
            okr = np.array([r[0] for r in res]); rows.append(dict(base, developer="random", feasible=float(okr.mean()), depth=float(np.mean([r[1] for r in res if r[0]])) if okr.any() else np.nan,
                                                           breadth=float(np.mean([r[2] for r in res if r[0]])) if okr.any() else np.nan))
    print(t, len(rows), round(time.time() - t0), flush=True)
    pd.DataFrame(rows).to_csv(out, index=False)
print("done", len(rows), round(time.time() - t0))
