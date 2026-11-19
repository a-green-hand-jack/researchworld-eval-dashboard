"""Stage 1: repeated stochastic SHAP runs. For each (dataset, model, explainer, budget, instance),
run the explainer N_RUNS times with independent seeds on the SAME trained model, SAME instance, SAME background.
Output: results/runs_{ds}_{model}.npz with phi[expl|B] (n_inst, R, d), rows, secs."""
import os, sys, pickle, time, warnings
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
warnings.filterwarnings("ignore")
os.environ["OMP_NUM_THREADS"] = "1"; os.environ["OPENBLAS_NUM_THREADS"] = "1"; os.environ["MKL_NUM_THREADS"] = "1"
import numpy as np
from joblib import Parallel, delayed
from common import *

_cache = {}
def _get(ds, m):
    if (ds, m) not in _cache:
        _cache.clear()
        Xtr, Xte, ytr, yte, names, cat = split(ds)
        o = pickle.load(open(os.path.join(RES, f"model_{ds}_{m}.pkl"), "rb"))
        _cache[(ds, m)] = (Fn(o["model"]), Xtr[o["meta"]["bg_idx"]], Xte[o["meta"]["inst"]])
    return _cache[(ds, m)]

def task(ds, m, ex, B, ii, R):
    fn, bg, X = _get(ds, m)
    phis, rows, secs = [], [], []
    for r in range(R):
        seed = 100003 * ii + 101 * r + 7
        fn.rows = 0; t = time.time()
        phis.append(explain_once(ex, fn, bg, X[ii], B, seed))
        secs.append(time.time() - t); rows.append(fn.rows)
    return np.array(phis), np.array(rows), np.array(secs)

if __name__ == "__main__":
    only = sys.argv[1:]  # optional list of datasets
    R = int(os.environ.get("N_RUNS", N_RUNS)); NI = int(os.environ.get("N_INST", N_INST))
    for ds in (only or DATASETS):
        for m in MODELS:
            out = os.path.join(RES, f"runs_{ds}_{m}.npz")
            if os.path.exists(out): continue
            t0 = time.time()
            jobs = [(ex, B, ii) for ex in EXPLAINERS for B in BUDGETS[ds] for ii in range(NI)]
            res = Parallel(n_jobs=int(os.environ.get("NJ", 38)), batch_size=1)(
                delayed(task)(ds, m, ex, B, ii, R) for ex, B, ii in jobs)
            d = {}
            for ex in EXPLAINERS:
                for B in BUDGETS[ds]:
                    sel = [res[k] for k, j in enumerate(jobs) if j[0] == ex and j[1] == B]
                    d[f"{ex}|{B}|phi"] = np.stack([s[0] for s in sel])
                    d[f"{ex}|{B}|rows"] = np.stack([s[1] for s in sel])
                    d[f"{ex}|{B}|secs"] = np.stack([s[2] for s in sel])
            np.savez_compressed(out, **d)
            print(f"{ds} {m} done in {time.time()-t0:.0f}s", flush=True)
