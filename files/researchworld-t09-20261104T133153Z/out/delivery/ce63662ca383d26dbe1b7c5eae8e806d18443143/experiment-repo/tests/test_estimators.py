"""Known-answer tests for the estimators and variance estimators in netgate.estimators (run: pytest code/tests -q)."""
import numpy as np
import pytest
import scipy.sparse as sp

from netgate import estimators, graphs
from netgate.outcomes import Outcome

NOISELESS = dict(sigma=0.0, alpha_graph=0.0, alpha_deg=0.0, alpha_iid=0.0)


def small_graph(seed=3):
    return graphs.make("sbm:400,8,10,0.8", seed=seed)


def ctx_for(g, outcome=None, acl=None, **kw):
    outcome = outcome or Outcome(**NOISELESS)
    acl = g.clusters(1.0) if acl is None else acl
    return estimators.make_ctx(g, outcome, acl, **kw)


def design_matrix(g, z, ctx, spec="OLS_f"):
    X = np.column_stack(estimators._cols(spec, estimators.feats(g, z), ctx))
    X1 = np.column_stack(estimators._cols(spec, ctx["F1"], ctx))
    X0 = np.column_stack(estimators._cols(spec, ctx["F0"], ctx))
    return X, (X1 - X0).mean(0)


def test_ols_f_recovers_exact_gate_on_noiseless_linear_world():
    g = small_graph()
    o = Outcome(mech="shape", kind="linear", gamma=2.0, **NOISELESS)
    rng = np.random.default_rng(0)
    w = o.world(g, rng)
    z = (rng.random(g.n) < 0.5).astype(float)
    y = o.Y(g, w, z)
    gate = o.gate(g, w)
    assert gate == pytest.approx(3.0)  # tau + gamma * (h(1) - h(0))
    est = estimators.ols_gate("OLS_f", g, z, y, ctx_for(g, o))["est"]
    assert est == pytest.approx(gate, abs=1e-8)


def test_oracle_recovers_exact_gate_for_concave_spillover_without_noise():
    g = small_graph()
    o = Outcome(mech="shape", kind="concave", gamma=2.0, **NOISELESS)
    rng = np.random.default_rng(1)
    w = o.world(g, rng)
    z = (rng.random(g.n) < 0.5).astype(float)
    est = estimators.ols_gate("ORACLE", g, z, o.Y(g, w, z), ctx_for(g, o))["est"]
    assert est == pytest.approx(o.gate(g, w), abs=1e-8)


def _noisy_fit(seed=5):
    g = small_graph()
    rng = np.random.default_rng(seed)
    z = (rng.random(g.n) < 0.5).astype(float)
    y = rng.standard_normal(g.n) + 0.7 * z + 0.4 * (g.W @ z)
    ctx = ctx_for(g)
    X, c = design_matrix(g, z, ctx)
    return g, z, y, ctx, X, c


def test_hc0_matches_statsmodels_and_closed_form():
    sm = pytest.importorskip("statsmodels.api")
    g, z, y, ctx, X, c = _noisy_fit()
    out = estimators.ols_gate("OLS_f", g, z, y, ctx)
    fit = sm.OLS(y, X).fit(cov_type="HC0")
    assert out["est"] == pytest.approx(float(c @ fit.params), abs=1e-10)
    assert out["se"] == pytest.approx(float(np.sqrt(c @ fit.cov_params() @ c)), rel=1e-9)
    # closed form (X'X)^-1 X' diag(e^2) X (X'X)^-1
    b = np.linalg.solve(X.T @ X, X.T @ y)
    e = y - X @ b
    bread = np.linalg.inv(X.T @ X)
    assert out["se"] == pytest.approx(float(np.sqrt(c @ bread @ ((X * e[:, None] ** 2).T @ X) @ bread @ c)), rel=1e-9)


def test_cluster_robust_matches_statsmodels_without_small_sample_correction():
    sm = pytest.importorskip("statsmodels.api")
    g, z, y, ctx, X, c = _noisy_fit()
    lab = ctx["acl"]
    out = estimators.ols_gate("OLS_f", g, z, y, ctx)
    fit = sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": lab, "use_correction": False})
    assert out["se_cl"] == pytest.approx(float(np.sqrt(c @ fit.cov_params() @ c)), rel=1e-9)


def _hac1_by_hand(A, X, y, c):
    """sum over ordered pairs (i, j) with i = j or an edge between them of (x_i e_i)(x_j e_j)', sandwiched; explicit loops."""
    n = len(y)
    b = np.linalg.solve(X.T @ X, X.T @ y)
    e = y - X @ b
    meat = np.zeros((X.shape[1], X.shape[1]))
    for i in range(n):
        for j in range(n):
            if i == j or A[i, j] != 0:
                meat += np.outer(X[i] * e[i], X[j] * e[j])
    bread = np.linalg.inv(X.T @ X)
    return float(np.sqrt(c @ bread @ meat @ bread @ c))


@pytest.mark.parametrize("shape", ["path", "star"])
def test_graph_hac_one_hop_matches_hand_computation(shape):
    n = 9
    A = np.zeros((n, n))
    if shape == "path":
        for i in range(n - 1):
            A[i, i + 1] = A[i + 1, i] = 1
    else:
        A[0, 1:] = A[1:, 0] = 1
    g = graphs.Graph(shape, sp.csr_matrix(A))
    rng = np.random.default_rng(2)
    z = np.array([1, 0, 1, 1, 0, 0, 1, 0, 1], dtype=float)
    y = rng.standard_normal(n) + 0.5 * z
    ctx = ctx_for(g, acl=np.arange(n))
    X, c = design_matrix(g, z, ctx)
    if np.linalg.matrix_rank(X) < X.shape[1]:
        pytest.skip("degenerate design on this tiny graph")
    out = estimators.ols_gate("OLS_f", g, z, y, ctx)
    assert out["se_hac1"] == pytest.approx(_hac1_by_hand(A, X, y, c), rel=1e-9)


def test_hac1_reduces_to_hc0_on_edgeless_kernel():
    """With a kernel equal to the identity the HAC sandwich is the HC0 sandwich."""
    g, z, y, ctx, X, c = _noisy_fit()
    ctx2 = dict(ctx, K1=sp.identity(g.n).tocsr())
    out = estimators.ols_gate("OLS_f", g, z, y, ctx2)
    assert out["se_hac1"] == pytest.approx(out["se"], rel=1e-9)


def test_block_bootstrap_of_a_mean_matches_the_analytic_block_sd():
    rng = np.random.default_rng(3)
    K, b = 60, 10
    lab = np.repeat(np.arange(K), b)
    y = rng.standard_normal(K)[lab] + 0.3 * rng.standard_normal(K * b)
    X = np.ones((K * b, 1))
    out = estimators.block_bootstrap(X, y, np.array([1.0]), lab, 4000, np.random.default_rng(4))
    block_means = y.reshape(K, b).mean(1)
    analytic = block_means.std(ddof=0) / np.sqrt(K)  # SD of the mean of K resampled equal-size blocks
    assert out["se_boot"] == pytest.approx(analytic, rel=0.06)
    assert out["boot_lo"] < y.mean() < out["boot_hi"]


def test_ridge_with_negligible_penalty_equals_ols_big_on_clean_data():
    g = small_graph()
    o = Outcome(mech="shape", kind="linear", gamma=2.0, **NOISELESS)
    rng = np.random.default_rng(6)
    w = o.world(g, rng)
    z = (rng.random(g.n) < 0.5).astype(float)
    y = o.Y(g, w, z)
    ctx = ctx_for(g, o)
    r = estimators.ridge_big(g, z, y, ctx)["est"]
    assert r == pytest.approx(o.gate(g, w), abs=0.05)
