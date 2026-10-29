"""Black-hole superradiance likelihood for ultralight bosons (core library)."""
import numpy as np
from math import factorial

G_MSUN_S = 4.925490947e-6        # G Msun / c^3 [s]
HBAR_EVS = 6.582119569e-16       # hbar [eV s]
YR = 3.15576e7                   # s
MPL_GEV = 1.220890e19            # Planck mass [GeV]
ALPHA_PER = G_MSUN_S / HBAR_EVS  # alpha = ALPHA_PER * (M/Msun) * (mu/eV)

MODES = [1, 2, 3, 4, 5, 6]       # l = m, n = l+1 (2p, 3d, 4f, 5g, 6h, 7i)

def alpha_of(M, mu):
    return ALPHA_PER * M * mu

def a_crit(alpha, l):
    """Spin below which the (l=m, n=l+1) level is no longer superradiant."""
    n = l + 1
    w = alpha * (1 - alpha**2 / (2 * n**2))
    x = 2 * w / l
    return np.where(x < 1, 2 * x / (1 + x**2), 1.0)

def C_nl(n, l):
    return (2.0**(4*l+1) * factorial(n+l) / (n**(2*l+4) * factorial(n-l-1))
            * (factorial(l) / (factorial(2*l) * factorial(2*l+1)))**2)

def gamma(alpha, a, l):
    """Amplitude superradiance rate Gamma*G*M/c^3 (>0 growth); small-alpha (Detweiler/Baumann) form."""
    n, m = l + 1, l
    rp = 1 + np.sqrt(1 - a**2)
    w = alpha * (1 - alpha**2 / (2 * n**2))
    g = 1.0
    for k in range(1, l + 1):
        g = g * (k**2 * (1 - a**2) + (a * m - 2 * rp * w)**2)
    return 2 * rp * C_nl(n, l) * g * (m * a / (2 * rp) - w) * alpha**(4*l + 5)

def eps_bn(alpha, l, fa_gev):
    """Cloud-to-BH mass ratio at which attractive self-interaction collapses the cloud
    (Arvanitaki & Dubovsky 2011, eq. 48)."""
    return 2 * l**4 / alpha**2 * (fa_gev / MPL_GEV)**2

def prepare(M, a, mu, model='exact'):
    """Per-mode superradiance data for each (mu, sample) pair; independent of age, N_e, f_a.
    Returns list over l of (sup_mask, 2*Gamma [1/(GM/c^3)], eps_req) and the yr-per-unit-time array."""
    M = np.asarray(M)[None, :]; a = np.asarray(a)[None, :]; mu = np.asarray(mu)[:, None]
    al = alpha_of(M, mu) * np.ones_like(a)
    aa = a * np.ones_like(al)
    out = []
    for l in MODES:
        ac = acrit_fast(al, l) if model == 'exact' else a_crit(al, l)
        sup = aa > ac
        g2 = np.zeros(al.shape)
        if sup.any():
            gf = exact_gamma if model == 'exact' else gamma
            g2[sup] = 2 * gf(al[sup], np.minimum(aa[sup], 0.9999), l)
        eps = np.where(sup, al * (aa - ac) / l, 0.0)
        out.append((l, sup & (g2 > 0), g2, eps))
    return out, al

def allowed_from(pre, M, t_yr, fa_gev=np.inf, Ne=100.0):
    modes, al = pre
    t_unit = G_MSUN_S * np.asarray(M)[None, :] / YR
    ok = np.ones(al.shape, bool)
    for l, sup, g2, eps in modes:
        with np.errstate(divide='ignore', invalid='ignore'):
            extra = 0.0 if np.isinf(fa_gev) else np.maximum(eps / eps_bn(al, l, fa_gev) - 1, 0)
            tsd = (Ne + extra) / g2 * t_unit
            ok &= ~(sup & (tsd < t_yr))
    return ok

def allowed(M, a, mu, t_yr, fa_gev=np.inf, Ne=100.0, model='exact'):
    """Boolean array [n_mu, n_samples]: True if BH sample (M,a) is consistent with boson mass mu.
    A BH is inconsistent if some level l=1..6 is superradiant at the observed spin and would
    have extracted the required angular momentum within t_yr."""
    return allowed_from(prepare(M, a, mu, model), M, t_yr, fa_gev, Ne)

def allowed_fraction(M, a, mu, t_yr, fa_gev=np.inf, Ne=100.0, w=None, chunk=50, model='exact'):
    out = np.empty(len(mu))
    for i in range(0, len(mu), chunk):
        ok = allowed(M, a, mu[i:i+chunk], t_yr, fa_gev, Ne, model)
        out[i:i+chunk] = ok.mean(1) if w is None else (ok * w).sum(1) / w.sum()
    return out

def load(name):
    d = np.loadtxt(f'/work/data/{name}_samples.dat')
    return d[:, 0], d[:, 1]


# ---------------------------------------------------------------------------------------------
# "Exact" rates: analytic small-alpha rate multiplied by a correction rho(alpha,a) calibrated on
# a Leaver continued-fraction table (code/leaver.py, code/make_table.py), and the exact real
# frequency omega_R(alpha,a) in the superradiance condition omega_R < m Omega_H.
# ---------------------------------------------------------------------------------------------
import os
from scipy.interpolate import RegularGridInterpolator
from scipy.ndimage import distance_transform_edt

def _g_tilde(al, a, l):
    n, m = l + 1, l
    rp = 1 + np.sqrt(1 - a**2)
    w = al * (1 - al**2 / (2 * n**2))
    g = 1.0
    for k in range(1, l + 1):
        g = g * (k**2 * (1 - a**2) + (a * m - 2 * rp * w)**2)
    return 2 * rp * C_nl(n, l) * g

_TAB = {}
def _load_tab():
    T = np.load(os.path.join(os.path.dirname(__file__), '..', 'outputs', 'leaver_table.npz'))
    for l in MODES:
        a, al, w = T[f'l{l}_a'], T[f'l{l}_al'], T[f'l{l}_w']
        A, AL = np.meshgrid(a, al, indexing='ij')
        n = l + 1
        hyd = AL * (1 - AL**2 / (2 * n**2))
        wr, wi = w[..., 0], w[..., 1]
        rp = 1 + np.sqrt(1 - A**2)
        drive = l * A / (2 * rp) - wr
        with np.errstate(all='ignore'):
            rho = wi / (AL**(4*l+5) * drive * _g_tilde(AL, A, l))
        good = np.isfinite(rho) & (np.abs(wi) > 1e-14) & (drive > 0) & np.isfinite(wr) & (rho > 0.3) & (rho < 300)
        # fill invalid cells: constant extrapolation along alpha within each spin row (rho -> O(1) at small alpha),
        # rows without any valid cell take the nearest valid row
        rho_f = np.where(good, rho, np.nan)
        for i in range(rho_f.shape[0]):
            v = np.nonzero(good[i])[0]
            if len(v):
                j = np.arange(rho_f.shape[1]); k = v[np.abs(j[:, None] - v[None, :]).argmin(1)]
                rho_f[i] = rho[i, k]
        rows = np.nonzero(good.any(1))[0]
        for i in range(rho_f.shape[0]):
            if i not in rows: rho_f[i] = rho_f[rows[np.abs(rows - i).argmin()]]
        wr_ok = np.isfinite(wr) & (np.abs(wr - hyd) < 0.2 * AL)
        idx2 = distance_transform_edt(~wr_ok, return_distances=False, return_indices=True)
        dw = (wr - hyd)[tuple(idx2)]
        _TAB[l] = (RegularGridInterpolator((a, al), np.log(rho_f), bounds_error=False, fill_value=None),
                   RegularGridInterpolator((a, al), dw, bounds_error=False, fill_value=None),
                   (a[0], a[-1], al[0], al[-1]))

def _lookup(al, a, l):
    if not _TAB: _load_tab()
    f_rho, f_dw, (a0, a1, l0, l1) = _TAB[l]
    pts = np.stack(np.broadcast_arrays(np.clip(a, a0, a1), np.clip(al, l0, l1)), -1)
    return np.exp(f_rho(pts)), f_dw(pts)

def exact_omega_r(al, a, l):
    n = l + 1
    _, dw = _lookup(al, a, l)
    return al * (1 - al**2 / (2 * n**2)) + dw

def exact_gamma(al, a, l):
    rho, _ = _lookup(al, a, l)
    rp = 1 + np.sqrt(1 - a**2)
    drive = l * a / (2 * rp) - exact_omega_r(al, a, l)
    return rho * _g_tilde(al, a, l) * drive * al**(4*l + 5)

def exact_acrit(al, l, nit=40):
    if not _TAB: _load_tab()
    """Spin at which omega_R(alpha,a) = m Omega_H(a)."""
    al = np.asarray(al, float)
    lo = np.zeros_like(al); hi = np.ones_like(al) * 0.9999
    f = lambda x: l * x / (2 * (1 + np.sqrt(1 - x**2))) - exact_omega_r(al, x, l)
    n_ = l + 1
    none = (f(hi) <= 0) | (al * (1 - al**2 / (2 * n_**2)) >= l / 2) | (al > _TAB[l][2][3])
    for _ in range(nit):
        mid = 0.5 * (lo + hi)
        pos = f(mid) > 0
        hi = np.where(pos, mid, hi); lo = np.where(pos, lo, mid)
    return np.where(none, 1.0, 0.5 * (lo + hi))


_AC = {}
def acrit_fast(al, l):
    """exact_acrit tabulated on a dense log-alpha grid and interpolated."""
    if l not in _AC:
        g = np.logspace(-3, np.log10(4.0), 3000)
        _AC[l] = (g, exact_acrit(g, l))
    g, v = _AC[l]
    return np.interp(al, g, v, right=1.0)
