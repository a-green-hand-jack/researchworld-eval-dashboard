"""High-dimensional stress test (UCI Arrhythmia, d~270 players, XGBoost, log-odds output).

Ground truth: exact interventional TreeSHAP (shap.TreeExplainer with the same 100-row background), which is the exact
Shapley value of v(S)=mean_b margin(x_S, b_~S).  Estimators are run with REAL model calls.
usage: python exp_highd.py --procs 4
"""
import os, sys, time, pickle, argparse, itertools, warnings
os.environ.setdefault("OMP_NUM_THREADS", "1"); os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, multiprocessing as mp
import xgboost as xgb, shap
from math import comb
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
from metrics import vs_truth
from exp_main import seed_of

RAW = "/work/data/raw/arrhythmia/arrhythmia.data"
OUT = "/work/results/highd"
BUDGET_MULT = None
MS = [512, 1024, 2048, 4096, 8192, 16384]
NINST, NREP = 16, 20
G = {}


def load():
    df = pd.read_csv(RAW, header=None, na_values="?")
    y = (df.iloc[:, -1].values != 1).astype(int)  # 1 = any arrhythmia class, 0 = normal
    X = df.iloc[:, :-1]
    X = X.loc[:, X.nunique() > 1]  # drop constant columns
    return X.values.astype(np.float32), y


def kernel_sample(vfun, d, m, rng, mode="kernel"):
    """Kernel SHAP / leverage SHAP for large d with boolean masks (same logic as estimators.kernel_like, no dedupe)."""
    S = int(np.ceil((d - 1) / 2)); P = int(np.floor((d - 1) / 2))
    mass = np.array([(d - 1.0) / (s * (d - s)) for s in range(1, S + 1)]) if mode == "kernel" else np.ones(S)
    wv = mass.copy(); wv[:P] *= 2; wv /= wv.sum(); rem = wv.copy()
    ssum = sum(1.0 / (s * (d - s)) for s in range(1, d))
    masks, w = [], []
    nleft = float(m); nfull = 0
    for s in range(1, S + 1):
        nsub = comb(d, s) * (2 if s <= P else 1)
        if nleft * rem[s - 1] / nsub >= 1 - 1e-8:
            nfull += 1; nleft -= nsub
            if rem[s - 1] < 1: rem = rem / (1 - rem[s - 1])
            for c in itertools.combinations(range(d), s):
                mk = np.zeros(d, bool); mk[list(c)] = True
                masks.append(mk); w.append(1.0 / (comb(d, s) * s * (d - s) * ssum))
                if s <= P:
                    masks.append(~mk); w.append(1.0 / (comb(d, s) * s * (d - s) * ssum))
        else:
            break
    nfix = len(masks); left = m - nfix
    draws = None
    if nfull != S and left > 0:
        rw = mass[nfull:] / mass[nfull:].sum()
        sizes_all = np.arange(nfull + 1, S + 1)
        sz = rng.choice(sizes_all, size=left, p=rw)
        rows_per = np.where(sz <= P, 2, 1)
        keep = np.cumsum(rows_per) <= left
        sz = sz[keep]
        keys = rng.random((len(sz), d))
        ranks = np.argsort(np.argsort(keys, axis=1), axis=1)
        draws = (ranks < sz[:, None], sz)
    # ---- assemble design
    M = [np.array(masks, bool)] if nfix else []
    W = [np.array(w)] if nfix else []
    cd = None
    if draws is not None:
        mk, sz = draws
        paired = sz <= P
        allm = np.concatenate([mk, ~mk[paired]])
        # kernel mass left (share of Shapley kernel not enumerated)
        massfull = mass.copy(); massfull[:P] *= 2
        wleft = massfull[nfull:].sum() / massfull.sum()
        nd = len(sz)
        if mode == "kernel":
            cset = np.full(nd, wleft / (nd + paired.sum()))
        else:
            pi = rw[sz - nfull - 1]
            cset = 1.0 / (comb_arr(d, sz) * sz * (d - sz) * ssum) * comb_arr(d, sz) / pi / nd
        wd = np.concatenate([cset, cset[paired]])
        M.append(allm); W.append(wd)
        cd = (cset, paired, nd)
    Mk = np.concatenate(M); Wt = np.concatenate(W)
    v0, vf = G["v0"], G["vf"]
    vals = vfun(Mk)
    y = vals - v0; delta = vf - v0
    B = Mk.astype(np.float64)
    Z = B[:, :-1] - B[:, -1:]
    yt = y - B[:, -1] * delta
    Wz = Wt[:, None] * Z
    A = Z.T @ Wz
    theta = np.linalg.solve(A + 1e-12 * np.eye(d - 1), Wz.T @ yt)
    phi = np.append(theta, delta - theta.sum())
    return phi


def comb_arr(d, sz):
    return np.array([comb(d, int(s)) for s in sz], dtype=np.float64)


def make_vfun(model, xrow, bg, chunk=400):
    R = len(bg)
    def vfun(masks):
        out = np.empty(len(masks))
        for i in range(0, len(masks), chunk):
            mk = masks[i:i + chunk]
            H = np.where(mk[:, None, :], xrow[None, None, :], bg[None, :, :]).reshape(-1, bg.shape[1])
            out[i:i + chunk] = model.predict(H, output_margin=True).reshape(len(mk), R).mean(1)
        return out
    return vfun


def one(task):
    ii = task
    g = G["g"]
    model, bg, x = g["model"], g["bg"], g["Xte"][g["inst"][ii]]
    d = len(x)
    te = shap.TreeExplainer(model, data=bg, feature_perturbation="interventional", model_output="raw")
    phi = te.shap_values(x[None, :], check_additivity=False)[0]
    vfun = make_vfun(model, x, bg)
    v0 = vfun(np.zeros((1, d), bool))[0]; vf = vfun(np.ones((1, d), bool))[0]
    G["v0"], G["vf"] = v0, vf
    add_err = abs(phi.sum() - (vf - v0))
    res = dict(inst=int(g["inst"][ii]), phi=phi, add_err=float(add_err), runs={})
    for mode in ["kernel", "leverage"]:
        for m in MS:
            Ph = np.zeros((NREP, d))
            for r in range(NREP):
                rng = np.random.default_rng(seed_of(11, ii, m, r, 0 if mode == "kernel" else 1))
                Ph[r] = kernel_sample(vfun, d, m, rng, mode)
            res["runs"][(mode, m)] = Ph.astype(np.float32)
    # real shap library, default settings (nsamples auto, l1_reg num_features(10))
    ke = shap.KernelExplainer(lambda E: model.predict(np.asarray(E, np.float32), output_margin=True), bg)
    Pd = np.zeros((10, d)); Pn = np.zeros((10, d))
    for r in range(10):
        np.random.seed(seed_of(12, ii, r))
        Pd[r] = ke.shap_values(x[None, :], silent=True)[0]
        np.random.seed(seed_of(13, ii, r))
        Pn[r] = ke.shap_values(x[None, :], silent=True, l1_reg=False)[0]
    res["lib_default"], res["lib_noL1"] = Pd.astype(np.float32), Pn.astype(np.float32)
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--procs", type=int, default=4); a = ap.parse_args()
    X, y = load()
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, random_state=0, stratify=y)
    med = np.nanmedian(Xtr, 0)
    Xtr = np.where(np.isnan(Xtr), med, Xtr); Xte = np.where(np.isnan(Xte), med, Xte)
    model = xgb.XGBClassifier(n_estimators=150, max_depth=3, learning_rate=0.1, subsample=0.8, colsample_bytree=0.5,
                              tree_method="hist", n_jobs=1, random_state=0, verbosity=0).fit(Xtr, ytr)
    auc = roc_auc_score(yte, model.predict_proba(Xte)[:, 1])
    print("d", X.shape[1], "ntrain", len(Xtr), "AUC", auc, flush=True)
    rng = np.random.RandomState(1)
    bg = Xtr[rng.choice(len(Xtr), 100, replace=False)]
    inst = np.sort(rng.choice(len(Xte), NINST, replace=False))
    G["g"] = dict(model=model, bg=bg, Xte=Xte, inst=inst)
    t0 = time.time(); res = []
    with mp.get_context("fork").Pool(a.procs) as pool:
        for n, r in enumerate(pool.imap_unordered(one, range(NINST))):
            res.append(r); print(f"[{time.time()-t0:6.0f}s] {n+1}/{NINST} add_err={r['add_err']:.2e}", flush=True)
    os.makedirs(OUT, exist_ok=True)
    pickle.dump(dict(res=res, auc=auc, d=X.shape[1], ntrain=len(Xtr)), open(f"{OUT}/highd.pkl", "wb"))
