"""Main experiment: repeat-run reliability of Kernel / Leverage / Permutation SHAP against exact Shapley values.

For every (dataset, model) we train one model, draw test instances, tabulate the full interventional game
(2^d coalitions, fixed 100-row background), compute exact Shapley values, and run each estimator
`reps` times at each budget m.  Everything per-instance is stored in results/main/<ds>_<model>/inst_<i>.npz.

usage: python exp_main.py --ds pima --models lr,mlp,rf,xgb [--procs 40]
"""
import os, sys, time, argparse, pickle
os.environ.setdefault("OMP_NUM_THREADS", "1"); os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import numpy as np
import multiprocessing as mp
from common import *
from estimators import *
from metrics import vs_truth, rank_pos

OUT = os.environ.get("SHAP_OUT", "/work/results/main")
SPLIT = int(os.environ.get("SHAP_SPLIT", "0"))  # split/model seed (replicate analysis uses 1)
BUDGETS = [32, 64, 128, 256, 512, 1024, 2048, 4096, 8192]
ESTS = ["kernel", "leverage", "perm"]
REPS = 100
B_MAIN = 100  # background rows used for the main experiment (first B_MAIN rows of the reference sample)

G = {}  # filled in parent before fork


def seed_of(*key):
    return int(np.random.SeedSequence([int(k) for k in key]).generate_state(1)[0] & 0x7FFFFFFF)


def prepare(ds, kind):
    f, Xtr, ytr, Xte, yte = split_and_fit(ds, kind, split_seed=SPLIT, model_seed=SPLIT)
    cfg = TABLE_CFG[ds]
    bg = Xtr.sample(n=min(cfg["R"], len(Xtr)), random_state=1).reset_index(drop=True)
    rng = np.random.RandomState(123)
    inst = np.sort(rng.choice(len(Xte), cfg["n_inst"], replace=False))
    return dict(f=f, bg=bg, Xte=Xte, yte=yte, inst=inst, ds=ds, kind=kind)


def run_instance(task):
    ds, kind, ii = task
    g = G[(ds, kind)]
    f, bg, Xte = g["f"], g["bg"], g["Xte"]
    d = len(f.prep.cols)
    path = f"{OUT}/{ds}_{kind}/inst_{ii}.pkl"
    if os.path.exists(path):
        return task, 0.0
    t0 = time.time()
    row = Xte.iloc[[g["inst"][ii]]]
    keep_full = d <= 10
    vbar_ref, V = build_table(f, row, bg, keep_full=keep_full)
    vbar = V[:, :B_MAIN].astype(np.float64).mean(1) if keep_full else vbar_ref
    pc = popcount_table(d)
    phi = exact_shapley(vbar, d, pc)
    rho = additivity_residual(vbar, d, phi, pc)
    a = np.sort(np.abs(phi))[::-1]
    res = dict(ds=ds, kind=kind, inst=int(g["inst"][ii]), d=d, phi=phi, fx=float(vbar[-1]), f0=float(vbar[0]),
               y=int(g["yte"][g["inst"][ii]]), rho=rho, a_sorted=a, auc=f.auc)
    vfun = lambda ids: vbar[np.asarray(ids)]
    out = {}
    maxm = (1 << d) - 2
    for m in BUDGETS:
        if m >= maxm:
            continue
        for ei, est in enumerate(ESTS):
            if est == "perm" and m < 2 * (d - 1):
                continue
            Phi = np.zeros((REPS, d), dtype=np.float32); SE = np.zeros((REPS, d), dtype=np.float32)
            for r in range(REPS):
                s = seed_of(DATASETS.index(ds), MODELS.index(kind), ii, m, ei, r)
                p, se = run_estimator(est, vfun, d, m, s, want_se=True, pc=pc)
                Phi[r] = p; SE[r] = se
            out[(est, m)] = (Phi, SE)
    res["runs"] = out
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + ".tmp", "wb") as fh:
        pickle.dump(res, fh)
    os.replace(path + ".tmp", path)
    return task, time.time() - t0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ds", required=True); ap.add_argument("--models", default=",".join(MODELS))
    ap.add_argument("--procs", type=int, default=40)
    a = ap.parse_args()
    tasks = []
    for ds in a.ds.split(","):
        for kind in a.models.split(","):
            G[(ds, kind)] = prepare(ds, kind)
            print(ds, kind, "AUC", round(G[(ds, kind)]["f"].auc, 4), flush=True)
            tasks += [(ds, kind, i) for i in range(len(G[(ds, kind)]["inst"]))]
    # slowest first: tree ensembles on larger d
    cost = {"rf": 4, "xgb": 2, "mlp": 1, "lr": 0.5}
    tasks.sort(key=lambda t: -cost[t[1]] * (1 << len(G[(t[0], t[1])]["f"].prep.cols)))
    t0 = time.time()
    with mp.get_context("fork").Pool(a.procs) as pool:
        for n, (task, dt) in enumerate(pool.imap_unordered(run_instance, tasks)):
            if n % 10 == 0:
                print(f"[{time.time()-t0:7.0f}s] {n+1}/{len(tasks)} done; last {task} {dt:.0f}s", flush=True)
    print("total wall", time.time() - t0)
