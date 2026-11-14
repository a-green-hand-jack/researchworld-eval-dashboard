"""Resampling experiments on the ppi-python example datasets (ppi-python==0.2.3 data)."""
import os
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from common import run_reps, summarize, asym_variances, theory_ratio

BASE_SEED = 20261112
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
DATASETS = ["galaxies", "forest", "alphafold", "gene_expression", "census_income", "census_healthcare",
            "census_education", "plankton", "ballots"]
SMALL = {"forest", "ballots"}


def load(name):
    d = np.load(os.path.join(DATA, f"{name}.npz"))
    return d["Y"].astype(float), d["Yhat"].astype(float), (d["X"].astype(float) if "X" in d.files else None)


def oracle_cond_moments(Y, F, X=None, seed=0):
    """Estimate g(.) = E[Y|f] (or E[Y|f,X]) and EV = E Var(Y|.) on the pool using 10-fold
    cross-fitted gradient boosting (honest residuals -> EV slightly over-estimated, headroom conservative).
    Discrete predictions (<=8 values): exact group means."""
    A = F[:, None] if X is None else np.column_stack([F, X])
    if X is None and len(np.unique(F)) <= 8:
        g = np.zeros_like(Y)
        for v in np.unique(F):
            g[F == v] = Y[F == v].mean()
        return g
    rng = np.random.default_rng(seed)
    fold = rng.permutation(len(Y)) % 10
    g = np.zeros_like(Y)
    for k in range(10):
        m = HistGradientBoostingRegressor(max_depth=3, max_iter=200, learning_rate=0.1,
                                          min_samples_leaf=50, random_state=0).fit(A[fold != k], Y[fold != k])
        g[fold == k] = m.predict(A[fold == k])
    return g


def theory_real(Y, F, n, N, g_cf):
    """Population asymptotic variances.  EV from cross-fitted residuals; Var(g) := Var(Y) - EV."""
    EV = np.mean((Y - g_cf) ** 2)
    varY = Y.var()
    g = Y.mean() + (g_cf - g_cf.mean()) * np.sqrt(max(varY - EV, 0) / g_cf.var())  # rescale so Var(g)=VarY-EV
    # linear / spline oracles need (f, g) pairs: use g_cf shape for covariances with f,
    # but set the marginal variance of g consistently
    return asym_variances(g, np.full(len(Y), EV), F, n, N)


def cached_oracle(name):
    p = os.path.join(DATA, f"oracle_{name}.npy")
    if os.path.exists(p):
        return np.load(p)
    Y, F, _ = load(name)
    g = oracle_cond_moments(Y, F)
    np.save(p, g)
    return g


def one_config(cid, name, n, N, R):
    Y, F, _ = load(name)
    pool = len(Y)
    truth = Y.mean()
    seed = int(np.random.SeedSequence([BASE_SEED, cid]).generate_state(1)[0])

    def draw(rng):
        iL = rng.integers(0, pool, n)
        iU = rng.integers(0, pool, N)
        return Y[iL], F[iL], F[iU]
    th, se = run_reps(draw, truth, R, seed)
    rows = summarize(th, se, truth)
    g_cf = cached_oracle(name)
    tr = theory_ratio(theory_real(Y, F, n, N, g_cf))
    for r in rows:
        r.update(dataset=name, n=n, N=N, theory_ratio=tr.get(r["method"], np.nan), theory_ratio_eff=tr["efficient"])
    return rows
