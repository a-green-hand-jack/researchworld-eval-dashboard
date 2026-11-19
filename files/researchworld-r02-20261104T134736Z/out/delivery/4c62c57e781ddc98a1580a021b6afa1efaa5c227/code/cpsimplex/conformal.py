"""Split / CV+ conformal quantiles and membership."""
import numpy as np


def conformal_quantile(s, alpha):
    """Finite-sample split-conformal threshold: ceil((n+1)(1-alpha))-th smallest score (inf if > n)."""
    n = len(s)
    k = int(np.ceil((n + 1) * (1 - alpha)))
    if k > n:
        return np.inf
    return np.partition(s, k - 1)[k - 1]
