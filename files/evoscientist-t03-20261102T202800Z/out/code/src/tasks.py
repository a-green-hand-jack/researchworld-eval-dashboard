"""Experiment tasks (imported by run_main.py; kept in a module so joblib/loky can pickle them by reference).
Raw attributions are stored as npz under results/<stage>/ ; analysis is in analyze.py."""
import os, sys, time, warnings
os.environ["OMP_NUM_THREADS"] = "1"; os.environ["OPENBLAS_NUM_THREADS"] = "1"; os.environ["MKL_NUM_THREADS"] = "1"
import numpy as np, joblib
from joblib import Parallel, delayed
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C, explain, models, data

warnings.filterwarnings("ignore")


import functools


@functools.lru_cache(maxsize=4)
def load_cell(dn, k):
    return joblib.load(f"{C.ART}/{dn}_data.joblib"), joblib.load(f"{C.ART}/{dn}_{k}.joblib")


def seed_of(*a):
    """Deterministic 31-bit seed from a tuple of ints."""
    return int(np.random.SeedSequence([int(v) for v in a]).generate_state(1)[0] % (2 ** 31 - 1)) + 1


# ---------------------------------------------------------------- E1 : repeated runs, fixed background
def e1_instance(dn, k, est, i, budgets, R):
    Dd, m = load_cell(dn, k)
    x, bg = Dd["Xte"][i], Dd["bg"]; d = len(x)
    out = np.zeros((len(budgets), R, d)); runs = np.zeros(len(budgets), int)
    for bi, B in enumerate(budgets):
        exact = est == "kernel" and B >= 2 ** d - 2
        n_run = 1 if exact else R
        for r in range(n_run):
            s = seed_of(hash_ds(dn), hash_ds(k), hash_ds(est), i, bi, r)
            out[bi, r] = (explain.kernel_phi(m.predict, x, bg, 2 ** d - 2 if exact else B, s) if est == "kernel"
                          else explain.perm_phi(m.predict, x, bg, B, s))
        if exact:
            out[bi, 1:] = out[bi, 0]
    ref, kind = explain.reference_phi(m, x, bg)
    return out, ref, kind


def hash_ds(s):  # deterministic small int from a string
    return sum(ord(c) * (31 ** j) for j, c in enumerate(s)) % 100003


def run_E1(n_jobs):
    out = f"{C.RES}/E1"; os.makedirs(out, exist_ok=True)
    for dn in C.DATASETS:
        for k in C.MODELS:
            for est in C.ESTIMATORS:
                f = f"{out}/{dn}_{k}_{est}.npz"
                if os.path.exists(f): continue
                t = time.time()
                res = Parallel(n_jobs=n_jobs)(delayed(e1_instance)(dn, k, est, i, C.BUDGETS, C.R) for i in range(C.N_INST))
                phi = np.stack([r[0] for r in res]); ref = np.stack([r[1] for r in res])
                np.savez_compressed(f, phi=phi, ref=ref, ref_kind=res[0][2], budgets=C.BUDGETS)
                print(f"E1 {dn} {k} {est} done {time.time()-t:.0f}s", flush=True)


# ---------------------------------------------------------------- E2 : background resampling
def e2_instance(dn, k, i, mbg, B, R):
    Dd, m = load_cell(dn, k)
    x = Dd["Xte"][i]; d = len(x); Xtr = Dd["Xtr"]
    exact = B >= 2 ** d - 2
    out = np.zeros((R, d))
    for r in range(R):
        rs = np.random.RandomState(seed_of(hash_ds(dn), hash_ds(k), i, mbg, r, 99))
        bg = Xtr[rs.choice(len(Xtr), mbg, replace=False)]
        out[r] = explain.kernel_phi(m.predict, x, bg, 2 ** d - 2 if exact else B, int(rs.randint(1, 2 ** 31 - 1)))
    return out


def run_E2(n_jobs):
    out = f"{C.RES}/E2"; os.makedirs(out, exist_ok=True)
    for dn in C.DATASETS:
        for k in C.MODELS:
            f = f"{out}/{dn}_{k}.npz"
            if os.path.exists(f): continue
            t = time.time(); store = {}
            for mbg in C.E2_M:
                res = Parallel(n_jobs=n_jobs)(delayed(e2_instance)(dn, k, i, mbg, C.E2_B, C.E2_R) for i in range(C.E2_N))
                store[f"m{mbg}"] = np.stack(res)
            np.savez_compressed(f, **store)
            print(f"E2 {dn} {k} done {time.time()-t:.0f}s", flush=True)


# ---------------------------------------------------------------- E3 : model retraining replicates
def e3_instance(dn, k, rep, idx):
    # model replicate trained on 80% subsample with seed `rep`; same instances and same background as E1
    Dd = joblib.load(f"{C.ART}/{dn}_data.joblib")
    D = dict(Xtr=Dd["Xtr"], ytr=Dd["ytr"], cat=Dd["cat"])
    m = models.train(k, D, seed=100 + rep, subsample=C.E3_SUB)
    X, bg = Dd["Xte"][:C.N_INST], Dd["bg"]
    refs = np.stack([explain.reference_phi(m, x, bg)[0] for x in X])
    P = m.predict(X)
    return refs, P


def run_E3(n_jobs):
    out = f"{C.RES}/E3"; os.makedirs(out, exist_ok=True)
    for dn in C.DATASETS:
        for k in C.MODELS:
            f = f"{out}/{dn}_{k}.npz"
            if os.path.exists(f): continue
            t = time.time()
            res = Parallel(n_jobs=n_jobs)(delayed(e3_instance)(dn, k, r, None) for r in range(C.E3_K))
            np.savez_compressed(f, ref=np.stack([r[0] for r in res]), pred=np.stack([r[1] for r in res]))
            print(f"E3 {dn} {k} done {time.time()-t:.0f}s", flush=True)


# ---------------------------------------------------------------- E4 : shap library defaults (nsamples='auto', l1_reg='num_features(10)')
def e4_instance(dn, k, i, R):
    Dd, m = load_cell(dn, k)
    x, bg = Dd["Xte"][i], Dd["bg"]; d = len(x)
    out = np.zeros((R, d))
    for r in range(R):
        np.random.seed(seed_of(hash_ds(dn), hash_ds(k), i, r, 4242))
        ex = explain.shap.KernelExplainer(m.predict, bg)
        out[r] = np.asarray(ex.shap_values(x[None, :], silent=True)).reshape(-1)  # library defaults
    return out


def run_E4(n_jobs):
    out = f"{C.RES}/E4"; os.makedirs(out, exist_ok=True)
    for dn in C.DATASETS:
        for k in C.MODELS:
            f = f"{out}/{dn}_{k}.npz"
            if os.path.exists(f): continue
            t = time.time()
            res = Parallel(n_jobs=n_jobs)(delayed(e4_instance)(dn, k, i, C.R) for i in range(C.N_INST))
            np.savez_compressed(f, phi=np.stack(res))
            print(f"E4 {dn} {k} done {time.time()-t:.0f}s", flush=True)


# ---------------------------------------------------------------- E5 : high-dimensional stress test (Arrhythmia, d=262)
def e5_instance(k, est, i, budgets, R):
    Dd, m = load_cell(C.E5_DS, k)
    x, bg = Dd["Xte"][i], Dd["bg"]; d = len(x)
    out = np.zeros((len(budgets), R, d))
    for bi, B in enumerate(budgets):
        for r in range(R):
            s = seed_of(hash_ds(k), hash_ds(est), i, bi, r, 555)
            out[bi, r] = explain.kernel_phi(m.predict, x, bg, B, s) if est == "kernel" else explain.perm_phi(m.predict, x, bg, B, s)
    ref = explain.tree_phi(m, x, bg) if k == "rf" else np.full(d, np.nan)
    return out, ref


def run_E5(n_jobs):
    out = f"{C.RES}/E5"; os.makedirs(out, exist_ok=True)
    for k in C.E5_MODELS:
        for est in C.ESTIMATORS:
            f = f"{out}/{k}_{est}.npz"
            if os.path.exists(f): continue
            t = time.time()
            res = Parallel(n_jobs=n_jobs)(delayed(e5_instance)(k, est, i, C.E5_BUDGETS, C.E5_R) for i in range(C.E5_N))
            np.savez_compressed(f, phi=np.stack([r[0] for r in res]), ref=np.stack([r[1] for r in res]), budgets=C.E5_BUDGETS)
            print(f"E5 {k} {est} done {time.time()-t:.0f}s", flush=True)


def main():
    stage = sys.argv[1]; nj = int(sys.argv[2]) if len(sys.argv) > 2 else 38
    dict(E1=run_E1, E2=run_E2, E3=run_E3, E4=run_E4, E5=run_E5)[stage](nj)
