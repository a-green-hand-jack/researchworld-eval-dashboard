"""Superradiance physics for ultralight bosons around Kerr black holes.

Natural units hbar = c = 1 internally; masses in eV, times in seconds.
References: Detweiler 1980; Arvanitaki & Dubovsky 2010 (paper_000) eq. (18)
and Sec. 3.2.1 (bosenova); Stott 2018 (paper_001) for the exclusion logic.
"""
import numpy as np
from math import factorial, pi

HBAR_EV_S = 6.582119569e-16          # eV s
G_MSUN_S = 4.925490947e-6            # G Msun / c^3 [s]
MSUN_EV = 1.11566e66                 # Msun c^2 [eV]
MPL_EV = 1.220890e28                 # G-Planck mass [eV]  (G = 1/Mpl^2)
YR_S = 3.15576e7                     # s
GEV = 1e9


def rg_seconds(M):
    return G_MSUN_S * np.asarray(M, float)


def alpha_of(mu_eV, M):
    """Gravitational fine-structure constant alpha = G M mu / (hbar c)."""
    return mu_eV * rg_seconds(M) / HBAR_EV_S


def horizon(a):
    return 1.0 + np.sqrt(np.clip(1.0 - a * a, 0.0, None))     # r_+/r_g


def a_final(alpha, m):
    """Spin at which m*Omega_H = mu (superradiance saturates): a = 4x/(1+4x^2), x = alpha/m."""
    x = np.asarray(alpha, float) / m
    return np.where(x >= 0.5, 1.0, 4.0 * x / (1.0 + 4.0 * x * x))   # x >= 1/2: never superradiant


def detweiler_C(l, n=0):
    return (2.0 ** (4 * l + 2) * factorial(2 * l + n + 1) / ((l + n + 1) ** (2 * l + 4) * factorial(n))
            * (factorial(l) / (factorial(2 * l) * factorial(2 * l + 1))) ** 2)


def gamma_detweiler(alpha, a, l, m=None, n=0):
    """Growth rate Gamma * r_g of the (l, m, n) level; eq. (18) of paper_000
    (Detweiler's analytic small-alpha result). Negative when not superradiant."""
    m = l if m is None else m
    rp = horizon(a)
    d = m * a - 2.0 * alpha * rp                    # = 2 r_+ (m Omega_H - mu) / r_g
    prod = np.ones(np.broadcast(alpha, a).shape)
    for j in range(1, l + 1):
        prod = prod * (j * j * (1.0 - a * a) + d * d)
    return alpha ** (4 * l + 5) * d * detweiler_C(l, n) * prod


def n_max_bosenova(alpha, M, fa_eV, l, kappa=1.0):
    """Cloud occupation number at which attractive self-interaction triggers the
    bosenova: N ~ 16 pi alpha f_a^2 r_c^2, r_c = l^2 r_g/alpha^2 (paper_000 Sec. 3.2.1)."""
    frg = fa_eV * rg_seconds(M) / HBAR_EV_S           # f_a r_g, dimensionless
    return kappa * 16.0 * pi * alpha * frg ** 2 * l ** 4 / alpha ** 4


def n_total(M, a, alpha, m):
    """Number of bosons that carry the spin excess a - a_final away: Delta J / (m hbar)."""
    return np.clip(a - a_final(alpha, m), 0.0, None) * (np.asarray(M) * MSUN_EV / MPL_EV) ** 2 / m


def excluded(mu_eV, M, a, t_yr, fa_eV=np.inf, levels=(1, 2, 3, 4, 5), kappa=1.0,
             rate=gamma_detweiler, efold_min=0.0):
    """Boolean array over broadcast(M, a): the BH (M, a) is incompatible with a boson of
    mass mu_eV (decay constant fa_eV) because the spin would have been extracted within t_yr.

    Extraction time of the dominant l=m, n=0 level:
        t = [ ln N* + max(N_tot/N_max - 1, 0) ] / Gamma ,  N* = min(N_tot, N_max)
    (exponential growth from one boson to N*, then, when N_max < N_tot, a
    bosenova-limited stage of angular-momentum extraction at rate m Gamma N_max).
    `efold_min` optionally imposes a floor on the number of e-folds.
    """
    M = np.asarray(M, float)
    a = np.asarray(a, float)
    al = alpha_of(mu_eV, M)
    t_rg = t_yr * YR_S / rg_seconds(M)
    out = np.zeros(np.broadcast(M, a, al).shape, bool)
    for l in levels:
        with np.errstate(over="ignore", invalid="ignore"):
            g = rate(np.minimum(al, 50.0), a, l)
        Nt = n_total(M, a, al, l)
        Nm = n_max_bosenova(al, M, fa_eV, l, kappa) if np.isfinite(fa_eV) else np.inf
        Ns = np.minimum(Nt, Nm)
        with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
            efold = np.maximum(np.log(np.maximum(Ns, 1.0)), efold_min) + np.maximum(Nt / Nm - 1.0, 0.0)
            ok = (g > 0) & (Nt > 1.0) & (efold <= g * t_rg)
        out |= ok
    return out


def make_calibrated_rate(table_npz):
    """Detweiler rate times a smooth correction ratio = Gamma_Leaver / Gamma_Detweiler tabulated on
    (x = alpha / alpha_crit, a*) for l = m = 1, 2, 3 (outputs/rate_table.npz, from code/make_rate_table.py).
    Missing nodes (failed roots) are filled by linear interpolation along x; outside the table the ratio is
    clamped to its edge values; l >= 4 keeps the plain Detweiler rate."""
    from scipy.interpolate import RegularGridInterpolator
    T = np.load(table_npz)
    ag, xg = T["a_grid"], T["x_grid"]
    interp = {}
    for l in (1, 2, 3):
        R = T[f"ratio_l{l}"].copy()                       # shape (n_a, n_x)
        if l == 3:
            R[:, xg < 0.2] = np.nan                        # small-alpha l=3 roots are not converged
        for i in range(R.shape[0]):
            ok = np.isfinite(R[i])
            if ok.sum() >= 2:
                R[i, ~ok] = np.interp(xg[~ok], xg[ok], R[i, ok])
        for j in range(R.shape[1]):                        # rows entirely missing -> fill along a
            ok = np.isfinite(R[:, j])
            if ok.sum() >= 1 and (~ok).any():
                R[~ok, j] = np.interp(ag[~ok], ag[ok], R[ok, j])
        interp[l] = RegularGridInterpolator((ag, xg), np.log(R), bounds_error=False, fill_value=None)

    def rate(alpha, a, l, m=None, n=0):
        g = gamma_detweiler(alpha, a, l, m, n)
        if l not in interp:
            return g
        al, aa = np.broadcast_arrays(np.asarray(alpha, float), np.asarray(a, float))
        x = np.clip(al / (l * aa / (2.0 * horizon(aa))), xg[0], xg[-1])
        corr = np.exp(interp[l](np.stack([np.clip(aa, ag[0], ag[-1]), x], axis=-1)))
        return corr * g
    return rate
