"""Experiment 1: adversarial and random sensitivity of every adjacent pair in each leaderboard.
Usage (from repo root): python code/run_pairs.py   -> results/pairs.csv, results/boot_rank.csv"""
import os, time
import numpy as np, pandas as pd
from multiprocessing import Pool
from data import *
from bt import *

SEED = 20261102
B = 200      # bootstrap replicates
R = 50       # random-removal replicates per pair
NBA_SEASONS = list(range(2000, 2016))


def get_unit(u):
    kind, key = u
    if kind == "nba":
        return load_nba_season(key)
    return {"arena": load_arena, "mt_human": load_mt_human, "mt_gpt4": load_mt_gpt4}[kind]()


def analyze(u):
    kind, key = u
    label = kind if kind != "nba" else f"nba{key}"
    ds = get_unit(u)
    n = len(ds["names"])
    rng = np.random.default_rng([SEED, sum(map(ord, label))])
    cells = Cells.from_votes(n, ds["a"], ds["b"], ds["y"])
    th, H = fit(cells)
    order = ranking(th)
    nv = np.bincount(ds["a"], minlength=n) + np.bincount(ds["b"], minlength=n)
    TH = np.zeros((B, n))
    for b in range(B):
        TH[b], _ = fit(bootstrap_cells(cells, rng), th)
    taus = np.array([kendall_tau(th, TH[b]) for b in range(B)])
    top1 = float(np.mean(TH.argmax(1) == order[0]))
    brow = dict(unit=label, kind=kind, N=cells.N, n=n, tau_boot_mean=taus.mean(), tau_boot_lo=np.quantile(taus, .025),
                tau_boot_hi=np.quantile(taus, .975), top1_retention=top1)
    full = with_all_pairs(cells)
    rows = []
    for r in range(n - 1):
        i, j = order[r], order[r + 1]
        gap = th[i] - th[j]
        diff = TH[:, i] - TH[:, j]
        nij = int(cells.C[(cells.pa == min(i, j)) & (cells.pb == max(i, j))].sum())
        nloc = int(nv[i] + nv[j] - nij)
        sd = float(diff.std(ddof=1))
        row = dict(unit=label, kind=kind, N=cells.N, n_players=n, rank=r + 1, a=ds["names"][i], b=ds["names"][j],
                   gap=gap, n_i=int(nv[i]), n_j=int(nv[j]), n_ij=nij, n_local=nloc,
                   boot_sd=sd, z=gap / sd, p_flip_boot=float(np.mean(diff < 0)))
        for mode in ("remove", "relabel", "insert"):
            cc = full if mode == "insert" else cells
            k, _ = greedy_flip(cc, i, j, mode, theta0=th)
            row["k_" + mode] = k
            row["oneshot_" + mode] = oneshot_k(cc, i, j, mode, th, H)
        kr = row["k_remove"]
        if np.isfinite(kr):
            fl = 0
            for _ in range(R):
                t2, _ = fit(remove_random(cells, int(kr), rng), th)
                fl += t2[i] < t2[j]
            row["rand_remove_flip_rate"] = fl / R
        rows.append(row)
    return rows, brow


if __name__ == "__main__":
    units = [("arena", 0), ("mt_human", 0), ("mt_gpt4", 0)] + [("nba", y) for y in NBA_SEASONS]
    t = time.time()
    with Pool(min(len(units), 20)) as p:
        out = p.map(analyze, units)
    rows = [r for o in out for r in o[0]]
    pd.DataFrame(rows).to_csv(os.path.join(RES, "pairs.csv"), index=False)
    pd.DataFrame([o[1] for o in out]).to_csv(os.path.join(RES, "boot_rank.csv"), index=False)
    print("done %.1fs" % (time.time() - t), len(rows))
