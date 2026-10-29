"""E6 (SEMI-SYNTHETIC): does the comparison schedule, holding true strengths fixed, change fragility?

True strengths := BT scores fitted on the real data.  Synthetic decisive outcomes
(no ties) are drawn from the BT model under two schedules with the same total N:
  'empirical' : the real per-pair comparison counts,
  'balanced'  : N spread uniformly over all player pairs.
All results of this script are synthetic and are labelled as such in the paper.
-> results/e6_schedule.csv, results/e6_pairs.csv
"""
from common import *  # noqa
import multiprocessing as mp
import numpy as np
import pandas as pd
from scipy.special import expit
from lbrobust import data as D
from lbrobust.bt import CompData, from_records
from lbrobust.perturb import Searcher
from lbrobust.analysis import analyze_dataset

SEEDS = 20


def synth(d, theta, schedule, seed):
    rng = np.random.default_rng(seed)
    K = d.K
    # empirical per-pair counts (ignoring labels)
    if d.home is None:
        key_i, key_j = d.i, d.j
    else:
        key_i, key_j = d.i, d.j
    pc = {}
    for a, b, n in zip(key_i, key_j, d.n):
        pc[(a, b)] = pc.get((a, b), 0) + n
    N = int(d.N)
    if schedule == "empirical":
        pairs = list(pc.keys())
        cnt = np.array([pc[p] for p in pairs], int)
    else:
        if d.home is None:
            ii, jj = np.triu_indices(K, 1)
        else:
            ii, jj = np.where(~np.eye(K, dtype=bool))
        pairs = list(zip(ii, jj))
        cnt = rng.multinomial(N, np.full(len(pairs), 1.0 / len(pairs)))
    a = np.repeat([p[0] for p in pairs], cnt)
    b = np.repeat([p[1] for p in pairs], cnt)
    s = theta[a] - theta[b] + (theta[-1] if d.home is not None else 0.0)
    y = (rng.random(len(a)) < expit(s)).astype(float)
    names = list(range(K))
    out = from_records(a, b, y, names=names, home=None if d.home is None else np.ones(len(a)),
                       meta=dict(name=d.meta["name"] + f"-synth-{schedule}", design="synthetic"))
    out.names = list(d.names)
    return out


def job(spec):
    name, schedule, seed = spec
    d = D.load(name)
    theta = Searcher(d).fit0.theta
    ds = synth(d, theta, schedule, 5000 + seed)
    pairs, s = analyze_dataset(ds, families=("drop", "flip"), top1_cands=3, sig_cands=10)
    s.update(source=name, schedule=schedule, seed=seed)
    pairs["source"] = name
    pairs["schedule"] = schedule
    pairs["seed"] = seed
    return pairs[pairs.roles.str.contains("adjacent")], s


if __name__ == "__main__":
    specs = [(n, sch, s) for n in ("arena55k", "arena140k", "mt_human", "nba2015")
             for sch in ("empirical", "balanced") for s in range(SEEDS)]
    with Timer("e6"):
        with mp.Pool(NPROC) as p:
            out = p.map(job, specs, chunksize=1)
    pd.concat([o[0] for o in out]).to_csv(f"{RES}/e6_pairs.csv", index=False)
    pd.DataFrame([o[1] for o in out]).to_csv(f"{RES}/e6_schedule.csv", index=False)
