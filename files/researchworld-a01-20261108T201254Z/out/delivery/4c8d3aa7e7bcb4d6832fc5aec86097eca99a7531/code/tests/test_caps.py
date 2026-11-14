"""Cap scenarios of src/mti/data.py (request #6.1): composition subsets and the target-dependent caps."""
import pathlib, sys
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from mti import data as dt


def test_pair_subsets_partition():
    n = {s: len(dt.empirical_pairs(s)[2]) for s in ("all", "chat", "nochat")}
    assert n["chat"] + n["nochat"] == n["all"] == 540 and n["chat"] == 154
    assert len(dt.empirical_pairs("nochatname")[2]) == 207


def test_caps_are_between_score_and_100():
    X, names, tasks, _ = dt.load("ollb")
    for sc in ("emp95", "emp95_nochat", "emp95_nochatname", "emp95_chat", "empfrac95", "empfrac95_nochat", "head0.25", "gain10", "ceil"):
        for i in (0, 10, 2000):
            c = dt.make_cap(sc, X, i)
            assert (c >= X[i] - 1e-12).all() and (c <= 100 + 1e-12).all(), sc


def test_head_fraction_and_default_unchanged():
    X, *_ = dt.load("ollb")
    assert np.allclose(dt.make_cap("head0.25", X, 5), X[5] + 0.25 * (100 - X[5]))
    # plain emp95 is the all-pairs q95 gain, as before the subset argument existed
    hq, n = dt.empirical_gain_caps(95)
    assert n == 540 and np.allclose(dt.make_cap("emp95", X, 5), np.minimum(X[5] + np.maximum(hq, 0), 100))
    assert np.allclose(dt.make_cap("emp95", X, 5), dt.make_cap("emp95_all", X, 5))
