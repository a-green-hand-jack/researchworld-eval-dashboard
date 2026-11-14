"""Validation against the real `shap` library (model calls, not table lookups) with an XGBoost model.

Checks (i) that our table-based Kernel / Permutation SHAP reproduce the error of shap.KernelExplainer /
shap.PermutationExplainer at equal budget, (ii) what shap's default `l1_reg="num_features(10)"` does when d > 10.
usage: python exp_shaplib.py --procs 40
"""
import os, sys, time, pickle, argparse, warnings
os.environ.setdefault("OMP_NUM_THREADS", "1"); os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
warnings.filterwarnings("ignore")
import numpy as np, multiprocessing as mp
import shap
from common import *
from estimators import *
from metrics import vs_truth
from exp_main import prepare, B_MAIN, seed_of

OUT = "/work/results/shaplib"
CFGS = [("pima", "xgb"), ("acsincome", "xgb"), ("acsemployment", "xgb"), ("german", "xgb")]
BUDGETS = [64, 256, 1024, 2048]
NINST, NREP = 8, 20
G = {}


def one(task):
    ds, kind, ii = task
    g = G[(ds, kind)]
    f, bg, Xte = g["f"], g["bg"].iloc[:B_MAIN], g["Xte"]
    d = len(f.prep.cols); pc = popcount_table(d)
    row = Xte.iloc[[g["inst"][ii]]]
    vbar, _ = build_table(f, row, bg, keep_full=False)
    phi = exact_shapley(vbar, d, pc)
    xe = f.prep.encode(row); be = f.prep.encode(bg)
    pred = lambda E: f.predict(np.asarray(E, dtype=np.float32)).astype(np.float64)
    out = {}
    ke = shap.KernelExplainer(pred, be)
    pe = shap.PermutationExplainer(pred, be)
    for m in BUDGETS + ["auto"]:
        mm = 2 * d + 2048 if m == "auto" else m
        if mm >= (1 << d) - 2:
            continue
        for variant in ["kernel_noL1", "kernel_default", "perm"]:
            if variant == "kernel_default" and not (m == "auto" or d > 10):
                continue
            Ph = np.zeros((NREP, d))
            for r in range(NREP):
                s = seed_of(9, DATASETS.index(ds), ii, mm, r)
                if variant == "perm":
                    if m == "auto":
                        continue
                    npairs = max(m // (2 * (d - 1)), 1)
                    Ph[r] = pe(xe, max_evals=2 * d * npairs + 1, silent=True).values[0]
                else:
                    np.random.seed(s)
                    kw = dict(l1_reg=False) if variant == "kernel_noL1" else {}
                    Ph[r] = ke.shap_values(xe, nsamples=("auto" if m == "auto" else m), silent=True, **kw)[0]
            if variant == "perm" and m == "auto":
                continue
            out[(variant, m)] = vs_truth(Ph, phi)
            out[(variant, m)]["n_zero"] = (np.abs(Ph) < 1e-12).sum(1).astype(np.float32)
    return dict(ds=ds, kind=kind, ii=ii, inst=int(g["inst"][ii]), phi=phi, out=out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--procs", type=int, default=40); a = ap.parse_args()
    tasks = []
    for ds, kind in CFGS:
        G[(ds, kind)] = prepare(ds, kind)
        tasks += [(ds, kind, i) for i in range(NINST)]
    t0 = time.time(); res = []
    with mp.get_context("fork").Pool(a.procs) as pool:
        for n, r in enumerate(pool.imap_unordered(one, tasks)):
            res.append(r); print(f"[{time.time()-t0:6.0f}s] {n+1}/{len(tasks)}", flush=True)
    os.makedirs(OUT, exist_ok=True)
    pickle.dump(res, open(f"{OUT}/shaplib.pkl", "wb"))
