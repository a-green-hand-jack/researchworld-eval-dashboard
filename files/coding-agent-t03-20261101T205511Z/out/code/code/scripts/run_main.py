"""Main experiment: for one (dataset, model) and a chunk of instances, run
  protocol A  (full reruns: new random background AND new coalition seed), kernel + permutation, all budgets;
  protocol B  (fixed background, new coalition seed only), kernel + permutation, all budgets, plus truth;
  'kernel_default' = shap.KernelExplainer.shap_values(x) with library defaults (l1_reg=num_features(10), nsamples auto).
Usage: python run_main.py DATASET MODEL i0 i1   -> results/main/{DATASET}_{MODEL}_{i}.npz"""
import os, sys, time
os.environ.setdefault("OMP_NUM_THREADS", "1")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import numpy as np
from shapre import data, models, estimators as E, truth as T, config as C

OUT = os.environ.get("SHAPRE_OUT", "/work/results/main")


def instances(D, n):
    return np.random.RandomState(C.INSTANCE_SEED).choice(len(D["Xte"]), n, replace=False)


def bg(D, i, r, role, b=C.B):
    rs = np.random.RandomState(7_000_000 + 1000 * i + 10 * r + role)
    return D["Xtr"][rs.choice(len(D["Xtr"]), b, replace=False)]


def run_unit(ds, kind, i0, i1):
    cfg = C.DATASETS[ds]
    D = data.load(ds, n_sub=cfg["n_sub"])
    d = D["d"]
    mo = models.train(kind, D["is_cat"], D["Xtr"], D["ytr"], seed=0)
    ev = models.evaluate(mo, D["Xte"], D["yte"])
    idx = instances(D, cfg["n_inst"])
    grid = [m for m in cfg["grid"]]
    for ii in range(i0, min(i1, len(idx))):
        fn = f"{OUT}/{ds}_{kind}_{ii}.npz"
        if os.path.exists(fn):
            continue
        x = D["Xte"][idx[ii]]
        res = dict(x=x, test_index=idx[ii], px=mo.predict(x[None])[0], auc=ev["auc"], acc=ev["acc"], grid=np.array(grid))
        t_unit = time.time()
        # truth w.r.t. fixed background Z0
        Z0 = bg(D, ii, 0, 99)
        t = time.time(); ph, se, kd = T.truth(mo, x, Z0, ref_seed=ii); res.update(truth=ph, truth_se=se, truth_kind=kd, truth_time=time.time() - t)
        res["base_value"] = mo.predict(Z0).mean()
        # population-level target: background = up to 1000 training rows
        rs = np.random.RandomState(8_000_000 + ii); Zp = D["Xtr"][rs.choice(len(D["Xtr"]), min(1000, len(D["Xtr"])), replace=False)]
        t = time.time(); ph, se, kd = T.truth(mo, x, Zp, ref_seed=10_000 + ii, ref_coal=16384, enum_d=10)
        res.update(pop_truth=ph, pop_truth_se=se, pop_truth_kind=kd, pop_truth_time=time.time() - t)
        # protocol A and B
        tm = {}
        for est, fn_est in (("kernel", E.kernel_run), ("perm", E.perm_run)):
            for m in grid:
                if est == "perm" and m < 2 * d + 1:
                    continue
                if est == "kernel" and m < d + 1:
                    continue
                A = np.zeros((C.R_A, d)); Bm = np.zeros((C.R_B, d)); t = time.time()
                for r in range(C.R_A):
                    A[r] = fn_est(mo.predict, x, bg(D, ii, r, 1), m, seed=100_000 + 7 * r + m % 997)
                tm[f"{est}_{m}"] = (time.time() - t) / C.R_A
                for r in range(C.R_B):
                    Bm[r] = fn_est(mo.predict, x, Z0, m, seed=500_000 + 11 * r + m % 991)
                res[f"A_{est}_{m}"] = A; res[f"B_{est}_{m}"] = Bm
        # library-default Kernel SHAP call (unregularised variant above is our 'kernel')
        Ad = np.zeros((C.R_A, d))
        for r in range(C.R_A):
            np.random.seed(900_000 + r)
            import shap
            Ad[r] = np.asarray(shap.KernelExplainer(mo.predict, bg(D, ii, r, 1)).shap_values(x[None], silent=True)).reshape(-1)
        res["A_kernel_default"] = Ad
        res["times"] = tm; res["unit_time"] = time.time() - t_unit
        np.savez_compressed(fn + ".tmp.npz", **{k: (np.array(v, dtype=object) if k == "times" else v) for k, v in res.items()})
        os.replace(fn + ".tmp.npz", fn)


if __name__ == "__main__":
    ds, kind, i0, i1 = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    os.makedirs(OUT, exist_ok=True)
    run_unit(ds, kind, i0, i1)
