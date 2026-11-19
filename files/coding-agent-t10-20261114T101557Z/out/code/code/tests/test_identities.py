"""Sanity checks for the estimator identities used in the paper.

Run: python -m pytest -q /work/code/tests   (or python /work/code/tests/test_identities.py)
"""
import sys
import numpy as np
sys.path.insert(0, "/work/code")
import ppi_flex as P


def dgp(rng, n, N):
    # X ~ N(0,1); Y = m(X) + sigma(X) eps, m nonlinear; f = a biased, linear-in-X predictor
    X_L = rng.normal(size=n); X_U = rng.normal(size=N)
    m = lambda x: np.sin(2 * x) + 0.5 * x
    Y_L = m(X_L) + 0.5 * (1 + 0.3 * X_L**2) * rng.normal(size=n)
    f_L = 0.8 * X_L + 0.1
    f_U = 0.8 * X_U + 0.1
    return Y_L, f_L, f_U, X_L, X_U, m


def test_ppi_linear_equals_ppi_pp():
    rng = np.random.default_rng(1)
    Y_L, f_L, f_U, *_ = dgp(rng, 80, 300)
    e1, v1 = P.ppi_pp(Y_L, f_L, f_U)
    e2, v2 = P.ppi_linear(Y_L, f_L, f_U)
    assert np.isclose(e1, e2) and np.isclose(v1, v2), (e1, e2, v1, v2)


def test_ppi_is_special_case_of_lambda1():
    rng = np.random.default_rng(2)
    Y_L, f_L, f_U, *_ = dgp(rng, 50, 200)
    e, v = P.ppi(Y_L, f_L, f_U)
    assert np.isclose(e, f_U.mean() + (Y_L - f_L).mean())
    assert np.isclose(v, f_U.var(ddof=1) / 200 + (Y_L - f_L).var(ddof=1) / 50)


def test_oracle_calibrator_attains_efficient_variance():
    """Oracle m: Monte Carlo variance of the pooled estimator matches [E(Y-m)^2 + a Var(m)]/n."""
    rng = np.random.default_rng(3)
    n, N = 100, 300
    a = n / (n + N)
    ests = []
    for _ in range(4000):
        Y_L, f_L, f_U, X_L, X_U, m = dgp(rng, n, N)
        mL, mU = m(X_L), m(X_U)
        ests.append(Y_L.mean() + (1 - a) * (mU.mean() - mL.mean()))
    mc_var = np.var(ests, ddof=1)
    # population quantities by quadrature-like large MC
    xs = rng.normal(size=2_000_000)
    mx = np.sin(2 * xs) + 0.5 * xs
    sig2 = (0.5 * (1 + 0.3 * xs**2))**2
    V_star = (sig2.mean() + a * mx.var()) / n
    print("MC var", mc_var, "V* (theory)", V_star)
    assert abs(mc_var / V_star - 1) < 0.08


def test_cross_fit_unbiased_linear():
    rng = np.random.default_rng(4)
    ests = []
    for r in range(1500):
        Y_L, f_L, f_U, X_L, X_U, m = dgp(rng, 60, 240)
        e, _, _, _ = P.wald(*P.cf_ppi(Y_L, f_L, f_U, learner="linear", seed=r))
        ests.append(e)
    truth = 0.0 + 0.0  # E[sin(2X)] = 0 and E[0.5X] = 0 for X ~ N(0,1)
    se = np.std(ests, ddof=1) / np.sqrt(len(ests))
    print("cf mean", np.mean(ests), "se", se)
    assert abs(np.mean(ests) - truth) < 4 * se


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("PASS", name)
