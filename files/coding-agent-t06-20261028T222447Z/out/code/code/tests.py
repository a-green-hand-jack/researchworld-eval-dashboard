"""Validation: (1) solver vs scipy, (2) greedy attack vs brute-force optimum on small instances,
(3) first-order influence prediction accuracy, (4) data-consistency checks.  Writes results/validation.json"""
import itertools, json, time, numpy as np
from scipy.optimize import minimize
import bt, loaders as D

out = {}
# (1) solver vs generic optimiser on row-level likelihood (MT-Bench human, NBA 2007)
for nm, d in [("mt_human", D.mtbench("human")), ("nba2007", D.nba_seasons()[2007]), ("arena55k", D.arena55k())]:
    P = bt.Problem(d); th = P.fit()
    p = P.p; a, b, h, y = d["a"], d["b"], d["h"], d["y"]
    def f(t):
        dd = t[a] - t[b] + (t[p] * h if P.has_h else 0)
        return np.sum(np.logaddexp(0, dd) - y * dd) + 0.5 * bt.LAM * np.sum(t[:p] ** 2)
    r = minimize(f, np.zeros(P.P), method="L-BFGS-B", options=dict(maxiter=5000, ftol=1e-15, gtol=1e-10))
    out[f"solver_maxabs_diff_{nm}"] = float(np.abs(r.x - th).max())
    out[f"solver_obj_diff_{nm}"] = float(f(th) - r.fun)

# (2) brute force
rng = np.random.default_rng(0)
res = []
for inst in range(12):
    p = 4
    true = rng.normal(0, 0.6, p)
    n = 26
    a = rng.integers(0, p, n); b = (a + rng.integers(1, p, n)) % p
    pr = 1 / (1 + np.exp(-(true[a] - true[b])))
    y = (rng.random(n) < pr).astype(float)
    sw = a > b
    a, b, y = np.where(sw, b, a), np.where(sw, a, b), np.where(sw, 1 - y, y)
    d = dict(items=list("ABCD"), a=a, b=b, h=np.zeros(n, int), y=y)
    P = bt.Problem(d)
    if P.L < 2: continue
    th = P.fit(); order = np.argsort(-th[:p])
    i, j = order[1], order[2]
    # row-level enumeration of subsets for drop and relabel (binary labels -> relabel = flip)
    cell_of = {}
    for c in range(P.C):
        pass
    key = {(int(P.ca[c]), int(P.cb[c])): c for c in range(P.C)}
    li = np.searchsorted(P.labels, y)
    rows = [(key[(int(a[t]), int(b[t]))], int(li[t])) for t in range(n)]
    def opt(kind, kmax=5):
        for k in range(1, kmax + 1):
            for S in itertools.combinations(range(n), k):
                N = P.N0.copy()
                for t in S:
                    c, l = rows[t]
                    N[c, l] -= 1
                    if kind == "relabel": N[c, 1 - l] += 1   # binary labels only
                thp = P.fit(N, th)
                if thp[i] < thp[j]: return k
        return np.nan
    if P.L != 2: continue
    kd, kr = opt("drop"), opt("relabel")
    gd, _ = P.attack(i, j, ("drop",), th_full=th, max_frac=1.0); gr, _ = P.attack(i, j, ("relabel",), th_full=th, max_frac=1.0)
    res.append(dict(opt_drop=kd, greedy_drop=gd if gd is not None else np.nan, opt_relabel=kr, greedy_relabel=gr if gr is not None else np.nan))
res = [r for r in res if not np.isnan(r["opt_drop"])]
out["bruteforce"] = res
out["bruteforce_n"] = len(res)
out["bruteforce_greedy_equals_opt_drop"] = int(sum(r["greedy_drop"] == r["opt_drop"] for r in res))
out["bruteforce_greedy_equals_opt_relabel"] = int(sum(r["greedy_relabel"] == r["opt_relabel"] for r in res if not np.isnan(r["opt_relabel"])))
out["bruteforce_n_relabel"] = int(sum(not np.isnan(r["opt_relabel"]) for r in res))
out["bruteforce_greedy_never_below_opt"] = bool(all(r["greedy_drop"] >= r["opt_drop"] for r in res))

# (3) first-order prediction vs exact refit, Arena top pairs, removal of the k top-influence comparisons
P = bt.Problem(D.arena55k()); th = P.fit(); order = np.argsort(-th[:P.p])
pred = []
for r in range(0, 20):
    i, j = order[r], order[r + 1]; u = P.contrast(i, j)
    k_, c_, l_, l2_, g_, cap_ = P._candidates(P.N0, th, u, ("drop",))
    for K in (10, 50, 200):
        acc, used, chunks = 0.0, 0, []
        for t in range(len(g_)):
            m = int(min(cap_[t], K - used)); 
            if m <= 0: break
            chunks.append((0, int(c_[t]), int(l_[t]), -1, m)); acc += m * g_[t]; used += m
            if used >= K: break
        thk = P.fit(P._apply(P.N0, chunks), th)
        pred.append(dict(pair=r, K=K, predicted=acc, actual=float(u @ th - u @ thk), gap=float(u @ th)))
out["influence_pred"] = pred
a_ = np.array([x["predicted"] for x in pred]); b_ = np.array([x["actual"] for x in pred])
out["influence_pred_corr"] = float(np.corrcoef(a_, b_)[0, 1])
out["influence_pred_median_ratio_actual_over_pred"] = float(np.median(b_ / a_))

# (4) data checks
import json as _j
ids = [[_j.loads(l)["id"] for l in open(f"/work/data/judges/{f}.jsonl")] for f in
       ["Meta-Llama-3-70B-Instruct", "Qwen2-72B-Instruct", "Mistral-7B-Instruct-v0.2"]]
out["judge_files_same_id_order"] = bool(ids[0] == ids[1] == ids[2])
json.dump(out, open("/work/results/validation.json", "w"), indent=1, default=float)
print({k: v for k, v in out.items() if k not in ("bruteforce", "influence_pred")})
print(res)
