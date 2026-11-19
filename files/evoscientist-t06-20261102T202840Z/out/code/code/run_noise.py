"""Experiment 4: random (non-adversarial) data perturbation.  For a fraction f of votes chosen uniformly
at random, (i) relabel to a uniformly chosen other admissible outcome, or (ii) remove.  Records Kendall tau
to the unperturbed BT ranking, top-1 retention and the fraction of adjacent pairs whose order flips.
-> results/noise.csv     Run from code/: python run_noise.py"""
import os
import numpy as np, pandas as pd
from multiprocessing import Pool
from data import *
from common import *

SEED = 11
FS = [0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.4]
NBA = list(range(2000, 2016))


def relabel_random(cells, k, rng, has_tie):
    C = cells.C.copy()
    flat = C.ravel()
    idx = rng.choice(np.repeat(np.arange(flat.size), flat), size=k, replace=False)
    P = C.shape[0]
    new = C.copy()
    for t in idx:
        p, o = divmod(int(t), 3)
        opts = [x for x in (0, 1, 2) if x != o and (has_tie or x != 1)]
        o2 = opts[rng.integers(len(opts))]
        new[p, o] -= 1; new[p, o2] += 1
    return Cells(cells.n, cells.pa, cells.pb, new)


def job(args):
    u, rep = args
    ds = {"arena": load_arena, "mt_human": load_mt_human, "mt_gpt4": load_mt_gpt4}[u]() if isinstance(u, str) else load_nba_season(u)
    lab = u if isinstance(u, str) else f"nba{u}"
    cells = cells_of(ds)
    has_tie = bool(cells.C[:, 1].sum() > 0)
    rng = np.random.default_rng([SEED, rep, sum(map(ord, lab))])
    th, _ = fit(cells)
    order = ranking(th)
    rank0 = np.empty(len(th), int); rank0[order] = np.arange(len(th))
    rows = []
    for f in FS:
        k = int(round(f * cells.N))
        for kind in ("relabel", "remove"):
            c2 = relabel_random(cells, k, rng, has_tie) if kind == "relabel" else remove_random(cells, k, rng)
            t2, _ = fit(c2, th)
            adj_flip = np.mean([t2[order[r]] < t2[order[r + 1]] for r in range(len(th) - 1)])
            rows.append(dict(unit=lab, rep=rep, f=f, kind=kind, tau=kendall_tau(th, t2),
                             top1_kept=float(np.argmax(t2) == order[0]), adj_flip=float(adj_flip)))
    return rows


if __name__ == "__main__":
    jobs = [("arena", r) for r in range(30)] + [("mt_human", r) for r in range(30)] + [("mt_gpt4", r) for r in range(30)] \
        + [(y, r) for y in NBA for r in range(5)]
    with Pool(20) as p:
        rows = [r for o in p.map(job, jobs) for r in o]
    pd.DataFrame(rows).to_csv(os.path.join(RES, "noise.csv"), index=False)
    print(len(rows))
