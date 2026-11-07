"""Experiments 2-3.
 (a) rank-shift cost: pairs (r, r+d), d=1..5 for every unit            -> results/rankshift.csv
 (b) Arena subsampling (fraction of votes kept)                         -> results/subsample.csv
 (c) matched control: Arena restricted to the six MT-Bench models        -> results/matched.csv
Run from code/: python run_rankshift_scaling.py"""
import os
import numpy as np, pandas as pd
from multiprocessing import Pool
from data import *
from common import *

SEED = 7
NBA = list(range(2000, 2016))
FRACS = [1 / 32, 1 / 16, 1 / 8, 1 / 4, 1 / 2]
REPS = 10
MT6 = {"gpt-4-0314": "gpt-4", "claude-1": "claude-v1", "gpt-3.5-turbo-0314": "gpt-3.5-turbo",
       "vicuna-13b": "vicuna-13b-v1.2", "alpaca-13b": "alpaca-13b", "llama-13b": "llama-13b"}


def unit_ds(u):
    return {"arena": load_arena, "mt_human": load_mt_human, "mt_gpt4": load_mt_gpt4}[u]() if isinstance(u, str) else load_nba_season(u)


def rankshift(u):
    ds = unit_ds(u); lab = u if isinstance(u, str) else f"nba{u}"
    rng = np.random.default_rng([SEED, 1, sum(map(ord, lab))])
    rows, th, order = pair_table(cells_of(ds), rng, B=100, modes=("remove", "relabel"), dmax=5)
    for r in rows:
        r["unit"] = lab; r["a"] = ds["names"][r["i"]]; r["b"] = ds["names"][r["j"]]
    return rows


def sub_job(args):
    frac, rep = args
    ds = load_arena()
    rng = np.random.default_rng([SEED, 2, int(1 / frac), rep])
    cells = subsample_cells(ds, frac, rng)
    rows, th, order = pair_table(cells, rng, B=50, modes=("remove", "relabel"), dmax=1)
    for r in rows:
        r["frac"] = frac; r["rep"] = rep; r["a"] = ds["names"][r["i"]]; r["b"] = ds["names"][r["j"]]
    return rows


def matched():
    ds = load_arena()
    keep = [ds["names"].index(m) for m in MT6]
    mp = {k: t for t, k in enumerate(keep)}
    m = np.isin(ds["a"], keep) & np.isin(ds["b"], keep)
    a = np.array([mp[x] for x in ds["a"][m]]); b = np.array([mp[x] for x in ds["b"][m]])
    names = [list(MT6.values())[t] for t in range(6)]
    out = dict(names=names, a=a, b=b, y=ds["y"][m])
    return out


if __name__ == "__main__":
    units = ["arena", "mt_human", "mt_gpt4"] + NBA
    with Pool(20) as p:
        rs = [r for o in p.map(rankshift, units) for r in o]
        pd.DataFrame(rs).to_csv(os.path.join(RES, "rankshift.csv"), index=False)
        jobs = [(f, r) for f in FRACS for r in range(REPS)]
        ss = [r for o in p.map(sub_job, jobs) for r in o]
        pd.DataFrame(ss).to_csv(os.path.join(RES, "subsample.csv"), index=False)
    # matched control: Arena restricted to the six MT-Bench models (N is whatever remains)
    ds = matched()
    print("matched Arena-6: votes", len(ds["y"]), "tie frac", (ds["y"] == 0.5).mean())
    rng = np.random.default_rng([SEED, 3])
    cells = cells_of(ds)
    rows, th, order = pair_table(cells, rng, B=200, modes=("remove", "relabel", "insert"), dmax=1)
    for r in rows:
        r["a"] = ds["names"][r["i"]]; r["b"] = ds["names"][r["j"]]
    pd.DataFrame(rows).to_csv(os.path.join(RES, "matched.csv"), index=False)
    # also the same six models in MT-Bench human for theta comparison
    print({ds["names"][q]: round(float(th[q]), 3) for q in order})
    mh = load_mt_human(); ch = cells_of(mh); t2, _ = fit(ch)
    print({mh["names"][q]: round(float(t2[q]), 3) for q in ranking(t2)})
