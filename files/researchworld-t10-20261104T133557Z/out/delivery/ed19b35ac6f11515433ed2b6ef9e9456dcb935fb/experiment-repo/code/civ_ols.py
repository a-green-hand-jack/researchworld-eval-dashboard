"""OLS-coefficient intervals with vector-valued control variates (labeled-fit, cross-fitted).

theta_hat_j = beta_cl,j + lam_j' (Gbar_u - Gbar_l); lam_j is the variance-minimising row for coordinate j
(closed form, plug-in), G_i a user-chosen vector of control variates built from (x_i, f_i).
beta_cl is OLS on the labeled sample.  Variance = Var_l(r_j - lam_j'G)/n + lam_j' Cov_u(G) lam_j / N,
with r_i = (H_l^{-1} x_i (y_i - x_i' beta_cl))_j the labeled influence function.
"""
import numpy as np
from scipy.stats import norm
from civ import LEARNERS, COLS

Z = norm.ppf(0.975)


def _influence(X, y, H):
    """Labeled OLS and its influence functions, normalised by the (pooled) Gram matrix H."""
    beta = np.linalg.solve(X.T @ X / len(y), X.T @ y / len(y))
    R = (X * (y - X @ beta)[:, None]) @ np.linalg.inv(H).T       # n x d
    return beta, R


def cv_adjust(R, G_l, G_u, ridge=1e-8):
    """Return (shift, se) per coordinate; R is n x d labeled influence, G_* control variates."""
    n, N = R.shape[0], G_u.shape[0]
    d = R.shape[1]
    G_all = np.vstack([G_l, G_u])
    mu_all = G_all.mean(0)
    Sg = np.cov(G_all, rowvar=False, ddof=0).reshape(G_all.shape[1], -1) * (1 + n / N)
    Sg = Sg + ridge * np.trace(Sg) / Sg.shape[0] * np.eye(Sg.shape[0])
    Gc = G_l - G_l.mean(0)
    shift, se = np.empty(d), np.empty(d)
    for j in range(d):
        c = (Gc * (R[:, j] - R[:, j].mean())[:, None]).mean(0)
        lam = np.linalg.solve(Sg, c)
        shift[j] = lam @ (G_u.mean(0) - G_l.mean(0))
        se[j] = np.sqrt((R[:, j] - G_l @ lam).var(ddof=1) / n + lam @ np.atleast_2d(np.cov(G_u, rowvar=False)) @ lam / N)
    return shift, se


def crossfit_m(X_l, f_l, y_l, X_u, f_u, learner, K=5, rng=None):
    n, N = len(y_l), len(f_u)
    Zl, Zu = np.column_stack([f_l, X_l]), np.column_stack([f_u, X_u])
    cols = COLS[learner]
    if cols is not None: Zl, Zu = Zl[:, cols], Zu[:, cols]
    rng = rng or np.random.default_rng(0)
    m_l, m_u = np.empty(n), np.zeros(N)
    for idx in np.array_split(rng.permutation(n), K):
        tr = np.setdiff1d(np.arange(n), idx, assume_unique=True)
        mdl = LEARNERS[learner]().fit(Zl[tr], y_l[tr])
        m_l[idx] = mdl.predict(Zl[idx]); m_u += mdl.predict(Zu) / K
    return m_l, m_u


def ols_intervals(X_l, y_l, f_l, X_u, f_u, learners=("lin_fX", "gbm_fX"), K=5, rng=None):
    """dict name -> (theta (d,), halfwidth (d,)).

    Control variates are G_i = H^{-1} x_i (m_i - x_i' beta_cl), the efficient-influence structure with
    imputation m_i (f_i, or a cross-fitted fit of E[Y|f,X]).  `*_coord` lets coordinate j use only G_j
    (PPI++ with coord=j); `*_full` lets it use all d components.  H is the Gram matrix of ALL x (x is
    observed for unlabeled points too).
    """
    n, d = len(y_l), X_l.shape[1]
    H = np.vstack([X_l, X_u]); H = H.T @ H / len(H)
    Hinv = np.linalg.inv(H)
    beta, R = _influence(X_l, y_l, H)
    out = {"classical": (beta, Z * np.sqrt(R.var(0, ddof=1) / n))}

    def G(X, m): return (X * (m - X @ beta)[:, None]) @ Hinv.T

    ms = {"f": (f_l, f_u)}
    for L in learners: ms["cf_" + L] = crossfit_m(X_l, f_l, y_l, X_u, f_u, L, K, rng)
    for name, (m_l, m_u) in ms.items():
        Gl, Gu = G(X_l, m_l), G(X_u, m_u)
        s, se = cv_adjust(R, Gl, Gu); out[f"cv_{name}_full"] = (beta + s, Z * se)
        if name == "f":
            th, hw = np.empty(d), np.empty(d)
            for j in range(d):
                s, se = cv_adjust(R, Gl[:, [j]], Gu[:, [j]]); th[j], hw[j] = beta[j] + s[j], Z * se[j]
            out["cv_f_coord"] = (th, hw)
    return out
