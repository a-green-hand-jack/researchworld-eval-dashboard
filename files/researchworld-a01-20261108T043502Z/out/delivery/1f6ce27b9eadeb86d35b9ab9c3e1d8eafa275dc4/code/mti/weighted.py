"""Minimum investment for a weighted mean V(y) = sum_t w_t y_t (w >= 0, sum w = 1): fractional knapsack.
L1: raise the tasks with the largest weight first (each point on task t buys w_t of score), up to the headroom;
K: smallest number of tasks whose maximal contribution w_t h_t covers the need (largest contributions first).
Returns (L1, K); inf when infeasible. First means V(y) >= tau + eps, tau = best rival weighted mean."""
import numpy as np

INF = np.inf


def weighted_min_investment(X, i, cap, w, eps=1e-3):
    w = np.asarray(w, float); x = X[i]; c = np.maximum(np.asarray(cap, float), x); h = c - x
    V = X @ w; tau = np.delete(V, i).max()
    if V[i] > tau: return 0.0, 0
    need = tau + eps - V[i]
    contrib = w * h
    if contrib.sum() < need - 1e-12: return INF, INF
    L1 = 0.0; rem = need
    for t in np.argsort(-w, kind="stable"):                   # most points of score per point of investment first
        if rem <= 1e-15: break
        d = min(h[t], rem / w[t]) if w[t] > 0 else 0.0
        L1 += d; rem -= w[t] * d
    k = int(np.searchsorted(np.cumsum(np.sort(contrib)[::-1]), need - 1e-12) + 1)
    return L1, k
