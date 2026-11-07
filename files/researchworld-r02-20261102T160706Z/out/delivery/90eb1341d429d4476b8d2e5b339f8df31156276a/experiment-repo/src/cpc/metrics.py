import numpy as np
from scipy import stats


def clopper_pearson(k, n, a=0.05):
    lo = 0.0 if k == 0 else stats.beta.ppf(a / 2, k, n - k + 1)
    hi = 1.0 if k == n else stats.beta.ppf(1 - a / 2, k + 1, n - k)
    return lo, hi


def binned_gap(cover, g, nbins=5):
    """Quantile bins of g; return (min bin coverage, max bin coverage)."""
    edges = np.quantile(g, np.linspace(0, 1, nbins + 1)[1:-1])
    b = np.searchsorted(edges, g)
    c = np.array([cover[b == k].mean() for k in range(nbins) if (b == k).any()])
    return c.min(), c.max()


def wsc(cover, F, delta=0.1, M=200, rng=None):
    """Worst-slab coverage (Romano et al. 2020 style): choose slab on half the data, evaluate on the other half."""
    rng = rng or np.random.default_rng(0)
    n = len(cover)
    idx = rng.permutation(n)
    a, b = idx[: n // 2], idx[n // 2:]
    Fa, Fb = F[a], F[b]
    mu, sd = Fa.mean(0), Fa.std(0) + 1e-12
    Fa, Fb = (Fa - mu) / sd, (Fb - mu) / sd
    w = max(int(np.ceil(delta * len(a))), 1)
    best, bestv = None, np.inf
    V = rng.normal(size=(M, F.shape[1]))
    V /= np.linalg.norm(V, axis=1, keepdims=True)
    ca = cover[a].astype(float)
    for v in V:
        pa = Fa @ v
        o = np.argsort(pa)
        cs = np.r_[0, np.cumsum(ca[o])]
        win = (cs[w:] - cs[:-w]) / w
        j = int(np.argmin(win))
        if win[j] < bestv:
            bestv, best = win[j], (v, pa[o][j], pa[o][j + w - 1])
    v, lo, hi = best
    pb = Fb @ v
    m = (pb >= lo) & (pb <= hi)
    return cover[b][m].mean() if m.sum() >= 5 else np.nan
