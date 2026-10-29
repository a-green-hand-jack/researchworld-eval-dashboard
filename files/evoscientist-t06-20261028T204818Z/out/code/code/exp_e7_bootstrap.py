"""E7: sampling uncertainty of the fragility metrics themselves.

For each main dataset, draw B nonparametric bootstrap resamples of the comparisons, refit, and
recompute (i) k*_top1 = min verified drops that dethrone the (resample's) leader, minimised over
challengers in ranks 2..4, and (ii) median verified drop count over the top-5 adjacent pairs.
Also computes the same metrics on monthly slices of Arena-140k (temporal replicates).
Output: artifacts/results/e7_bootstrap.csv, e7_monthly.csv
"""
import os
import time
import zlib

import numpy as np
import pandas as pd

from common import LAM, RES, bt, D, pool_map, table

TABLES = {}
B = 30
SEED = 20261028


def metrics(tt, n=None):
    if n is not None:
        tt = bt.TypeTable(players=tt.players, a=tt.a, b=tt.b, h=tt.h, y=tt.y, n=n, key=tt.key, use_home=tt.use_home)
    f0 = bt.fit_bt(tt, lam=LAM)
    r = bt.ranking(f0.theta, tt.m)
    ks = []
    for q in range(1, min(4, tt.m)):
        i, j = int(r[0]), int(r[q])
        if f0.theta[i] - f0.theta[j] <= 1e-8:
            ks.append(0)
            continue
        ks.append(bt.min_perturbation(tt, i, j, "drop", lam=LAM, fit0=f0)["k"])
    adj = [ks[0]]
    for q in range(1, min(5, tt.m - 1)):
        i, j = int(r[q]), int(r[q + 1])
        if f0.theta[i] - f0.theta[j] <= 1e-8:
            adj.append(0)
            continue
        adj.append(bt.min_perturbation(tt, i, j, "drop", lam=LAM, fit0=f0)["k"])
    ks = [k for k in ks if k is not None]
    adj = [k for k in adj if k is not None]
    return dict(N=tt.N, leader=tt.players[r[0]], k_top1=min(ks), med_adj5=float(np.median(adj)))


def boot_job(args):
    key, b = args
    tt = TABLES[key]
    rng = np.random.default_rng(SEED + zlib.crc32(f"boot|{key}|{b}".encode()) % 10**6)
    n2 = rng.multinomial(int(tt.N), tt.n / tt.N).astype(float) if b >= 0 else None
    out = dict(dataset=key, b=b)
    out.update(metrics(tt, n2))
    return out


def month_job(month):
    d, raw = D.arena140k()
    df = raw[raw.ts.str[:7] == month].copy()
    p = D._pack(df, "crowd", f"Arena-140k {month}")
    tt = table(p)
    out = dict(dataset="arena140k", month=month, m=tt.m)
    out.update(metrics(tt))
    return out


def main():
    ds = D.all_main(include_nba_all=False)
    for k, d in ds.items():
        TABLES[k] = table(d)
    jobs = [(k, b) for k in ds for b in [-1] + list(range(B))]
    jobs.sort(key=lambda t: -TABLES[t[0]].N)
    t0 = time.time()
    rows = pool_map(boot_job, jobs)
    pd.DataFrame(rows).to_csv(os.path.join(RES, "e7_bootstrap.csv"), index=False)
    print(f"bootstrap done {time.time() - t0:.0f}s", flush=True)
    months = ["2025-04", "2025-05", "2025-06", "2025-07"]
    rows = pool_map(month_job, months, workers=4)
    pd.DataFrame(rows).to_csv(os.path.join(RES, "e7_monthly.csv"), index=False)
    print(f"all done {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
