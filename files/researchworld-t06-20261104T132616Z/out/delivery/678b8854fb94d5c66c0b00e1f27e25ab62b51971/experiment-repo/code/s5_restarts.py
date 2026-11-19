"""Randomised-restart check of the greedy+polish adversarial search (paper-repo request #10a).

For the claim pair (a, b) that gave the verified budget of each C1 / C2 claim in results/budgets_remove.csv, the removal search is repeated R = 50
times with randomised cell order (gains multiplied by exp(sigma * N(0,1)), sigma in {0.3, 1.0} alternately) and a random chunk fraction in
[0.1, 0.6] (core.adversarial_flip(gain_noise=...)); every result is verified by exact refits. Reported per claim: the deterministic budget,
the minimum / median / maximum over the restarts and the share of restarts that reach the deterministic budget or better.
This is an empirical check of the search, NOT a certificate: no lower bound is proven (the flip problem is a combinatorial optimisation over
integer cell counts; the first-order estimate lin_est is reported next to it as a heuristic reference only).
Writes results/parts/s5_restarts_<unit>.csv.   Usage: python code/s5_restarts.py --units mt_human,mt_gpt4 [--R 50] [--workers 2]"""
import argparse
import os
import zlib
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

from btlib import core, prov
from s5_published import build

OUT = os.path.join(os.path.dirname(__file__), "..", "results")
_U = {}


def unit(name):
    if name not in _U:
        _U[name] = build(name)
    return _U[name]


def work(args):
    name, claim, a, b, r0, r1 = args
    u = unit(name)
    names = {n: i for i, n in enumerate(u.c.names)}
    ia, ib = names[a], names[b]
    ks = []
    for r in range(r0, r1):
        rng = np.random.default_rng([13, zlib.crc32(f"{name}|{claim}".encode()), r])
        res = core.adversarial_flip(u.c, ia, ib, u.lam, mode="remove", x0=u.x0, lam_h=u.lam_h, rng=rng, gain_noise=0.3 if r % 2 == 0 else 1.0)
        ks.append(res["k"] if res["flipped"] else np.nan)
    return name, claim, ks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--units", default="mt_human,mt_gpt4,arena55k,nba_all")
    ap.add_argument("--R", type=int, default=50)
    ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args()
    d = pd.read_csv(f"{OUT}/budgets_remove.csv")
    d = d[d.claim.eq("c1") | d.claim.str.startswith("c2_")]
    step = 10
    for name in a.units.split(","):
        s = d[d.unit == name]
        tasks = [(name, r.claim, r.a, r.b, r0, min(r0 + step, a.R)) for r in s.itertuples() for r0 in range(0, a.R, step)]
        with ProcessPoolExecutor(a.workers) as ex:
            res = list(ex.map(work, tasks, chunksize=1))
        rows = []
        for r in s.itertuples():
            ks = np.array([k for (_, cl, kk) in res if cl == r.claim for k in kk], dtype=float)
            ok = ks[np.isfinite(ks)]
            rows.append(dict(unit=name, claim=r.claim, a=r.a, b=r.b, N=r.N, budget_det=r.budget, lin_est=r.lin_est, R=len(ks), n_flipped=len(ok),
                             restart_min=ok.min() if len(ok) else np.nan, restart_median=np.median(ok) if len(ok) else np.nan,
                             restart_max=ok.max() if len(ok) else np.nan,
                             share_le_det=float(np.mean(ok <= r.budget)) if len(ok) else np.nan,
                             best_overall=min(ok.min(), r.budget) if len(ok) else r.budget))
        os.makedirs(f"{OUT}/parts", exist_ok=True)
        pd.DataFrame(rows).to_csv(f"{OUT}/parts/s5_restarts_{name}.csv", index=False, float_format="%.6g")
        prov.write_meta(f"{OUT}/parts/s5_restarts_{name}.meta.json", script="code/s5_restarts.py", R=a.R)


if __name__ == "__main__":
    main()
