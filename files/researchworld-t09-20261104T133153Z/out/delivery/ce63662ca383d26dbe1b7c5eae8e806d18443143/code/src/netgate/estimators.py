"""GATE estimators. All take (g, z, y, design, ctx) and return dict(est=..., se=..., se_cl=...)."""
import numpy as np
from scipy.stats import binom



def feats(g, z):
    """Exposure features implied by an assignment vector (valid for any z, incl. all-1 / all-0)."""
    f1 = g.W @ z
    f2 = (g.W @ f1 - g.diag2 * z) / (1 - g.diag2)
    return {"z": z, "f1": f1, "cnt": g.A @ z, "f2": f2, "ld": np.log(g.deg)}


def _cols(spec, F, ctx):
    one = np.ones_like(F["z"])
    z, f1, f2, cnt, ld = F["z"], F["f1"], F["f2"], F["cnt"], F["ld"]
    ldc = ld - ctx["ld_mean"]
    cntn = cnt / ctx["mean_deg"]
    table = {
        "OLS_f": [one, z, f1],
        "OLS_zf": [one, z, f1, z * f1],
        "OLS_cnt": [one, z, cntn],
        "OLS_fd": [one, z, f1, ldc, z * ldc, f1 * ldc],
        "OLS_f2": [one, z, f1, f2],
        "OLS_quad": [one, z, f1, f1**2, z * f1],
        "OLS_cubic": [one, z, f1, f1**2, f1**3, z * f1],
        "OLS_big": [one, z, f1, f2, cntn, ldc, z * ldc, f1 * ldc, z * f1, f1**2, f2**2],
    }
    if spec in ("ORACLE", "ORACLE_D"):
        o = ctx["outcome"]
        extra = [ldc] if spec == "ORACLE_D" else []
        c = _oracle(o, one, z, f1, f2, cntn, ldc)
        return None if c is None else c + extra
    return table[spec]


def _oracle(o, one, z, f1, f2, cntn, ldc):
    """Columns of the correctly specified exposure model for each mechanism (None if none is finite)."""
    if o.mech == "shape":
        return [one, z, o._h(f1)]
    if o.mech == "step":
        return [one, z, (f1 >= o.kappa - 1e-12).astype(np.float64)]
    if o.mech == "count":
        return [one, z, cntn]
    if o.mech == "twohop":
        return [one, z, f1, f2]
    if o.mech == "hetero":
        return [one, z, z * ldc, f1]
    return None


def ols_gate(spec, g, z, y, ctx, rcond=1e-10):
    cols = _cols(spec, feats(g, z), ctx)
    if cols is None:
        return {"est": np.nan, "se": np.nan, "se_cl": np.nan, "se_hac1": np.nan, "se_hac2": np.nan}
    X = np.column_stack(cols)
    X1 = np.column_stack(_cols(spec, ctx["F1"], ctx))
    X0 = np.column_stack(_cols(spec, ctx["F0"], ctx))
    c = (X1 - X0).mean(0)
    XtX_inv = np.linalg.pinv(X.T @ X, rcond=rcond)
    beta = XtX_inv @ (X.T @ y)
    e = y - X @ beta
    est = float(c @ beta)
    # HC0 sandwich for c'beta (pretends independent units)
    Xe = X * e[:, None]
    meat = Xe.T @ Xe
    se = float(np.sqrt(max(c @ XtX_inv @ meat @ XtX_inv @ c, 0)))
    # cluster-robust sandwich over fixed analysis clusters (absorbs within-cluster dependence)
    lab = ctx["acl"]
    if lab is None:  # large factorial grids skip the cluster-dependent columns
        se_cl = np.nan
    else:
        S = np.zeros((lab.max() + 1, X.shape[1]))
        np.add.at(S, lab, Xe)
        meat_cl = S.T @ S
        se_cl = float(np.sqrt(max(c @ XtX_inv @ meat_cl @ XtX_inv @ c, 0)))
    out = {"est": est, "se": se, "se_cl": se_cl}
    if ctx.get("boot") and spec == "OLS_f":
        out.update(block_bootstrap(X, y, c, lab, ctx["boot"], ctx["boot_rng"]))
    for nm, K in (("se_hac1", ctx.get("K1")), ("se_hac2", ctx.get("K2"))):
        if K is None:
            out[nm] = np.nan
        else:  # Conley-type graph HAC: errors correlated within graph distance 1 (resp. 2); variance clipped at 0
            if K.dtype == np.float32:   # dense 2-hop kernel (Stanford3): keep the product in float32
                Xf = Xe.astype(np.float32)
                m = (Xf.T @ (K @ Xf)).astype(np.float64)
            else:
                m = Xe.T @ (K @ Xe)
            m = (m + m.T) / 2
            out[nm] = float(np.sqrt(max(c @ XtX_inv @ m @ XtX_inv @ c, 0)))
    return out


def block_bootstrap(X, y, c, lab, B, rng):
    """Block bootstrap of c'beta: resample the K blocks `lab` with replacement, refit OLS on the resampled units.
    Uses per-block sufficient statistics, so a draw costs a K-vector multinomial and a p x p solve. Returns the bootstrap SD
    and the 2.5% / 97.5% percentiles (percentile interval)."""
    K, p = int(lab.max()) + 1, X.shape[1]
    Sxx = np.zeros((K, p * p))
    for a in range(p):
        for b in range(p):
            Sxx[:, a * p + b] = np.bincount(lab, weights=X[:, a] * X[:, b], minlength=K)
    Sxy = np.column_stack([np.bincount(lab, weights=X[:, a] * y, minlength=K) for a in range(p)])
    m = rng.multinomial(K, np.full(K, 1.0 / K), size=B).astype(np.float64)
    A = (m @ Sxx).reshape(B, p, p)
    bvec = m @ Sxy
    beta = np.einsum("bij,bj->bi", np.linalg.pinv(A, rcond=1e-10), bvec)
    est = beta @ c
    return {"se_boot": float(est.std(ddof=1)), "boot_lo": float(np.percentile(est, 2.5)), "boot_hi": float(np.percentile(est, 97.5))}


def dm(g, z, y, ctx):
    est = y[z == 1].mean() - y[z == 0].mean()
    se = np.sqrt(y[z == 1].var(ddof=1) / (z == 1).sum() + y[z == 0].var(ddof=1) / (z == 0).sum())
    return {"est": float(est), "se": float(se), "se_cl": np.nan}


def gbm(g, z, y, ctx, seed=0):
    from sklearn.ensemble import HistGradientBoostingRegressor

    def X(F):
        return np.column_stack([F["z"], F["f1"], F["f2"], F["ld"], F["cnt"]])

    m = HistGradientBoostingRegressor(max_iter=150, max_depth=4, learning_rate=0.1, random_state=seed)
    m.fit(X(feats(g, z)), y)
    est = float((m.predict(X(ctx["F1"])) - m.predict(X(ctx["F0"]))).mean())
    return {"est": est, "se": np.nan, "se_cl": np.nan}


def _big_feats(F, ctx):
    """OLS_big columns without the constant (z, f1, f2, cnt, ld, z*ld, f1*ld, z*f1, f1^2, f2^2), as a matrix."""
    return np.column_stack(_cols("OLS_big", F, ctx)[1:])


def ridge_big(g, z, y, ctx):
    """Ridge on the 10 non-constant OLS_big features (standardised; penalty chosen by efficient leave-one-out CV, RidgeCV);
    GATE = mean prediction at the all-treated minus the all-control exposure features. The Han-Ugander (2023) style penalised richer model."""
    from sklearn.linear_model import RidgeCV
    from sklearn.preprocessing import StandardScaler
    X = _big_feats(feats(g, z), ctx)
    sc = StandardScaler().fit(X)
    m = RidgeCV(alphas=np.logspace(-3, 3, 13)).fit(sc.transform(X), y)
    est = float((m.predict(sc.transform(_big_feats(ctx["F1"], ctx))) - m.predict(sc.transform(_big_feats(ctx["F0"], ctx)))).mean())
    return {"est": est, "se": np.nan, "se_cl": np.nan, "lam": float(m.alpha_)}


def lasso_big(g, z, y, ctx, seed=0):
    """Lasso (LassoCV, 5-fold, standardised) selects columns of the OLS_big features; unpenalised OLS refit on the selected columns."""
    from sklearn.linear_model import LassoCV
    from sklearn.preprocessing import StandardScaler
    X = _big_feats(feats(g, z), ctx)
    sc = StandardScaler().fit(X)
    Xs = sc.transform(X)
    las = LassoCV(cv=5, alphas=30, max_iter=5000, random_state=seed).fit(Xs, y)
    sel = np.flatnonzero(las.coef_ != 0)
    if len(sel) == 0:
        return {"est": 0.0, "se": np.nan, "se_cl": np.nan, "nsel": 0}
    ols_X = np.column_stack([np.ones(len(y)), Xs[:, sel]])
    beta = np.linalg.lstsq(ols_X, y, rcond=None)[0]
    P1, P0 = sc.transform(_big_feats(ctx["F1"], ctx))[:, sel], sc.transform(_big_feats(ctx["F0"], ctx))[:, sel]
    est = float(((P1 - P0).mean(0)) @ beta[1:])
    return {"est": est, "se": np.nan, "se_cl": np.nan, "nsel": int(len(sel))}


def gbm_tuned(g, z, y, ctx, seed=0):
    """GBM with hyper-parameters chosen by 3-fold CV over depth {2,3,6} x learning rate {0.03,0.1,0.3} x iterations {100,300}.
    Tuned on the first replicate of each world and reused for the other replicates of that world."""
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.model_selection import GridSearchCV

    def X(F):
        return np.column_stack([F["z"], F["f1"], F["f2"], F["ld"], F["cnt"]])

    if ctx.get("gbm_params") is None:
        gs = GridSearchCV(HistGradientBoostingRegressor(random_state=seed),
                          {"max_depth": [2, 3, 6], "learning_rate": [0.03, 0.1, 0.3], "max_iter": [100, 300]},
                          cv=3, scoring="neg_mean_squared_error", n_jobs=1).fit(X(feats(g, z)), y)
        ctx["gbm_params"] = gs.best_params_
    m = HistGradientBoostingRegressor(random_state=seed, **ctx["gbm_params"]).fit(X(feats(g, z)), y)
    est = float((m.predict(X(ctx["F1"])) - m.predict(X(ctx["F0"]))).mean())
    return {"est": est, "se": np.nan, "se_cl": np.nan, "gbm_depth": ctx["gbm_params"]["max_depth"], "gbm_lr": ctx["gbm_params"]["learning_rate"],
            "gbm_iter": ctx["gbm_params"]["max_iter"]}


def hajek_kappa_cluster(g, z, y, design, ctx, kappa=0.75):
    """Hajek estimator of the fractional-exposure contrast under a cluster design (exact probabilities from design.kappa_exposure_prob):
    treated exposure = unit and >= kappa of its neighbours treated; control exposure = unit control and <= 1-kappa treated."""
    pi1, pi0 = ctx["kappa_prob"][kappa]
    f = g.W @ z
    e1 = (z == 1) & (f >= kappa - 1e-12)
    e0 = (z == 0) & (f <= 1 - kappa + 1e-12)
    if e1.sum() == 0 or e0.sum() == 0:
        return {"est": np.nan, "se": np.nan, "se_cl": np.nan, "n1": int(e1.sum()), "n0": int(e0.sum())}
    w1, w0 = 1 / pi1[e1], 1 / pi0[e0]
    est = (y[e1] * w1).sum() / w1.sum() - (y[e0] * w0).sum() / w0.sum()
    return {"est": float(est), "se": np.nan, "se_cl": np.nan, "n1": int(e1.sum()), "n0": int(e0.sum())}


def hajek_full(g, z, y, design, ctx):
    """Hajek (ratio) estimator of the contrast between 'self and all neighbours treated' and
    'self and all neighbours control' exposures, with exact design probabilities."""
    p1, p0 = design.full_exposure_prob(g)
    nb = g.A @ z
    full1 = (z == 1) & (nb == g.deg)
    full0 = (z == 0) & (nb == 0)
    if full1.sum() == 0 or full0.sum() == 0:
        return {"est": np.nan, "se": np.nan, "se_cl": np.nan, "n1": int(full1.sum()), "n0": int(full0.sum())}
    w1, w0 = 1 / p1[full1], 1 / p0[full0]
    est = (y[full1] * w1).sum() / w1.sum() - (y[full0] * w0).sum() / w0.sum()
    return {"est": float(est), "se": np.nan, "se_cl": np.nan, "n1": int(full1.sum()), "n0": int(full0.sum())}


def hajek_kappa(g, z, y, design, ctx, kappa=0.75):
    """Fractional-exposure Hajek under Bernoulli(p): treated exposure = self treated and >=kappa of
    neighbours treated; control exposure = self control and <=1-kappa treated. Probabilities exact."""
    p = design.p
    d = g.deg.astype(int)
    f = g.W @ z
    e1 = (z == 1) & (f >= kappa - 1e-12)
    e0 = (z == 0) & (f <= 1 - kappa + 1e-12)
    pi1 = p * binom.sf(np.ceil(kappa * d - 1e-12) - 1, d, p)
    pi0 = (1 - p) * binom.cdf(np.floor((1 - kappa) * d + 1e-12), d, p)
    if e1.sum() == 0 or e0.sum() == 0:
        return {"est": np.nan, "se": np.nan, "se_cl": np.nan}
    w1, w0 = 1 / pi1[e1], 1 / pi0[e0]
    est = (y[e1] * w1).sum() / w1.sum() - (y[e0] * w0).sum() / w0.sum()
    return {"est": float(est), "se": np.nan, "se_cl": np.nan}


OLS_SPECS = ["OLS_f", "OLS_zf", "OLS_cnt", "OLS_fd", "OLS_f2", "OLS_quad", "OLS_cubic", "OLS_big", "ORACLE", "ORACLE_D"]


def _dense_two_hop(K1):
    """Dense float32 0/1 matrix of 'within graph distance 2' (K1 = A + I) for graphs too dense for a sparse square (Stanford3):
    built in row chunks so the sparse product never holds more than a chunk. 4 bytes x n^2 (0.54 GB at n = 11,586)."""
    n = K1.shape[0]
    out = np.zeros((n, n), dtype=np.float32)
    for a in range(0, n, 1000):
        blk = (K1[a:a + 1000] @ K1).tocsr()
        blk.data[:] = 1.0
        out[a:a + 1000] = blk.toarray()
    return out


def make_ctx(g, outcome, acl, hac=True, dense_k2=False, boot=0, boot_rng=None, design=None, kappas=()):
    """hac=False skips the graph-HAC kernels; dense_k2=True builds the 2-hop kernel densely when the sparse square would be too large;
    boot>0 adds the block bootstrap of OLS_f; kappas lists fractional-exposure thresholds whose cluster-design probabilities are precomputed."""
    one = np.ones(g.n)
    zero = np.zeros(g.n)
    ld = np.log(g.deg)
    import scipy.sparse as sp
    K1 = (g.A + sp.identity(g.n)).tocsr() if hac else None
    K2 = None
    if hac and g.n * g.mean_deg**2 < 4e7:
        K2 = (K1 @ K1).tocsr()
        K2.data[:] = 1.0
    elif hac and dense_k2:
        K2 = _dense_two_hop(K1)
    ctx = {
        "K1": K1, "K2": K2,
        "F1": feats(g, one), "F0": feats(g, zero), "ld_mean": ld.mean(), "mean_deg": g.mean_deg,
        "outcome": outcome, "acl": acl, "boot": boot, "boot_rng": boot_rng,
    }
    if kappas:
        ctx["kappa_prob"] = {k: design.kappa_exposure_prob(g, k) for k in kappas}
    return ctx


def run_all(g, z, y, design, ctx, specs, use_gbm=False, use_hajek=True, seed=0, extra=()):
    """extra: any of 'RIDGE_big', 'LASSO_big', 'GBM_tuned', 'HajekKappaCl' (post-freeze additions; see experiments e14-e19)."""
    out = {"DM": dm(g, z, y, ctx)}
    for s in specs:
        out[s] = ols_gate(s, g, z, y, ctx)
    if use_gbm:
        out["GBM"] = gbm(g, z, y, ctx, seed)
    if "RIDGE_big" in extra:
        out["RIDGE_big"] = ridge_big(g, z, y, ctx)
    if "LASSO_big" in extra:
        out["LASSO_big"] = lasso_big(g, z, y, ctx, seed)
    if "GBM_tuned" in extra:
        out["GBM_tuned"] = gbm_tuned(g, z, y, ctx, seed)
    if "HajekKappaCl" in extra:
        for k in ctx["kappa_prob"]:
            out[f"HajekKappaCl{k}"] = hajek_kappa_cluster(g, z, y, design, ctx, k)
    if use_hajek:
        out["HajekFull"] = hajek_full(g, z, y, design, ctx)
        if design.kind == "bernoulli":
            out["HajekKappa"] = hajek_kappa(g, z, y, design, ctx)
    return out
