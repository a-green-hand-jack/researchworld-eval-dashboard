"""Run repeated KernelSHAP; usage: python run.py [datasets...]. Saves results/{ds}_{model}.npz"""
import os, sys, time, numpy as np, shap, pickle
from joblib import Parallel, delayed
from common import *
BUDGETS = [128, 512, 2048, 8192]
R = 10; NINST = 60; NBG = 50; NRETRAIN = 5; NBGRES = 10; REFM = 16384; REFR = 5

def f_of(model):
    # XGBoost is explained on the log-odds (margin): shap's interventional TreeSHAP is exact there, but its
    # "probability" mode is not the exact Shapley value of the probability function (verified on Pima, see README).
    if isinstance(model, xgb.XGBClassifier): return lambda A: model.predict(A, output_margin=True)
    return lambda A: model.predict_proba(A)[:, 1]

def tree_exact(model, bg, X):
    v = shap.TreeExplainer(model, data=bg, feature_perturbation="interventional", model_output="raw" if isinstance(model, xgb.XGBClassifier) else "probability").shap_values(X, check_additivity=False)
    return v[..., 1] if v.ndim == 3 else v

def explain_inst(model, bg, x, i, seed0, reps_budgets):
    ex = shap.KernelExplainer(f_of(model), bg)
    out = {}
    for M, reps in reps_budgets:
        arr = []
        for r in range(reps):
            np.random.seed(seed0 + 100003 * i + 1009 * M % 99991 + r * 7919)
            arr.append(ex.shap_values(x, nsamples=M, silent=True, l1_reg=0))
        out[M] = np.array(arr).reshape(reps, -1)
    return out

def main(ds, kind):
    Xtr, Xte, ytr, yte = split(ds)
    model = make_model(kind, 0).fit(Xtr, ytr)
    rs = np.random.RandomState(1)
    bg = Xtr.values[rs.choice(len(Xtr), NBG, replace=False)]
    idx = rs.choice(len(Xte), NINST, replace=False)
    X = Xte.values[idx]; d = X.shape[1]
    t0 = time.time()
    rb = [(M, R) for M in BUDGETS]
    need_ref_kernel = kind in ("lr", "mlp")
    if need_ref_kernel: rb = rb + [(REFM, REFR)]
    res = Parallel(n_jobs=(5 if ds == "arr" else 16))(delayed(explain_inst)(model, bg, X[i], i, 12345, rb) for i in range(NINST))
    phi = np.stack([np.stack([res[i][M] for M in BUDGETS]) for i in range(NINST)])  # n, B, R, d
    out = dict(phi=phi, budgets=np.array(BUDGETS), X=X, pred=f_of(model)(X), d=d, cols=np.array(Xtr.columns), time=time.time() - t0)
    if need_ref_kernel:
        out["ref"] = np.stack([res[i][REFM].mean(0) for i in range(NINST)])
        out["ref_runs"] = np.stack([res[i][REFM] for i in range(NINST)])
    else:
        out["ref"] = tree_exact(model, bg, X)
        rt = []
        for s in range(1, NRETRAIN + 1):  # retrain noise, same bg/instances
            m2 = make_model(kind, s).fit(Xtr, ytr)
            rt.append(tree_exact(m2, bg, X))
        out["retrain"] = np.stack(rt)
        rb2 = []
        for s in range(NBGRES):  # background-resample noise, same model
            b2 = Xtr.values[np.random.RandomState(100 + s).choice(len(Xtr), NBG, replace=False)]
            rb2.append(tree_exact(model, b2, X))
        out["bgres"] = np.stack(rb2)
    np.savez(f"/work/results/{ds}_{kind}.npz", **out)
    print(ds, kind, "done", round(time.time() - t0), "s", flush=True)

if __name__ == "__main__":
    dss = sys.argv[1:] or DATASETS
    for ds in dss:
        ks = (["rf", "xgb"] if ds in TREE_ONLY else MODELS)
        if os.environ.get("ONLY"): ks = [k for k in ks if k in os.environ["ONLY"].split(",")]
        for k in ks: main(ds, k)
