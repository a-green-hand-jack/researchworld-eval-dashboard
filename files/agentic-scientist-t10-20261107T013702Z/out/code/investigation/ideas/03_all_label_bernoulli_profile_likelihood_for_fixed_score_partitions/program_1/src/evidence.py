"""Unexecuted, offline-only comparators and paired repetition summaries.

Truth is an argument of summaries only; none of these inputs extend the RPC.
No experiments, downloads, artifact writes or evaluation calls occur on import.
"""

import numpy as np
from scipy.special import ndtri
from scipy.stats import t

from incumbent import honest_score_intervals
from partition import (
    clopper_pearson,
    exact_partition_interval,
    partition_counts,
    partition_variance,
    profile_interval,
)


def wald_interval(estimate, variance, alpha):
    radius = float(ndtri(1.0 - alpha / 2.0) * np.sqrt(max(0.0, variance)))
    return float(np.clip(estimate - radius, 0.0, 1.0)), float(np.clip(estimate + radius, 0.0, 1.0))


def scalar_ppi(labels, predictions, unlabeled, alpha, optimized):
    """Original scalar PPI or unrestricted plug-in PPI++ Wald mean interval."""
    coefficient = 1.0
    if optimized:
        covariance = np.cov(labels, predictions, ddof=1)[0, 1]
        denominator = np.var(predictions, ddof=1) + labels.size / unlabeled.size * np.var(unlabeled, ddof=1)
        coefficient = float(covariance / denominator) if denominator > 0.0 else 0.0
    residuals = labels - coefficient * predictions
    estimate = float(residuals.mean() + coefficient * unlabeled.mean())
    variance = float(np.var(residuals, ddof=1) / labels.size + coefficient**2 * np.var(unlabeled, ddof=1) / unlabeled.size)
    return wald_interval(estimate, variance, alpha)


def wilson_interval(labels, alpha):
    estimate = float(labels.mean())
    adjustment = float(ndtri(1 - alpha / 2)**2 / labels.size)
    center = (estimate + adjustment / 2) / (1 + adjustment)
    radius = np.sqrt(adjustment * estimate * (1 - estimate) + adjustment**2 / 4) / (1 + adjustment)
    return float(max(0.0, center - radius)), float(min(1.0, center + radius))


def matched_partition_wald(successes, failures, unlabeled_counts, alpha):
    labeled_counts = successes + failures
    probabilities = (labeled_counts + unlabeled_counts) / np.sum(labeled_counts + unlabeled_counts)
    if np.any((labeled_counts == 0) & (probabilities > 0)):
        return 0.0, 1.0
    conditional_means = np.divide(successes, labeled_counts, out=np.full(successes.size, 0.5), where=labeled_counts > 0)
    estimate = float(np.dot(probabilities, conditional_means))
    variance = partition_variance(probabilities, conditional_means, int(labeled_counts.sum()), int(unlabeled_counts.sum()))
    return wald_interval(estimate, variance, alpha)


def compare_on_arrays(labels, predictions, unlabeled, alpha, seed):
    """Paired internal calls on identical samples; no empirical claims implied."""
    labels = np.asarray(labels, dtype=float)
    predictions = np.asarray(predictions, dtype=float)
    unlabeled = np.asarray(unlabeled, dtype=float)
    successes, failures, unlabeled_counts = partition_counts(labels, predictions, unlabeled, seed)
    diagnostics = {}
    candidate_profile = profile_interval(successes, failures, unlabeled_counts, alpha, diagnostics)
    exact = clopper_pearson(int(labels.sum()), labels.size, alpha)
    incumbent = exact if labels.size < 16 else honest_score_intervals(labels, predictions, unlabeled, alpha, seed)["wald"]
    intervals = {
        "labeled_exact": exact,
        "labeled_wilson": wilson_interval(labels, alpha),
        "original_ppi": scalar_ppi(labels, predictions, unlabeled, alpha, optimized=False),
        "scalar_ppiplus": scalar_ppi(labels, predictions, unlabeled, alpha, optimized=True),
        "incumbent": incumbent,
        "matched_partition_wald": matched_partition_wald(successes, failures, unlabeled_counts, alpha),
        "profile": exact if labels.size < 16 else candidate_profile,
        "profile_without_small_n_branch": candidate_profile,
        "exact_partition": exact_partition_interval(successes, failures, unlabeled_counts, alpha),
    }
    for name, budget, fixed in (("single_cell_profile", 1, False), ("fixed_cut_profile", None, True)):
        counts = partition_counts(labels, predictions, unlabeled, seed, cell_budget=budget, fixed=fixed)
        intervals[name] = profile_interval(*counts, alpha)
    diagnostics["analysis_count"] = int(unlabeled_counts.sum())
    diagnostics["cell_count"] = int(successes.size)
    diagnostics["raw_profile_optimization_failure"] = diagnostics["optimization_failure"]
    if labels.size < 16:
        diagnostics["optimization_failure"] = False
    return intervals, diagnostics


def known_prevalence_wald(successes, failures, cell_probabilities, alpha):
    """Synthetic oracle ablation, NOT deployable through the documented RPC."""
    labeled_counts = successes + failures
    if np.any((cell_probabilities > 0) & (labeled_counts == 0)):
        return 0.0, 1.0
    means = np.divide(successes, labeled_counts, out=np.zeros(successes.size), where=labeled_counts > 0)
    estimate = float(np.dot(cell_probabilities, means))
    variance = float(np.sum(np.divide(cell_probabilities**2 * means * (1 - means), labeled_counts, out=np.zeros(successes.size), where=labeled_counts > 0)))
    return wald_interval(estimate, variance, alpha)


def summarize_repetitions(intervals_by_method, truth, optimization_failures=None, boundary_cells=None):
    """Independent repetition coverage uncertainty and paired width MC errors."""
    summaries = {}
    truth = np.asarray(truth, dtype=float)
    if not np.isfinite(truth).all() or truth.ndim > 1:
        raise ValueError("truth must be a finite scalar or aligned vector")
    repetition_count = None
    for method, intervals in intervals_by_method.items():
        intervals = np.asarray(intervals, dtype=float)
        if intervals.ndim != 2 or intervals.shape[1] != 2 or intervals.shape[0] < 2:
            raise ValueError("at least two paired repetitions required")
        if not np.isfinite(intervals).all() or np.any(intervals[:, 0] > intervals[:, 1]):
            raise ValueError("invalid interval records")
        if truth.ndim == 1 and truth.shape != (intervals.shape[0],):
            raise ValueError("truth vector must align with repetitions")
        if repetition_count is not None and intervals.shape[0] != repetition_count:
            raise ValueError("all method records must be paired")
        repetition_count = intervals.shape[0]
        covered = (intervals[:, 0] <= truth) & (truth <= intervals[:, 1])
        widths = intervals[:, 1] - intervals[:, 0]
        coverage_interval = clopper_pearson(int(np.sum(covered)), covered.size, 0.05)
        summaries[method] = {
            "repetitions": int(covered.size),
            "coverage": float(np.mean(covered)),
            "coverage_interval": coverage_interval,
            "mean_width": float(np.mean(widths)),
            "width_mcse": float(np.std(widths, ddof=1) / np.sqrt(widths.size)),
        }
    profile_intervals = np.asarray(intervals_by_method["profile"], dtype=float)
    incumbent_intervals = np.asarray(intervals_by_method["incumbent"], dtype=float)
    if profile_intervals.shape != incumbent_intervals.shape:
        raise ValueError("paired records must have identical shapes and ordering")
    profile_widths = profile_intervals[:, 1] - profile_intervals[:, 0]
    incumbent_widths = incumbent_intervals[:, 1] - incumbent_intervals[:, 0]
    paired_width_differences = profile_widths - incumbent_widths
    paired_width_mcse = np.std(paired_width_differences, ddof=1) / np.sqrt(paired_width_differences.size)
    mean_difference = float(np.mean(paired_width_differences))
    radius = float(t.ppf(0.975, paired_width_differences.size - 1) * paired_width_mcse)
    summaries["paired_profile_minus_incumbent"] = {
        "mean_width_difference": mean_difference,
        "paired_width_mcse": float(paired_width_mcse),
        "paired_width_interval": (mean_difference - radius, mean_difference + radius),
    }
    if optimization_failures is not None:
        failures = np.asarray(optimization_failures, dtype=bool)
        if failures.shape != profile_widths.shape:
            raise ValueError("failure records must align with repetitions")
        covered = (profile_intervals[:, 0] <= truth) & (truth <= profile_intervals[:, 1])
        summaries["profile_diagnostics"] = {
            "optimization_failure_count": int(np.sum(failures)),
            "misses_without_optimization_failure": int(np.sum(~covered & ~failures)),
        }
        if boundary_cells is not None:
            boundary = np.asarray(boundary_cells) > 0
            if boundary.shape != failures.shape:
                raise ValueError("boundary records must align with repetitions")
            summaries["profile_diagnostics"]["boundary_regime_misses"] = int(np.sum(~covered & boundary & ~failures))
    return summaries
