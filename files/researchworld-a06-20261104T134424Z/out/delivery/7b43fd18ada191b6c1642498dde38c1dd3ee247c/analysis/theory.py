"""Gaussian-max prediction of the winner's-curse gap for full-evaluation argmax:
tuning-set scores ~ N(mu, Sigma/n) with Sigma the question-level covariance of the K configs' correctness;
gap_pred = E[ eps_sel ], sel = argmax(mu + eps) over a random K-subset (random search with full evaluation)."""
import numpy as np
def predict_gap(Y, n, K, M=20000, seed=0):
    rng = np.random.default_rng(seed); Kp = Y.shape[0]
    mu = Y.mean(1); Sig = np.cov(Y.astype(float)) + 1e-12 * np.eye(Kp)
    Lc = np.linalg.cholesky(Sig / n); gaps = np.empty(M); reg = np.empty(M)
    for m in range(M):
        c = np.arange(Kp) if K == Kp else rng.choice(Kp, K, replace=False)
        eps = Lc @ rng.standard_normal(Kp)       # full-pool draw; subset marginal is the right Gaussian
        k = c[np.argmax(mu[c] + eps[c])]; gaps[m] = eps[k]
    return gaps.mean(), gaps.std() / np.sqrt(M)
