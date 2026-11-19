"""Synthetic data-generating processes with known target E[Y].

Each scenario returns (Y_L, f_L, f_U, X_L, X_U) for a labeled sample of size n and an
unlabeled sample of size N, drawn i.i.d. from the same population, together with the
population mean mu = E[Y] (computed once by a large Monte Carlo draw with a fixed seed).

Scenarios
  lin      : m(X) linear in f                        -> PPI++ should be efficient (no gain)
  nl       : m(f) = E[Y|f] nonlinear, f-only         -> gain from nonlinear calibration
  bin      : binary Y, miscalibrated probability f   -> nonlinear calibration, discrete outcome
  xonly    : m(X) depends on a covariate not in f    -> gain only when X is used
  heavy    : nonlinear m with t(3) noise             -> small-sample tail behaviour
"""
import numpy as np

SCENARIOS = ["lin", "nl", "bin", "xonly", "heavy"]
HAS_X = {"lin": False, "nl": False, "bin": False, "xonly": True, "heavy": False}


def _sig(z):
    return 1.0 / (1.0 + np.exp(-z))


def draw(name, rng, size):
    """Return (X, Y, f) for `size` i.i.d. units. X is (size, d)."""
    if name == "lin":
        X = rng.normal(size=(size, 1))
        m = 1.0 + 2.0 * X[:, 0]
        sd = 0.5 * np.sqrt(1 + 0.3 * X[:, 0] ** 2)
        Y = m + sd * rng.normal(size=size)
        f = 0.8 * X[:, 0] + 0.1
    elif name == "nl":
        X = rng.normal(size=(size, 1))
        f = X[:, 0]
        m = np.sin(2 * f) + 0.5 * f
        Y = m + 0.5 * rng.normal(size=size)
    elif name == "bin":
        X = rng.uniform(-2, 2, size=(size, 1))
        p = _sig(3 * np.sin(X[:, 0]))
        Y = (rng.uniform(size=size) < p).astype(float)
        f = _sig(X[:, 0])          # predicted probability, miscalibrated
    elif name == "xonly":
        X = rng.normal(size=(size, 2))
        f = X[:, 0]                # predictor uses only X1
        Y = X[:, 0] + np.sin(2 * X[:, 1]) + 0.5 * rng.normal(size=size)
    elif name == "heavy":
        X = rng.normal(size=(size, 1))
        f = X[:, 0]
        m = np.sin(2 * f) + 0.5 * f
        Y = m + rng.standard_t(3, size=size) * 0.5
    else:
        raise ValueError(name)
    return X, Y, f


_TRUTH_CACHE = {}


def truth(name, size=10_000_000, seed=20260101):
    """Population mean E[Y] via a large Monte Carlo draw (SE ~ 1e-4 * sd)."""
    key = (name, size, seed)
    if key not in _TRUTH_CACHE:
        rng = np.random.default_rng(seed)
        acc = 0.0
        chunk = 2_000_000
        done = 0
        while done < size:
            s = min(chunk, size - done)
            _, Y, _ = draw(name, rng, s)
            acc += Y.sum()
            done += s
        _TRUTH_CACHE[key] = acc / size
    return _TRUTH_CACHE[key]


def sample(name, rng, n, N):
    """Labeled (n) and unlabeled (N) samples, independent i.i.d. from the population."""
    XL, YL, fL = draw(name, rng, n)
    XU, _, fU = draw(name, rng, N)
    return YL, fL, fU, XL, XU
