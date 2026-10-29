"""Worst-case budgets for the RQ1 decisions (top1, top-k set, Kendall tau) on the original data (replicate -1) and on
B bootstrap resamples of the comparisons; also direct/involving baselines on the original data.
Usage: 02_decisions.py DATASET B B_TAU  ->  results/decisions_<DATASET>.csv (tidy, one row per budget)"""
import sys, time, numpy as np, pandas as pd, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rsens
DESIGN = {"arena55k": "crowd", "mtbench_human": "expert", "mtbench_gpt4": "model_judge"}
ds, B, BT = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
c0 = rsens.load(ds); design = DESIGN.get(ds, "sports"); out = []; t0 = time.time()


def pairs_for(r, p):
    """a priori target pairs per decision: (upper a, lower b)."""
    d = {"top1": [(r[0], r[j]) for j in (1, 2, 3) if j < p]}
    for k in (3, 5, 10):
        if p > k:
            d[f"topk{k}"] = [(r[i], r[j]) for i in (k - 2, k - 1) for j in (k, k + 1) if j < p]
    return d


def rec(rep, c, dec, method, ptype, k, pair=""):
    out.append(dict(dataset=ds, eval_design=design, replicate=rep, seed=1000 + rep, decision=dec, method=method, perturbation_type=ptype,
                    budget_k=k, budget_frac=k / c.n if k == k else np.nan, N=c.n, p=c.p, pair=pair))


for rep in range(-1, B):
    if rep < 0: c = c0
    else:
        idx = np.random.default_rng(1000 + rep).integers(0, c0.n, c0.n); c = c0.subset(idx)
    th = rsens.fit(c); r = rsens.ranking(th, c.p)
    for dec, prs in pairs_for(r, c.p).items():
        for mode in ("drop", "flip"):
            best = (np.inf, "")
            for a, b in prs:
                k = rsens.worst_case(c, a, b, mode, th0=th)["k"]
                if k == k and k < best[0]: best = (k, f"{c.names[a]}>{c.names[b]}")
            rec(rep, c, dec, "influence_exact", mode, best[0] if best[0] < np.inf else np.nan, best[1])
        if rep < 0 or dec == "top1":
            for kind in ("a_wins", "b_loses"):
                best = (np.inf, "")
                for a, b in prs:
                    kk = rsens.inject_case(c, b, a, kind, th0=th)["k"]
                    if kk == kk and kk < best[0]: best = (kk, f"{c.names[b]}>{c.names[a]}")
                rec(rep, c, dec, "influence_exact", "add_" + kind, best[0] if best[0] < np.inf else np.nan, best[1])
        if rep < 0:                                           # head-to-head / involving-only baselines (original data)
            for mode in ("drop", "flip"):
                for name, mk in (("direct", lambda a, b: ((c.I == a) & (c.J == b)) | ((c.I == b) & (c.J == a))),
                                 ("involving", lambda a, b: (c.I == a) | (c.J == a) | (c.I == b) | (c.J == b))):
                    best = (np.inf, "")
                    for a, b in prs:
                        k = rsens.worst_case(c, a, b, mode, allowed=mk(a, b), th0=th)["k"]
                        if k == k and k < best[0]: best = (k, f"{c.names[a]}>{c.names[b]}")
                    rec(rep, c, dec, "baseline_" + name, mode, best[0] if best[0] < np.inf else np.nan, best[1])
    if rep < BT:
        for thr in (0.95, 0.9):
            for mode in ("drop", "flip"):
                res = rsens.tau_attack(c, mode, thr, th0=th)
                rec(rep, c, f"tau{thr}", "influence_exact_greedy", mode, res["k"], f"steps={res['steps']}")
    print(ds, "rep", rep, round(time.time() - t0), flush=True)
    pd.DataFrame(out).to_csv(f"{os.path.dirname(os.path.abspath(__file__))}/../results/decisions_{ds.replace(':', '_')}.csv", index=False)
