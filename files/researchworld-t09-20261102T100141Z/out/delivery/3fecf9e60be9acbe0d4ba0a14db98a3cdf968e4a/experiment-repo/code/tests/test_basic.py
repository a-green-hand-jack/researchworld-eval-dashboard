"""Sanity tests (run: python3 -m pytest tests -q  or  python3 tests/test_basic.py)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
from netgate.graphs import make_graph
from netgate.outcomes import Outcome
from netgate import estimators as E
from netgate.sim import run_cell


def _setup(kind="lin_2hop"):
    net = make_graph("sbm", 600, 1, d=8, k=6); E.prep(net)
    out = Outcome(kind=kind, gamma=0.7, gamma2=0.3).setup(net, net.communities(), np.random.default_rng(0))
    return net, out


def test_gate_bruteforce():
    for k in ("lin_frac", "lin_2hop", "lin_count", "sat", "thresh", "pow"):
        net, out = _setup(k)
        one, zero = np.ones(net.n), np.zeros(net.n)
        assert abs(out.gate() - (out.signal(one) - out.signal(zero)).mean()) < 1e-12
    net, out = _setup("lin_frac")           # linear: gate = tau + gamma
    assert abs(out.gate() - 1.7) < 1e-9


def test_exposure_at_extremes():
    net, _ = _setup()
    assert np.allclose(net.W @ np.ones(net.n), 1) and np.allclose(net.W @ np.zeros(net.n), 0)


def test_seed_reproducible():
    spec = dict(graph=dict(kind="er", n=300, d=8), outcome=dict(kind="lin_frac"), design=dict(kind="bernoulli", p=.5),
                ests=["dm", "ols_f"], G=1, R=3)
    a, b = run_cell(spec), run_cell(spec)
    assert np.array_equal(a.est.values, b.est.values)


def test_ols_unbiased_linear():
    spec = dict(graph=dict(kind="er", n=800, d=8), outcome=dict(kind="lin_frac", rho_deg=0, sigma_c=0), design=dict(kind="bernoulli", p=.5),
                ests=["ols_f", "dm"], G=1, R=300)
    df = run_cell(spec); df["err"] = df.est - df.gate
    g = df.groupby("est_name").err
    assert abs(g.mean()["ols_f"]) < 4 * g.std()["ols_f"] / np.sqrt(300)
    assert abs(g.mean()["dm"] + 1.0) < 0.05   # DM estimates tau only (bias = -gamma)


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f(); print("ok", n)
