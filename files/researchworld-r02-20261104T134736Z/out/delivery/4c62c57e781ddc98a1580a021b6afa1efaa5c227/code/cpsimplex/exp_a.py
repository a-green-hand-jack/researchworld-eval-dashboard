"""Experiment A: split-conformal regions for simplex-valued targets with known DGP.

One replication = fresh train / calibration / test draw from a fixed DGP population.
Ground-truth conditional coverage is computed on a fixed stratified x-grid with R fresh y-draws per x.
"""
import argparse, json, os, time, hashlib
import numpy as np
import pandas as pd
from scipy.special import ndtri, ndtr
from .dgp import DGP
from .scores import SCORES, score as base_score
from .simplex import clr, replace_zeros, uniform_simplex, dirichlet_logpdf, closure
from .models import ConstClr, ClrOLS, LogScale, DirichletReg
from .conformal import conformal_quantile

NSLAB = 10
NS_LIST = (5, 10, 20)
NTE_LIST = (500, 2000, 10000)
BASE = ["euc", "l1", "hell", "aitch", "kl_fwd", "kl_rev"]
METHODS = BASE + [b + "/n" for b in BASE] + ["euc/nq", "aitch/nq", "dirnll"]


try:
    import subprocess
    GIT_REV = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                             cwd=os.path.dirname(os.path.abspath(__file__))).stdout.strip()
except Exception:
    GIT_REV = "unknown"


def observe(Y, digits, delta):
    if digits is None:
        return Y
    Yr = closure(np.round(Y, digits))
    return replace_zeros(Yr, delta)


class Grid:
    """Fixed evaluation grid + oracle HPD volume (cached per DGP/alpha/obs settings)."""
    def __init__(self, dgp, alpha, per_slab=300, R=30, nv=20, M=100_000, digits=None, delta=1e-4, seed=777):
        r = np.random.default_rng(seed)
        self.dgp, self.alpha, self.digits, self.delta = dgp, alpha, digits, delta
        edges = ndtri(np.linspace(0, 1, NSLAB + 1)[1:-1])
        edges = np.r_[-np.inf, edges, np.inf]
        self.edges = edges
        # round-robin over slabs so that the first nv x's are stratified
        X = dgp.sample_x(r, per_slab * NSLAB)
        u = r.uniform(size=per_slab * NSLAB)
        slab = np.tile(np.arange(NSLAB), per_slab)
        lo = np.r_[0, np.linspace(0, 1, NSLAB + 1)[1:-1], 1.0]
        ps = np.linspace(0, 1, NSLAB + 1)
        X[:, 0] = ndtri(np.clip(ps[slab] + u / NSLAB, 1e-9, 1 - 1e-9))
        self.X, self.slab = X, slab
        self.Y = observe(dgp.sample_y(r, X, reps=R), digits, delta)           # (R, n, K)
        self.nv = nv
        # oracle HPD regions
        K = dgp.K
        Yo = dgp.sample_y(r, X[:nv], reps=1000)
        nl = dgp.neglogdens(X[:nv], Yo)
        t = np.quantile(nl, 1 - alpha, axis=0)               # (nv,)
        self.U = uniform_simplex(r, M, K)
        self.oracle_frac = np.array([(dgp.neglogdens(np.repeat(X[i:i + 1], M, 0), self.U) <= t[i]).mean()
                                     for i in range(nv)])
        # oracle true coverage on grid sample (sanity) -- by construction ~ 1-alpha
        nlg = dgp.neglogdens(X[:nv], self.Y[:, :nv])
        self.oracle_cov = (nlg <= t).mean()
        self.t = t
        self.vmask = self.oracle_frac >= 20.0 / M   # volumes of regions below MC resolution are not compared


def run_rep(dgp, grid, seed, n_tr=500, n_cal=500, n_te=10000, alpha=0.1, digits=None, delta=1e-4,
            methods=METHODS, volume=True, halfsplit=False, const_mean=False, cells=False):
    r = np.random.default_rng(seed)
    def draw(n):
        X = dgp.sample_x(r, n)
        return X, observe(dgp.sample_y(r, X), digits, delta)
    Xtr, Ytr = draw(n_tr); Xc, Yc = draw(n_cal); Xt, Yt = draw(n_te)
    mean = (ConstClr() if const_mean else ClrOLS()).fit(Xtr, Ytr)
    ytr_h, yc_h, yt_h, yg_h = (mean.predict(Xtr), mean.predict(Xc), mean.predict(Xt), mean.predict(grid.X))
    need_dir = "dirnll" in methods
    if need_dir:
        dm = DirichletReg().fit(Xtr, Ytr)
        ac, at, ag = dm.alpha(Xc), dm.alpha(Xt), dm.alpha(grid.X)
    rows = []
    for m in methods:
        t0 = time.time()
        if m == "dirnll":
            sc = lambda Y, a: -dirichlet_logpdf(Y, a)
            s_cal, s_te = sc(Yc, ac), sc(Yt, at)
            s_g = sc(grid.Y, ag)                       # (R,n)
            s_u = lambda i: sc(grid.U, ag[i])
        elif m == "maha":
            # Mahalanobis distance of the clr residual, pseudo-inverse of the training-residual covariance (rank K-1)
            Rtr = clr(Ytr) - clr(ytr_h)
            Sinv = np.linalg.pinv(np.cov(Rtr.T))
            f = lambda Y, mu: np.einsum("...i,ij,...j->...", clr(Y) - clr(mu), Sinv, clr(Y) - clr(mu))
            s_cal, s_te, s_g = f(Yc, yc_h), f(Yt, yt_h), f(grid.Y, yg_h)
            s_u = lambda i: f(grid.U, yg_h[i])
        else:
            nm = m
            norm = None
            if m.endswith("/nq"):
                nm, norm = m[:-3], True
            elif m.endswith("/n"):
                nm, norm = m[:-2], False
            f = SCORES[nm]
            if norm is None:
                sig_c = sig_t = sig_g = 1.0
            else:
                ls = LogScale(quad=norm).fit(Xtr, f(Ytr, ytr_h))
                sig_c, sig_t, sig_g = ls.predict(Xc), ls.predict(Xt), ls.predict(grid.X)
            s_cal = f(Yc, yc_h) / sig_c
            s_te = f(Yt, yt_h) / sig_t
            s_g = f(grid.Y, yg_h) / sig_g
            sg_arr = np.broadcast_to(sig_g, (len(grid.X),))
            s_u = lambda i: f(grid.U, yg_h[i]) / sg_arr[i]
        q = conformal_quantile(s_cal, alpha)
        cov_te = s_te <= q
        # --- stratified coverage: estimated from a finite test set vs ground truth on the grid ---
        # (i) strata of the heteroscedasticity axis x_0 (equal-probability bins, ns in NS_LIST)
        # (ii) strata of the smallest predicted component (cut points from the calibration set; 10 bins)
        cov_g = (s_g <= q)                                    # (R, n)
        cg = cov_g.mean(0)                                    # per-x true conditional coverage
        stats_ = {}
        u_te, u_g = ndtr(Xt[:, 0]), ndtr(grid.X[:, 0])
        cut = np.quantile(yc_h.min(1), np.linspace(0, 1, 11)[1:-1])
        b_te, b_g = np.searchsorted(cut, yt_h.min(1)), np.searchsorted(cut, yg_h.min(1))
        strata = {f"x0_{ns}": (np.minimum((u_te * ns).astype(int), ns - 1), np.minimum((u_g * ns).astype(int), ns - 1), ns)
                  for ns in NS_LIST}
        strata["bd_10"] = (b_te, b_g, 10)
        for name, (bt, bg, ns) in strata.items():
            tr = np.array([cg[bg == j].mean() if (bg == j).any() else np.nan for j in range(ns)])
            stats_[f"true_{name}_min"] = np.nanmin(tr)
            stats_[f"true_{name}_dev"] = np.nanmean(np.abs(tr - (1 - alpha)))
            for nn in NTE_LIST:
                if nn > n_te:
                    continue
                c = np.array([cov_te[:nn][bt[:nn] == j].mean() if (bt[:nn] == j).any() else np.nan for j in range(ns)])
                stats_[f"est_{name}_min_{nn}"] = np.nanmin(c)
                if cells and name in ("x0_10", "bd_10"):
                    # per-cell estimated coverage and cell size (inputs of the plug-in version of Prop. 2)
                    for j in range(ns):
                        stats_[f"cell_{name}_{nn}_{j}"] = c[j]
                        stats_[f"cnt_{name}_{nn}_{j}"] = int((bt[:nn] == j).sum())
                    for j in range(ns):
                        stats_[f"truecell_{name}_{j}"] = tr[j]
                if halfsplit and name in ("x0_10", "bd_10"):
                    # select the apparent worst cell on one half, measure its coverage on the other; average both directions
                    h = nn // 2
                    est, tru = [], []
                    for A, B in ((slice(0, h), slice(h, nn)), (slice(h, nn), slice(0, h))):
                        ca = np.array([cov_te[A][bt[A] == j].mean() if (bt[A] == j).any() else np.nan for j in range(ns)])
                        js = int(np.nanargmin(ca))
                        mb = bt[B] == js
                        est.append(cov_te[B][mb].mean() if mb.any() else np.nan)
                        tru.append(tr[js])
                    stats_[f"est_{name}_hs_{nn}"] = np.nanmean(est)
                    stats_[f"true_{name}_hssel_{nn}"] = np.mean(tru)   # true coverage of the cells that were selected
        slab_cov = np.array([cg[strata["x0_10"][1] == j].mean() for j in range(10)])
        x_cov = cg
        # volume fraction on nv grid x's
        if volume:
            fr = np.array([(s_u(i) <= q).mean() for i in range(grid.nv)])
            lr = np.log10(np.maximum(fr, 0.5 / len(grid.U)) / np.maximum(grid.oracle_frac, 1e-300))[grid.vmask]
        else:
            fr = np.full(grid.nv, np.nan); lr = np.array([np.nan])
        rows.append(dict(method=m, seed=seed, q=q, marg_cov=cov_te.mean(),
                         true_marg_cov=cov_g.mean(),
                         x_dev=np.abs(x_cov - (1 - alpha)).mean(), **stats_,
                         log_vol_ratio=lr.mean(), vol_frac=fr[grid.vmask].mean(), vol_zero=(fr[grid.vmask] == 0).mean(), n_vmask=int(grid.vmask.sum()),
                         **{f"slab{j}": slab_cov[j] for j in range(10)}))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)  # json string of DGP kwargs + run kwargs
    ap.add_argument("--reps", type=int, default=10)
    ap.add_argument("--seed0", type=int, default=0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tag", default="")
    a = ap.parse_args()
    cfg = json.loads(a.config)
    run_kw = {k: cfg.pop(k) for k in list(cfg) if k in ("n_tr", "n_cal", "n_te", "alpha", "digits", "delta", "volume", "halfsplit", "const_mean", "cells")}
    methods = cfg.pop("methods", METHODS)
    dgp = DGP(**cfg)
    alpha = run_kw.get("alpha", 0.1)
    t0 = time.time()
    grid = Grid(dgp, alpha, digits=run_kw.get("digits"), delta=run_kw.get("delta", 1e-4))
    print(f"grid built {time.time()-t0:.1f}s oracle_cov={grid.oracle_cov:.3f}", flush=True)
    all_rows = []
    for i in range(a.reps):
        t0 = time.time()
        rows = run_rep(dgp, grid, a.seed0 + i, methods=methods, **run_kw)
        for rw in rows:
            rw.update(config=a.tag or json.dumps(cfg, sort_keys=True), git_rev=GIT_REV, K=dgp.K, kind=dgp.kind, hetero=dgp.hetero,
                      form=dgp.form, nl=dgp.nl, a=dgp.a, s=dgp.s, **{k: v for k, v in run_kw.items()})
        all_rows += rows
        print(f"rep {i} {time.time()-t0:.1f}s", flush=True)
    df = pd.DataFrame(all_rows)
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    df.to_csv(a.out, index=False)


if __name__ == "__main__":
    main()
