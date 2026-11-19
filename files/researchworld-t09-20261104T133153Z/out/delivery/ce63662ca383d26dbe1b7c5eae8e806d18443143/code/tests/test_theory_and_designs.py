"""Closed-form bias against simulation, exact exposure probabilities against Monte Carlo, graph generators, determinism."""
import numpy as np
import pytest

from netgate import designs, estimators, graphs
from netgate.outcomes import Outcome
from netgate.runner import run_cell

NOISELESS = dict(sigma=0.0, alpha_graph=0.0, alpha_deg=0.0, alpha_iid=0.0)


def test_closed_form_bias_matches_simulation_on_one_noiseless_cell():
    from theory_bias import predict
    g = graphs.make("er:3000,20", seed=1)
    o = Outcome(mech="shape", kind="concave", gamma=2.0, **NOISELESS)
    rng = np.random.default_rng(0)
    w = o.world(g, rng)
    gate = o.gate(g, w)
    ctx = estimators.make_ctx(g, o, g.clusters(1.0), hac=False)
    errs = []
    for _ in range(150):
        z = (rng.random(g.n) < 0.5).astype(float)
        errs.append(estimators.ols_gate("OLS_f", g, z, o.Y(g, w, z), ctx)["est"] - gate)
    errs = np.array(errs)
    pred, _ = predict(g, "concave", None, 0.5, gamma=2.0)
    se = errs.std(ddof=1) / np.sqrt(len(errs))
    assert abs(errs.mean() - pred) < 3 * se + 0.01
    assert pred < -0.3  # concave spillover: the linear exposure regression understates the effect


def test_bernoulli_full_exposure_probability_is_exact():
    g = graphs.make("er:300,6", seed=2)
    D = designs.Bernoulli(0.5)
    p1, p0 = D.full_exposure_prob(g)
    rng = np.random.default_rng(0)
    N, hit1 = 20000, np.zeros(g.n)
    for _ in range(N):
        z = D.draw(g, rng)
        hit1 += (z == 1) & (g.A @ z == g.deg)
    assert np.abs(hit1 / N - p1).max() < 5 * np.sqrt(0.25 / N) + 1e-3 or np.abs(hit1 / N - p1).max() < 0.01


@pytest.mark.parametrize("kappa", [0.75, 1.0])
def test_cluster_kappa_exposure_probability_matches_monte_carlo(kappa):
    g = graphs.make("sbm:400,10,8,0.7", seed=1)
    D = designs.Cluster(g.clusters(1.0), 0.5)
    pi1, pi0 = D.kappa_exposure_prob(g, kappa)
    rng = np.random.default_rng(1)
    N = 6000
    e1, e0 = np.zeros(g.n), np.zeros(g.n)
    for _ in range(N):
        z = D.draw(g, rng)
        f = g.W @ z
        e1 += (z == 1) & (f >= kappa - 1e-12)
        e0 += (z == 0) & (f <= 1 - kappa + 1e-12)
    tol = 4.5 * np.sqrt(0.25 / N)
    assert np.abs(e1 / N - pi1).max() < tol and np.abs(e0 / N - pi0).max() < tol
    if kappa == 1.0:  # kappa = 1 is the full-exposure probability p^k
        p1, p0 = D.full_exposure_prob(g)
        assert np.allclose(pi1, p1) and np.allclose(pi0, p0)


def test_graph_generators_after_the_freeze():
    reg = graphs.make("reg:500,10", seed=1)
    assert reg.deg.min() == reg.deg.max() == 10
    ba = graphs.ba(800, 5, seed=1)
    cm = graphs.make("cmba:800,5", seed=1)
    assert abs(cm.mean_deg - ba.mean_deg) < 0.8 and abs(cm.deg.max() - ba.deg.max()) < 0.5 * ba.deg.max()
    pl = graphs.make("pl:2000,2.5,12", seed=1)
    assert 9 < pl.mean_deg < 12.5 and pl.deg.max() > 5 * pl.mean_deg


def test_run_cell_is_deterministic_and_paired_across_estimator_sets():
    cfg = dict(graph="sbm:300,6,8,0.8", design="bern:0.5", outcome=dict(mech="shape", kind="concave", gamma=2.0), worlds=2, reps=4, tag="t", seed=77, hajek=False)
    a = run_cell({**cfg, "specs": ["OLS_f"]})
    b = run_cell({**cfg, "specs": ["OLS_f", "OLS_zf"], "no_acl": True, "hac": False})
    c = run_cell({**cfg, "specs": ["OLS_f"]})
    pa = a[a.est_name == "OLS_f"].est.values
    assert np.array_equal(pa, c[c.est_name == "OLS_f"].est.values)
    assert np.allclose(pa, b[b.est_name == "OLS_f"].est.values)  # same worlds and assignments whatever else is computed
    assert np.array_equal(a.gate.values[:4], b.gate.values[:4])


def test_regular_graph_with_degree_baseline_has_no_nan():
    g = graphs.make("reg:200,6", seed=1)
    w = Outcome(alpha_deg=0.5).world(g, np.random.default_rng(0))
    assert np.isfinite(w["base"]).all()
