"""Run the simulation experiments E1-E4 (see README.md / paper Section 4).

Usage (from /work/code):
  python run_sim.py --exp E1 --reps 500 --workers 38
  python run_sim.py --exp E1 --reps 5 --workers 4 --smoke   # quick check, output not kept

Each setting writes /work/results/raw/<setting_id>__R<reps>.csv (one row per
replication and estimator). Existing files are skipped, so runs are resumable.
"""
import os

for _v in ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"]:
    os.environ[_v] = "1"  # one BLAS thread per worker; parallelism is across settings

import argparse  # noqa: E402
import multiprocessing as mp  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, "/work/code")
from gate import dgp, estimators, graphs  # noqa: E402

RAW = "/work/results/raw"
BASE_SEED = 20261114  # fixed master seed; rep seeds are derived from (setting, rep)


EXPS = {
    # E1: main grid, three graphs x seven mechanisms x five designs
    "E1": [dict(graph=g, mech=m, design=d, p=p)
           for g in ["stanford3", "egofb", "ba_n5000_m3"]
           for m in ["M0", "M1", "M2", "M3", "M4", "M5", "M6"]
           for d, p in [("bern", 0.1), ("bern", 0.3), ("bern", 0.5), ("gcr", 0.1), ("gcr", 0.5)]],
    # E2: degree sweep on ER graphs (n about 5000), Bernoulli(0.5)
    "E2": [dict(graph=f"er_n5000_d{d}", mech=m, design="bern", p=0.5)
           for d in [5, 10, 20, 50, 100, 200] for m in ["M1", "M2", "M4", "M5"]],
    # E3: sample-size sweep at fixed mean degree 20
    "E3": [dict(graph=f"er_n{n}_d20", mech=m, design="bern", p=0.5)
           for n in [1000, 4000, 16000] for m in ["M1", "M2", "M3", "M5"]],
    # E4: treatment-probability sweep on ego-Facebook, Bernoulli
    "E4": [dict(graph="egofb", mech=m, design="bern", p=p)
           for m in ["M1", "M2", "M3", "M5"] for p in [0.1, 0.2, 0.3, 0.5, 0.7, 0.9]],
}

_CACHE = {}


def _load(name):
    if name not in _CACHE:
        g = graphs.load_cached(name)
        A = dgp.adjacency(g["src"], g["dst"], g["n"])
        deg = np.asarray(A.sum(axis=1)).ravel()
        _CACHE.clear()
        _CACHE[name] = (g, A, deg)
    return _CACHE[name]


def setting_id(exp, s):
    return f"{exp}__{s['graph']}__{s['mech']}__{s['design']}__p{s['p']}"


def run_setting(job):
    exp, s, reps = job
    sid = setting_id(exp, s)
    out_path = os.path.join(RAW, f"{sid}__R{reps}.csv")
    if os.path.exists(out_path):
        return sid, "cached"
    t0 = time.time()
    g, A, deg = _load(s["graph"])
    n, labels, K = g["n"], g["labels"], g["n_clusters"]
    truth = dgp.true_gate(s["mech"])
    rows = []
    for rep in range(reps):
        rng = np.random.default_rng([BASE_SEED, graphs.seed_from_name(sid), rep])
        z = dgp.assign(s["design"], s["p"], n, rng, labels, K)
        y, f1, f2, x = dgp.simulate(s["mech"], A, deg, z, labels, K, rng)
        res = estimators.all_estimators(z, f1, f2, x, y, labels, K, seed=rep)
        for name, r in res.items():
            rows.append(dict(exp=exp, setting=sid, graph=s["graph"], n=n, n_clusters=K,
                             mean_deg=float(deg.mean()), mech=s["mech"], design=s["design"],
                             p=s["p"], rep=rep, estimator=name, truth=truth, **r))
    df = pd.DataFrame(rows)
    os.makedirs(RAW, exist_ok=True)
    df.to_csv(out_path, index=False)
    return sid, f"{time.time() - t0:.1f}s"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp", required=True, choices=list(EXPS))
    ap.add_argument("--reps", type=int, default=500)
    ap.add_argument("--workers", type=int, default=38)
    ap.add_argument("--only", type=int, default=None, help="run only the first k settings")
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    settings = EXPS[args.exp][: args.only] if args.only else EXPS[args.exp]
    jobs = [(args.exp, s, args.reps) for s in settings]
    if args.smoke:
        RAW = "/tmp/smoke_raw"  # module-level global, read by run_setting
    print(f"{args.exp}: {len(jobs)} settings x {args.reps} reps", flush=True)
    t0 = time.time()
    with mp.get_context("fork").Pool(args.workers) as pool:
        for sid, msg in pool.imap_unordered(run_setting, jobs):
            print(f"[{time.time() - t0:7.1f}s] {sid} {msg}", flush=True)
    if not args.smoke:
        files = [os.path.join(RAW, f) for f in os.listdir(RAW)
                 if f.endswith(f"__R{args.reps}.csv") and f.startswith(args.exp + "__")]
        allrows = pd.concat([pd.read_csv(f) for f in sorted(files)], ignore_index=True)
        allrows.to_csv(f"/work/results/reps_{args.exp}.csv", index=False)
        print("wrote", len(allrows), "rows", flush=True)
    print("done", round(time.time() - t0, 1), "s", flush=True)
