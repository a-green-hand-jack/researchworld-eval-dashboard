"""A4 (covariate shift with known density ratio, weighted split conformal) and
A5 (split vs CV+ / jackknife+ at small n) for simplex-valued targets.  Same DGPs / Grid as exp_a."""
import argparse, json, os, time
import numpy as np, pandas as pd
from scipy.special import ndtr
from .dgp import DGP
from .scores import SCORES
from .simplex import uniform_simplex
from .models import ClrOLS, LogScale
from .conformal import conformal_quantile
from .exp_a import Grid, observe, GIT_REV

SCORE_SET = ["euc", "hell", "aitch", "euc/n"]


def fit_model(X, Y, name):
    """returns f(X) -> (yhat, sigma) for score `name` ('euc/n' uses a log-linear scale model)."""
    mean = ClrOLS().fit(X, Y)
    if name.endswith("/n"):
        sc = LogScale().fit(X, SCORES[name[:-2]](Y, mean.predict(X)))
        return lambda Z: (mean.predict(Z), sc.predict(Z))
    return lambda Z: (mean.predict(Z), np.ones(len(Z)))


def sc(name, Y, yh, sg):
    return SCORES[name.split("/")[0]](Y, yh) / sg


# ---------------- A4: weighted split conformal ----------------
def weighted_threshold(s_cal, w_cal, w_test, alpha):
    """Per-test-point threshold of weighted split conformal (Tibshirani et al. 2019): smallest s_k with
    sum_{i: s_i<=s_k} w_i >= (1-alpha) * (sum_i w_i + w(x))   (inf if none)."""
    o = np.argsort(s_cal); s, cw = s_cal[o], np.cumsum(w_cal[o])
    target = (1 - alpha) * (w_cal.sum() + w_test)
    k = np.searchsorted(cw, target, side="left")
    return np.where(k < len(s), s[np.minimum(k, len(s) - 1)], np.inf)


def run_a4(dgp, grid, seed, delta, n_tr=500, n_cal=500, n_te=5000, alpha=0.1, scores=SCORE_SET):
    r = np.random.default_rng(seed)
    X1 = dgp.sample_x(r, n_tr); Y1 = dgp.sample_y(r, X1)
    Xc = dgp.sample_x(r, n_cal); Yc = dgp.sample_y(r, Xc)
    Xt = dgp.sample_x(r, n_te); Xt[:, 0] += delta; Yt = dgp.sample_y(r, Xt)       # test covariate shift in x_0
    logw = lambda X: delta * X[:, 0] - delta ** 2 / 2                              # N(delta,1)/N(0,1) density ratio
    wc, wt = np.exp(logw(Xc)), np.exp(logw(Xt))
    ess = wc.sum() ** 2 / (wc ** 2).sum()
    rows = []
    for nm in scores:
        f = fit_model(X1, Y1, nm)
        yc, sgc = f(Xc); yt, sgt = f(Xt)
        s_cal, s_te = sc(nm, Yc, yc, sgc), sc(nm, Yt, yt, sgt)
        q_u = conformal_quantile(s_cal, alpha)
        q_w = weighted_threshold(s_cal, wc, wt, alpha)
        cu, cw = s_te <= q_u, s_te <= q_w
        rows.append(dict(method=nm, seed=seed, delta=delta, ess=ess, cov_unweighted=cu.mean(), cov_weighted=cw.mean(),
                         inf_frac_w=np.isinf(q_w).mean(), q_u=q_u))
    return rows


# ---------------- A5: split vs CV+ / jackknife+ ----------------
def cvplus_fit(X, Y, folds, name):
    """returns per-fold predictors and the out-of-fold calibration scores R_i with their fold ids"""
    n = len(X); fid = np.zeros(n, int); models = []
    R = np.empty(n)
    for k, idx in enumerate(folds):
        fid[idx] = k
        tr = np.setdiff1d(np.arange(n), idx)
        f = fit_model(X[tr], Y[tr], name)
        models.append(f)
        yh, sg = f(X[idx]); R[idx] = sc(name, Y[idx], yh, sg)
    return models, R, fid


def cvplus_member(models, R, fid, x, Ycand, name, alpha):
    """membership of candidate Ycand (m,K) in the CV+ set at a single x (1,d)."""
    n = len(R); cnt = np.zeros(len(Ycand))
    for k, f in enumerate(models):
        yh, sg = f(x)
        s = sc(name, Ycand, np.repeat(yh, len(Ycand), 0), sg[0])
        Rk = np.sort(R[fid == k])
        cnt += np.searchsorted(Rk, s, side="left")       # number of R_i (fold k) strictly below s
    return cnt < (1 - alpha) * (n + 1)


def run_a5(dgp, grid, seed, n, mode, n_te=2000, alpha=0.1, scores=("euc", "hell", "aitch", "euc/n"), Mv=30000, nfold=5):
    r = np.random.default_rng(seed)
    X = dgp.sample_x(r, n); Y = dgp.sample_y(r, X)
    Xt = dgp.sample_x(r, n_te); Yt = dgp.sample_y(r, Xt)
    rows = []
    U = grid.U[:Mv]; vm = grid.oracle_frac >= 20.0 / Mv
    perm = r.permutation(n)
    for nm in scores:
        t0 = time.time()
        if mode == "split":
            tr, ca = perm[: n // 2], perm[n // 2:]
            f = fit_model(X[tr], Y[tr], nm)
            yc, sgc = f(X[ca]); q = conformal_quantile(sc(nm, Y[ca], yc, sgc), alpha)
            yt, sgt = f(Xt); cov = sc(nm, Yt, yt, sgt) <= q
            yg, sgg = f(grid.X)
            sg_ = np.broadcast_to(sgg, (len(grid.X),))
            cg = (SCORES[nm.split("/")[0]](grid.Y, yg) / sg_ <= q).mean(0)
            fr = np.array([(SCORES[nm.split("/")[0]](U, yg[i]) / sg_[i] <= q).mean() for i in range(grid.nv)])
        else:
            nf = n if mode == "jackknife+" else nfold
            folds = np.array_split(perm, nf) if nf < n else [np.array([i]) for i in range(n)]
            models, R, fid = cvplus_fit(X, Y, folds, nm)
            # coverage on test points
            cov = np.empty(n_te); sub = min(n_te, 1000)
            cov = np.array([cvplus_member(models, R, fid, Xt[i:i + 1], Yt[i:i + 1], nm, alpha)[0] for i in range(sub)])
            cg = np.array([cvplus_member(models, R, fid, grid.X[i:i + 1], grid.Y[:, i], nm, alpha).mean() for i in range(600)])
            fr = np.array([cvplus_member(models, R, fid, grid.X[i:i + 1], U, nm, alpha).mean() for i in range(grid.nv)])
        slab = grid.slab if mode == "split" else grid.slab[:600]
        sl = np.array([cg[slab == j].mean() for j in range(10)])
        lr = np.log10(np.maximum(fr, 0.5 / Mv) / grid.oracle_frac)[vm]
        rows.append(dict(method=nm, seed=seed, n=n, mode=mode, cov=cov.mean(), n_test_used=len(cov), true_marg_cov=cg.mean(),
                         true_x0_10_min=sl.min(), true_x0_10_dev=np.abs(sl - (1 - alpha)).mean(), log_vol_ratio=lr.mean(),
                         vol_zero=(fr[vm] == 0).mean(), secs=time.time() - t0))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp", choices=["a4", "a5"], required=True)
    ap.add_argument("--config", required=True); ap.add_argument("--reps", type=int, default=100)
    ap.add_argument("--seed0", type=int, default=0); ap.add_argument("--out", required=True); ap.add_argument("--tag", default="")
    a = ap.parse_args(); cfg = json.loads(a.config)
    ex = {k: cfg.pop(k) for k in list(cfg) if k in ("delta", "n", "mode", "n_cal", "n_tr")}
    dgp = DGP(**cfg)
    grid = Grid(dgp, 0.1) if a.exp == "a5" else None
    rows = []
    for i in range(a.reps):
        t0 = time.time()
        rs = run_a4(dgp, grid, a.seed0 + i, **ex) if a.exp == "a4" else run_a5(dgp, grid, a.seed0 + i, **ex)
        for r_ in rs: r_.update(config=a.tag, git_rev=GIT_REV, kind=dgp.kind, K=dgp.K, hetero=dgp.hetero, form=dgp.form)
        rows += rs
        if i % 10 == 0: print(f"rep {i} {time.time()-t0:.1f}s", flush=True)
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    pd.DataFrame(rows).to_csv(a.out, index=False)


if __name__ == "__main__":
    main()
