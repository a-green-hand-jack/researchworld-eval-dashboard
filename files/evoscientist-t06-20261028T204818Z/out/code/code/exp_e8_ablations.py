"""E8: robustness of the conclusions to analysis choices.
Variants: tie handling (half-win vs. ties removed), minimum-comparisons filter (0 / 50 / 500),
ridge strength (1e-4 / 1e-2 / 1), and for NBA the home-advantage covariate (on / off, all seasons).
Metric: verified k*_top1 (drops; leader vs ranks 2..4) and median verified drops over top-5
adjacent pairs.  Output: artifacts/results/e8_ablations.csv
"""
import os
import time

import numpy as np
import pandas as pd

import common
from common import RES, bt, D, pool_map, table


def metrics(tt, lam):
    f0 = bt.fit_bt(tt, lam=lam)
    r = bt.ranking(f0.theta, tt.m)

    def k_of(i, j):
        if f0.theta[i] - f0.theta[j] <= 1e-8:
            return 0
        return bt.min_perturbation(tt, i, j, "drop", lam=lam, fit0=f0)["k"]
    ks = [k_of(int(r[0]), int(r[q])) for q in range(1, min(4, tt.m))]
    adj = [ks[0]] + [k_of(int(r[q]), int(r[q + 1])) for q in range(1, min(5, tt.m - 1))]
    ks = [k for k in ks if k is not None]
    adj = [k for k in adj if k is not None]
    return dict(N=tt.N, m=tt.m, leader=tt.players[r[0]], runner_up=tt.players[r[1]], k_top1=min(ks),
                med_adj5=float(np.median(adj)), frac_top1=min(ks) / tt.N)


def loader(key, min_games):
    if key == "arena55k":
        return D.arena55k(min_games=min_games)[0]
    if key == "arena140k":
        return D.arena140k(min_games=min_games)[0]
    if key == "st_crowd":
        return D.arena_single_turn(None, min_games=min_games)[0]
    if key == "mt_human":
        return D.mtbench("human", min_games=min_games)[0]
    if key == "mt_gpt4":
        return D.mtbench("gpt4", min_games=min_games)[0]
    if key.startswith("nba"):
        return D.nba_season(int(key[3:]))[0]
    raise KeyError(key)


def job(args):
    key, variant, val = args
    min_games, lam, ties, home = 50, common.LAM, "half", True
    if variant == "min_games":
        min_games = val
    elif variant == "lam":
        lam = val
    elif variant == "ties":
        ties = val
    elif variant == "home":
        home = val
    d = dict(loader(key, min_games if not key.startswith("nba") else 0))
    if ties == "drop":
        keep = d["y"] != 0.5
        d = {k: (v[keep] if isinstance(v, np.ndarray) else v) for k, v in d.items()}
    if key.startswith("nba"):
        d["use_home"] = home
    tt = table(d)
    out = dict(dataset=key, variant=variant, value=str(val))
    out.update(metrics(tt, lam))
    return out


def main():
    keys = ["arena140k", "arena55k", "st_crowd", "mt_human", "mt_gpt4", "nba2015"]
    jobs = []
    for k in keys:
        jobs.append((k, "default", "-"))
        jobs += [(k, "lam", v) for v in (1e-4, 1.0)]
        jobs.append((k, "ties", "drop"))
        if not k.startswith("nba"):
            jobs += [(k, "min_games", v) for v in (0, 500)]
    for yr in D.NBA_SEASONS:
        jobs.append((f"nba{yr}", "home", True))
        jobs.append((f"nba{yr}", "home", False))
    t0 = time.time()
    rows = pool_map(job, jobs)
    pd.DataFrame(rows).to_csv(os.path.join(RES, "e8_ablations.csv"), index=False)
    print(f"done {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
