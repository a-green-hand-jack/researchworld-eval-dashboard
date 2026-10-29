"""Non-adversarial baselines: random deletion, random label noise and the
non-parametric bootstrap.  For each dataset and perturbation level we refit R
times and record how often the leaderboard's conclusions change.

Outputs results/random/<dataset>.parquet (one row per replicate) and
results/random/<dataset>.boot_theta.npy (bootstrap score draws, for SE checks).
"""
import os, sys, time
import numpy as np
import pandas as pd
from multiprocessing import Pool

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from lbstab import bt
from lbstab.prep import prepare, ALL_SETS, LAM

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "results", "random")
FRACS = [0.001, 0.003, 0.01, 0.03, 0.1, 0.3]
R = 200
B = 500


def metrics(theta, c, order0):
    m = c.m
    order = bt.ranking(theta, c)
    rank = np.empty(m, int)
    rank[order] = np.arange(m)
    r0 = np.empty(m, int)
    r0[order0] = np.arange(m)
    # discordant pairs relative to the original ranking
    s = theta[:m]
    s0 = -r0.astype(float)
    iu = np.triu_indices(m, 1)
    disc = np.mean(np.sign(s[iu[0]] - s[iu[1]]) != np.sign(s0[iu[0]] - s0[iu[1]]))
    adj = np.mean([theta[order0[k]] < theta[order0[k + 1]] for k in range(m - 1)])
    top5 = min(5, m - 1)
    return dict(top1_changed=float(order[0] != order0[0]),
                top3_set_changed=float(set(order[:3]) != set(order0[:3])),
                top5_set_changed=float(set(order[:top5]) != set(order0[:top5])),
                kendall_dist=float(disc), adj_reversed=float(adj),
                max_rank_shift=float(np.abs(rank - r0).max()))


def flip_units(rng, c, sel):
    """Move `sel` units out of each cell to the opposite outcome (ties -> random side)."""
    w = c.w - sel
    base = (np.arange(len(c.w)) // 3) * 3
    for n in np.where(sel > 0)[0]:
        if c.y[n] == 1.0:
            w[base[n]] += sel[n]
        elif c.y[n] == 0.0:
            w[base[n] + 2] += sel[n]
        else:
            k1 = rng.binomial(int(sel[n]), 0.5)
            w[base[n] + 2] += k1
            w[base[n]] += sel[n] - k1
    return w


def run(name):
    t0 = time.time()
    c, _ = prepare(name)
    theta0 = bt.fit(c, LAM)
    order0 = bt.ranking(theta0, c)
    rng = np.random.default_rng(abs(hash(name)) % (2 ** 32) if False else 12345)
    wint = c.w.astype(np.int64)
    n = int(wint.sum())
    rows = []
    for p in FRACS:
        K = int(round(p * n))
        for rep in range(R):
            sel = rng.multivariate_hypergeometric(wint, K).astype(float)
            th = bt.fit(c.copy(c.w - sel), LAM, theta0)
            rows.append(dict(kind="drop", frac=p, K=K, rep=rep, **metrics(th, c, order0)))
            sel = rng.multivariate_hypergeometric(wint, K).astype(float)
            th = bt.fit(c.copy(flip_units(rng, c, sel)), LAM, theta0)
            rows.append(dict(kind="flip", frac=p, K=K, rep=rep, **metrics(th, c, order0)))
    boots = []
    for rep in range(B):
        w = rng.multinomial(n, c.w / c.w.sum()).astype(float)
        th = bt.fit(c.copy(w), LAM, theta0)
        boots.append(th)
        rows.append(dict(kind="bootstrap", frac=np.nan, K=n, rep=rep, **metrics(th, c, order0)))
    os.makedirs(OUT, exist_ok=True)
    pd.DataFrame(rows).to_parquet(os.path.join(OUT, name + ".parquet"))
    np.save(os.path.join(OUT, name + ".boot_theta.npy"), np.array(boots))
    return name, time.time() - t0


if __name__ == "__main__":
    names = sys.argv[1:] or ALL_SETS
    with Pool(min(len(names), 38)) as pool:
        for nm, sec in pool.imap_unordered(run, names):
            print(nm, f"{sec:.0f}s", flush=True)
