"""Retraining baseline: how much do exact SHAP attributions of *equally accurate* models differ?

K bootstrap-retrained models per (dataset, model type) (fresh bootstrap of the training set + fresh model seed),
exact Shapley values on the same instances and the same 100-row background as the main experiment.
usage: python exp_retrain.py --procs 40
"""
import os, sys, time, pickle, argparse
os.environ.setdefault("OMP_NUM_THREADS", "1"); os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import numpy as np, multiprocessing as mp
from common import *
from estimators import *
from exp_main import prepare, B_MAIN

OUT = "/work/results/retrain"
K = 8
NINST = 50
DS = ["pima", "gmsc", "acsincome"]


def one(task):
    ds, kind, k = task
    f, Xtr, ytr, Xte, yte = split_and_fit(ds, kind, model_seed=100 + k, bootstrap=True)
    g = prepare(ds, "lr")  # only for instance list / background rows (independent of the model)
    cfg = TABLE_CFG[ds]
    bg = g["bg"].iloc[:B_MAIN]
    inst = g["inst"][:NINST]
    d = len(f.prep.cols); pc = popcount_table(d)
    Phi = np.zeros((len(inst), d)); fx = np.zeros(len(inst))
    for i, ix in enumerate(inst):
        vbar, _ = build_table(f, Xte.iloc[[ix]], bg, keep_full=False)
        Phi[i] = exact_shapley(vbar, d, pc); fx[i] = vbar[-1]
    return dict(ds=ds, kind=kind, k=k, auc=f.auc, Phi=Phi, fx=fx, inst=inst)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--procs", type=int, default=40); a = ap.parse_args()
    tasks = [(ds, kind, k) for ds in DS for kind in MODELS for k in range(K)]
    t0 = time.time(); res = []
    with mp.get_context("fork").Pool(a.procs) as pool:
        for n, r in enumerate(pool.imap_unordered(one, tasks)):
            res.append(r); print(f"[{time.time()-t0:6.0f}s] {n+1}/{len(tasks)} {r['ds']} {r['kind']} {r['k']} auc={r['auc']:.3f}", flush=True)
    os.makedirs(OUT, exist_ok=True)
    pickle.dump(res, open(f"{OUT}/retrain.pkl", "wb"))
