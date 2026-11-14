"""Offline repetition harness (not used by the RPC entrypoint): coverage/width cells with
Wilson and paired-bootstrap uncertainty, plus a known-truth synthetic generator.

Usage sketch::

    from program import crppi_mean_ci, ppi_plus_plus_mean_ci
    prob = make_synthetic_problem("monotone_miscal", seed=0)
    cell = run_coverage_width_cell(prob["sampler"], prob["truth"], n=200, big_n=5000,
                                   methods={"ppi++": ppi_plus_plus_mean_ci, "crppi": crppi_mean_ci},
                                   n_rep=1000, seed=1001)
"""

import math

import numpy as np


def wilson_interval(successes, trials, z=1.959963984540054):
    """Wilson score interval for a binomial proportion."""
    if trials <= 0:
        return float("nan"), float("nan")
    p = successes / trials
    denom = 1.0 + z * z / trials
    centre = (p + z * z / (2 * trials)) / denom
    half = z * math.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials)) / denom
    return centre - half, centre + half


def paired_bootstrap_ci(diff, n_boot=2000, seed=0, level=0.95):
    """Percentile bootstrap CI for the mean of paired differences."""
    rng = np.random.default_rng(seed)
    diff = np.asarray(diff, dtype=float)
    idx = rng.integers(0, diff.size, size=(n_boot, diff.size))
    means = diff[idx].mean(axis=1)
    tail = (1 - level) / 2
    return float(np.quantile(means, tail)), float(np.quantile(means, 1 - tail))


def make_synthetic_problem(kind="monotone_miscal", seed=0, noise=1.0):
    """Known-truth generators. Returns {"sampler": f(rng, m) -> (Y, Yhat), "truth": float}.

    kinds: calibrated, linear_bias, monotone_miscal, nonmonotone, pure_noise.
    X ~ N(0,1); Y = m(X) + noise * eps; the predictor is a function of X plus noise. The true
    mean is computed by a large Monte Carlo draw with its own seeded generator (error ~1e-3).
    """
    shapes = {
        "calibrated": lambda x: x,
        "linear_bias": lambda x: x,
        "monotone_miscal": lambda x: x,
        "nonmonotone": lambda x: x,
        "pure_noise": lambda x: x,
    }
    if kind not in shapes:
        raise ValueError(f"unknown kind {kind}")

    def mean_fn(x):
        return 1.0 + x + 0.5 * x ** 2 if kind == "nonmonotone" else 1.0 + x

    def predictor(x, rng):
        e = 0.3 * rng.standard_normal(x.shape)
        if kind == "calibrated":
            return mean_fn(x) + 0.0 * e
        if kind == "linear_bias":
            return 0.5 + 0.6 * mean_fn(x) + e
        if kind == "monotone_miscal":
            return np.exp(0.8 * (x + e))
        if kind == "nonmonotone":
            return x + e
        return rng.standard_normal(x.shape)

    def sampler(rng, m):
        x = rng.standard_normal(m)
        y = mean_fn(x) + noise * (1 + 0.5 * (kind == "nonmonotone") * np.abs(x)) * rng.standard_normal(m)
        return y, predictor(x, rng)

    truth_rng = np.random.default_rng(10_000 + seed)
    xs = truth_rng.standard_normal(2_000_000)
    truth = float(np.mean(mean_fn(xs)))  # exact in expectation: E[eps]=0
    return {"sampler": sampler, "truth": truth, "kind": kind}


def run_coverage_width_cell(sampler, truth, n, big_n, methods, n_rep=1000, seed=1001, alpha=0.05,
                            reference="ppi++"):
    """Repeat labeled/unlabeled draws, evaluate each interval method, summarise.

    ``sampler(rng, m)`` returns (Y, Yhat) for m i.i.d. records; ``methods`` maps a name to a
    function f(y, yhat, yhat_unl, alpha) -> (lo, hi) or None (None => classical-failure miss).
    Returns per-method coverage with Wilson CI, mean width, and paired width difference vs
    ``reference`` with a bootstrap CI.
    """
    rng = np.random.default_rng(seed)
    cover = {k: np.zeros(n_rep, dtype=bool) for k in methods}
    width = {k: np.full(n_rep, np.nan) for k in methods}
    for r in range(n_rep):
        y, yh = sampler(rng, n)
        _, yh_unl = sampler(rng, big_n)
        for name, fn in methods.items():
            out = fn(y, yh, yh_unl, alpha)
            if out is None:
                continue
            lo, hi = out
            cover[name][r] = lo <= truth <= hi
            width[name][r] = hi - lo
    result = {}
    for name in methods:
        ok = np.isfinite(width[name])
        k = int(cover[name].sum())
        lo_w, hi_w = wilson_interval(k, n_rep)
        entry = {"coverage": k / n_rep, "coverage_wilson": (lo_w, hi_w),
                 "mean_width": float(np.nanmean(width[name])) if ok.any() else float("nan"),
                 "n_failed": int((~ok).sum())}
        if reference in methods and name != reference:
            both = ok & np.isfinite(width[reference])
            d = np.log(width[name][both] / width[reference][both])
            entry["mean_log_ratio_vs_ref"] = float(d.mean())
            entry["log_ratio_boot_ci"] = paired_bootstrap_ci(d, seed=seed)
        result[name] = entry
    return result
