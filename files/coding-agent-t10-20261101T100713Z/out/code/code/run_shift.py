"""Failure case: plankton, labeled data from 2013, unlabeled data from 2014, target = mean label in 2014.
The MCAR-labeling assumption is violated (covariate/label shift), so no method is expected to be valid.
usage: python run_shift.py --reps 1000 --out ../results/shift.csv.gz
"""
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
import argparse, numpy as np, pandas as pd
from multiprocessing import Pool
import warnings; warnings.filterwarnings("ignore")
from methods import baselines, aipw_methods
from run_experiments import BASE_SEED

d = np.load(os.path.join(os.environ.get("PPI_DATA_DIR", "/work/data"), "plankton.npz"))
Y2013, F2013, Fu2014, Yu2014 = (d[k].astype(float) for k in ["Y", "Yhat", "Yhat_unlabeled", "Y_unlabeled"])
TRUTH2014 = Yu2014.mean()


def one(args):
    n, N, rep = args
    rng = np.random.default_rng(np.random.SeedSequence([BASE_SEED, 777, n, N, rep]))
    i = rng.integers(0, len(Y2013), n); j = rng.integers(0, len(Fu2014), N)
    Y, F, Fu = Y2013[i], F2013[i], Fu2014[j]
    X0, Xu0 = np.zeros((n, 0)), np.zeros((N, 0))
    res = {k: (v[0], v[1], n - 1) for k, v in baselines(Y, F, Fu).items()}
    r2 = aipw_methods(Y, F, X0, Fu, Xu0, ["lin", "iso"], rng=rng); r2.pop("_auto_choice"); res.update(r2)
    return [dict(n=n, N=N, rep=rep, method=m, est=e, se=s, df=df, truth=TRUTH2014) for m, (e, s, df) in res.items()]


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--reps", type=int, default=1000)
    ap.add_argument("--out", required=True); ap.add_argument("--procs", type=int, default=38)
    a = ap.parse_args()
    tasks = [(n, 5000, r) for n in [100, 200, 500, 1000, 5000] for r in range(a.reps)]
    with Pool(a.procs) as p:
        rows = [x for rr in p.imap_unordered(one, tasks, chunksize=20) for x in rr]
    pd.DataFrame(rows).to_csv(a.out, index=False)
    print("true 2014 mean %.4f; 2013 mean %.4f" % (TRUTH2014, Y2013.mean()))
