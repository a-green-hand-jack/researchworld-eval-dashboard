"""E1: worst-case fragility of leaderboard orderings.

For every dataset: fit BT, then for (a) every adjacent pair among the top-10 and (b) the leader
vs. every challenger in ranks 2..10, find the smallest verified perturbation (drop / flip / add)
that reverses the pair.  Output: artifacts/results/e1_pairs.csv

Usage: python code/exp_e1_fragility.py [--nba-all] [--kinds drop,flip,add]
"""
import argparse
import math
import time

import numpy as np
import pandas as pd

from common import LAM, RES, bt, D, move_profile, pool_map, table

TABLES = {}
TABLES_ADD = {}
META = {}


def pair_task(args):
    key, i, j, kind, ptype = args
    tt = TABLES_ADD[key] if kind == "add" else TABLES[key]
    f0 = bt.fit_bt(tt, lam=LAM)
    r = bt.ranking(f0.theta, tt.m)
    rank = {p: q + 1 for q, p in enumerate(r)}
    gap = f0.theta[i] - f0.theta[j]
    se_m, se_s = bt.pair_se(tt, f0, i, j)
    pc = tt.player_counts()
    nij = float(tt.n[((tt.a == i) & (tt.b == j)) | ((tt.a == j) & (tt.b == i))].sum())
    row = dict(dataset=key, design=META[key]["design"], label=META[key]["label"], kind=kind, pair_type=ptype,
               i=tt.players[i], j=tt.players[j], rank_i=rank[i], rank_j=rank[j], N=tt.N, m=tt.m,
               gap=gap, se_model=se_m, se_sand=se_s, z_model=gap / se_m, z_sand=gap / se_s,
               n_i=pc[i], n_j=pc[j], n_ij=nij)
    t0 = time.time()
    if gap <= 1e-8:
        row.update(k=0, k_iter=0, k_oneshot=0, k_pred=0)
    else:
        res = bt.min_perturbation(tt, i, j, kind=kind, lam=LAM, fit0=f0)
        row.update(k=res["k"], k_iter=res["k_iter"], k_oneshot=res["k_oneshot"], k_pred=res["k_pred"],
                   n_iter=res["n_iter"])
        if res["moves"]:
            row.update(move_profile(tt, res["moves"], i, j))
            # first-order prediction of the gap change for the found set vs actual refit
            eff, src, dst, cap = bt.candidate_moves(tt, f0, tt.n, i, j, kind)
            lookup = {(int(s), int(d)): e for e, s, d in zip(eff, src, dst)}
            pred = 0.0
            for s, d, c in res["moves"]:
                e = lookup.get((s, d))
                if e is None:   # flip destination differs from the initially-best one: compute directly
                    cdir = bt.gap_direction(tt, f0, i, j)
                    t = s if s >= 0 else d
                    e = cdir[t] * (tt.y[d] - tt.y[s]) if (s >= 0 and d >= 0) else (
                        -cdir[t] * (tt.y[t] - f0.p[t]) if d < 0 else cdir[t] * (tt.y[t] - f0.p[t]))
                pred += c * e
            f1 = bt.fit_bt(tt, bt._apply(tt.n, res["moves"]), lam=LAM, theta0=f0.theta)
            row.update(pred_gap_change=pred, actual_gap_change=(f1.theta[i] - f1.theta[j]) - gap)
    row["seconds"] = time.time() - t0
    return row


def tasks_for(key, kinds, top=10):
    tt = TABLES[key]
    f0 = bt.fit_bt(tt, lam=LAM)
    r = bt.ranking(f0.theta, tt.m)
    R = min(top, tt.m)
    out = []
    for kind in kinds:
        for q in range(R - 1):
            out.append((key, int(r[q]), int(r[q + 1]), kind, "adjacent"))
        for q in range(2, R):     # leader vs ranks 3..R (rank 2 already covered by adjacent)
            out.append((key, int(r[0]), int(r[q]), kind, "leader"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nba-all", action="store_true")
    ap.add_argument("--kinds", default="drop,flip,add")
    ap.add_argument("--only", default=None, help="comma-separated dataset keys")
    ap.add_argument("--out", default="e1_pairs.csv")
    args = ap.parse_args()
    ds = D.all_main(include_nba_all=args.nba_all)
    if args.only:
        ds = {k: v for k, v in ds.items() if k in args.only.split(",")}
    kinds = args.kinds.split(",")
    for k, d in ds.items():
        TABLES[k] = table(d)
        if "add" in kinds:
            TABLES_ADD[k] = table(d, all_pairs=True)
        META[k] = dict(design=d["design"], label=d["label"])
    tasks = [t for k in ds for t in tasks_for(k, kinds)]
    # big tables first for load balance
    tasks.sort(key=lambda t: -TABLES[t[0]].N)
    print(f"{len(tasks)} tasks", flush=True)
    t0 = time.time()
    rows = pool_map(pair_task, tasks)
    df = pd.DataFrame(rows)
    df.to_csv(f"{RES}/{args.out}", index=False)
    print(f"done in {time.time() - t0:.0f}s -> {RES}/{args.out}")


if __name__ == "__main__":
    main()
