"""Background-size experiments (d <= 10 datasets).

Target phi* = exact Shapley values of the interventional game with the whole reference sample (R rows).
Part A  (exact solver, background-size effect only): subsets of size b of the reference -> exact phi_b vs phi*.
Part B  (fixed total model-call budget N = m * b, Kernel SHAP): split N between #coalitions m and background size b;
        each run draws a fresh random background subset (as a practitioner would) and a fresh coalition sample.
usage: python exp_bg.py --procs 40
"""
import os, sys, time, pickle, argparse
os.environ.setdefault("OMP_NUM_THREADS", "1"); os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import numpy as np, multiprocessing as mp
from common import *
from estimators import *
from metrics import vs_truth
from exp_main import prepare, seed_of

OUT = "/work/results/bg"
BS = [5, 10, 25, 50, 100, 250]
NS = [2000, 5000, 10000, 20000, 50000, 100000, 200000]
NSUB, NREP, NINST = 30, 20, 50
G = {}


def run_instance(task):
    ds, kind, ii = task
    path = f"{OUT}/{ds}_{kind}/inst_{ii}.pkl"
    if os.path.exists(path):
        return task
    g = G[(ds, kind)]
    f, bg, Xte = g["f"], g["bg"], g["Xte"]
    d = len(f.prep.cols); R = len(bg)
    row = Xte.iloc[[g["inst"][ii]]]
    _, V = build_table(f, row, bg, keep_full=True)
    pc = popcount_table(d)
    phi_star = exact_shapley(V.astype(np.float64).mean(1), d, pc)
    rng = np.random.default_rng(seed_of(7, DATASETS.index(ds), MODELS.index(kind), ii))
    A, B = {}, {}
    for b in BS:
        if b > R // 2:
            continue
        Ph = []
        for _ in range(NSUB):
            sub = rng.choice(R, b, replace=False)
            Ph.append(exact_shapley(V[:, sub].astype(np.float64).mean(1), d, pc))
        A[b] = vs_truth(np.array(Ph), phi_star)
    for N in NS:
        for b in BS:
            if b > R // 2:
                continue
            m = min(N // b, (1 << d) - 2)
            if m < 2 * d:
                continue
            Ph = []
            for r in range(NREP):
                sub = rng.choice(R, b, replace=False)
                vb = V[:, sub].astype(np.float64).mean(1)
                s = seed_of(8, DATASETS.index(ds), MODELS.index(kind), ii, N, b, r)
                Ph.append(kernel_like(lambda ids: vb[np.asarray(ids)], d, m, s, mode="kernel", pc=pc))
            B[(N, b)] = dict(m=m, **vs_truth(np.array(Ph), phi_star))
    res = dict(ds=ds, kind=kind, inst=int(g["inst"][ii]), phi_star=phi_star, A=A, B=B)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        pickle.dump(res, fh)
    return task


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--procs", type=int, default=40); a = ap.parse_args()
    tasks = []
    for ds in ["pima", "gmsc", "acsincome"]:
        for kind in MODELS:
            G[(ds, kind)] = prepare(ds, kind)
            tasks += [(ds, kind, i) for i in range(NINST)]
    t0 = time.time()
    with mp.get_context("fork").Pool(a.procs) as pool:
        for n, task in enumerate(pool.imap_unordered(run_instance, tasks)):
            if n % 20 == 0:
                print(f"[{time.time()-t0:6.0f}s] {n+1}/{len(tasks)}", flush=True)
