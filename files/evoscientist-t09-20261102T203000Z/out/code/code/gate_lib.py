"""Core library: graphs, interference mechanisms, designs, GATE estimators, theory predictions.

All randomness is seeded explicitly; see README.md for the seeding scheme.
"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import gzip
import pickle
import numpy as np
import scipy.sparse as sp
import scipy.io as sio
import networkx as nx

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
CACHE = os.path.join(ROOT, "cache")
os.makedirs(CACHE, exist_ok=True)


# ----------------------------------------------------------------------------- graphs
def _sym_clean(A):
    A = sp.csr_matrix(A, dtype=float)
    A = A + A.T
    A.setdiag(0)
    A.eliminate_zeros()
    A.data[:] = 1.0
    return A.tocsr()


def _lcc(A):
    nc, lab = sp.csgraph.connected_components(A, directed=False)
    big = np.argmax(np.bincount(lab))
    keep = np.where(lab == big)[0]
    return A[keep][:, keep].tocsr()


def sbm_adjacency(n, K, d, ratio, seed):
    """Planted-partition SBM with K equal blocks, expected degree d, p_in/p_out=ratio (K=1: Erdos-Renyi)."""
    rng = np.random.default_rng(seed)
    lab = np.repeat(np.arange(K), int(np.ceil(n / K)))[:n]
    nb = n / K
    p_out = d / (nb * ratio + (n - nb)) if K > 1 else d / (n - 1)
    p_in = ratio * p_out if K > 1 else p_out
    rows, cols = [], []
    chunk = 500
    for a in range(0, n, chunk):
        b = min(n, a + chunk)
        same = lab[a:b, None] == lab[None, :]
        P = np.where(same, p_in, p_out)
        U = rng.random((b - a, n)) < P
        # keep strict upper triangle
        ii = np.arange(a, b)[:, None]
        jj = np.arange(n)[None, :]
        U &= jj > ii
        r, c = np.nonzero(U)
        rows.append(r + a)
        cols.append(c)
    r = np.concatenate(rows)
    c = np.concatenate(cols)
    A = sp.csr_matrix((np.ones(len(r)), (r, c)), shape=(n, n))
    return _sym_clean(A)


def make_adjacency(kind, n=None, d=20, gseed=0, **kw):
    if kind == "er":
        A = sbm_adjacency(n, 1, d, 1.0, gseed)
    elif kind == "sbm":
        A = sbm_adjacency(n, kw.get("K", 20), d, kw.get("ratio", 10.0), gseed)
    elif kind == "ba":
        G = nx.barabasi_albert_graph(n, max(1, int(round(d / 2))), seed=gseed)
        A = _sym_clean(nx.to_scipy_sparse_array(G))
    elif kind == "ws":
        G = nx.watts_strogatz_graph(n, int(d), kw.get("beta", 0.1), seed=gseed)
        A = _sym_clean(nx.to_scipy_sparse_array(G))
    elif kind == "rgg":
        r = np.sqrt(d / (n * np.pi))
        G = nx.random_geometric_graph(n, r, seed=gseed)
        A = _sym_clean(nx.to_scipy_sparse_array(G))
    elif kind == "stanford3":
        A = _sym_clean(sio.mmread(os.path.join(DATA, "socfb-Stanford3.mtx")))
    elif kind == "egofb":
        e = np.loadtxt(os.path.join(DATA, "facebook_combined.txt.gz"), dtype=int)
        N = e.max() + 1
        A = _sym_clean(sp.csr_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(N, N)))
    else:
        raise ValueError(kind)
    return _lcc(A)


class Net:
    """Graph + cached derived quantities."""

    def __init__(self, A, name=""):
        self.name = name
        self.A = A.tocsr()
        self.n = A.shape[0]
        self.deg = np.asarray(A.sum(1)).ravel()
        self.invdeg = np.where(self.deg > 0, 1.0 / np.maximum(self.deg, 1), 0.0)
        self.P = sp.diags(self.invdeg) @ self.A  # row-normalised
        self.dbar = self.deg.mean()
        ld = np.log1p(self.deg)
        self.ld = (ld - ld.mean()) / (ld.std() + 1e-12)
        self._cl = {}

    def exposures(self, z):
        s = self.A @ z
        f = s * self.invdeg
        f2 = self.P @ f
        return s, f, f2

    def clusters(self, res, seed=0):
        key = (round(float(res), 6), seed)
        if key not in self._cl:
            cfile = None
            if self.name in ("stanford3", "egofb"):
                cfile = os.path.join(CACHE, f"louvain_{self.name}_{res}_{seed}.npy")
                if os.path.exists(cfile):
                    self._cl[key] = np.load(cfile)
                    return self._cl[key]
            G = nx.from_scipy_sparse_array(self.A)
            comms = nx.community.louvain_communities(G, resolution=res, seed=seed)
            lab = np.empty(self.n, dtype=int)
            for k, c in enumerate(comms):
                lab[list(c)] = k
            self._cl[key] = lab
            if cfile:
                np.save(cfile, lab)
        return self._cl[key]

    def intra_fraction(self, lab):
        r, c = self.A.nonzero()
        return float(np.mean(lab[r] == lab[c]))


_NET_CACHE = {}


def get_net(spec):
    """spec: dict(kind, n, d, gseed, ...extra). Cached per process."""
    key = tuple(sorted(spec.items()))
    if key not in _NET_CACHE:
        if len(_NET_CACHE) > 6:
            _NET_CACHE.clear()
        kw = {k: v for k, v in spec.items() if k not in ("kind", "n", "d", "gseed")}
        A = make_adjacency(spec["kind"], spec.get("n"), spec.get("d", 20), spec.get("gseed", 0), **kw)
        _NET_CACHE[key] = Net(A, spec["kind"])
    return _NET_CACHE[key]


def perturb_graph(net, q, seed):
    """Observed graph: drop each edge w.p. q, then add the same expected number of random non-edges."""
    rng = np.random.default_rng(seed)
    A = sp.triu(net.A, 1).tocoo()
    m = A.nnz
    keep = rng.random(m) >= q
    r, c = A.row[keep], A.col[keep]
    n_add = int(round(q * m))
    ra = rng.integers(0, net.n, n_add)
    ca = rng.integers(0, net.n, n_add)
    r = np.concatenate([r, ra])
    c = np.concatenate([c, ca])
    B = sp.csr_matrix((np.ones(len(r)), (r, c)), shape=(net.n, net.n))
    return Net(_sym_clean(B), net.name + "_obs")


# ----------------------------------------------------------------------------- mechanisms
def _logistic(x):
    return 1.0 / (1.0 + np.exp(-x))


def h_thresh(f, theta=0.5, w=0.1):
    lo, hi = _logistic((0 - theta) / w), _logistic((1 - theta) / w)
    return (_logistic((f - theta) / w) - lo) / (hi - lo)


MECHS = ["lin-frac", "lin-sum", "pow", "thresh", "lin-2hop", "het-frac"]


def mech_h(mech, kappa, s, f, f2, net, w2=0.5, het=0.5):
    """Return (h_i, gamma_scale_i): indirect effect = gam * gamma_scale_i * h_i. h(all-treated mean)=1 on average."""
    gs = 1.0
    if mech == "lin-frac":
        h = f
    elif mech == "lin-sum":
        h = s / net.dbar  # mean over nodes of h(1) = 1
    elif mech == "pow":
        h = np.power(f, kappa)
    elif mech == "thresh":
        h = h_thresh(f)
    elif mech == "lin-2hop":
        h = (1 - w2) * f + w2 * f2
    elif mech == "het-frac":
        h = f
        gs = 1.0 + het * net.ld  # mean 1 (ld standardised)
    else:
        raise ValueError(mech)
    return h, gs


def mech_oracle_cols(mech, kappa, z, s, f, f2, ld, dbar):
    if mech == "lin-frac":
        return [f]
    if mech == "lin-sum":
        return [s / dbar]
    if mech == "pow":
        return [np.power(f, kappa)]
    if mech == "thresh":
        return [h_thresh(f)]
    if mech == "lin-2hop":
        return [f, f2]  # oracle spans (1-w2) f + w2 f2 for any w2
    if mech == "het-frac":
        return [f, f * ld]
    raise ValueError(mech)


class Outcome:
    """mu_i(Z) = a_i + tau z_i + gam * gs_i * h_i(Z); a_i = 0.5 ld_i + comm_sd * u_{c(i)} (fixed given graph seed)."""

    def __init__(self, net, mech, kappa=2.0, tau=1.0, gam=1.0, sigma=1.0, comm_sd=0.5, seed=0, w2=0.5, het=0.5):
        self.net, self.mech, self.kappa = net, mech, kappa
        self.w2, self.het = w2, het
        self.tau, self.gam, self.sigma = tau, gam, sigma
        lab = net.clusters(1.0, 0)
        u = np.random.default_rng([seed, 991]).standard_normal(lab.max() + 1)
        self.a = 0.5 * net.ld + comm_sd * u[lab]
        n = net.n
        self.mu1 = self.mu(np.ones(n))
        self.mu0 = self.mu(np.zeros(n))
        self.gate = float(np.mean(self.mu1 - self.mu0))

    def mu(self, z):
        s, f, f2 = self.net.exposures(z)
        h, gs = mech_h(self.mech, self.kappa, s, f, f2, self.net, self.w2, self.het)
        return self.a + self.tau * z + self.gam * gs * h


# ----------------------------------------------------------------------------- designs
class Design:
    def __init__(self, net, kind="bern", p=0.5, res=1.0):
        self.net, self.kind, self.p, self.res = net, kind, p, res
        if kind in ("cluster", "dose"):
            self.lab = net.clusters(res, 0)
            self.K = self.lab.max() + 1
            self.k_nbhd = None
        else:
            self.lab = None

    def draw(self, rng):
        if self.kind == "bern":
            return (rng.random(self.net.n) < self.p).astype(float)
        if self.kind == "dose":  # cluster-level treatment probability q_c ~ U(0,1), then Bernoulli(q_c) within cluster
            q = rng.random(self.K)
            return (rng.random(self.net.n) < q[self.lab]).astype(float)
        t = rng.random(self.K) < self.p
        return t[self.lab].astype(float)

    def n_independent_units_in_closed_nbhd(self):
        """k_i: number of independent randomisation units covering closed neighbourhood of i."""
        net = self.net
        if self.kind == "bern":
            return net.deg + 1
        lab = self.lab
        A = net.A.tocoo()
        pairs = np.concatenate([np.stack([A.row, lab[A.col]], 1), np.stack([np.arange(net.n), lab], 1)])
        pairs = np.unique(pairs, axis=0)
        return np.bincount(pairs[:, 0], minlength=net.n)


# ----------------------------------------------------------------------------- estimators
OLS_SETS = ["OLS-f", "OLS-s", "OLS-sx", "OLS-fx", "OLS-fs", "OLS-quad", "OLS-2hop", "OLS-full", "Oracle"]
OTHER = ["DM", "GBM", "Hajek-full", "Hajek-eps"]
ALL_EST = ["DM"] + OLS_SETS + ["GBM", "Hajek-full", "Hajek-eps"]


def design_matrix(name, z, s, f, f2, ld, dbar, mech=None, kappa=2.0):
    one = np.ones_like(z)
    if name == "OLS-f":
        cols = [one, z, f]
    elif name == "OLS-s":
        cols = [one, z, s]
    elif name == "OLS-sx":
        cols = [one, z, s, ld]
    elif name == "OLS-fx":
        cols = [one, z, f, ld]
    elif name == "OLS-fs":
        cols = [one, z, f, s / dbar, ld]
    elif name == "OLS-quad":
        cols = [one, z, f, f * f]
    elif name == "OLS-2hop":
        cols = [one, z, f, f2]
    elif name == "OLS-full":
        cols = [one, z, f, s / dbar, f * f, f2, z * f, ld, f * ld]
    elif name == "Oracle":
        cols = [one, z, ld] + mech_oracle_cols(mech, kappa, z, s, f, f2, ld, dbar)
    else:
        raise ValueError(name)
    return np.stack(cols, 1)


def ols_gate(X, y, X1, X0, cl=None):
    """OLS fit; GATE = mean_i (x_i(1)-x_i(0))' beta. Returns est, HC1 delta-method se, cluster-robust se."""
    n, k = X.shape
    d = (X1 - X0).mean(0)
    sc = np.sqrt((X ** 2).mean(0))
    sc[sc == 0] = 1.0
    Xs = X / sc
    ds = d / sc
    Gi = np.linalg.pinv(Xs.T @ Xs, hermitian=True, rcond=1e-10)
    b = Gi @ (Xs.T @ y)
    est = float(ds @ b)
    e = y - Xs @ b
    a = (Xs @ (Gi @ ds)) * e
    se_hc = float(np.sqrt(np.sum(a * a) * n / max(n - k, 1)))
    se_cl = np.nan
    if cl is not None:
        K = cl.max() + 1
        sa = np.bincount(cl, weights=a, minlength=K)
        se_cl = float(np.sqrt(np.sum(sa * sa) * K / max(K - 1, 1) * (n - 1) / max(n - k, 1)))
    return est, se_hc, se_cl


def dm_gate(z, y):
    t, c = y[z == 1], y[z == 0]
    est = t.mean() - c.mean()
    se = np.sqrt(t.var(ddof=1) / len(t) + c.var(ddof=1) / len(c))
    return float(est), float(se)


def hajek(y, ind, pi):
    m = ind & (pi > 0)
    if m.sum() == 0:
        return np.nan
    w = 1.0 / pi[m]
    return float(np.sum(w * y[m]) / np.sum(w))


class Context:
    """Everything fixed for one scenario (graph x outcome model x design x estimator set)."""

    def __init__(self, sc):
        self.sc = sc
        self.net = get_net(sc["graph"])
        net = self.net
        o = sc.get("outcome", {})
        self.out = Outcome(net, sc["mech"], kappa=o.get("kappa", 2.0), tau=o.get("tau", 1.0),
                           gam=o.get("gam", 1.0), sigma=o.get("sigma", 1.0), comm_sd=o.get("comm_sd", 0.5),
                           seed=sc["graph"].get("gseed", 0), w2=o.get("w2", 0.5), het=o.get("het", 0.5))
        dz = sc.get("design", {})
        self.des = Design(net, dz.get("kind", "bern"), dz.get("p", 0.5), dz.get("res", 1.0))
        self.obs = net
        q = sc.get("obs_noise", 0.0)
        if q > 0:
            self.obs = perturb_graph(net, q, seed=sc["graph"].get("gseed", 0) + 7)
        self.est_names = sc.get("estimators", ["DM", "OLS-f"])
        self.cl_eval = net.clusters(1.0, 0)
        n = net.n
        ones, zeros = np.ones(n), np.zeros(n)
        e1, e0 = self.obs.exposures(ones), self.obs.exposures(zeros)
        kap = self.out.kappa
        self.X1, self.X0 = {}, {}
        for nm in self.est_names:
            if nm.startswith("OLS") or nm == "Oracle":
                self.X1[nm] = design_matrix(nm, ones, *e1, self.obs.ld, self.obs.dbar, sc["mech"], kap)
                self.X0[nm] = design_matrix(nm, zeros, *e0, self.obs.ld, self.obs.dbar, sc["mech"], kap)
        if "GBM" in self.est_names:
            # column order [z, s, f, f2, ld] must match Xg in one_rep
            self.G1 = np.stack([ones, e1[0], e1[1], e1[2], self.obs.ld], 1)
            self.G0 = np.stack([zeros, e0[0], e0[1], e0[2], self.obs.ld], 1)
        self.eps_exp = sc.get("eps", 0.25)
        self.pi_full = None
        if "Hajek-full" in self.est_names:
            k = self.des.n_independent_units_in_closed_nbhd()
            p = self.des.p
            self.pi1_full = p ** k.astype(float)
            self.pi0_full = (1 - p) ** k.astype(float)
        if "Hajek-eps" in self.est_names:
            rng = np.random.default_rng([sc.get("seed", 0), 4242])
            R = 400
            c1 = np.zeros(n)
            c0 = np.zeros(n)
            for _ in range(R):
                z = self.des.draw(rng)
                _, f, _ = self.obs.exposures(z)
                c1 += (z == 1) & (f >= 1 - self.eps_exp)
                c0 += (z == 0) & (f <= self.eps_exp)
            self.pi1_eps, self.pi0_eps = c1 / R, c0 / R

    def one_rep(self, rng):
        net, out = self.net, self.out
        z = self.des.draw(rng)
        y = out.mu(z) + out.sigma * rng.standard_normal(net.n)
        s, f, f2 = self.obs.exposures(z)
        res = {}
        for nm in self.est_names:
            if nm == "DM":
                res[nm] = dm_gate(z, y) + (np.nan,)
            elif nm.startswith("OLS") or nm == "Oracle":
                X = design_matrix(nm, z, s, f, f2, self.obs.ld, self.obs.dbar, self.sc["mech"], out.kappa)
                res[nm] = ols_gate(X, y, self.X1[nm], self.X0[nm], self.cl_eval)
            elif nm == "GBM":
                from sklearn.ensemble import HistGradientBoostingRegressor
                Xg = np.stack([z, s, f, f2, self.obs.ld], 1)
                # column order must match G1: [z, s, f, f2, ld]
                m = HistGradientBoostingRegressor(max_iter=100, learning_rate=0.1, max_depth=3,
                                                  random_state=int(rng.integers(1 << 30)))
                m.fit(Xg, y)
                res[nm] = (float(np.mean(m.predict(self.G1) - m.predict(self.G0))), np.nan, np.nan)
            elif nm == "Hajek-full":
                e1 = ((z == 1) & (f >= 1.0 - 1e-12))
                e0 = ((z == 0) & (f <= 1e-12))
                if e1.sum() > 0 and e0.sum() > 0:
                    est = hajek(y, e1, self.pi1_full) - hajek(y, e0, self.pi0_full)
                else:
                    est = np.nan
                res[nm] = (est, np.nan, np.nan)
            elif nm == "Hajek-eps":
                e1 = ((z == 1) & (f >= 1 - self.eps_exp))
                e0 = ((z == 0) & (f <= self.eps_exp))
                est = np.nan
                if e1.sum() > 0 and e0.sum() > 0:
                    est = hajek(y, e1, self.pi1_eps) - hajek(y, e0, self.pi0_eps)
                res[nm] = (est, np.nan, np.nan)
        return res



# ----------------------------------------------------------------------------- theory predictions
def predict_ols(ctx, est_name, R=400, seed=0):
    """Population-OLS limit under the design: beta* = M^{-1} b, M=E[X'X]/n, b=E[X'mu(Z)]/n.
    Returns predicted bias d'beta* - GATE (extrapolation bias) and noise-only variance sigma^2 d'M^{-1}d / n."""
    rng = np.random.default_rng([seed, 777])
    net, out = ctx.net, ctx.out
    n = net.n
    X1, X0 = ctx.X1[est_name], ctx.X0[est_name]
    k = X1.shape[1]
    M = np.zeros((k, k))
    b = np.zeros(k)
    m2 = 0.0
    for _ in range(R):
        z = ctx.des.draw(rng)
        s, f, f2 = ctx.obs.exposures(z)
        X = design_matrix(est_name, z, s, f, f2, ctx.obs.ld, ctx.obs.dbar, ctx.sc["mech"], out.kappa)
        mu = out.mu(z)
        M += X.T @ X / n
        b += X.T @ mu / n
        m2 += mu @ mu / n
    M /= R
    b /= R
    m2 /= R
    Mi = np.linalg.pinv(M, hermitian=True, rcond=1e-10)
    beta = Mi @ b
    d = (X1 - X0).mean(0)
    bias = float(d @ beta - out.gate)
    dMd = float(d @ Mi @ d)
    var = float(out.sigma ** 2 * dMd / n)
    r2 = max(float(m2 - 2 * beta @ b + beta @ M @ beta), 0.0)  # mean squared projection residual of mu
    var_tot = float((out.sigma ** 2 + r2) * dMd / n)
    return bias, var, var_tot, dMd


def predict_ols2(ctx, est_name, R=300, R2=300, seed=0):
    """First-order prediction of bias and variance of the OLS-type GATE estimator under the design.

    bias  = delta' beta* - GATE                       (extrapolation bias; beta* = population OLS limit)
    var_noise  = sigma^2 delta' M^-1 delta / n         (observation noise)
    var_design = delta' M^-1 Omega M^-1 delta          (randomisation variance of the unexplained signal:
                 Omega = Cov_Z( (1/n) sum_i phi_i(Z) r_i(Z) ), r_i = mu_i(Z) - phi_i(Z)' beta*; includes
                 network dependence between units and fixed heterogeneity not in the model)
    """
    rng = np.random.default_rng([seed, 778])
    net, out = ctx.net, ctx.out
    n = net.n
    X1, X0 = ctx.X1[est_name], ctx.X0[est_name]
    k = X1.shape[1]
    M = np.zeros((k, k))
    b = np.zeros(k)
    for _ in range(R):
        z = ctx.des.draw(rng)
        s, f, f2 = ctx.obs.exposures(z)
        X = design_matrix(est_name, z, s, f, f2, ctx.obs.ld, ctx.obs.dbar, ctx.sc["mech"], out.kappa)
        M += X.T @ X / n
        b += X.T @ out.mu(z) / n
    M /= R
    b /= R
    Mi = np.linalg.pinv(M, hermitian=True, rcond=1e-10)
    beta = Mi @ b
    d = (X1 - X0).mean(0)
    bias = float(d @ beta - out.gate)
    dMd = float(d @ Mi @ d)
    G = np.zeros((R2, k))
    for t in range(R2):
        z = ctx.des.draw(rng)
        s, f, f2 = ctx.obs.exposures(z)
        X = design_matrix(est_name, z, s, f, f2, ctx.obs.ld, ctx.obs.dbar, ctx.sc["mech"], out.kappa)
        G[t] = X.T @ (out.mu(z) - X @ beta) / n
    Om = np.cov(G.T).reshape(k, k)
    w = Mi @ d
    return dict(bias=bias, var_noise=float(out.sigma ** 2 * dMd / n), var_design=float(w @ Om @ w), dMd=dMd,
                gbar_norm=float(np.linalg.norm(G.mean(0))))
