"""Offline repetition harness (not used by the RPC entrypoint): coverage/width cells with
Wilson and paired-bootstrap uncertainty, a known-truth synthetic generator, real ppi_py
example datasets, and ablations of the label-free basis PPI method.

Usage sketch::

    python harness.py --mode synthetic --n_rep 500 --out synth.json
    python harness.py --mode real --data_dir ./data --n_rep 500 --out real.json

or from Python::

    prob = make_synthetic_problem("monotone_miscal", seed=0)
    cell = run_coverage_width_cell(prob["sampler"], prob["truth"], n=200, big_n=5000,
                                   methods=default_methods(), n_rep=500, seed=1001)
    abl = run_ablation(prob["sampler"], prob["truth"], n=200, big_n=5000, n_rep=500, seed=1001)
"""

import argparse
import json
import math
from functools import partial

import numpy as np

from program import (basis_press_ppi_ci, classical_ci, crppi_mean_ci, ppi_mean_ci,
                     ppi_plus_plus_mean_ci, stratified_ppi_mean_ci)


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


def _sigmoid(v):
    return 1.0 / (1.0 + np.exp(-v))


SYNTHETIC_KINDS = ("calibrated", "linear_bias", "monotone_miscal", "nonmonotone", "pure_noise",
                   "sine_miscal", "binary_calibrated", "binary_miscal", "binary_noise")


def make_synthetic_problem(kind="monotone_miscal", seed=0, noise=1.0):
    """Known-truth generators. Returns {"sampler": f(rng, m) -> (Y, Yhat), "truth": float}.

    X ~ N(0,1); Y = m(X) + noise * eps (continuous kinds) or Y ~ Bernoulli(m(X)) (binary kinds);
    the predictor is a function of X plus noise. kinds:
      calibrated        Yhat = E[Y|X]                       (PPI++ already near-efficient)
      linear_bias       Yhat = affine(E[Y|X]) + noise        (linearly calibrated)
      monotone_miscal   Yhat = exp(0.8 (X + e))              (monotone nonlinear miscalibration)
      nonmonotone       quadratic mean, Yhat = X + e         (E[Y|Yhat] nonlinear, heteroscedastic)
      sine_miscal       E[Y|X] = 1 + sin(2X), Yhat = X + e   (non-monotone E[Y|Yhat])
      pure_noise        Yhat independent of Y                (no gain possible)
      binary_*          Bernoulli outcome with calibrated / miscalibrated / noise score
    The true mean is computed by a large Monte Carlo draw with its own seeded generator.
    """
    if kind not in SYNTHETIC_KINDS:
        raise ValueError(f"unknown kind {kind}")
    binary = kind.startswith("binary")

    def mean_fn(x):
        if kind == "nonmonotone":
            return 1.0 + x + 0.5 * x ** 2
        if kind == "sine_miscal":
            return 1.0 + np.sin(2.0 * x)
        if binary:
            return _sigmoid(1.5 * x - 0.5)
        return 1.0 + x

    def predictor(x, rng):
        e = 0.3 * rng.standard_normal(x.shape)
        if kind == "calibrated":
            return mean_fn(x)
        if kind == "linear_bias":
            return 0.5 + 0.6 * mean_fn(x) + e
        if kind == "monotone_miscal":
            return np.exp(0.8 * (x + e))
        if kind in ("nonmonotone", "sine_miscal"):
            return x + e
        if kind == "binary_calibrated":
            return mean_fn(x)
        if kind == "binary_miscal":
            return _sigmoid(3.0 * (1.5 * x - 0.5) + e) ** 2
        return rng.standard_normal(x.shape)  # pure_noise, binary_noise

    def sampler(rng, m):
        x = rng.standard_normal(m)
        if binary:
            y = (rng.random(m) < mean_fn(x)).astype(float)
        else:
            scale = noise * (1 + 0.5 * (kind == "nonmonotone") * np.abs(x))
            y = mean_fn(x) + scale * rng.standard_normal(m)
        return y, predictor(x, rng)

    truth_rng = np.random.default_rng(10_000 + seed)
    xs = truth_rng.standard_normal(2_000_000)
    truth = float(np.mean(mean_fn(xs)))  # E[eps] = 0 / E[Bernoulli(p)] = p
    return {"sampler": sampler, "truth": truth, "kind": kind}


REAL_DATASETS = ("galaxies", "forest", "alphafold", "gene_expression", "census_income",
                 "census_healthcare", "census_education")


def make_real_problem(name, data_dir="./data"):
    """Bootstrap sampler over the ppi_py example dataset ``name`` (labeled pool = whole
    dataset, truth = pool mean of Y). Requires ppi-python==0.2.3 (downloads the .npz)."""
    from ppi_py.datasets import load_dataset  # lazy: only needed offline for real data
    data = load_dataset(data_dir, name)
    y_all = np.asarray(data["Y"], dtype=float)
    yh_all = np.asarray(data["Yhat"], dtype=float)

    def sampler(rng, m):
        idx = rng.integers(0, y_all.size, size=m)
        return y_all[idx], yh_all[idx]

    return {"sampler": sampler, "truth": float(y_all.mean()), "kind": name}


def default_methods():
    """Baselines plus the submitted method; all take (y, yhat, yhat_unl, alpha)."""
    return {
        "ppi++": ppi_plus_plus_mean_ci,
        "classical": lambda y, yh, yu, a: classical_ci(y, a),
        "ppi_lambda1": ppi_mean_ci,
        "stratified": stratified_ppi_mean_ci,
        "crppi": crppi_mean_ci,
        "basis_press": basis_press_ppi_ci,
    }


def ablation_methods(p_grid=(2, 3, 5, 8)):
    """Submitted method plus single-factor ablations (fixed p, PRESS vs plain residual
    variance as selection criterion, HC3 vs plain variance, t vs normal critical value)."""
    methods = {"ppi++": ppi_plus_plus_mean_ci, "basis_press": basis_press_ppi_ci}
    for p in p_grid:
        methods[f"fixed_p{p}"] = partial(basis_press_ppi_ci, fixed_p=p)
    methods["select_resid_var"] = partial(basis_press_ppi_ci, criterion="resid")
    methods["plain_var"] = partial(basis_press_ppi_ci, hc3=False)
    methods["normal_crit"] = partial(basis_press_ppi_ci, use_t=False)
    methods["no_iso"] = partial(basis_press_ppi_ci, use_iso=False)
    return methods


def run_coverage_width_cell(sampler, truth, n, big_n, methods, n_rep=1000, seed=1001, alpha=0.05,
                            reference="ppi++"):
    """Repeat labeled/unlabeled draws, evaluate each interval method, summarise.

    ``sampler(rng, m)`` returns (Y, Yhat) for m i.i.d. records; ``methods`` maps a name to a
    function f(y, yhat, yhat_unl, alpha) -> (lo, hi) or None (None => classical-failure miss).
    Returns per-method coverage with Wilson CI, mean width, and paired mean log width ratio vs
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
            both = ok & np.isfinite(width[reference]) & (width[reference] > 0) & (width[name] > 0)
            d = np.log(width[name][both] / width[reference][both])
            entry["mean_log_ratio_vs_ref"] = float(d.mean())
            entry["log_ratio_boot_ci"] = paired_bootstrap_ci(d, seed=seed)
        result[name] = entry
    return result


def run_ablation(sampler, truth, n, big_n, n_rep=500, seed=1001, alpha=0.05, p_grid=(2, 3, 5, 8)):
    """One cell with the ablation method set (log ratios are vs PPI++, negative = narrower)."""
    return run_coverage_width_cell(sampler, truth, n, big_n, ablation_methods(p_grid),
                                   n_rep=n_rep, seed=seed, alpha=alpha)


def _jsonable(obj):
    if isinstance(obj, dict):
        return {k: _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    return obj


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["synthetic", "real"], default="synthetic")
    ap.add_argument("--ablation", action="store_true", help="use the ablation method set")
    ap.add_argument("--n_rep", type=int, default=500)
    ap.add_argument("--seed", type=int, default=1001)
    ap.add_argument("--n_list", type=int, nargs="+", default=[50, 100, 200, 500])
    ap.add_argument("--N_list", type=int, nargs="+", default=[2000, 20000])
    ap.add_argument("--data_dir", default="./data")
    ap.add_argument("--families", nargs="*", default=None)
    ap.add_argument("--out", default="harness_out.json")
    args = ap.parse_args()
    families = args.families or (SYNTHETIC_KINDS if args.mode == "synthetic" else REAL_DATASETS)
    methods = ablation_methods() if args.ablation else default_methods()
    results = {}
    for fam in families:
        prob = (make_synthetic_problem(fam, seed=args.seed) if args.mode == "synthetic"
                else make_real_problem(fam, args.data_dir))
        for n in args.n_list:
            for big_n in args.N_list:
                key = f"{fam}|n={n}|N={big_n}"
                results[key] = run_coverage_width_cell(prob["sampler"], prob["truth"], n, big_n,
                                                       methods, n_rep=args.n_rep, seed=args.seed)
                print(key, {m: (round(v["coverage"], 3), round(v.get("mean_log_ratio_vs_ref", 0.0), 4))
                            for m, v in results[key].items()}, flush=True)
    with open(args.out, "w") as fh:
        json.dump(_jsonable(results), fh, indent=1)


if __name__ == "__main__":
    main()
