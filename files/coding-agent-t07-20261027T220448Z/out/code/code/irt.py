"""Multidimensional 2PL IRT (logistic matrix factorisation), fitted with L-BFGS on source models, and batched MAP
ability inference for target models from a coreset."""
import numpy as np
from scipy.optimize import minimize


def _sig(x):
    return 0.5 * (1.0 + np.tanh(0.5 * x))


def fit_irt(Y, d, reg_a=1.0, reg_b=0.1, reg_t=1.0, seed=0, maxiter=150):
    """P(y_ji=1)=sigmoid(theta_j . a_i + b_i). Y: [m x N] in {0,1}. Returns dict(A [N x d], b [N], theta [m x d])."""
    rng = np.random.default_rng(seed)
    m, N = Y.shape
    Y = Y.astype(np.float32)
    p0 = np.clip(Y.mean(0), 0.02, 0.98)
    b0 = np.log(p0 / (1 - p0))
    x0 = np.concatenate([(0.1 * rng.standard_normal((m, d))).ravel(), (0.1 * rng.standard_normal((N, d))).ravel(), b0])

    def unpack(x):
        th = x[: m * d].reshape(m, d)
        A = x[m * d: m * d + N * d].reshape(N, d)
        b = x[m * d + N * d:]
        return th, A, b

    def f(x):
        th, A, b = unpack(x)
        z = (th.astype(np.float32) @ A.T.astype(np.float32)) + b.astype(np.float32)[None]
        p = _sig(z)
        # BCE = softplus(z) - y z
        loss = np.sum(np.logaddexp(0, z) - Y * z, dtype=np.float64)
        loss += 0.5 * reg_t * np.sum(th ** 2) + 0.5 * reg_a * np.sum(A ** 2) + 0.5 * reg_b * np.sum((b - b0) ** 2)
        R = (p - Y)
        gth = R @ A.astype(np.float32) + reg_t * th
        gA = R.T @ th.astype(np.float32) + reg_a * A
        gb = R.sum(0) + reg_b * (b - b0)
        g = np.concatenate([gth.ravel(), gA.ravel(), gb]).astype(np.float64)
        return loss, g

    res = minimize(f, x0, jac=True, method="L-BFGS-B", options=dict(maxiter=maxiter, maxcor=20))
    th, A, b = unpack(res.x)
    return dict(A=A.astype(np.float64), b=b.astype(np.float64), theta=th, d=d, loss=res.fun)


def infer_theta(A_C, b_C, Yc, prior_var=4.0, iters=25, w=None):
    """Batched MAP ability for T targets. A_C [n x d], b_C [n], Yc [T x n]. w: optional item weights [n] (<=1 scale)."""
    T, n = Yc.shape
    d = A_C.shape[1]
    th = np.zeros((T, d))
    w = np.ones(n) if w is None else w
    for _ in range(iters):
        p = _sig(th @ A_C.T + b_C[None])
        g = ((Yc - p) * w[None]) @ A_C - th / prior_var
        W = p * (1 - p) * w[None]
        H = np.einsum("tn,nd,ne->tde", W, A_C, A_C) + np.eye(d)[None] / prior_var
        step = np.linalg.solve(H, g[..., None])[..., 0]
        step = np.clip(step, -2, 2)
        th = th + step
        if np.abs(step).max() < 1e-5:
            break
    return th


def predict_probs(th, A, b):
    return _sig(th @ A.T + b[None])


def platt(zc, Yc, lam=1.0, iters=20, lam_c=None):
    """Per-target recalibration y ~ sigmoid(s*z + c), ridge towards (s,c)=(1,0). zc,Yc: [T x n]. Returns s,c [T]."""
    T, n = zc.shape
    s = np.ones(T); c = np.zeros(T)
    lam_c = lam if lam_c is None else lam_c
    for _ in range(iters):
        p = _sig(s[:, None] * zc + c[:, None])
        g0 = ((Yc - p) * zc).sum(1) - lam * (s - 1)
        g1 = (Yc - p).sum(1) - lam_c * c
        w = p * (1 - p)
        h00 = (w * zc * zc).sum(1) + lam; h01 = (w * zc).sum(1); h11 = w.sum(1) + lam_c
        det = h00 * h11 - h01 ** 2
        ds = (h11 * g0 - h01 * g1) / det; dc = (-h01 * g0 + h00 * g1) / det
        s = s + np.clip(ds, -1, 1); c = c + np.clip(dc, -1, 1)
    return s, c
