"""Estimator sensitivity of the flip budgets (paper-repo request #9b).

Variants of the fit for every dataset: base (L2 lambda=1, a tie is a half win: FastChat's compute_bt also labels a draw 0.5),
lam_1e-6 (practically unregularised), drop_ties (tied battles deleted), tie_wl (a tie counts as one win AND one loss of the pair, i.e. weight 2).
Each variant defines its own base ranking and its own claims (C1 and the adjacent-pair orders of the window); budgets are verified exact-refit
upper bounds of the greedy search with pruning factor 10 (as the other secondary analyses). Datasets without ties (NBA) only differ in lambda.
Writes results/s5_estimator.csv (budgets) and results/s5_estimator_rank.csv (agreement of each variant's ranking with the base one).
Usage: python code/s5_estimator.py"""
import os
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

from btlib import analysis as an
from btlib import data, prov, units
from btlib.core import Counts

OUT = os.path.join(os.path.dirname(__file__), "..", "results")
PRUNE = 10.0
DATASETS = ["arena55k", "mt_human", "mt_gpt4", "nba_all"]


def base_unit(name, lam=1.0, drop_ties=False):
    if name == "arena55k":
        return units.arena_unit(lam=lam, drop_ties=drop_ties)[0]
    if name in ("mt_human", "mt_gpt4"):
        return units.mt_unit(name[3:], lam=lam, drop_ties=drop_ties)[0]
    return units.nba_all_unit(lam=lam)[0]


def tie_wl(u):
    """Same unit with each tie replaced by one win and one loss: n -> [n0 + n1, 0, n2 + n1]."""
    c = u.c
    n = np.stack([c.n[:, 0] + c.n[:, 1], np.zeros(c.P), c.n[:, 2] + c.n[:, 1]], 1)
    c2 = c.with_n(n)
    return an.Unit(u.name, u.design, c2, u.elig if u.window is None else None, lam=u.lam, lam_h=u.lam_h, meta=dict(u.meta, has_ties=False), window=u.window)


def work(args):
    name, variant = args
    if variant == "base":
        u = base_unit(name)
    elif variant == "lam_1e-6":
        u = base_unit(name, lam=1e-6)
    elif variant == "drop_ties":
        u = base_unit(name, drop_ties=True)
    else:
        u = tie_wl(base_unit(name))
    pairs = {k: v for k, v in an.claim_pairs(u).items() if k == "c1" or k.startswith("c2_")}
    rows = an.budgets(u, "remove", pairs=pairs, prune=PRUNE)
    for r in rows:
        r.update(dataset=name, variant=variant, N=float(u.c.N), top1=u.c.names[u.order[0]])
    return rows, u.x0[: u.c.K], u.c.names, u.order, u.W


def main():
    tasks = []
    for n in DATASETS:
        for v in ("base", "lam_1e-6", "drop_ties", "tie_wl"):
            if n == "nba_all" and v in ("drop_ties", "tie_wl"):
                continue
            tasks.append((n, v))
    with ProcessPoolExecutor(2) as ex:
        res = list(ex.map(work, tasks, chunksize=1))
    rows, rk = [], []
    base = {}
    for (n, v), (r, x, names, order, W) in zip(tasks, res):
        rows += r
        if v == "base":
            base[n] = (x, order, W)
    for (n, v), (r, x, names, order, W) in zip(tasks, res):
        x0, o0, W0 = base[n]
        top0 = o0[:W0]
        # agreement on the base window: Kendall tau of the variant scores against the base scores, and top-1 / window-set overlap
        iu = np.triu_indices(W0, 1)
        d0 = x0[top0][iu[0]] - x0[top0][iu[1]]
        d1 = x[top0][iu[0]] - x[top0][iu[1]]
        tau = float((np.sum(np.sign(d0) == np.sign(d1)) - np.sum(np.sign(d0) != np.sign(d1))) / len(d0))
        rk.append(dict(dataset=n, variant=v, top1=names[order[0]], top1_same=bool(order[0] == o0[0]),
                       window_overlap=len(set(order[:W0]) & set(top0)), window=W0, tau_vs_base_window=tau,
                       max_abs_dscore=float(np.max(np.abs(x[top0] - x0[top0])))))
    pd.DataFrame(rows).to_csv(f"{OUT}/s5_estimator.csv", index=False, float_format="%.6g")
    pd.DataFrame(rk).to_csv(f"{OUT}/s5_estimator_rank.csv", index=False, float_format="%.6g")
    prov.write_meta(f"{OUT}/s5_estimator.meta.json", script="code/s5_estimator.py", prune=PRUNE)


if __name__ == "__main__":
    main()
