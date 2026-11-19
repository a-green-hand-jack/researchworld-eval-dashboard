"""Cluster / block bootstrap of the BT fit: resample whole clusters of comparisons (question, prompt, season, week) instead of single comparisons."""
from __future__ import annotations

import numpy as np
import scipy.sparse as sp

from . import core


def row_cells(c: core.Counts, ds, rows=None):
    """Flat cell index (type * 3 + outcome) of every comparison row of `ds` in the aggregated counts `c` (built with ds.counts(), home=False)."""
    i, j, y = ds.i, ds.j, ds.y
    if rows is not None:
        i, j, y = i[rows], j[rows], y[rows]
    swap = i > j
    i2 = np.where(swap, j, i); j2 = np.where(swap, i, j)
    y2 = np.where(swap & (y != 1), 2 - y, y)
    key = (i2.astype(np.int64) * c.K + j2) * 3 + 1  # h = 0 -> +1
    ck = (c.ti * c.K + c.tj) * 3 + (c.th + 1).astype(np.int64)
    pos = np.searchsorted(ck, key)
    assert np.all(ck[pos] == key)
    return pos * 3 + y2


def cluster_matrix(c: core.Counts, ds):
    """Sparse (n_clusters, P*3) matrix of cell counts per cluster."""
    cell = row_cells(c, ds)
    cl = np.unique(ds.cluster, return_inverse=True)[1]
    return sp.csr_matrix((np.ones(len(cell)), (cl, cell)), shape=(cl.max() + 1, c.P * 3))


def cluster_bootstrap_fits(unit, ds, B, seed=0):
    """(B, K) scores of B cluster-bootstrap refits (clusters drawn with replacement, same number of clusters)."""
    c = unit.c
    M = cluster_matrix(c, ds)
    G = M.shape[0]
    out = np.empty((B, c.K))
    for b in range(B):
        rng = np.random.default_rng([seed, 20_000 + b])
        m = rng.multinomial(G, np.full(G, 1.0 / G))
        n2 = (M.T @ m).reshape(-1, 3)
        out[b] = core.fit(c.with_n(n2), unit.lam, unit.lam_h, theta0=unit.x0)[: c.K]
    return out
