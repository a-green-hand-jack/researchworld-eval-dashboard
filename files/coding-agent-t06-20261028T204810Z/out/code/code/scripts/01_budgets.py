"""Main experiment: for every dataset and every ordered pair (i ranked above j) compute
the smallest found number of comparisons that must be dropped / flipped / injected
so that j overtakes i (greedy-with-refit, verified by exact refit).

Outputs results/budgets/<dataset>.parquet (one row per pair) and
results/budgets/<dataset>.meta.json (scores, names, dataset statistics).
Usage: python 01_budgets.py [dataset ...]   (default: all)
"""
import json, os, sys, time
import numpy as np
import pandas as pd
from multiprocessing import Pool

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from lbstab import attacks, bt
from lbstab.prep import prepare, pair_stats, ALL_SETS, LAM

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "results", "budgets")
KINDS = ("drop", "flip", "inject")
G = {}


def _categorise(c, moves, i, j, kind):
    cat = dict(direct=0.0, i_other=0.0, j_other=0.0, neither=0.0, tie_src=0.0)
    for s_, d_, u in moves:
        cell = s_ if s_ >= 0 else d_
        a, b = c.a[cell], c.b[cell]
        S = {a, b}
        if S == {i, j}:
            cat["direct"] += u
        elif i in S:
            cat["i_other"] += u
        elif j in S:
            cat["j_other"] += u
        else:
            cat["neither"] += u
        if s_ >= 0 and c.y[s_] == 0.5:
            cat["tie_src"] += u
    return cat


def run_pair(args):
    i, j = args
    c, ce, theta, H, p = G["c"], G["ce"], G["theta"], G["H"], G["p"]
    delta, se_f, se_s, lev = pair_stats(c, theta, i, j, LAM, H, p)
    row = dict(i=int(i), j=int(j), delta=delta, se_fisher=se_f, se_sand=se_s)
    # first-order (no refit) drop budget
    pos = np.where((lev > 0) & (c.w > 0))[0]
    o = pos[np.argsort(-lev[pos])]
    cum = np.cumsum(lev[o] * c.w[o])
    t = np.searchsorted(cum, delta)
    if t < len(o):
        prev = cum[t - 1] if t > 0 else 0.0
        row["k_drop_lin"] = float(c.w[o[:t]].sum() + np.ceil((delta - prev) / lev[o[t]]))
    else:
        row["k_drop_lin"] = np.inf
    for kind in KINDS:
        cc = ce if kind == "inject" else c
        t0 = time.time()
        r = attacks.min_budget(cc, i, j, kind, LAM, theta0=theta, max_budget=c.n, prune=True, prune_max=60)
        row[f"k_{kind}"] = float(r["k"])
        row[f"rounds_{kind}"] = r["rounds"]
        row[f"sec_{kind}"] = time.time() - t0
        if np.isfinite(r["k"]):
            for key, v in _categorise(cc, r["moves"], i, j, kind).items():
                row[f"{kind}_{key}"] = v
    return row


def run_dataset(name, pool_size=38):
    c, df = prepare(name)
    theta = bt.fit(c, LAM)
    _, H, p = bt.grad_hess(c, theta, LAM)
    ce = attacks.extend_for_injection(c)
    G.update(c=c, ce=ce, theta=theta, H=H, p=p)
    order = bt.ranking(theta, c)
    pairs = [(order[a], order[b]) for a in range(c.m) for b in range(a + 1, c.m)]
    t0 = time.time()
    with Pool(pool_size) as pool:
        rows = pool.map(run_pair, pairs, chunksize=4)
    res = pd.DataFrame(rows)
    rank = np.empty(c.m, int)
    rank[order] = np.arange(c.m)
    res["rank_i"] = rank[res.i.values]
    res["rank_j"] = rank[res.j.values]
    cnt = pd.concat([df.a, df.b]).value_counts().reindex(range(c.m)).fillna(0).values
    res["n_i"] = cnt[res.i.values]
    res["n_j"] = cnt[res.j.values]
    key = df.a.values * c.m + df.b.values
    direct = pd.Series(np.r_[key, df.b.values * c.m + df.a.values]).value_counts()
    res["n_ij"] = [direct.get(i * c.m + j, 0) for i, j in zip(res.i, res.j)]
    res["z"] = res.delta / res.se_sand
    res["z_fisher"] = res.delta / res.se_fisher
    os.makedirs(OUT, exist_ok=True)
    res.to_parquet(os.path.join(OUT, name + ".parquet"))
    meta = dict(name=name, n=float(c.n), m=c.m, names=c.names, theta=theta.tolist(), order=order.tolist(),
                tie_rate=float(c.w[c.y == 0.5].sum() / c.n), home=c.home,
                eta=float(theta[c.m]) if c.home else None, n_pairs_observed=int(len(np.unique(key))),
                counts=cnt.tolist(), seconds=time.time() - t0)
    json.dump(meta, open(os.path.join(OUT, name + ".meta.json"), "w"), indent=1)
    print(f"{name}: m={c.m} n={int(c.n)} pairs={len(pairs)} {time.time()-t0:.1f}s", flush=True)


if __name__ == "__main__":
    names = sys.argv[1:] or ALL_SETS
    for nm in names:
        run_dataset(nm)
