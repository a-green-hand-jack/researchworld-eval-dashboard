"""E2/E6 yardsticks (tables datasets only, d <= 10, so every attribution below is an EXACT Shapley value of the
interventional value function and no coalition-sampling noise is involved):
  (a) model-retraining variability: K=5 models retrained on bootstrap resamples of the training set
  (b) background-sampling variability: 10 independent random backgrounds of size B in {10,50,100,200}
  (c) value-function choice: tree path-dependent TreeSHAP vs exact interventional SHAP (tree models)
Writes results/yard/<dataset>_<model>.npz.  Usage: python code/run_yard.py [--quick]"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
import sys, time, argparse
import numpy as np, pandas as pd
from multiprocessing import Pool
from data import load, RESULTS, DATASETS
from models import Model, MODELS
from shapsim import *
from run_core import setup

OUT = os.path.join(RESULTS, "yard")
os.makedirs(OUT, exist_ok=True)
K = 5
BG_SIZES = [10, 50, 100, 200]
N_BG_DRAWS = 10


def exact_phi(M, x, bg, logit=False):
    return exact_shapley(build_table(M.proba, x, bg, logit))


def work(args):
    ds, kind, quick = args
    t0 = time.process_time()
    N = 6 if quick else 100
    Nb = 3 if quick else 30
    D, bg, inst = setup(ds, 100)
    inst = inst[:N]
    X = D["X"]
    d = X.shape[1]
    out = dict(inst=inst)
    # (a) retraining
    phis = np.zeros((K, N, d))
    for k in range(K):
        rs = np.random.RandomState(500 + k)
        idx = rs.choice(D["train"], len(D["train"]), replace=True)
        Mk = Model(kind, D, seed=k + 1, train_idx=idx)
        for n in range(N):
            phis[k, n] = exact_phi(Mk, X[inst[n]], bg)
    out["phi_retrain"] = phis
    # (b) background sampling (model 0 as in E1)
    M0 = Model(kind, D, seed=0)
    out["phi_ref"] = np.stack([exact_phi(M0, X[inst[n]], bg) for n in range(N)])
    for Bs in BG_SIZES:
        arr = np.zeros((N_BG_DRAWS if not quick else 4, Nb, d))
        for r in range(arr.shape[0]):
            rs = np.random.RandomState(9000 + 17 * r + Bs)
            bgr = X[D["train"]][rs.choice(len(D["train"]), Bs, replace=False)]
            for n in range(Nb):
                arr[r, n] = exact_phi(M0, X[inst[n]], bgr)
        out[f"phi_bg_{Bs}"] = arr
    # (c) path-dependent TreeSHAP vs interventional
    if kind in ("xgb", "rf"):
        import shap
        te = shap.TreeExplainer(M0.m)
        sv = te.shap_values(X[inst])
        sv = sv[:, :, 1] if np.ndim(sv) == 3 else sv
        out["phi_pathdep"] = np.asarray(sv)
        logit = kind == "xgb"  # shap TreeExplainer explains the raw margin for xgboost
        out["pathdep_scale_logit"] = np.array(logit)
        out["phi_interv_matched"] = np.stack([exact_phi(M0, X[inst[n]], bg, logit) for n in range(N)])
    np.savez_compressed(os.path.join(OUT, f"{ds}_{kind}{'_quick' if quick else ''}.npz"), **out)
    return ds, kind, time.process_time() - t0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--procs", type=int, default=12)
    a = ap.parse_args()
    jobs = [(ds, k, a.quick) for ds in DATASETS if ds != "german" for k in MODELS]
    jobs.sort(key=lambda j: -(j[1] == "rf"))
    cpu = []
    with Pool(a.procs) as p:
        for ds, kind, c in p.imap_unordered(work, jobs):
            print("done", ds, kind, "%.0f cpu s" % c, flush=True)
            cpu.append(dict(dataset=ds, model=kind, cpu_s=c))
    cp = pd.DataFrame(cpu)
    cp.to_csv(os.path.join(OUT, "cpu_time%s.csv" % ("_quick" if a.quick else "")), index=False)
    print("total cpu hours %.3f" % (cp.cpu_s.sum() / 3600))
