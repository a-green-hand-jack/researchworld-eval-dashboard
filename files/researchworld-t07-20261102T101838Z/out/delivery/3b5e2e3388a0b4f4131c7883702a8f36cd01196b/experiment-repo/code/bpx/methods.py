"""Item selectors and score estimators.

A *selector* sees only the source-model matrix and returns (idx, pi): the chosen item indices and their
inclusion probabilities (for design-based estimators) / weights. An *estimator* sees the source matrix, the
selected indices and the target's responses on those items ONLY, and returns the predicted full-benchmark score.
"""
import numpy as np
from sklearn.cluster import KMeans
from sklearn.linear_model import RidgeCV
from .irt import IRT


class Source:
    """Everything fitted on the source models (shared by all methods within one split)."""

    def __init__(self, Ssrc, irt_d=4, seed=0, fit_irt=True):
        self.S = Ssrc.astype(np.float32)
        self.M, self.N = Ssrc.shape
        self.q = self.S.mean(0)                    # item difficulty (source accuracy)
        self.full = self.S.mean(1)
        self.irt = IRT(d=irt_d, seed=seed).fit(Ssrc) if fit_irt else None
        # low-rank (PCA) model of the centred matrix, MAP-ability with Gaussian prior
        mu = self.q
        U, s, Vt = np.linalg.svd(self.S - mu, full_matrices=False)
        self._svd = (U, s, Vt)
        self.rank_models = {}
        for k in (2, 4, 8, 16, 32):
            kk = min(k, len(s))
            Vk = Vt[:kk].T * (s[:kk] / np.sqrt(self.M))                 # N x k, columns scaled to prior std
            R = (self.S - mu) - (U[:, :kk] * s[:kk]) @ Vt[:kk]
            self.rank_models[k] = (Vk, float((R ** 2).mean()))
        self.mu = mu
        self.V, self.sig2 = self.rank_models[8]
        # item residual variance under the IRT fit, for variance-aware sampling
        if fit_irt:
            P = self.irt.prob(self.irt.th_src)
            self.resid_var = ((self.S - P) ** 2).mean(0)
        self._emb = None

    def embedding(self, dim=16):
        if self._emb is None:
            Xc = self.S - self.S.mean(0)
            U, s, Vt = np.linalg.svd(Xc, full_matrices=False)
            self._emb = (Vt[:dim].T * s[:dim])
        return self._emb


# ------------------------------------------------------------------ selectors
def _systematic_pps(w, n, rng):
    """Fixed-size unequal-probability sample (systematic PPS) with inclusion probs pi = n*w/sum(w) capped at 1."""
    N = len(w)
    w = np.asarray(w, float) + 1e-12
    pi = np.zeros(N); free = np.ones(N, bool); m = n
    for _ in range(50):
        pi[free] = m * w[free] / w[free].sum()
        over = free & (pi >= 1)
        if not over.any():
            break
        pi[over] = 1; free &= ~over; m = n - int((~free).sum())
    perm = rng.permutation(N)                      # random order -> no periodicity artefacts
    cs = np.cumsum(pi[perm])
    u = rng.uniform()
    pts = u + np.arange(n)
    pos = np.searchsorted(cs, pts, side="right")
    idx = np.unique(perm[np.minimum(pos, N - 1)])
    return idx, pi[idx]


def sel_random(src, n, rng):
    idx = np.sort(rng.choice(src.N, n, replace=False))
    return idx, np.full(n, n / src.N)


def sel_strat(src, n, rng):
    """One random item from each of n strata of equal size, formed by sorting items on source difficulty."""
    order = np.argsort(src.q + 1e-6 * rng.uniform(size=src.N))
    cuts = np.linspace(0, src.N, n + 1).astype(int)
    idx = np.array([order[rng.integers(cuts[i], max(cuts[i] + 1, cuts[i + 1]))] for i in range(n)])
    return np.sort(idx), np.full(n, n / src.N)


def sel_anchor(src, n, rng):
    """Anchor points: cluster items by their source-model response vectors, take the medoid of each cluster;
    weights = cluster size / N (returned in 'pi' slot as 1/(weight*N)... see est_anchor)."""
    X = src.embedding(16)
    km = KMeans(n_clusters=n, n_init=1, random_state=int(rng.integers(1 << 30))).fit(X)
    idx, size = [], []
    for c in range(n):
        mem = np.where(km.labels_ == c)[0]
        if len(mem) == 0:
            continue
        d = ((X[mem] - km.cluster_centers_[c]) ** 2).sum(1)
        idx.append(mem[np.argmin(d)]); size.append(len(mem))
    idx, size = np.array(idx), np.array(size, float)
    o = np.argsort(idx)
    return idx[o], size[o] / src.N      # second return = weights, sum to 1


def sel_pps(src, n, rng):
    """Variance-aware sampling: inclusion prob ∝ sqrt(item residual variance under the IRT fit) (floored)."""
    w = np.sqrt(src.resid_var)
    w = np.maximum(w, 0.1 * w.mean())
    return _systematic_pps(w, n, rng)


def sel_pps_q(src, n, rng):
    """Inclusion prob ∝ sqrt(q(1-q)) of source item accuracy (model-free variance proxy)."""
    w = np.sqrt(np.clip(src.q * (1 - src.q), 0, None))
    w = np.maximum(w, 0.1 * w.mean())
    return _systematic_pps(w, n, rng)



def sel_omp(src, n, rng):
    """Greedy forward selection (orthogonal matching pursuit): items whose responses best explain the sources' full score.
    Deterministic given the sources."""
    X = src.S - src.q
    y = src.full - src.full.mean()
    r = y.copy(); idx = []
    Xo = X.copy()
    for _ in range(n):
        nrm = np.sqrt((Xo ** 2).sum(0))
        sc = np.abs(Xo.T @ r) / np.maximum(nrm, 1e-6)
        sc[nrm < 1e-6] = -1
        if idx:
            sc[idx] = -1
        j = int(np.argmax(sc)); idx.append(j)
        qv = Xo[:, j] / nrm[j]
        r = r - qv * (qv @ r)
        Xo = Xo - np.outer(qv, qv @ Xo)
    idx = np.array(sorted(idx))
    return idx, np.full(len(idx), n / src.N)


def sel_copt(src, n, rng):
    """Bayesian c-optimal design for the low-rank model: greedily choose items minimising the posterior variance of the
    mean-score direction c = mean_j V_j (plus the full latent covariance through the greedy update)."""
    V = src.V; k = V.shape[1]
    c = V.mean(0)
    Ginv = np.eye(k)            # posterior covariance (prior N(0,I))
    idx = []
    for _ in range(n):
        Gv = V @ Ginv                                       # N x k
        denom = 1.0 + (Gv * V).sum(1) / src.sig2           # N
        gain = (Gv @ c) ** 2 / (src.sig2 * denom)         # variance reduction of c^T z
        gain[idx] = -1
        j = int(np.argmax(gain)); idx.append(j)
        g = Gv[j]
        Ginv = Ginv - np.outer(g, g) / (src.sig2 * denom[j])
    idx = np.array(sorted(idx))
    return idx, np.full(len(idx), n / src.N)


SELECTORS = dict(omp=sel_omp, copt=sel_copt, random=sel_random, strat=sel_strat, anchor=sel_anchor, pps=sel_pps, ppsq=sel_pps_q)


# ------------------------------------------------------------------ estimators
# each: f(src, idx, wt, Yobs, rng) -> (T,) predicted full scores.  wt = pi (inclusion probs) or anchor weights.
def est_mean(src, idx, wt, Y, rng):
    return Y.mean(1)


def est_anchor(src, idx, wt, Y, rng):
    return (Y * wt).sum(1) / wt.sum()


def est_const(src, idx, wt, Y, rng):
    return np.full(Y.shape[0], src.full.mean())


def est_cal(src, idx, wt, Y, rng):
    """Subset mean recalibrated by 1-D linear regression on source models (subset mean -> full score)."""
    x = src.S[:, idx].mean(1); y = src.full
    if x.std() < 1e-9:
        return np.full(Y.shape[0], y.mean())
    b = np.cov(x, y)[0, 1] / x.var(ddof=1); a = y.mean() - b * x.mean()
    return np.clip(a + b * Y.mean(1), 0, 1)


def est_ridge(src, idx, wt, Y, rng):
    X = src.S[:, idx]
    r = RidgeCV(alphas=np.logspace(-2, 2, 5)).fit(X, src.full)
    return np.clip(r.predict(Y), 0, 1)


def est_knn(src, idx, wt, Y, rng, k=10):
    X = src.S[:, idx]
    D = (Y[:, None, :] != X[None, :, :]).mean(2)         # (T, Ms) Hamming
    nn = np.argsort(D, 1)[:, :k]
    return src.full[nn].mean(1)


def _lowrank_prob(src, idx, Y, rank=8):
    Vfull, sig2 = src.rank_models[rank]
    V = Vfull[idx]                                          # n x k
    k = V.shape[1]
    G = V.T @ V / sig2 + np.eye(k)
    z = np.linalg.solve(G, (V.T @ (Y - src.mu[idx]).T) / sig2)   # k x T
    return np.clip(src.mu[None, :] + (Vfull @ z).T, 0, 1)


def est_lowrank(src, idx, wt, Y, rng):
    return _lowrank_prob(src, idx, Y).mean(1)


def _irt_prob(src, idx, Y):
    return src.irt.prob(src.irt.ability(idx, Y))


def est_irt(src, idx, wt, Y, rng):
    return _irt_prob(src, idx, Y).mean(1)


def _dr(P, idx, pi, Y):
    """Model-assisted (difference / generalised-regression) estimator: mean model prediction + Hajek-weighted
    mean residual on the sampled items. Design-unbiased (up to the Hajek ratio) whatever the model."""
    w = 1.0 / pi
    resid = ((Y - P[:, idx]) * w).sum(1) / w.sum()
    return np.clip(P.mean(1) + resid, 0, 1)


def est_irt_dr(src, idx, pi, Y, rng):
    return _dr(_irt_prob(src, idx, Y), idx, pi, Y)


def est_lowrank_dr(src, idx, pi, Y, rng):
    return _dr(_lowrank_prob(src, idx, Y), idx, pi, Y)



def _eb(P, idx, pi, Y):
    """Empirical-Bayes shrinkage of the residual correction: pred = mean(P) + g * rbar, g = rbar^2 / (rbar^2 + var(rbar)).
    g -> 1 (full design-based correction) when the model is visibly biased on the sample, g -> 0 when the
    residual mean is within sampling noise (then the model prediction is kept)."""
    w = 1.0 / pi; e = Y - P[:, idx]; sw = w.sum()
    rbar = (e * w).sum(1) / sw
    n = len(idx)
    v = ((w ** 2) * (e - rbar[:, None]) ** 2).sum(1) / sw ** 2 * n / max(n - 1, 1)
    g = rbar ** 2 / (rbar ** 2 + v + 1e-12)
    return np.clip(P.mean(1) + g * rbar, 0, 1)


def est_irt_eb(src, idx, pi, Y, rng):
    return _eb(_irt_prob(src, idx, Y), idx, pi, Y)


def est_lowrank_eb(src, idx, pi, Y, rng):
    return _eb(_lowrank_prob(src, idx, Y), idx, pi, Y)


def est_ht(src, idx, pi, Y, rng):
    w = 1.0 / pi
    return (Y * w).sum(1) / w.sum()


def est_girt(src, idx, wt, Y, rng):
    """tinyBenchmarks-style gp-IRT: convex mix of the (anchor-)weighted accuracy and the IRT prediction;
    mixing weight chosen by held-out source models (3 folds, items params refit not repeated: see notes)."""
    lam = getattr(src, "girt_lam", {}).get(len(idx))
    if lam is None:
        lam = _choose_lambda(src, idx, wt)
        src.__dict__.setdefault("girt_lam", {})[len(idx)] = lam
    a = (Y * wt).sum(1) / wt.sum()
    return lam * a + (1 - lam) * est_irt(src, idx, wt, Y, rng)


def _choose_lambda(src, idx, wt, grid=np.linspace(0, 1, 11)):
    # pseudo-targets: sources (item parameters were fitted including them -> optimistic for IRT; documented)
    rs = np.random.default_rng(123)
    sub = rs.choice(src.M, min(src.M, 100), replace=False)
    Y = src.S[sub][:, idx]
    a = (Y * wt).sum(1) / wt.sum(); p = est_irt(src, idx, wt, Y, rs); true = src.full[sub]
    errs = [np.mean(np.abs(l * a + (1 - l) * p - true)) for l in grid]
    return float(grid[int(np.argmin(errs))])


def _rank_variant(rank, kind):
    def f(src, idx, wt, Y, rng):
        P = _lowrank_prob(src, idx, Y, rank)
        if kind == "plain":
            return P.mean(1)
        return _dr(P, idx, wt, Y) if kind == "dr" else _eb(P, idx, wt, Y)
    return f


ESTIMATORS = dict(mean=est_mean, anchor=est_anchor, const=est_const, cal=est_cal, ridge=est_ridge, knn=est_knn,
                  lowrank=est_lowrank, irt=est_irt, irt_dr=est_irt_dr, irt_eb=est_irt_eb, lowrank_eb=est_lowrank_eb, lowrank_dr=est_lowrank_dr, ht=est_ht, girt=est_girt)

# pipelines = (selector, estimator); names follow "selector+estimator"
PIPELINES = {
    "const": ("random", "const"),
    "random+mean": ("random", "mean"),
    "random+cal": ("random", "cal"),
    "strat+mean": ("strat", "mean"),
    "anchor+anchor": ("anchor", "anchor"),
    "anchor+girt": ("anchor", "girt"),
    "random+ridge": ("random", "ridge"),
    "random+knn": ("random", "knn"),
    "random+lowrank": ("random", "lowrank"),
    "random+irt": ("random", "irt"),
    "strat+lowrank": ("strat", "lowrank"),
    "anchor+irt": ("anchor", "irt"),
    "random+irt_dr": ("random", "irt_dr"),
    "random+lowrank_dr": ("random", "lowrank_dr"),
    "strat+irt_dr": ("strat", "irt_dr"),
    "pps+irt_dr": ("pps", "irt_dr"),
    "pps+lowrank_dr": ("pps", "lowrank_dr"),
    "ppsq+irt_dr": ("ppsq", "irt_dr"),
    "random+irt_eb": ("random", "irt_eb"),
    "random+lowrank_eb": ("random", "lowrank_eb"),
    "strat+lowrank_eb": ("strat", "lowrank_eb"),
    "pps+irt_eb": ("pps", "irt_eb"),
    "pps+lowrank_eb": ("pps", "lowrank_eb"),
    "pps+ht": ("pps", "ht"),
    "omp+ridge": ("omp", "ridge"),
    "omp+lowrank": ("omp", "lowrank"),
    "omp+cal": ("omp", "cal"),
    "copt+lowrank": ("copt", "lowrank"),
    "copt+ridge": ("copt", "ridge"),
    "copt+irt": ("copt", "irt"),
}
# P3 candidate designs (selector x model-assisted estimator) evaluated by source-internal CV in freeze_design.py
for _s in ("random", "strat", "pps", "ppsq"):
    for _e in ("irt_dr", "irt_eb", "lowrank_dr", "lowrank_eb"):
        PIPELINES.setdefault(f"{_s}+{_e}", (_s, _e))


def factorial_grid():
    """Selector x estimator grid (Q7 / selector-vs-predictor effects); estimators that need inclusion probabilities
    are paired only with probability-sampling designs."""
    design = ("random", "strat", "pps")
    grid = {}
    for s in ("random", "strat", "pps", "anchor", "omp", "copt"):
        for e in ("mean", "cal", "ridge", "knn", "lowrank", "irt", "lowrank_dr", "irt_dr"):
            if e.endswith("_dr") and s not in design:
                continue
            if s == "anchor" and e == "mean":
                e = "anchor"
            if s == "pps" and e == "mean":
                e = "ht"                    # unequal-probability design needs the Horvitz-Thompson/Hajek mean
            grid[f"{s}+{e}"] = (s, e)
    grid["const"] = ("random", "const")
    return grid


for _k in (2, 4, 16, 32):
    for _kind in ("plain", "dr", "eb"):
        _n = {"plain": "lowrank", "dr": "lowrank_dr", "eb": "lowrank_eb"}[_kind] + f"_k{_k}"
        ESTIMATORS[_n] = _rank_variant(_k, _kind)
        PIPELINES[f"strat+{_n}"] = ("strat", _n)
