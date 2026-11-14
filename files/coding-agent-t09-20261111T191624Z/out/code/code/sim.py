"""Core simulation library: worlds (graph + potential-outcome model), designs,
regression-based GATE estimators, baselines and variance estimators.

Conventions
-----------
* A world fixes a graph and a deterministic potential-outcome function Y_i(z) (node-level
  heterogeneity parameters are drawn once per world).  The only randomness inside a
  world is the treatment assignment z (and optional additive noise).  Hence the
  "bias / SD / RMSE" of an estimator are *design-based* quantities.
* GATE: tau = mean_i [Y_i(1) - Y_i(0)] (noise-free potential outcomes).
"""
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import numpy as np
import scipy.sparse as sp
from scipy.special import expit

import graphs as G
from theory import lev_theory, proj_bias_bern

# ----------------------------------------------------------------------------------
# worlds
# ----------------------------------------------------------------------------------
_GRAPH_CACHE = {}


def build_graph(spec, seed):
    """spec: dict(name=..., **params). Returns CSR adjacency."""
    key = (tuple(sorted(spec.items())), seed)
    if key in _GRAPH_CACHE:
        return _GRAPH_CACHE[key]
    rng = np.random.default_rng(seed)
    nm = spec["name"]
    if nm == "stanford3":
        A = G.load_stanford3()
    elif nm == "egofb":
        A = G.load_egofb()
    elif nm == "er":
        A = G.er(spec["n"], spec["d"], rng)
    elif nm == "regular":
        A = G.regular(spec["n"], spec["d"], rng)
    elif nm == "sbm":
        A = G.sbm(spec["n"], spec["d"], spec["K"], spec["ratio"], rng)
    elif nm == "ba":
        A = G.ba(spec["n"], spec["m"], rng)
    elif nm == "ws":
        A = G.ws(spec["n"], spec["d"], spec["beta"], rng)
    else:
        raise ValueError(nm)
    if len(_GRAPH_CACHE) > 4:
        _GRAPH_CACHE.clear()
    _GRAPH_CACHE[key] = A
    return A


class World:
    def __init__(self, A, mech, seed):
        self.A = A.tocsr()
        n = self.n = A.shape[0]
        self.deg = np.asarray(A.sum(1)).ravel()
        self.W = sp.diags(1.0 / self.deg) @ self.A  # row-stochastic
        self.W = self.W.tocsr()
        self.ld = np.log(self.deg)
        self.ldz = (self.ld - self.ld.mean()) / self.ld.std()
        self.mech = dict(mech)
        rng = np.random.default_rng(seed)
        m = self.mech
        h = m.get("het", 0.5)
        xi, ze, eps = rng.standard_normal((3, n))
        # baseline (acts as design-based "noise"); optionally correlated with degree
        self.a = m.get("sig_a", 1.0) * (np.sqrt(1 - m.get("a_deg", 0.0) ** 2) * eps + m.get("a_deg", 0.0) * self.ldz)
        beta = m.get("beta", 1.0)
        gamma = m.get("gamma", 1.0)
        bi = beta * (1 + h * xi)
        gi = gamma * (1 + h * ze)
        gh = m.get("gam_het", "none")  # degree-dependent spillover heterogeneity (mean-normalised)
        if gh != "none":
            if gh == "inv":      # low-degree nodes are influenced more
                w = np.exp(-0.7 * self.ldz)
            elif gh == "pos":    # high-degree nodes are influenced more
                w = np.exp(0.7 * self.ldz)
            else:
                raise ValueError(gh)
            gi = gi * w / w.mean()
        self.bi, self.gi = bi, gi
        self.tau = float(np.mean(self.Y(np.ones((n, 1)), noise=False) - self.Y(np.zeros((n, 1)), noise=False)))

    # mechanisms ---------------------------------------------------------------------
    def _g(self, s):
        m = self.mech
        shape = m.get("shape", "pow")
        if shape == "pow":
            return s ** m.get("k", 1.0)
        if shape == "sigmoid":  # threshold response, normalised so g(0)=0, g(1)=1
            c, w = m.get("c", 0.5), m.get("w", 0.08)
            f = lambda x: expit((x - c) / w)
            return (f(s) - f(0.0)) / (f(1.0) - f(0.0))
        raise ValueError(shape)

    def Y(self, Z, noise=True, rng=None, sigma=0.0):
        m = self.mech
        kind = m.get("kind", "frac")
        a = self.a[:, None]
        if kind == "frac":
            S = self.W @ Z
            Y = a + self.bi[:, None] * Z + self.gi[:, None] * self._g(S)
        elif kind == "count":  # spill proportional to number of treated neighbours / mean degree
            C = (self.A @ Z) / self.deg.mean()
            Y = a + self.bi[:, None] * Z + self.gi[:, None] * C
        elif kind == "multihop":  # linear-in-means equilibrium: y = lam W y + a + beta z
            lam = m["lam"]
            base = a + self.bi[:, None] * Z
            Y = base.copy()
            term = base
            for _ in range(int(m.get("iters", 200))):
                term = lam * (self.W @ term)
                Y += term
                if np.abs(term).max() < 1e-9:
                    break
        elif kind == "mixed":  # 1-hop fraction effect plus 2-hop effect with weight gamma2
            S = self.W @ Z
            S2 = self.W @ S
            Y = a + self.bi[:, None] * Z + self.gi[:, None] * S + m["gamma2"] * S2
        else:
            raise ValueError(kind)
        if noise and sigma > 0:
            Y = Y + sigma * rng.standard_normal(Y.shape)
        return Y


def get_clusters(gspec, gseed, A, K):
    key = None
    if gspec["name"] in ("stanford3", "egofb"):
        key = gspec["name"]
    return G.cluster_graph(A, K, seed=1, key=key)


def perturb_graph(A, noise, rng):
    """Observed graph: drop fraction `drop` of true edges and add the same number of random
    false edges (keeps edge count); isolated nodes are attached to a random node."""
    n = A.shape[0]
    U = sp.triu(A, 1).tocoo()
    m = len(U.row)
    keep = rng.random(m) >= noise["drop"]
    r, c = U.row[keep], U.col[keep]
    nadd = m - keep.sum()
    ra, ca = rng.integers(0, n, nadd), rng.integers(0, n, nadd)
    B = sp.coo_matrix((np.ones(len(r) + nadd), (np.r_[r, ra], np.r_[c, ca])), shape=(n, n))
    B = ((B + B.T) > 0).astype(float).tolil()
    B.setdiag(0)
    B = B.tocsr()
    iso = np.where(np.asarray(B.sum(1)).ravel() == 0)[0]
    if len(iso):
        B = B.tolil()
        for i in iso:
            j = int(rng.integers(0, n))
            if j != i:
                B[i, j] = 1
                B[j, i] = 1
        B = B.tocsr()
    return B


# ----------------------------------------------------------------------------------
# designs
# ----------------------------------------------------------------------------------
def draw_Z(world, design, R, rng, clusters=None):
    n = world.n
    p = design.get("p", 0.5)
    if design["type"] == "bern":
        return (rng.random((n, R)) < p).astype(np.float64)
    if design["type"] == "cluster":
        K = clusters.max() + 1
        ZK = (rng.random((K, R)) < p).astype(np.float64)
        # an experiment needs both arms: redraw replications with all clusters in one arm
        bad = np.where((ZK.sum(0) == 0) | (ZK.sum(0) == K))[0]
        while len(bad):
            ZK[:, bad] = (rng.random((K, len(bad))) < p)
            bad = bad[(ZK[:, bad].sum(0) == 0) | (ZK[:, bad].sum(0) == K)]
        return ZK[clusters]
    raise ValueError(design)


# ----------------------------------------------------------------------------------
# estimators
# ----------------------------------------------------------------------------------
def _feats(model, z, s, c, s2, w):
    one = np.ones_like(z)
    if model == "ols_s":
        return np.column_stack([one, z, s])
    if model == "ols_cnt":
        return np.column_stack([one, z, c])
    if model == "ols_s_cnt":
        return np.column_stack([one, z, s, c])
    if model == "ols_s_int":
        return np.column_stack([one, z, s, z * s])
    if model == "ols_s_quad":
        return np.column_stack([one, z, s, s * s])
    if model == "ols_s_cub":
        return np.column_stack([one, z, s, s * s, s ** 3])
    if model == "ols_s2":
        return np.column_stack([one, z, s, s2])
    if model == "ols_s_deg":
        return np.column_stack([one, z, s, s * w.ldz, w.ldz])
    if model == "ols_s_deg_z":  # also lets the direct effect vary with degree
        return np.column_stack([one, z, s, s * w.ldz, w.ldz, z * w.ldz])
    if model == "gbm_in":
        return np.column_stack([z, s, s2, w.ldz])
    raise ValueError(model)


LINEAR_MODELS = ["ols_s", "ols_cnt", "ols_s_cnt", "ols_s_int", "ols_s_quad", "ols_s_cub", "ols_s2",
                 "ols_s_deg", "ols_s_deg_z"]


def _cf(world):
    n = world.n
    one, zero = np.ones(n), np.zeros(n)
    return (one, one, world.deg.astype(float), one), (zero, zero, zero, zero)


def fit_linear(model, world, z, s, c, s2, y, cf=None):
    """OLS fit; returns tau_hat, leverage L=dbar'(X'X/n)^{-1}dbar, beta, X, resid, dbar."""
    X = _feats(model, z, s, c, s2, world)
    (o1, o2, o3, o4), (q1, q2, q3, q4) = cf if cf is not None else _cf(world)
    F1 = _feats(model, o1, o2, o3, o4, world)
    F0 = _feats(model, q1, q2, q3, q4, world)
    dbar = (F1 - F0).mean(0)
    XtX = X.T @ X / world.n
    beta = np.linalg.solve(XtX, X.T @ y / world.n)
    tau = float(dbar @ beta)
    L = float(dbar @ np.linalg.solve(XtX, dbar))
    return tau, L, beta, X, y - X @ beta, dbar, XtX


def hc_var(X, e, dbar, XtX, n):
    Xe = X * e[:, None]
    meat = Xe.T @ Xe / n
    Ai = np.linalg.inv(XtX)
    V = Ai @ meat @ Ai / n
    return float(dbar @ V @ dbar) * n / (n - X.shape[1])


def cr_var(X, e, dbar, XtX, n, lab_idx):
    """cluster-robust sandwich; lab_idx: sparse indicator (n x K)."""
    U = lab_idx.T @ (X * e[:, None])  # K x k
    meat = U.T @ U / n
    Ai = np.linalg.inv(XtX)
    V = Ai @ meat @ Ai / n
    return float(dbar @ V @ dbar)


def hac_var(X, e, dbar, XtX, n, P):
    """graph-HAC: errors of units within 2 hops are allowed to be dependent. P binary pattern."""
    U = X * e[:, None]
    meat = U.T @ (P @ U) / n
    Ai = np.linalg.inv(XtX)
    V = Ai @ meat @ Ai / n
    return float(dbar @ V @ dbar)


def unit_exposure_var(world, design, clusters):
    """q_i = Var(s_i)/(p(1-p)): variance of unit i's neighbour-treated fraction under the design."""
    if design["type"] == "bern":
        return 1.0 / world.deg
    n = world.n
    K = clusters.max() + 1
    B = sp.csr_matrix((np.ones(n), (np.arange(n), clusters)), shape=(n, K))
    Mf = sp.diags(1.0 / world.deg) @ (world.A @ B).tocsr()
    return np.asarray(Mf.multiply(Mf).sum(1)).ravel()


def wls_est(world, z, s, y, w):
    """weighted LS of y on (1,z,s); returns beta_z+beta_s"""
    X = np.column_stack([np.ones_like(z), z, s])
    Xw = X * w[:, None]
    beta = np.linalg.solve(X.T @ Xw, Xw.T @ y)
    return float(beta[1] + beta[2])


def strat_est(world, z, s, y, bins, nb):
    """separate OLS (1,z,s) within degree strata, strata-size-weighted average of beta_z+beta_s"""
    tot = 0.0
    for b in range(nb):
        m = bins == b
        X = np.column_stack([np.ones(m.sum()), z[m], s[m]])
        beta = np.linalg.lstsq(X, y[m], rcond=None)[0]
        tot += m.mean() * (beta[1] + beta[2])
    return float(tot)


def hajek_prob(world, design, clusters):
    """Probabilities of the 'full-neighbourhood treated / control' exposure for each unit."""
    p = design.get("p", 0.5)
    if design["type"] == "bern":
        k = world.deg + 1
    else:
        K = clusters.max() + 1
        B = sp.csr_matrix((np.ones(world.n), (np.arange(world.n), clusters)), shape=(world.n, K))
        M = ((world.A + sp.eye(world.n)) @ B)
        M.data = (M.data > 0).astype(float)
        k = np.asarray(M.sum(1)).ravel()
    return p ** k, (1 - p) ** k


def hajek_est(world, z, y, c, pi1, pi0):
    e1 = (c == world.deg) & (z == 1)
    e0 = (c == 0) & (z == 0)
    if e1.sum() == 0 or e0.sum() == 0:
        return np.nan
    w1, w0 = 1 / pi1[e1], 1 / pi0[e0]
    return float((w1 * y[e1]).sum() / w1.sum() - (w0 * y[e0]).sum() / w0.sum())


def ols_cf_gbm(world, z, s, s2, y, seed):
    from sklearn.ensemble import HistGradientBoostingRegressor
    X = _feats("gbm_in", z, s, None, s2, world)
    mdl = HistGradientBoostingRegressor(max_iter=150, learning_rate=0.1, max_leaf_nodes=15,
                                        random_state=seed).fit(X, y)
    n = world.n
    X1 = np.column_stack([np.ones(n), np.ones(n), np.ones(n), world.ldz])
    X0 = np.column_stack([np.zeros(n), np.zeros(n), np.zeros(n), world.ldz])
    return float((mdl.predict(X1) - mdl.predict(X0)).mean())


# ----------------------------------------------------------------------------------
# one configuration: R replications of assignment -> outcomes -> all estimators
# ----------------------------------------------------------------------------------
def run_config(cfg):
    """cfg keys: graph(spec), gseed, mech, wseed, design, R, sigma, models, extras(list of
    'dm','hajek','gbm'), infer(list of 'hc','cr','hac'), seed."""
    A = build_graph(cfg["graph"], cfg["gseed"])
    world = World(A, cfg["mech"], cfg["wseed"])
    rng = np.random.default_rng(cfg["seed"])
    design = cfg["design"]
    n = world.n
    clusters = None
    if design["type"] == "cluster":
        clusters = get_clusters(cfg["graph"], cfg["gseed"], A, design.get("K", 100))
    R = cfg["R"]
    sigma = cfg.get("sigma", 0.0)
    models = cfg.get("models", ["ols_s"])
    extras = cfg.get("extras", [])
    infer = cfg.get("infer", [])
    Z = draw_Z(world, design, R, rng, clusters)
    Y = world.Y(Z, noise=True, rng=rng, sigma=sigma)
    fw = world  # world providing the (possibly mis-measured) graph features
    if cfg.get("obs_noise"):
        fw = World(perturb_graph(A, cfg["obs_noise"], np.random.default_rng(cfg["seed"] + 99)), cfg["mech"], cfg["wseed"])
    S = fw.W @ Z
    C = fw.A @ Z
    S2 = fw.W @ S
    cf = _cf(fw)
    world_true, world = world, fw
    if "hajek" in extras:
        pi1, pi0 = hajek_prob(world, design, clusters)
    if "wls_s" in extras:
        wls_w = 1.0 / unit_exposure_var(world, design, clusters)
        wls_w = wls_w / wls_w.mean()
    if "strat_s" in extras:
        strata = np.minimum((np.argsort(np.argsort(world.deg, kind="stable"), kind="stable") * 5) // world.n, 4)
    if infer:
        K = clusters.max() + 1 if clusters is not None else None
    # inference clusters: Louvain communities (always computed if cr requested)
    if "cr" in infer:
        icl = clusters if clusters is not None else get_clusters(cfg["graph"], cfg["gseed"], A, 100)
        lab = sp.csr_matrix((np.ones(n), (np.arange(n), icl)), shape=(n, icl.max() + 1))
    if "hac" in infer:
        P = (world.A + sp.eye(n)).tocsr()
        P = (P @ P)
        P.data[:] = 1.0
        hac_density = P.nnz / n ** 2
    est = {}
    se = {}
    lev = {}
    def add(name, r, v):
        est.setdefault(name, np.full(R, np.nan))[r] = v
    for r in range(R):
        z, s, c, s2, y = Z[:, r], S[:, r], C[:, r], S2[:, r], Y[:, r]
        if "dm" in extras:
            add("dm", r, y[z == 1].mean() - y[z == 0].mean())
        if "hajek" in extras:
            add("hajek", r, hajek_est(world, z, y, c, pi1, pi0))
        for mdl in models:
            try:
                tau, L, beta, X, e, dbar, XtX = fit_linear(mdl, world, z, s, c, s2, y, cf)
            except np.linalg.LinAlgError:
                add(mdl, r, np.nan)
                continue
            add(mdl, r, tau)
            lev.setdefault(mdl, []).append(L)
            for kind in infer:
                if mdl not in cfg.get("infer_models", ["ols_s"]):
                    continue
                if kind == "hc":
                    v = hc_var(X, e, dbar, XtX, n)
                elif kind == "cr":
                    v = cr_var(X, e, dbar, XtX, n, lab)
                elif kind == "hac":
                    v = hac_var(X, e, dbar, XtX, n, P)
                se.setdefault((mdl, kind), np.full(R, np.nan))[r] = np.sqrt(max(v, 0.0))
        if "wls_s" in extras:
            add("wls_s", r, wls_est(world, z, s, y, wls_w))
        if "strat_s" in extras:
            add("strat_s", r, strat_est(world, z, s, y, strata, 5))
        if "gbm" in extras:
            add("gbm", r, ols_cf_gbm(world, z, s, s2, y, cfg["seed"] + r))
    world = world_true
    tau = world.tau
    rows = []
    for name, v in est.items():
        ok = ~np.isnan(v)
        row = dict(estimator=name, truth=tau, n=n, R=R, fail=1 - ok.mean())
        if ok.sum() >= 2:
            err = v[ok] - tau
            row.update(mean_est=v[ok].mean(), bias=err.mean(), sd=err.std(ddof=1),
                       rmse=np.sqrt((err ** 2).mean()),
                       rmse_se=(err ** 2).std(ddof=1) / (2 * np.sqrt((err ** 2).mean()) * np.sqrt(ok.sum()) + 1e-300),
                       med_abs=np.median(np.abs(err)), q90_abs=np.quantile(np.abs(err), 0.9))
        if name in lev:
            row["lev"] = float(np.mean(lev[name]))
        for (m2, kind), sev in se.items():
            if m2 == name:
                lo, hi = v - 1.96 * sev, v + 1.96 * sev
                row[f"cov_{kind}"] = float(np.mean((lo <= tau) & (tau <= hi)))
                row[f"se_{kind}"] = float(np.nanmean(sev))
                row[f"se_ratio_{kind}"] = float(np.nanmean(sev) / (v.std(ddof=1) + 1e-300))
        rows.append(row)
    meta = dict(cfg_id=cfg.get("id"), world_tau=tau, n=n, mean_deg=float(world.deg.mean()))
    if design["type"] == "cluster":
        meta["n_clusters"] = int(clusters.max() + 1)
    if "hac" in infer:
        meta["hac_density"] = hac_density
    # distribution of exposures under design (support diagnostic)
    try:
        meta["lev_theory"] = float(lev_theory(world, design, clusters))
    except Exception:
        pass
    if design["type"] == "bern" and cfg["mech"].get("kind", "frac") == "frac" and cfg["mech"].get("gam_het", "none") == "none":
        meta["proj_bias_theory"] = float(proj_bias_bern(world, design.get("p", 0.5), world._g) * cfg["mech"].get("gamma", 1.0))
    if clusters is not None:
        Ac = A.tocoo()
        meta["cut_frac"] = float((clusters[Ac.row] != clusters[Ac.col]).mean())
    meta["frac_s_ge_90"] = float((S >= 0.9).mean())
    meta["frac_s_le_10"] = float((S <= 0.1).mean())
    meta["sd_s"] = float(S.std())
    for r_ in rows:
        r_.update(meta)
    return rows
