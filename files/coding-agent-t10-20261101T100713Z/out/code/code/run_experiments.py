"""Monte-Carlo coverage / width experiments.

usage: python run_experiments.py --suite {real,synth} --reps 1000 --out ../results/real.csv.gz [--procs 38]
Each cell (dataset, n, N) is repeated `reps` times; seeds are SeedSequence([BASE_SEED, dataset id, n, N, rep]).
"""
import os
os.environ.setdefault("OMP_NUM_THREADS", "1"); os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
import argparse, time, zlib
import numpy as np, pandas as pd
from multiprocessing import Pool
import warnings; warnings.filterwarnings("ignore")
from datasets import REAL, SYNTH, get_pop, learners_for
from methods import baselines, aipw_methods

BASE_SEED = 20261101
N_SWEEP = [25, 50, 100, 200, 500, 1000]; BIG_N = 5000
UNL_SWEEP = [50, 200, 1000, 5000, 20000]; FIXED_n = 200
_POPS = {}


def cells():
    s = {(n, BIG_N) for n in N_SWEEP} | {(FIXED_n, N) for N in UNL_SWEEP}
    return sorted(s)


def one_rep(args):
    name, n, N, rep = args
    if name not in _POPS:
        _POPS[name] = get_pop(name)
    pop = _POPS[name]
    rng = np.random.default_rng(np.random.SeedSequence([BASE_SEED, zlib.crc32(name.encode()), n, N, rep]))
    Y, F, X = pop.draw(rng, n)
    _, Fu, Xu = pop.draw(rng, N)
    res = {}
    for k, v in baselines(Y, F, Fu).items():
        res[k] = (v[0], v[1], n - 1)
    res.update(aipw_methods(Y, F, X, Fu, Xu, learners_for(pop), rng=rng))
    choice = res.pop("_auto_choice")
    rows = [dict(dataset=name, n=n, N=N, rep=rep, method=m, est=e, se=s, df=d, truth=pop.truth,
                 choice=choice if m.startswith("aipw-auto") else "")
            for m, (e, s, d) in res.items()]
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", required=True); ap.add_argument("--reps", type=int, default=1000)
    ap.add_argument("--out", required=True); ap.add_argument("--procs", type=int, default=38)
    ap.add_argument("--datasets", default=None)
    a = ap.parse_args()
    names = a.datasets.split(",") if a.datasets else (REAL if a.suite == "real" else list(SYNTH))
    # plankton's unlabeled 2014 half is not used here (distribution shift is treated in run_shift.py)
    tasks = [(d, n, N, r) for d in names for (n, N) in cells() for r in range(a.reps)]
    print(len(tasks), "replications", flush=True)
    t0 = time.time()
    with Pool(a.procs) as pool:
        out = []
        for i, rows in enumerate(pool.imap_unordered(one_rep, tasks, chunksize=20)):
            out.extend(rows)
            if i % 5000 == 0:
                print(i, "%.0fs" % (time.time() - t0), flush=True)
    pd.DataFrame(out).to_csv(a.out, index=False)
    print("done %.0fs" % (time.time() - t0))
