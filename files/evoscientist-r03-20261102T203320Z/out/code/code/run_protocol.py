"""Held-out-model evaluation protocol.

For each fold (a set of held-out models; the rest is the training matrix):
  1. standardise columns, tune hyper-parameters (rank r, covariance shrinkage) by inner validation on training rows
  2. fit factor model / covariance on the training matrix only
  3. for each held-out model with enough observed benchmarks: for each budget k and each selection method choose
     S (|S|=k) among the benchmarks that this model has *observed* (selection never sees the model's scores),
     reveal its scores on S, predict all remaining observed benchmarks T, record error metrics.
Splits: 'family' = grouped K-fold (a whole family/organisation is held out together), 'random' = ordinary K-fold.

Usage: python code/run_protocol.py --data mteb_mid --split family --kmax 24 --folds 10
"""
import os
os.environ.setdefault("OMP_NUM_THREADS", "1"); os.environ.setdefault("OPENBLAS_NUM_THREADS", "1"); os.environ.setdefault("MKL_NUM_THREADS", "1")
import argparse, re, time
import numpy as np, pandas as pd
from joblib import Parallel, delayed
import bsp

BASE_K = [1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 24, 32, 40, 48]
SELS_ALL = ["random", "greedy_iopt", "top_load", "piv_qr", "kmeans", "cov_greedy"]
PREDS_ALL = ["mean", "fa1", "fa", "ppca", "gauss", "knn"]


def family_of(name, data):
    if data.startswith("mteb"):
        return name.split("__")[0]
    if data == "olb":
        return name.split("/")[0]
    return re.split(r"[ ._\-(/:]", name.strip())[0].lower()


def make_folds(models, data, split, n_folds, seed):
    rng = np.random.default_rng(seed)
    n = len(models)
    if split == "random":
        perm = rng.permutation(n)
        return [perm[i::n_folds] for i in range(n_folds)]
    fam = np.array([family_of(m, data) for m in models])
    uf = list(pd.unique(fam))
    rng.shuffle(uf)
    sizes = {f: (fam == f).sum() for f in uf}
    uf.sort(key=lambda f: -sizes[f])          # largest families first, then to the lightest fold (balanced)
    folds = [[] for _ in range(n_folds)]
    load = np.zeros(n_folds)
    for f in uf:
        j = int(np.argmin(load))
        folds[j].extend(np.where(fam == f)[0].tolist()); load[j] += sizes[f]
    return [np.array(f) for f in folds]


def err_metrics(zhat, z, sd, mu, y, T):
    e = zhat[T] - z[T]
    return (float(np.mean(e ** 2)), float(np.mean(np.abs(e) * sd[T])),
            float(abs(np.mean(zhat[T] * sd[T] + mu[T]) - np.mean(y[T]))), float(np.mean(np.abs(e))))


def inner_val(Ztr, ks_val, rcands, alphas, seed):
    rng = np.random.default_rng(seed)
    M = len(Ztr)
    perm = rng.permutation(M)
    nv = max(10, M // 5)
    val, fit = perm[:nv], perm[nv:]
    Zf = Ztr[fit]
    O = ~np.isnan(Ztr)
    draws = []
    for i in val:
        C = np.where(O[i])[0]
        for k in ks_val:
            if len(C) < k + 3:
                continue
            for _ in range(2):
                S = rng.permutation(C)[:k]
                T = np.setdiff1d(C, S)
                draws.append((i, S, T))
    out = {"fa": {}, "gauss": {}}
    for r in rcands:
        V, psi = bsp.fa_em(Zf, r, iters=60)
        e = [np.sqrt(np.mean((bsp.predict_fa(V, psi, S, Ztr[i, S])[T] - Ztr[i, T]) ** 2)) for i, S, T in draws]
        out["fa"][r] = float(np.mean(e))
    R = bsp.pairwise_corr(Zf)
    for a in alphas:
        Sg = bsp.shrink_cov(R, a)
        e = [np.sqrt(np.mean((bsp.predict_gauss(Sg, S, Ztr[i, S])[T] - Ztr[i, T]) ** 2)) for i, S, T in draws]
        out["gauss"][a] = float(np.mean(e))
    r_best = min(out["fa"], key=out["fa"].get)
    a_best = min(out["gauss"], key=out["gauss"].get)
    return r_best, a_best, out


def run_fold(Y, models, test_idx, kgrid, cfg, fold_id, sels, preds, seed):
    t0 = time.time()
    rng = np.random.default_rng(seed * 1000 + fold_id)
    M, N = Y.shape
    train_idx = np.setdiff1d(np.arange(M), test_idx)
    Ytr = Y[train_idx]
    # optional artificial changes of the training set (data-condition sweeps)
    if cfg.get("train_frac", 1.0) < 1.0:
        keep = rng.permutation(len(train_idx))[: max(8, int(cfg["train_frac"] * len(train_idx)))]
        Ytr = Ytr[keep]
    if cfg.get("train_miss", 0.0) > 0:
        mask = rng.random(Ytr.shape) < cfg["train_miss"]
        Ytr = np.where(mask, np.nan, Ytr)
    mu, sd = bsp.fit_std(Ytr)
    Ztr = (Ytr - mu) / sd
    ks_val = sorted({kgrid[0], kgrid[len(kgrid) // 3], kgrid[2 * len(kgrid) // 3], kgrid[-1]})
    rcands = [r for r in cfg["rcands"] if r <= max(1, N // 2) and r < len(Ztr) // 4 + 1]
    r_best, a_best, iv = inner_val(Ztr, ks_val, rcands, cfg["alphas"], seed + fold_id)
    V, psi = bsp.fa_em(Ztr, r_best)
    V1, psi1 = bsp.fa_em(Ztr, 1)
    Vp, psip = bsp.fa_em(Ztr, r_best, iso=True)
    Rm = bsp.pairwise_corr(Ztr)
    Sg = bsp.shrink_cov(Rm, a_best)
    G = V.T @ V
    kmax = kgrid[-1]
    rows = []
    cand_test = [i for i in test_idx if (~np.isnan(Y[i])).sum() >= kmax + cfg["min_targets"]]
    if cfg.get("max_test") and len(cand_test) > cfg["max_test"]:
        cand_test = list(rng.permutation(cand_test)[: cfg["max_test"]])
    for i in cand_test:
        y = Y[i]
        C = np.where(~np.isnan(y))[0]
        z = (y - mu) / sd
        # selection orders (nested ones are computed once up to kmax)
        orders = {}
        if "greedy_iopt" in sels:
            orders["greedy_iopt"] = bsp.sel_greedy_iopt(C, kmax, V, psi, G)
        if "top_load" in sels:
            orders["top_load"] = bsp.sel_top_load(C, kmax, V, psi)
        if "piv_qr" in sels:
            orders["piv_qr"] = bsp.sel_piv_qr(C, kmax, V, psi)
        if "cov_greedy" in sels:
            orders["cov_greedy"] = bsp.sel_cov_greedy(C, kmax, Sg)
        for k in kgrid:
            T_cache = {}
            def evaluate(S, sel, rep=None):
                S = np.asarray(S)
                T = np.setdiff1d(C, S)
                for p in preds.get(sel, preds["_default"]):
                    if p == "mean":
                        zh = np.zeros(N)
                    elif p == "fa1":
                        zh = bsp.predict_fa(V1, psi1, S, z[S])
                    elif p == "fa":
                        zh = bsp.predict_fa(V, psi, S, z[S])
                    elif p == "ppca":
                        zh = bsp.predict_fa(Vp, psip, S, z[S])
                    elif p == "gauss":
                        zh = bsp.predict_gauss(Sg, S, z[S])
                    elif p == "knn":
                        zh = bsp.predict_knn(Ztr, S, z[S])
                    m = err_metrics(zh, z, sd, mu, y, T)
                    yield p, m, len(T)
            for sel in sels:
                if sel == "random":
                    acc = {}
                    for rep in range(cfg["nrep"]):
                        S = bsp.sel_random(C, k, rng)
                        for p, m, nt in evaluate(S, "random"):
                            acc.setdefault(p, []).append(m)
                    for p, ms in acc.items():
                        ms = np.array(ms)
                        rows.append((models[i], fold_id, sel, p, k, *ms.mean(0), nt, ms[:, 0].std(), ms[:, 0].max()))
                else:
                    S = bsp.sel_kmeans_cover(C, k, V, psi, seed) if sel == "kmeans" else orders[sel][:k]
                    for p, m, nt in evaluate(S, sel):
                        rows.append((models[i], fold_id, sel, p, k, *m, nt, 0.0, m[0]))
    df = pd.DataFrame(rows, columns=["model", "fold", "sel", "pred", "k", "mse_z", "mae", "agg", "mae_z", "n_targets", "mse_sd_reps", "mse_max_reps"])
    df["r_sel"] = r_best; df["alpha_sel"] = a_best
    # model-implied (theory) expected MSE curves, computed from the fitted models only (no held-out scores)
    imp = {}
    ir = np.random.default_rng(seed + 77 + fold_id)
    allc = np.arange(N)
    gS = bsp.sel_greedy_iopt(allc, kmax, V, psi, G)
    gC = bsp.sel_cov_greedy(allc, kmax, Sg)
    for k in kgrid:
        fa_r, ga_r = [], []
        for _ in range(20):
            S = ir.permutation(N)[:k]
            fa_r.append(bsp.implied_fa(V, psi, S)); ga_r.append(bsp.implied_gauss(Sg, S))
        imp[k] = dict(fa_random=float(np.mean(fa_r)), gauss_random=float(np.mean(ga_r)),
                      fa_greedy=bsp.implied_fa(V, psi, np.array(gS[:k])), gauss_covgreedy=bsp.implied_gauss(Sg, np.array(gC[:k])),
                      fa_noise_floor=float(psi.mean()))
    fit = dict(fold=fold_id, implied=imp, r=r_best, alpha=a_best, n_train=len(Ztr), inner_fa=iv["fa"], inner_gauss=iv["gauss"],
               psi_mean=float(psi.mean()), secs=time.time() - t0)
    return df, fit


def load(data):
    D = pd.read_csv(f"data/processed/{data}.csv", index_col=0)
    return D


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--split", default="family", choices=["family", "random"])
    ap.add_argument("--kmax", type=int, default=24)
    ap.add_argument("--folds", type=int, default=10)
    ap.add_argument("--min_targets", type=int, default=8)
    ap.add_argument("--nrep", type=int, default=10)
    ap.add_argument("--max_test", type=int, default=0)
    ap.add_argument("--min_obs_model", type=int, default=0, help="drop models with fewer observed benchmarks")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--train_frac", type=float, default=1.0)
    ap.add_argument("--train_miss", type=float, default=0.0)
    ap.add_argument("--rcands", default="1,2,3,4,6,8,12,16,24")
    ap.add_argument("--sels", default=",".join(SELS_ALL))
    ap.add_argument("--tag", default="")
    ap.add_argument("--jobs", type=int, default=20)
    a = ap.parse_args()
    D = load(a.data)
    if a.min_obs_model:
        D = D.loc[D.notna().sum(axis=1) >= a.min_obs_model]
    Y = D.values.astype(float)
    models = list(D.index)
    kgrid = [k for k in BASE_K if k <= a.kmax]
    cfg = dict(rcands=[int(x) for x in a.rcands.split(",")], alphas=[0.02, 0.05, 0.1, 0.2, 0.4], min_targets=a.min_targets,
               nrep=a.nrep, max_test=a.max_test, train_frac=a.train_frac, train_miss=a.train_miss)
    sels = a.sels.split(",")
    preds = {"_default": ["fa", "gauss"], "random": PREDS_ALL, "greedy_iopt": PREDS_ALL, "cov_greedy": PREDS_ALL}
    folds = make_folds(models, a.data, a.split, a.folds, a.seed)
    print(f"{a.data} {Y.shape} obs={np.mean(~np.isnan(Y)):.3f} split={a.split} kgrid={kgrid}", flush=True)
    t0 = time.time()
    res = Parallel(n_jobs=min(a.jobs, len(folds)))(
        delayed(run_fold)(Y, models, f, kgrid, cfg, j, sels, preds, a.seed) for j, f in enumerate(folds))
    df = pd.concat([r[0] for r in res], ignore_index=True)
    fits = [r[1] for r in res]
    df.insert(0, "data", a.data); df.insert(1, "split", a.split)
    name = f"{a.data}_{a.split}{a.tag}"
    os.makedirs("results/raw", exist_ok=True)
    df.to_csv(f"results/raw/{name}.csv.gz", index=False)
    pd.DataFrame(fits).to_json(f"results/raw/{name}_fits.json", orient="records", indent=1)
    print(f"done {name}: {len(df)} rows, {df.model.nunique()} test models, {time.time()-t0:.0f}s, r_sel={[f['r'] for f in fits]}", flush=True)
    df["rmse"] = np.sqrt(df.mse_z)
    for p in ["fa", "gauss"]:
        print(p); print(df[df.pred == p].groupby(["sel", "k"]).rmse.mean().unstack(0).round(3).to_string())


if __name__ == "__main__":
    main()
