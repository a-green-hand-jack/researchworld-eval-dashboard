"""Numerical growth rates of Kerr massive-scalar bound states (Leaver continued fraction).

Independent check of the analytic Detweiler rate used in sr.py. The three-term recurrence
was derived symbolically (see derive_leaver.py), for the radial equation (G = M = 1)
   Delta d/dr(Delta dR/dr) + [K^2 - Delta (mu^2 r^2 + lambda)] R = 0,
   R = (r-r+)^{-i sigma} (r-r-)^{i sigma + chi - 1} exp(q r) sum_n a_n [(r-r+)/(r-r-)]^n,
   q = sqrt(mu^2-w^2), chi = (mu^2-2w^2)/q, sigma = (2 r+ w - a m)/(r+ - r-),
following Leaver (1985) and Dolan (2007). Angular eigenvalue: spin-0 spheroidal
A_lm(c^2), c^2 = a^2 (w^2-mu^2), by diagonalisation in the Legendre basis.
"""
import os, pickle
import numpy as np
import mpmath as mp
import sympy as sp

mp.mp.dps = 40
_x, _n = sp.symbols("x n")
_rp, _rm, _w, _mu, _m, _a, _lam, _q, _A, _B = sp.symbols("rp rm w mu m a lam q A B")
_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leaver_coef.pkl")
_co = pickle.load(open(_FILE, "rb"))
_fs = [sp.lambdify((_n, _rp, _rm, _w, _mu, _m, _a, _lam, _q, _A, _B), c, "mpmath") for c in _co]


def _quad_coeffs(args):
    """Return [c0,c1,c2] each as (p0,p1,p2) with c_j(n)=p0+p1 n+p2 n^2."""
    vals = []
    for nn in (0, 1, 2):
        cur = [f(nn, *args) for f in _fs][::-1]               # highest power first
        for _ in range(8):                                     # numerator = (1-x)^8 * quadratic
            new = [cur[0]]
            for c in cur[1:-1]:
                new.append(c + new[-1])
            cur = new
        vals.append(cur[::-1])                                 # [c0, c1, c2] at this n
    out = []
    for j in range(3):
        y0, y1, y2 = (vals[i][j] for i in range(3))
        p2 = (y2 - 2 * y1 + y0) / 2
        p1 = y1 - y0 - p2
        out.append((y0, p1, p2))
    return out


def angular_A(l, m, c2, size=14):
    """Spin-0 spheroidal eigenvalue A_lm(c^2) (c^2 = a^2 (w^2 - mu^2)); A S = L^2 S - c^2 cos^2(theta) S.
    Matrix diagonalised in multiprecision (growth rates can be ~1e-16 of Re w, so double precision is not enough)."""
    ls = [abs(m) + i for i in range(size)]
    def c2diag(L):
        return mp.mpf((L + 1) ** 2 - m ** 2) / ((2 * L + 1) * (2 * L + 3)) + mp.mpf(L ** 2 - m ** 2) / ((2 * L - 1) * (2 * L + 1))
    def c2off(L):
        return mp.sqrt(mp.mpf(((L + 1) ** 2 - m ** 2) * ((L + 2) ** 2 - m ** 2))) / ((2 * L + 3) * mp.sqrt(mp.mpf((2 * L + 1) * (2 * L + 5))))
    Mx = mp.zeros(size, size)
    for i, L in enumerate(ls):
        Mx[i, i] = L * (L + 1) - c2 * c2diag(L)
        if i + 2 < size:
            Mx[i, i + 2] = -c2 * c2off(L); Mx[i + 2, i] = -c2 * c2off(L)
    ev = mp.eig(Mx, left=False, right=False)
    t = l * (l + 1)
    return min(ev, key=lambda e: abs(e - t))


def cf_residual(w, mu, a, l, m, depth=400):
    w = mp.mpc(w)
    b = mp.sqrt(1 - a * a); rp, rm = 1 + b, 1 - b
    q = mp.sqrt(mu ** 2 - w ** 2)
    if q.real > 0:                      # decaying bound state: exp(q r), Re q < 0
        q = -q
    chi = (mu ** 2 - 2 * w ** 2) / q
    sig = (2 * rp * w - a * m) / (rp - rm)
    c2 = a * a * (w ** 2 - mu ** 2)
    A = angular_A(l, m, c2)
    lam = A + a * a * w ** 2 - 2 * a * m * w
    co = _quad_coeffs((rp, rm, w, mu, m, a, lam, q, -1j * sig, 1j * sig + chi - 1))
    c = lambda j, N: co[j][0] + co[j][1] * N + co[j][2] * N * N
    # alpha'_N = c0(N+1), beta'_N = c1(N), gamma'_N = c2(N-1)
    # note: alpha'_{N-1} gamma'_N = c0(N) * c2(N-1)
    t = mp.mpc(0)
    for N in range(depth, 0, -1):
        t = c(0, N) * c(2, N - 1) / (c(1, N) - t)
    return c(1, 0) - t


def growth_rate(alpha, a, l=1, m=1, n=0, depth=None):
    """Im(omega) in units of 1/(G M) for mu = alpha/(G M)."""
    mu = mp.mpf(alpha)
    depth = depth or int(max(600, 80.0 / alpha))      # continued-fraction depth must grow ~1/alpha
    from sr import gamma_detweiler
    g0 = float(gamma_detweiler(alpha, a, l, m, n))
    w0 = mu * (1 - mu ** 2 / (2 * (l + n + 1) ** 2)) + 1j * g0
    f = lambda w: cf_residual(w, mu, mp.mpf(a), l, m, depth)
    root = mp.findroot(f, (w0, w0 * (1 + mp.mpf('1e-4'))), solver="secant", tol=1e-30, maxsteps=60)
    return root
