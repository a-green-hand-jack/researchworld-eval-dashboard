"""Gaussian selection model: closed-form optimism and plug-in prediction for a 0/1 matrix.

Model: m_k = theta_k + eps_k, theta_k ~ N(0, tau^2) iid, eps_k ~ N(0, s2) iid (s2 = sigma^2/n).
Selecting khat = argmax m_k:  E[eps_khat] = s2 / sqrt(s2 + tau^2) * E[Z_(K)]   (Prop. 1)
                              E[theta_khat] = tau^2 / sqrt(s2 + tau^2) * E[Z_(K)]
"""
import numpy as np
from scipy import integrate, stats


def exp_max_normal(K):
    if K == 1: return 0.0
    f = lambda x: x * K * stats.norm.pdf(x) * stats.norm.cdf(x) ** (K - 1)
    return integrate.quad(f, -10, 10)[0]


def optimism_pred(n, K, sigma2_item, tau2):
    s2 = sigma2_item / n
    return s2 / np.sqrt(s2 + tau2) * exp_max_normal(K)


def estimate_params(S):
    """From a full KxN matrix: item-level variance of the config-specific part, and tau^2 (true sd^2 of config effects)."""
    K, N = S.shape
    dev = S - S.mean(0, keepdims=True)      # remove shared question difficulty
    sigma2_item = (dev.var(1, ddof=1)).mean() * K / (K - 1)  # undo shrinkage from subtracting the config-mean
    m = S.mean(1); d = m - m.mean()
    tau2 = max(0.0, d.var(ddof=1) - sigma2_item / N)
    return sigma2_item, tau2
