"""E5: 'as-deployed' check with the actual `shap` package at its DEFAULT settings.
Explainers: KernelExplainer (default nsamples='auto'), PermutationExplainer (default max_evals=500),
TreeExplainer(interventional, background data) for tree models.
Background modes: 'fixed' (same 100 rows every run) vs 'resampled' (fresh random 100 training rows per run,
as with `shap.sample(X_train, 100)` called inside the explanation routine).
Writes results/deployed_metrics.csv.   Usage: python code/run_deployed.py [--quick]"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
import sys, time, argparse, warnings
import numpy as np, pandas as pd
from multiprocessing import Pool
import shap
from data import load, RESULTS, DATASETS
from models import Model, MODELS
from shapsim import pair_metrics, build_table, exact_shapley
from run_core import setup

warnings.filterwarnings("ignore")
NI, R = 20, 10


def work(args):
    ds, kind, quick = args
    t0 = time.process_time()
    ni, r_ = (3, 4) if quick else (NI, R)
    D, bg, inst = setup(ds, 100)
    inst = inst[:ni]
    X = D["X"]
    d = X.shape[1]
    M = Model(kind, D, seed=0)
    pool = X[D["train"]]
    explainers = ["kernel_default", "perm_default"] + (["tree_interventional"] if kind in ("xgb", "rf") else [])
    rows = []
    iu = np.triu_indices(r_, 1)
    for expl in explainers:
        for bgmode in ("fixed", "resampled"):
            for n in range(ni):
                x = X[inst[n]]
                P = np.zeros((r_, d))
                for r in range(r_):
                    seed = 100000 * (n + 1) + r
                    np.random.seed(seed)
                    if bgmode == "fixed":
                        b = bg
                    else:
                        b = pool[np.random.RandomState(seed).choice(len(pool), 100, replace=False)]
                    if expl == "kernel_default":
                        P[r] = shap.KernelExplainer(M.proba, b).shap_values(x[None], silent=True)[0]
                    elif expl == "perm_default":
                        P[r] = shap.PermutationExplainer(M.proba, b, seed=seed)(x[None], silent=True).values[0]
                    else:
                        te = shap.TreeExplainer(M.m, data=b, feature_perturbation="interventional")
                        sv = te.shap_values(x[None], check_additivity=False)
                        sv = sv[:, :, 1] if np.ndim(sv) == 3 else sv
                        P[r] = np.asarray(sv)[0]
                rr = pair_metrics(P[iu[0]], P[iu[1]])
                row = {k: float(np.nanmean(v)) for k, v in rr.items()}
                row.update(dataset=ds, model=kind, explainer=expl, bg=bgmode, inst=n, d=d)
                if bgmode == "fixed" and d <= 12 and expl != "tree_interventional":
                    ref = exact_shapley(build_table(M.proba, x, bg))
                    row["ref_rel_err"] = float(np.mean(np.linalg.norm(P - ref, axis=1)) / np.linalg.norm(ref))
                    rf = pair_metrics(P, np.broadcast_to(ref, P.shape))
                    for k, v in rf.items():
                        row["ref_" + k] = float(np.nanmean(v))
                rows.append(row)
    return rows, time.process_time() - t0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--procs", type=int, default=16)
    a = ap.parse_args()
    jobs = [(ds, k, a.quick) for ds in DATASETS for k in MODELS]
    jobs.sort(key=lambda j: -(j[0] == "german") * 2 - (j[1] in ("rf", "mlp")))
    allrows, cpu = [], 0
    with Pool(a.procs) as p:
        for rows, c in p.imap_unordered(work, jobs):
            allrows += rows
            cpu += c
            print("done", rows[0]["dataset"], rows[0]["model"], "%.0f cpu s" % c, flush=True)
    pd.DataFrame(allrows).to_csv(os.path.join(RESULTS, "deployed_metrics%s.csv" % ("_quick" if a.quick else "")), index=False)
    print("total cpu hours %.3f" % (cpu / 3600))
