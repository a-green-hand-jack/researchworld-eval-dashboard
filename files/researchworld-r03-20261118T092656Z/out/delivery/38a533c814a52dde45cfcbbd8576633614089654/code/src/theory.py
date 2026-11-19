"""Closed-form error forecasts for the factor model (all in standardised units)."""
import numpy as np
import fa as FA


def bayes_error(Lam, psi, S):
    """mean over T = complement of S of  psi_j + l_j' P_S l_j  (error of the Bayes predictor, formula (a))."""
    N = len(psi); T = np.setdiff1d(np.arange(N), S)
    return float(FA.predicted_mse(dict(Lam=Lam, psi=psi), np.asarray(S), T).mean())


def tail_floor(Lam, psi, S):
    """sanity floor (c): mean_T psi_j + sum_{i>k} lambda_i(Lam_T' Lam_T) / |T|  (valid for every selector with |S|=k)."""
    N = len(psi); S = np.asarray(S); T = np.setdiff1d(np.arange(N), S)
    ev = np.sort(np.linalg.eigvalsh(Lam[T].T @ Lam[T]))[::-1]
    return float((psi[T].sum() + ev[len(S):].sum()) / len(T))


def tail_floor_k(Lam, psi, k):
    """k-only version for the spectrum plot: (mean psi*(N-k)... ) uses full Lam'Lam spectrum / N (for display)."""
    N = len(psi)
    ev = np.sort(np.linalg.eigvalsh(Lam.T @ Lam))[::-1]
    return float((psi.sum() + ev[k:].sum()) / N)


def debias_spikes(Lam, psi, M):
    """invert the BBP sample-spike inflation (spiked model, isotropic noise psibar, c = N/M).
    returns Lam_c (recovered factors, rescaled), psi_c (unrecoverable factors folded into psi), rho_pop, rho_fit."""
    N, r = Lam.shape
    c = N / M
    if r == 0:
        return Lam, psi, np.array([]), np.array([])
    pb = psi.mean()
    U, s, _ = np.linalg.svd(Lam, full_matrices=False)       # Lam = U diag(s) V'
    rho_fit = s ** 2 / pb
    disc = (rho_fit - c) ** 2 - 4 * c
    ok = (rho_fit > c) & (disc >= 0)
    rho = np.where(ok, ((rho_fit - c) + np.sqrt(np.maximum(disc, 0))) / 2, 0.0)
    rec = ok & (rho > np.sqrt(c))
    Lc = U[:, rec] * (np.sqrt(rho[rec] * pb))[None, :]
    dropped = (U[:, ~rec] * s[~rec][None, :]) if (~rec).any() else np.zeros((N, 0))
    psi_c = psi + (dropped ** 2).sum(1)
    return Lc, psi_c, rho, rho_fit


def forecast_finite_m(Lam, psi, M, S, inflate=True):
    """finite-history forecast for selection S: de-biased spikes, unrecoverable factors -> noise, plus
    (d1)-type inflation (1 + k_eff/(M-k_eff-1)) on the reducible part (the part above the floor)."""
    Lc, psic, rho, rho_fit = debias_spikes(Lam, psi, M)
    N = len(psi); S = np.asarray(S); T = np.setdiff1d(np.arange(N), S)
    floor = psic[T].mean()
    full = bayes_error(Lc, psic, S) if Lc.shape[1] else floor
    red = full - floor
    k = len(S); keff = min(k, max(Lc.shape[1], 1))
    if inflate and M - keff - 1 > 0:
        red = red * (1 + keff / (M - keff - 1))
    return float(floor + red)
