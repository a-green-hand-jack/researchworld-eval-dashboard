"""Offline mathematical/reporting utilities, not additional RPC operations.

These helpers have not been executed in this stage. They do not generate or
claim empirical evidence and are never called by candidate inference. All
comparisons must use identical observations and repetition identifiers.
"""

import math

import numpy as np
from scipy.stats import binomtest, t


def oracle_frontier(labeled_count, unlabeled_count, conditional_noise_variance,
                    regression_variance, nonlinear_projection_error):
    """Population moments must be known analytically, not estimated from truth leaks."""
    if min(labeled_count, unlabeled_count) < 2:
        raise ValueError("two nonempty variance samples required")
    if min(conditional_noise_variance, regression_variance, nonlinear_projection_error) < 0:
        raise ValueError("negative variance moment")
    if nonlinear_projection_error > regression_variance + 1e-12:
        raise ValueError("projection error exceeds regression variance")
    oracle_variance = conditional_noise_variance / labeled_count + regression_variance / (labeled_count + unlabeled_count)
    oracle_gain = unlabeled_count * nonlinear_projection_error / (labeled_count * (labeled_count + unlabeled_count))
    return {"oracle_variance": float(oracle_variance),
            "best_affine_variance": float(oracle_variance + oracle_gain),
            "oracle_gain": float(oracle_gain)}


def paired_uncertainty(covered, candidate_widths, baseline_widths):
    """Exact binomial coverage CI and paired t width-difference CI across iid runs."""
    covered = np.asarray(covered, dtype=bool)
    candidate_widths = np.asarray(candidate_widths, dtype=float)
    baseline_widths = np.asarray(baseline_widths, dtype=float)
    if covered.ndim != 1 or candidate_widths.shape != covered.shape or baseline_widths.shape != covered.shape or covered.size < 2:
        raise ValueError("at least two paired repetitions required")
    if not np.isfinite(candidate_widths).all() or not np.isfinite(baseline_widths).all() or np.any(candidate_widths < 0) or np.any(baseline_widths < 0):
        raise ValueError("invalid widths")
    coverage_count = int(np.count_nonzero(covered))
    coverage_interval = binomtest(coverage_count, len(covered)).proportion_ci(confidence_level=0.95, method='exact')
    paired_width_difference = candidate_widths - baseline_widths
    difference_mean = float(np.mean(paired_width_difference))
    difference_se = float(np.std(paired_width_difference, ddof=1) / math.sqrt(len(covered)))
    critical = float(t.ppf(0.975, len(covered) - 1))
    return {
        "repetitions": len(covered),
        "coverage_count": coverage_count,
        "coverage": float(np.mean(covered)),
        "coverage_interval": [float(coverage_interval.low), float(coverage_interval.high)],
        "mean_width": float(np.mean(candidate_widths)),
        "mean_width_se": float(np.std(candidate_widths, ddof=1) / math.sqrt(len(covered))),
        "baseline_mean_width": float(np.mean(baseline_widths)),
        "paired_width_difference": difference_mean,
        "paired_width_difference_interval": [difference_mean - critical * difference_se,
                                             difference_mean + critical * difference_se],
    }


def repetition_record(repetition, method, estimate, lower, upper, validity_track):
    """Serializable per-repetition record; caller controls persistence, not RPC."""
    if validity_track not in {"asymptotic", "finite_sample", "oracle_asymptotic"}:
        raise ValueError("unknown validity track")
    record = {"repetition": int(repetition), "method": str(method),
              "estimate": float(estimate), "lower": float(lower),
              "upper": float(upper), "width": float(upper - lower)}
    record['validity_track'] = validity_track
    return record
