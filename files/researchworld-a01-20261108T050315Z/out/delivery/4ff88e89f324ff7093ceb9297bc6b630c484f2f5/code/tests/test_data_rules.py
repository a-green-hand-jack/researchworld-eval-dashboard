import numpy as np, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from mti import data as dt, ordinal as od
import pandas as pd

def test_ollb_mean_of_six_reproduces_average():
    d = pd.read_csv(dt.PROC / "ollb6.csv")
    assert np.abs(d[dt.OLLB_TASKS].mean(axis=1) - d["Average"]).max() < 1e-12

def test_copeland_matches_naive():
    rng = np.random.default_rng(0)
    for M, n in [(7, 4), (30, 5), (40, 6)]:
        X = rng.integers(0, 6, (M, n)).astype(float)       # integer scores: plenty of ties and n/2-ties
        naive = np.array([sum(od.wins(X[j], X[k]).sum() > n / 2 for k in range(M) if k != j) +
                          0.5 * sum(od.wins(X[j], X[k]).sum() == n / 2 for k in range(M) if k != j) for j in range(M)])
        assert np.allclose(od.copeland_scores(X, chunk=8), naive)

def test_standardised_variants():
    X, *_ = dt.load("ollb"); Z = dt.load("ollb_z")[0]; P = dt.load("ollb_pct")[0]
    assert np.allclose(Z.mean(axis=0), 0) and np.allclose(Z.std(axis=0), 1)
    assert P.max() <= 100 and P.min() > 0
    for t in range(6):      # monotone transforms: per-task order preserved
        for V in (Z, P): assert (np.diff(X[np.argsort(V[:, t], kind="stable"), t]) >= -1e-12).all()   # source scores carry 1e-16 float noise
    sd = X.std(axis=0); i = 5
    assert np.allclose(dt.make_cap("gain10", Z, i, "ollb_z"), np.minimum(Z[i] + 10 / sd, (100 - X.mean(axis=0)) / sd))
    assert np.allclose(dt.make_cap("ceil", Z, i, "ollb_z") * sd + X.mean(axis=0), 100)
