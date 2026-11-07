import numpy as np

SIZE_BINS = [(1, 1), (2, 2), (3, 4), (5, 10)]


def size_strat(cover, size, bins=SIZE_BINS):
    """Min coverage over size strata with >= 1 sample (+ list of per-bin coverage)."""
    cs = []
    for lo, hi in bins:
        m = (size >= lo) & (size <= hi)
        cs.append(cover[m].mean() if m.sum() > 0 else np.nan)
    return np.nanmin(cs), cs


def class_cov(cover, y, K):
    return np.array([cover[y == k].mean() if (y == k).any() else np.nan for k in range(K)])
