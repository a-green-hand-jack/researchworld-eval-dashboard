"""Estimators of the GATE. Regression estimators are feature maps Phi(state) + OLS + corner prediction:
tau_hat = mean_i[Phi_i(all treated) - Phi_i(all control)] . beta_hat."""
import numpy as np
from scipy.stats import binom

from .outcomes import oracle_exposure


# ----------------------------- feature maps -----------------------------
def _cols(*c):
    return np.column_stack(c)


def phi_L(s, ctx, spec): return _cols(np.ones(ctx.n), s["z"], s["g1"])
def phi_Lc(s, ctx, spec): return _cols(np.ones(ctx.n), s["z"], s["c1"])
def phi_Q(s, ctx, spec): return _cols(np.ones(ctx.n), s["z"], s["g1"], s["g1"] ** 2, s["z"] * s["g1"])
def phi_G(s, ctx, spec):
    ld = np.log(ctx.deg); ld = (ld - ld.mean()) / (ld.std() + 1e-12)
    return _cols(np.ones(ctx.n), s["z"], s["g1"], s["g2"], s["z"] * s["g1"], ld)
def phi_O(s, ctx, spec): return _cols(np.ones(ctx.n), s["z"], oracle_exposure(spec, ctx, s))
def phi_L2(s, ctx, spec): return _cols(np.ones(ctx.n), s["z"], s["g1"], s["g2"])   # linear in both hops


FEATURES = {"REG-L": phi_L, "REG-Lc": phi_Lc, "REG-Q": phi_Q, "REG-G": phi_G, "REG-O": phi_O, "REG-L2": phi_L2}


def reg_estimate(name, ctx, spec, state, y, corners=None):
    f = FEATURES[name]
    Phi = f(state, ctx, spec)
    c1, c0 = corners if corners is not None else (ctx.corner(1), ctx.corner(0))
    D = (f(c1, ctx, spec) - f(c0, ctx, spec)).mean(0)
    beta, *_ = np.linalg.lstsq(Phi, y, rcond=None)
    return float(D @ beta), Phi, beta, D


def sandwich_var(Phi, y, beta, D, S):
    """Network-robust (distance<=2 dependence) sandwich variance of D'beta_hat around the projection."""
    e = y - Phi @ beta
    s = Phi * e[:, None]
    meat = s.T @ (S @ s)
    bread = np.linalg.pinv(Phi.T @ Phi)
    return float(D @ bread @ meat @ bread @ D)


# ----------------------------- design-based -----------------------------
def dm(state, y):
    z = state["z"]
    if z.sum() == 0 or z.sum() == len(z):
        return np.nan
    return float(y[z == 1].mean() - y[z == 0].mean())


def _relaxed_pi_gcr(ctx, p, labels, deltas):
    """Exact propensities of the relaxed exposures under graph cluster randomisation (clusters treated independently with probability p), for each delta:
    pi1_i = P(z_i = 1, #treated neighbours >= ceil((1-delta) d_i)), pi0_i = P(z_i = 0, #treated neighbours <= floor(delta d_i)).
    Neighbours in i's own cluster share its arm; the others are independent Bernoulli(p) draws grouped by cluster, so the count of treated
    neighbours outside the own cluster is a weighted Poisson-binomial, convolved exactly."""
    A = ctx.A.tocsr()
    d = ctx.deg
    out = {dl: (np.zeros(ctx.n), np.zeros(ctx.n)) for dl in deltas}
    for i in range(ctx.n):
        nb = A.indices[A.indptr[i]:A.indptr[i + 1]]
        lab, cnt = np.unique(labels[nb], return_counts=True)
        own = int(cnt[lab == labels[i]].sum())
        w = cnt[lab != labels[i]]
        pm = np.zeros(int(w.sum()) + 1); pm[0] = 1.0       # distribution of treated neighbours outside the own cluster
        for m in w:
            new = pm * (1 - p)
            new[m:] += pm[:len(pm) - m] * p
            pm = new
        cs = np.cumsum(pm[::-1])[::-1]                    # cs[t] = P(T_out >= t)
        cd = np.cumsum(pm)
        for dl, (q1, q0) in out.items():
            k1 = int(np.ceil((1 - dl) * d[i] - 1e-9))
            k0 = int(np.floor(dl * d[i] + 1e-9))
            t1 = max(k1 - own, 0)
            q1[i] = p * (cs[t1] if t1 < len(cs) else 0.0)
            q0[i] = (1 - p) * cd[min(k0, len(pm) - 1)]       # own neighbours are control: need T_out <= k0
    return {dl: (np.maximum(q1, 1e-300), np.maximum(q0, 1e-300)) for dl, (q1, q0) in out.items()}


class HT:
    """Exposure-mapping estimators. 'full' exposure: unit and all neighbours in the same arm (Aronow-Samii);
    'relaxed(delta)': own arm and >= (1-delta) of neighbours in it (biased, lower variance)."""

    def __init__(self, ctx, p, design=None, deltas=(0.25,)):
        self.ctx, self.p, self.deltas = ctx, p, deltas
        d = ctx.deg
        self.design = design
        if design is not None and design.kind == "gcr":
            _, k = design.cluster_stats(ctx)
            self.pi1 = p ** k
            self.pi0 = (1 - p) ** k
        else:
            self.pi1 = p ** (d + 1)
            self.pi0 = (1 - p) ** (d + 1)
        self.rel = {}
        if design is not None and design.kind == "gcr":
            self.rel = _relaxed_pi_gcr(ctx, p, design.labels, deltas)
        if design is None or design.kind == "bern":
            for dl in deltas:
                k1 = np.ceil((1 - dl) * d - 1e-9)
                k0 = np.floor(dl * d + 1e-9)
                self.rel[dl] = (p * binom.sf(k1 - 1, d, p), (1 - p) * binom.cdf(k0, d, p))

    def estimate(self, state, y):
        ctx = self.ctx
        z, c1 = state["z"], state["c1"]
        out = {}
        if self.design is not None and self.design.kind == "gcr":
            tot = ctx.A @ z + z
            e1, e0 = tot == ctx.deg + 1, tot == 0
        else:
            e1, e0 = (z == 1) & (c1 == ctx.deg), (z == 0) & (c1 == 0)
        w1 = np.where(e1, 1 / np.maximum(self.pi1, 1e-300), 0.0)
        w0 = np.where(e0, 1 / np.maximum(self.pi0, 1e-300), 0.0)
        out["HT"] = float((w1 * y).mean() - (w0 * y).mean())
        n1, n0 = e1.sum(), e0.sum()
        m1 = (w1 * y).sum() / w1.sum() if n1 else (y[z == 1].mean() if z.sum() else np.nan)
        m0 = (w0 * y).sum() / w0.sum() if n0 else (y[z == 0].mean() if z.sum() < len(z) else np.nan)
        out["HAJEK"] = float(m1 - m0)
        out["n_exp1"], out["n_exp0"] = int(n1), int(n0)
        for dl, (q1, q0) in self.rel.items():
            r1 = (z == 1) & (state["g1"] >= 1 - dl - 1e-9)
            r0 = (z == 0) & (state["g1"] <= dl + 1e-9)
            v1 = r1 / q1; v0 = r0 / q0
            a1 = (v1 * y).sum() / v1.sum() if r1.sum() else (y[z == 1].mean() if z.sum() else np.nan)
            a0 = (v0 * y).sum() / v0.sum() if r0.sum() else (y[z == 0].mean() if z.sum() < len(z) else np.nan)
            out[f"HAJEK-r{dl:g}"] = float(a1 - a0)
        return out


def ht_exact_var(ctx, Y1, Y0, p, sigma=0.0, design=None, chunk=2000):
    """Exact design variance of the Horvitz-Thompson estimator with full-exposure map (own arm + all neighbours,
    or all clusters of the closed neighbourhood under GCR), given fixed potential outcomes Y1 = Y(all treated),
    Y0 = Y(all control).  Pairs whose exposure sets share o units (clusters) have
    E[a_i a_j] = Y1_i Y1_j p^-o + Y0_i Y0_j (1-p)^-o  (cross terms 0), independent otherwise.
    Idiosyncratic noise (sd sigma, frozen across arms) adds sigma^2 (1/pi1_i + 1/pi0_i)."""
    import scipy.sparse as sp
    n = ctx.n
    B = (ctx.A + sp.identity(n, format="csr")).tocsr()
    if design is not None and design.kind == "gcr":
        C = sp.csr_matrix((np.ones(n), (np.arange(n), design.labels)), shape=(n, design.K))
        K = (B @ C).tocsr(); K.data[:] = 1.0
        k = np.asarray(K.sum(1)).ravel()
    else:
        K, k = B, ctx.deg + 1
    pi1, pi0 = p ** k, (1 - p) ** k
    D = Y1 - Y0
    tot = 0.0
    Kt = K.T.tocsr()
    for s in range(0, n, chunk):
        O = (K[s:s + chunk] @ Kt).tocoo()
        o = O.data
        i, j = O.row + s, O.col
        with np.errstate(over="ignore"):
            term = Y1[i] * Y1[j] * p ** (-o) + Y0[i] * Y0[j] * (1 - p) ** (-o) - D[i] * D[j]
        tot += term.sum()
    with np.errstate(divide="ignore", over="ignore"):
        noise = sigma ** 2 * np.sum(1 / pi1 + 1 / pi0)
    return float((tot + noise) / n ** 2)
