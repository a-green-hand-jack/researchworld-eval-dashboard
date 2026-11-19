"""E4 (number of tasks m) and E5 (uncertainty: evaluation-noise bootstrap and task bootstrap).
Outputs results/e4_scaling.csv, results/e5_uncertainty.csv
Usage: python code/run_scaling_uncert.py [e4|e5]
"""
import os, sys
import numpy as np, pandas as pd
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lb import agg, boards, runner

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
RULES = agg.ALL_RULES
SEED = 20261102
SIZES = {"helm57": [3, 5, 9, 15, 25, 40, 57], "bbh24x": [3, 5, 8, 12, 18, 24]}
R4, R5 = 30, 100
B = {}


def job_e4(a):
    bname, msz, rep = a
    rng = np.random.default_rng([SEED, 4, msz, rep])
    idx = np.sort(rng.choice(B[bname].m, size=msz, replace=False)) if msz < B[bname].m else np.arange(msz)
    S = B[bname].S[:, idx]
    rows = runner.contender_costs(S, RULES, "ceil", 10)
    for r in rows:
        r.update(board=bname, m=msz, rep=rep)
    return rows


def job_e5(a):
    bname, kind, rep, scen = a
    rng = np.random.default_rng([SEED, 5, {"noise": 0, "taskboot": 1}[kind], rep])
    b = B[bname]
    if kind == "noise":
        S = np.clip(b.S + rng.standard_normal(b.S.shape) * b.noise_sd, 0, 100)
    else:  # task bootstrap
        idx = rng.integers(0, b.m, size=b.m)
        S = b.S[:, idx]
    rows = runner.contender_costs(S, RULES, scen, 10)
    for r in rows:
        r.update(board=bname, kind=kind, rep=rep, scenario=str(scen), m=S.shape[1])
    return rows


if __name__ == "__main__":
    which = sys.argv[1:] or ["e4", "e5"]
    for nm in boards.BOARDS:
        B[nm] = boards.load(nm)
    if "e4" in which:
        jobs = [(nm, msz, rep) for nm in SIZES for msz in SIZES[nm] for rep in range(R4 if msz < B[nm].m else 1)]
        with Pool(36) as pool:
            res = pool.map(job_e4, jobs, chunksize=1)
        pd.DataFrame([r for rows in res for r in rows]).to_csv(os.path.join(OUT, "e4_scaling.csv"), index=False)
        print("E4 done", flush=True)
    if "e5" in which:
        jobs = [(nm, kind, rep, sc) for nm in boards.BOARDS for kind in ("noise", "taskboot") for rep in range(R5)
                for sc in ("ceil", 10.0)]
        with Pool(36) as pool:
            res = pool.map(job_e5, jobs, chunksize=1)
        pd.DataFrame([r for rows in res for r in rows]).to_csv(os.path.join(OUT, "e5_uncertainty.csv"), index=False)
        print("E5 done", flush=True)
