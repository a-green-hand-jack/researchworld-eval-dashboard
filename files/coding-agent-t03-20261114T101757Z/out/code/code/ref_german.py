"""Approximate reference for German Credit (d=20, exact Shapley infeasible).

For the first N_REF_GERMAN explained instances, REF_RUNS independent KernelSHAP
runs at a high budget REF_BUDGET (same background K=100, same model, prob output).
The mean of these runs is used as an approximate truth; its own Monte Carlo
standard error (sd / sqrt(REF_RUNS)) is stored alongside it.
Output: /work/results/ref/german_{model}_B{budget}.npy, shape (REF_RUNS, N_REF, d).
"""
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import shap

from common import (N_REF_GERMAN, REF_BUDGET, REF_RUNS, RES_DIR, get_model, output_fn, split)

REFDIR = f"{RES_DIR}/ref"


def job(args):
    model_name, run = args
    path = f"{REFDIR}/german_{model_name}_B{REF_BUDGET}_r{run}.npy"
    if os.path.exists(path):
        return path
    s = split("german")
    m = get_model("german", model_name, 0)
    expl = shap.KernelExplainer(output_fn(m, model_name, "prob"), s["background"][:100])
    phi = np.zeros((N_REF_GERMAN, s["X_inst"].shape[1]))
    for i, x in enumerate(s["X_inst"][:N_REF_GERMAN]):
        np.random.seed(7_000_000 + run * 1_000 + i)
        phi[i] = expl.shap_values(x[None, :], nsamples=REF_BUDGET, l1_reg=False, silent=True)[0]
    os.makedirs(REFDIR, exist_ok=True)
    np.save(path, phi)
    return path


if __name__ == "__main__":
    workers = int(sys.argv[1])
    jobs = [(mn, r) for mn in ["LR", "LGBM", "RF", "MLP"] for r in range(REF_RUNS)]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for p in ex.map(job, jobs):
            print("wrote", p, flush=True)
