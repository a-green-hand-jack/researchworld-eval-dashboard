"""Exact (Leaver / Dolan continued fraction) quasi-bound-state frequencies of a massive scalar
on Kerr, units G=c=M=1.  Used to validate and calibrate the analytic small-alpha rates."""
import numpy as np
from explore_rec import coeffs_fun

def ang_eig(l, m, c2, nb=12):
    """Oblate spheroidal eigenvalue A (-> l(l+1) as c2->0) of
       (1/sin)(sin S')' + [c2 cos^2 - m^2/sin^2 + A] S = 0, via Legendre basis."""
    ls = np.arange(max(abs(m), 0), max(abs(m), 0) + nb + 1)
    n = len(ls)
    Al = np.sqrt(((ls + 1.0)**2 - m**2) / ((2*ls + 1.0) * (2*ls + 3.0)))
    C = np.zeros((n, n))
    for i in range(n):
        lo = ls[i]
        a_lo = Al[i]; a_lm = np.sqrt((lo**2 - m**2) / ((2*lo - 1.0) * (2*lo + 1.0))) if lo > abs(m) else 0.0
        C[i, i] = a_lo**2 + a_lm**2
        if i + 2 < n: C[i, i+2] = C[i+2, i] = Al[i] * Al[i+1]
    # A S = -(c2 cos^2) ... : (L-op) eigenvalue: A = l(l+1) - c2 <cos^2> in perturbation => matrix
    H = np.diag(ls * (ls + 1.0)) - c2 * C
    ev = np.linalg.eigvals(H.astype(complex))
    return ev[np.argmin(abs(ev - l*(l+1)))]

def residual(w, a, mu, l, m, N=800):
    c2 = a*a*(w*w - mu*mu)
    A = ang_eig(l, m, c2)
    f = coeffs_fun(a, w, mu, m, A)
    us = np.array([0.1, 0.25, 0.4, 0.55, 0.7])
    vals = np.array([f(u) for u in us])  # (5,3)
    sc = (1 - us)**2
    Q = []
    for k in range(3):
        Q.append(np.polyfit(us, vals[:, k]*sc, 4)[::-1])  # ascending powers 0..4
    Q2, Q1, Q0 = Q
    p = np.arange(0, N + 1, dtype=float)
    Ap = Q2[2]*p*(p-1) + Q1[1]*p + Q0[0]
    Bp = Q2[3]*(p-1)*(p-2) + Q1[2]*(p-1) + Q0[1]
    Cp = Q2[4]*(p-2)*(p-3) + Q1[3]*(p-2) + Q0[2]
    rho = 0j
    for pp in range(N, 1, -1):
        rho = -Cp[pp] / (Ap[pp]*rho + Bp[pp])   # rho_{pp-1}
    # rho now = rho_1
    return (Ap[1]*rho + Bp[1]) / abs(Bp[1]), Ap[0]

def solve(a, mu, l, m=None, N=800, w0=None):
    m = l if m is None else m
    n = l + 1
    if w0 is None:
        al = mu
        from sr import gamma
        g = float(gamma(al, a, l))
        w0 = mu*(1 - al**2/(2*n**2)) + 1j*g
    from scipy.optimize import root
    def fun(x):
        w = x[0] + 1j*x[1]*1e-8
        r, _ = residual(w, a, mu, l, m, N)
        return [r.real, r.imag]
    # secant on complex plane
    w1 = w0; w2 = w0*(1 + 1e-6) + 1e-9j
    f1, _ = residual(w1, a, mu, l, m, N); f2, _ = residual(w2, a, mu, l, m, N)
    for it in range(60):
        w3 = w2 - f2*(w2 - w1)/(f2 - f1)
        w1, f1 = w2, f2
        w2 = w3
        f2, _ = residual(w2, a, mu, l, m, N)
        if abs(w2 - w1) < 1e-15: break
    return w2
if __name__ == '__main__':
    import time
    t = time.time()
    f = coeffs_fun
    r, A0 = residual(0.1*(1-0.1**2/8)+0j, 0.9, 0.1, 1, 1)
    print('A0 (should be ~0):', A0, 'res', r)
    for al, a in [(0.1, 0.9), (0.2, 0.9), (0.4, 0.99), (0.3, 0.99)]:
        w = solve(a, al, 1)
        from sr import gamma
        print(al, a, 'w=', w, 'num Gamma', w.imag, 'analytic', float(gamma(al, a, 1)), time.time()-t)
