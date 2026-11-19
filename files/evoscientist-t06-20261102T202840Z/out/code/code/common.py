import numpy as np
from bt import *


def votes_per_player(cells):
    return np.bincount(cells.pa, cells.npair(), cells.n) + np.bincount(cells.pb, cells.npair(), cells.n)


def pair_table(cells, rng, B=100, modes=("remove", "relabel"), dmax=1, boot_fn=None, ranks=None):
    """Rows for pairs (rank r, rank r+d), d=1..dmax.  z = gap / bootstrap-sd of the contrast."""
    th, H = fit(cells)
    n = cells.n
    order = ranking(th)
    nv = votes_per_player(cells)
    boot_fn = boot_fn or bootstrap_cells
    TH = np.zeros((B, n))
    for b in range(B):
        TH[b], _ = fit(boot_fn(cells, rng), th)
    rows = []
    for d in range(1, dmax + 1):
        for r in range(n - d):
            if ranks is not None and (r + 1) not in ranks:
                continue
            i, j = order[r], order[r + d]
            nij = int(cells.C[(cells.pa == min(i, j)) & (cells.pb == max(i, j))].sum())
            nloc = int(nv[i] + nv[j] - nij)
            gap = th[i] - th[j]
            diff = TH[:, i] - TH[:, j]
            sd = float(diff.std(ddof=1))
            row = dict(rank=r + 1, d=d, i=int(i), j=int(j), gap=gap, n_local=nloc, N=cells.N, boot_sd=sd,
                       z=gap / sd if sd > 0 else np.nan, p_flip_boot=float(np.mean(diff < 0)))
            for mode in modes:
                cc = with_all_pairs(cells) if mode == "insert" else cells
                k, _ = greedy_flip(cc, i, j, mode, theta0=th)
                row["k_" + mode] = k
            rows.append(row)
    return rows, th, order


def subsample_cells(ds, frac, rng):
    N = len(ds["y"])
    idx = rng.choice(N, size=int(round(frac * N)), replace=False)
    return Cells.from_votes(len(ds["names"]), ds["a"][idx], ds["b"][idx], ds["y"][idx])


def cells_of(ds):
    return Cells.from_votes(len(ds["names"]), ds["a"], ds["b"], ds["y"])
