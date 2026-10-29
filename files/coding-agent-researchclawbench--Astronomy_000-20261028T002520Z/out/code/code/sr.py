"""Bayesian black-hole-superradiance framework for ultralight bosons.
Natural units hbar=c=1 internally; mu, f in eV, M in Msun, t in yr."""
import numpy as np
from math import factorial, pi

TM_SUN = 4.925491268e-6          # G Msun / c^3  [s]
EV_TO_INV_S = 1.519267447e15     # 1 eV / hbar [1/s]
YR = 3.15576e7                   # s
GMSUN2_HBARC = 8.3468e75         # G Msun^2 /(hbar c)   (checked in test_constants)
ALPHA_PER = TM_SUN * EV_TO_INV_S # alpha = ALPHA_PER * (M/Msun) * (mu/eV)

LEVELS = [(2, 1, 1), (3, 1, 1), (3, 2, 2), (4, 3, 3), (5, 4, 4)]   # (n,l,m)

def C_nl(n, l):
    return (2.0**(4*l+1) * factorial(n+l) / (n**(2*l+4) * factorial(n-l-1))
            * (factorial(l) / (factorial(2*l) * factorial(2*l+1)))**2)

def omega_tM(alpha, n):
    """real part of cloud frequency times GM (hydrogenic approx.)"""
    return alpha * (1 - alpha**2 / (2 * n**2))

def a_crit(alpha, n, m):
    """spin at which m*Omega_H = omega (superradiance saturation)"""
    x = omega_tM(alpha, n) / m
    return 4 * x / (1 + 4 * x**2)

def gamma_tM(a, alpha, n, l, m):
    """Amplitude growth rate Gamma * GM/c^3 (Baumann et al. 2019 eq. for Gamma_nlm);
    occupation number grows as exp(2 Gamma t). Negative => not superradiant."""
    rp = 1 + np.sqrt(1 - a**2)
    w = omega_tM(alpha, n)
    g = 1.0
    for k in range(1, l + 1):
        g = g * (k**2 * (1 - a**2) + (a * m - 2 * rp * w)**2)
    return 2 * rp * C_nl(n, l) * g * (m * a / (2 * rp) - w) * alpha**(4*l + 5)

def log_Nbn(alpha, mu, f, n, cbn=1.0):
    """log of bosenova / shape-change threshold occupation number,
    N_bn = 16 pi cbn n^4 f^2 /(alpha mu^2)   (Arvanitaki & Dubovsky 2011, eq. 48 generalised)"""
    return np.log(16 * pi * cbn * n**4) + 2 * np.log(f) - np.log(alpha) - 2 * np.log(mu)

def excluded(M, a, mu, f=np.inf, t_yr=3e6, levels=LEVELS, cbn=1.0, log10_tshift=0.0, N0=1.0, alpha_max=1.0):
    """Boolean array over (M,a) samples: True if for ANY level the cloud would have spun the BH
    down below the observed spin within t. mu,f scalars (eV). log10_tshift: nuisance shift of
    log10(t) (also absorbs the O(1) theory uncertainty of Gamma)."""
    M = np.asarray(M); a = np.asarray(a)
    alpha = ALPHA_PER * M * mu
    t_s = t_yr * YR * 10.0**log10_tshift
    out = np.zeros(M.shape, bool)
    for (n, l, m) in levels:
        G = gamma_tM(a, alpha, n, l, m) / TM_SUN / M       # 1/s, Gamma ~ per GM
        ac = a_crit(alpha, n, m)
        da = a - ac
        ok = (G > 0) & (da > 0) & (alpha < alpha_max)
        with np.errstate(all='ignore'):
            lnDN = np.log(np.where(ok, da, 1.0) * (M**2) * GMSUN2_HBARC / m)
            if np.isfinite(f):
                lnNcap = np.minimum(lnDN, log_Nbn(alpha, mu, f, n, cbn))
            else:
                lnNcap = lnDN
            # e-folds to reach N_cap from N0, plus cap-limited extraction time (N_DN/N_cap cycles)
            lam = np.maximum(lnNcap - np.log(N0), 0.0) + np.exp(lnDN - lnNcap)
            treq = lam / (2 * np.where(ok, G, 1.0))
        out |= ok & (treq < t_s)
    return out

def likelihood(M, a, mu_grid, f=np.inf, sigma_dex=0.0, nquad=1, **kw):
    """L(mu,f) = P(data compatible | boson) = fraction of posterior samples not excluded,
    optionally marginalised over a log-normal timescale nuisance (Gauss-Hermite)."""
    if sigma_dex > 0 and nquad > 1:
        x, w = np.polynomial.hermite_e.hermegauss(nquad); w = w / w.sum()
    else:
        x, w = np.array([0.0]), np.array([1.0])
    L = np.zeros(len(mu_grid))
    for i, mu in enumerate(mu_grid):
        s = 0.0
        for xi, wi in zip(x, w):
            s += wi * (1 - excluded(M, a, mu, f, log10_tshift=sigma_dex * xi, **kw).mean())
        L[i] = s
    return L

def limits(mu_grid, L, thr=0.05):
    """contiguous-agnostic: return list of (lo,hi) intervals where L<thr"""
    ex = L < thr; iv = []; i = 0
    while i < len(ex):
        if ex[i]:
            j = i
            while j + 1 < len(ex) and ex[j + 1]: j += 1
            iv.append((mu_grid[i], mu_grid[j])); i = j + 1
        else: i += 1
    return iv
