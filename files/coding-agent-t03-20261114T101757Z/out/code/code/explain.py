"""Run KernelSHAP repeatedly and store one attribution matrix per run.

Each job = (dataset, model, output scale, background size K, budget nsamples, run r):
it explains all N_INST test instances with a single seeded explainer run.
Outputs: /work/results/kernel/{ds}_{model}_{output}_K{K}_B{budget}_r{run}.npy
with shape (N_INST, d). Existing files are skipped so the driver can be resumed.

Seeding: np.random.seed(r * 1_000_000 + b_index * 10_000 + i) before each instance,
so runs r are independent replicates and each (run, budget, instance) is reproducible.
"""
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import shap

from common import (BUDGETS, BUDGETS_BY_DS, K_BG, R_RUNS, RES_DIR, get_model, output_fn, split)

KDIR = f"{RES_DIR}/kernel"


def out_path(ds, model, output, K, budget, run):
    return f"{KDIR}/{ds}_{model}_{output}_K{K}_B{budget}_r{run}.npy"


def run_job(job):
    ds, model, output, K, budget, run = job
    path = out_path(ds, model, output, K, budget, run)
    if os.path.exists(path):
        return path, 0.0
    t0 = time.time()
    s = split(ds)
    m = get_model(ds, model, 0)
    f = output_fn(m, model, output)
    expl = shap.KernelExplainer(f, s["background"][:K])
    b_index = BUDGETS.index(budget)
    phi = np.zeros((len(s["X_inst"]), s["X_inst"].shape[1]))
    for i, x in enumerate(s["X_inst"]):
        np.random.seed(run * 1_000_000 + b_index * 10_000 + i)
        phi[i] = expl.shap_values(x[None, :], nsamples=budget, l1_reg=False, silent=True)[0]
    os.makedirs(KDIR, exist_ok=True)
    np.save(path, phi)
    return path, time.time() - t0


def main_jobs(datasets, models, outputs=("prob",), Ks=(K_BG,), budgets=BUDGETS, runs=R_RUNS):
    jobs = []
    for ds in datasets:
        for mo in models:
            for output in outputs:
                for K in Ks:
                    for b in budgets:
                        for r in range(runs):
                            jobs.append((ds, mo, output, K, b, r))
    return jobs


if __name__ == "__main__":
    # usage: explain.py <workers> <spec>   spec in {main, margin, bg}
    workers = int(sys.argv[1])
    spec = sys.argv[2]
    if spec == "main":
        jobs = []
        for ds in ["german", "acs", "pima"]:
            jobs += main_jobs([ds], ["LR", "LGBM", "RF", "MLP"], budgets=BUDGETS_BY_DS[ds])
    elif spec == "margin":
        jobs = []
        for ds in ["german", "acs", "pima"]:
            jobs += main_jobs([ds], ["LR"], outputs=("margin",), budgets=BUDGETS_BY_DS[ds])
        for ds in ["acs", "pima"]:
            jobs += main_jobs([ds], ["LGBM"], outputs=("margin",), budgets=BUDGETS_BY_DS[ds])
    elif spec == "bg":
        jobs = main_jobs(["acs"], ["LGBM"], Ks=(25, 400), budgets=[250, 1000])
    else:
        raise SystemExit("unknown spec")
    # longest jobs first (larger budget, more expensive models) for load balance
    cost = {"LR": 1, "MLP": 2, "LGBM": 4, "RF": 3}
    jobs.sort(key=lambda j: -(j[4] * j[3] * cost[j[1]]))
    todo = [j for j in jobs if not os.path.exists(out_path(*j))]
    print(f"{len(jobs)} jobs, {len(todo)} to run", flush=True)
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(run_job, j) for j in todo]
        for k, fu in enumerate(as_completed(futs), 1):
            path, dt = fu.result()
            if k % 100 == 0 or k == len(futs):
                print(f"[{k}/{len(futs)}] elapsed {time.time() - t0:.0f}s last={os.path.basename(path)}",
                      flush=True)
    print("done", time.time() - t0, flush=True)
