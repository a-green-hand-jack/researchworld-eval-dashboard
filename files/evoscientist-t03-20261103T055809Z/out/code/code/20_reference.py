"""Stage 2: reference attributions and 'legitimate-variation' noise floors.

reference  : exact interventional SHAP (full enumeration for d<=12; TreeExplainer for rf/xgb at any d).
             Cells without an exact reference (german/arrhythmia x lr/mlp) get none (reported as such).
bg-variation  : exact SHAP of the same model/instance under 5 alternative random 100-row backgrounds.
seed-variation: exact SHAP after retraining the model with 5 other seeds (rf/xgb/mlp), same background.
Output results/ref_{ds}_{m}.npz
"""
import os, sys, pickle, time, warnings
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
warnings.filterwarnings("ignore")
for k in ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"]: os.environ[k] = "1"
import numpy as np
from joblib import Parallel, delayed
from common import *

N_ALT = 5


def exact_phi(model, kind, d, bg, X):
    if kind == "rf":  # TreeExplainer(interventional, probability) is exact for RF (verified vs enumeration, ~1e-9)
        return tree_exact(model, bg, X)
    if d <= 12:
        fn = Fn(model)
        return np.stack([exact_enum(fn, bg, x) for x in X])
    return None


def job(ds, m):
    out = os.path.join(RES, f"ref_{ds}_{m}.npz")
    if os.path.exists(out): return ds, m, "skip"
    Xtr, Xte, ytr, yte, names, cat = split(ds)
    o = pickle.load(open(os.path.join(RES, f"model_{ds}_{m}.pkl"), "rb"))
    mod, meta = o["model"], o["meta"]; d = meta["d"]
    X = Xte[meta["inst"]]; bg = Xtr[meta["bg_idx"]]
    res = {}
    ref = exact_phi(mod, m, d, bg, X)
    if ref is None: return ds, m, "no exact ref"
    res["ref"] = ref
    # sanity: for tree models with d<=12 compare TreeExplainer to enumeration
    if m == "rf" and d <= 12:
        res["enum_check"] = exact_phi(mod, "enum", d, bg, X[:5])  # enumeration cross-check of TreeExplainer
    rng = np.random.RandomState(123)
    res["bg_alt"] = np.stack([exact_phi(mod, m, d, Xtr[rng.choice(len(Xtr), N_BG, replace=False)], X) for _ in range(N_ALT)])
    if m != "lr":
        alts = []
        for s in range(1, N_ALT + 1):
            mod_s = make_model(m, cat, d, seed=s).fit(Xtr, ytr)
            alts.append(exact_phi(mod_s, m, d, bg, X))
        res["seed_alt"] = np.stack(alts)
    np.savez_compressed(out, **res)
    return ds, m, "ok"


if __name__ == "__main__":
    only = sys.argv[1:]
    jobs = [(ds, m) for ds in (only or DATASETS) for m in MODELS]
    for r in Parallel(n_jobs=int(os.environ.get("NJ", 20)))(delayed(job)(*j) for j in jobs):
        print(r, flush=True)
