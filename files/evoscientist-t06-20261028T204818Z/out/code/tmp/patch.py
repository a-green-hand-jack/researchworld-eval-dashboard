src=open("code/btlib.py").read()
start=src.index("def fit_bt(")
end=src.index("def ranking(")
new='''def _hess_index(tt):
    """Precomputed scatter indices so that H = bincount(idx, coef * W[rep]) (O(T) instead of O(T d^2))."""
    if getattr(tt, "_hidx", None) is not None:
        return tt._hidx
    m = tt.m
    d = m + (1 if tt.use_home else 0)
    a, b, h = tt.a, tt.b, tt.h
    idx = [a * d + a, b * d + b, a * d + b, b * d + a]
    coef = [np.ones_like(h), np.ones_like(h), -np.ones_like(h), -np.ones_like(h)]
    if tt.use_home:
        idx += [a * d + m, m * d + a, b * d + m, m * d + b, np.full_like(a, m * d + m)]
        coef += [h, h, -h, -h, h * h]
    tt._hidx = (np.concatenate(idx), np.concatenate(coef), len(idx), d)
    return tt._hidx


def _eta(tt, th):
    e = th[tt.a] - th[tt.b]
    if tt.use_home:
        e = e + tt.h * th[tt.m]
    return e


def _xt_dot(tt, r):
    """X^T r without forming X."""
    m = tt.m
    d = m + (1 if tt.use_home else 0)
    g = np.bincount(tt.a, weights=r, minlength=d) - np.bincount(tt.b, weights=r, minlength=d)
    if tt.use_home:
        g[m] += float(np.sum(tt.h * r))
    return g


def hessian(tt, W, lam):
    idx, coef, reps, d = _hess_index(tt)
    H = np.bincount(idx, weights=coef * np.tile(W, reps), minlength=d * d).reshape(d, d)
    return H + lam * np.eye(d)


def fit_bt(tt: TypeTable, n=None, lam=0.01, theta0=None, tol=1e-9, maxit=100):
    """Penalised maximum likelihood via damped Newton. Returns Fit."""
    n = tt.n if n is None else n
    y = tt.y
    d = tt.m + (1 if tt.use_home else 0)
    th = np.zeros(d) if theta0 is None else theta0.copy()

    def obj(t):
        eta = _eta(tt, t)
        lp = -np.logaddexp(0.0, -eta)
        lq = -np.logaddexp(0.0, eta)
        return float(np.sum(n * (y * lp + (1 - y) * lq)) - 0.5 * lam * t @ t)

    f = obj(th)
    converged = False
    it = 0
    for it in range(1, maxit + 1):
        p = sigmoid(_eta(tt, th))
        g = _xt_dot(tt, n * (y - p)) - lam * th
        H = hessian(tt, n * p * (1 - p), lam)
        step = np.linalg.solve(H, g)
        t = 1.0
        while True:
            th_new = th + t * step
            f_new = obj(th_new)
            if f_new >= f - 1e-12 * abs(f) or t < 1e-8:
                break
            t *= 0.5
        th, f = th_new, f_new
        if np.max(np.abs(t * step)) < tol:
            converged = True
            break
    p_all = sigmoid(_eta(tt, th))
    H = hessian(tt, n * p_all * (1 - p_all), lam)
    return Fit(theta=th, p=p_all, H=H, n_iter=it, converged=converged)


'''
src=src[:start]+new+src[end:]
src=src.replace('''    c = tt.X @ u
    psi = c * (tt.y - fit.p)''','''    c = _eta(tt, u)
    psi = c * (tt.y - fit.p)''')
src=src.replace('''    return tt.X @ u   # c_t = v^T H^{-1} x_t''','''    return _eta(tt, u)   # c_t = v^T H^{-1} x_t''')
src=src.replace('''    d = tt.X.shape[1]
    v = np.zeros(d)''','''    d = tt.m + (1 if tt.use_home else 0)
    v = np.zeros(d)''')
open("code/btlib.py","w").write(src)
