"""Split-conformal machinery shared by all experiments."""
import numpy as np


def conformal_quantile(scores, alpha):
    """Finite-sample-corrected (1-alpha) quantile: the ceil((n+1)(1-alpha))-th smallest score.
    Returns +inf if that rank exceeds n."""
    s = np.sort(np.asarray(scores))
    n = len(s)
    k = int(np.ceil((n + 1) * (1 - alpha)))
    return s[k - 1] if k <= n else np.inf


def weighted_conformal_quantile(scores, weights, w_test, alpha):
    """Tibshirani et al. (2019) weighted quantile for a test point with weight w_test."""
    o = np.argsort(scores)
    s, w = np.asarray(scores)[o], np.asarray(weights)[o]
    p = w / (w.sum() + w_test)
    c = np.cumsum(p)
    idx = np.searchsorted(c, 1 - alpha, side="left")
    return s[idx] if idx < len(s) else np.inf


def mondrian_quantiles(scores, bins, alpha, n_bins):
    """Per-bin conformal quantiles. bins: integer bin id per calibration point."""
    return np.array([conformal_quantile(scores[bins == b], alpha) if (bins == b).any() else np.inf
                     for b in range(n_bins)])


def beta_params(n, alpha):
    l = int(np.floor((n + 1) * alpha))
    return n + 1 - l, l   # conditional coverage ~ Beta(n+1-l, l)
