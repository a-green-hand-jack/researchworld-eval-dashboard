"""Pairwise agreement between exact Shapley values computed with two independently drawn b-row backgrounds
(background-induced run-to-run variability; complements exp_bg.py which only stored agreement with the reference)."""
import os, sys, time, pickle, argparse
os.environ.setdefault("OMP_NUM_THREADS", "1"); os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import numpy as np, multiprocessing as mp
from common import *
from estimators import *
from metrics import pair_metrics
from exp_main import prepare, seed_of
OUT = "/work/results/bgpair"
BS = [25, 100]
G = {}

def run_instance(task):
    ds, kind, ii = task
    g = G[(ds, kind)]
    f, bg, Xte = g["f"], g["bg"], g["Xte"]
    d = len(f.prep.cols); R = len(bg)
    _, V = build_table(f, Xte.iloc[[g["inst"][ii]]], bg, keep_full=True)
    pc = popcount_table(d)
    rng = np.random.default_rng(seed_of(21, DATASETS.index(ds), MODELS.index(kind), ii))
    out = {}
    for b in BS:
        Ph = np.array([exact_shapley(V[:, rng.choice(R, b, replace=False)].astype(np.float64).mean(1), d, pc) for _ in range(40)])
        i = np.arange(20); out[b] = {k: float(v.mean()) for k, v in pair_metrics(Ph[:20], Ph[20:], 3).items()}
    return dict(ds=ds, kind=kind, inst=int(g["inst"][ii]), out=out)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--procs", type=int, default=4); a = ap.parse_args()
    tasks = []
    for ds in ["pima", "gmsc", "acsincome"]:
        for kind in MODELS:
            G[(ds, kind)] = prepare(ds, kind); tasks += [(ds, kind, i) for i in range(50)]
    with mp.get_context("fork").Pool(a.procs) as pool:
        res = pool.map(run_instance, tasks, chunksize=2)
    os.makedirs(OUT, exist_ok=True); pickle.dump(res, open(f"{OUT}/bgpair.pkl", "wb"))
