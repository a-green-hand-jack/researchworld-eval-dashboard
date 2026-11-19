"""All-label observed-data likelihood; exact safety is a separate procedure."""

import numpy as np
from scipy.optimize import brentq, linprog, minimize
from scipy.special import betaincinv, xlogy
from scipy.stats import chi2


def clopper_pearson(successes, trials, alpha):
    if trials == 0:
        return 0.0, 1.0
    lower = 0.0 if successes == 0 else float(betaincinv(successes, trials - successes + 1, alpha / 2))
    upper = 1.0 if successes == trials else float(betaincinv(successes + 1, trials - successes, 1 - alpha / 2))
    return lower, upper


def partition_counts(labels, predictions, unlabeled, seed, cell_budget=None, fixed=False):
    """Choose cuts without labels; exclude the independent pilot from counts."""
    labels = np.asarray(labels, dtype=float)
    predictions = np.asarray(predictions, dtype=float)
    unlabeled = np.asarray(unlabeled, dtype=float)
    cell_budget = min(8, max(2, labels.size // 32)) if cell_budget is None else int(cell_budget)
    if not 1 <= cell_budget <= 8:
        raise ValueError("cell budget must be between one and eight")
    permutation = np.random.default_rng(seed).permutation(unlabeled.size)
    pilot_size = min(unlabeled.size // 5, 256)
    pilot_scores = unlabeled[permutation[:pilot_size]]
    analysis_scores = unlabeled[permutation[pilot_size:]]
    quantiles = np.arange(1, cell_budget) / cell_budget
    if pilot_scores.size and not fixed:
        cutpoints = np.unique(np.quantile(pilot_scores, quantiles))
    else:
        cutpoints = quantiles
    cutpoints = cutpoints[(cutpoints > 0.0) & (cutpoints < 1.0)]
    labeled_bins = np.searchsorted(cutpoints, predictions, side="right")
    unlabeled_bins = np.searchsorted(cutpoints, analysis_scores, side="right")
    cell_count = cutpoints.size + 1
    successes = np.bincount(labeled_bins, weights=labels, minlength=cell_count)
    labeled_counts = np.bincount(labeled_bins, minlength=cell_count)
    failures = labeled_counts - successes
    unlabeled_counts = np.bincount(unlabeled_bins, minlength=cell_count)
    return successes, failures, unlabeled_counts


def cell_loglik(joint_mass, successes, failures, unlabeled_counts):
    cell_count = successes.size
    positive_mass = joint_mass[:cell_count]
    negative_mass = joint_mass[cell_count:]
    return float(np.sum(xlogy(successes, positive_mass) + xlogy(failures, negative_mass) + xlogy(unlabeled_counts, positive_mass + negative_mass)))


def profile_mean_constraint(joint_mass, target_mean, cell_count):
    return float(np.sum(joint_mass[:cell_count]) - target_mean)


def cell_gradient(joint_mass, successes, failures, unlabeled_counts):
    cell_count = successes.size
    positive_mass = joint_mass[:cell_count]
    negative_mass = joint_mass[cell_count:]
    marginal_mass = positive_mass + negative_mass
    with np.errstate(divide="ignore", invalid="ignore"):
        marginal_gradient = np.divide(unlabeled_counts, marginal_mass, out=np.zeros(cell_count), where=unlabeled_counts > 0)
        positive_gradient = np.divide(successes, positive_mass, out=np.zeros(cell_count), where=successes > 0)
        negative_gradient = np.divide(failures, negative_mass, out=np.zeros(cell_count), where=failures > 0)
    return np.concatenate((positive_gradient + marginal_gradient, negative_gradient + marginal_gradient))


def joint_mle(successes, failures, unlabeled_counts):
    labeled_counts = successes + failures
    probabilities = (labeled_counts + unlabeled_counts) / np.sum(labeled_counts + unlabeled_counts)
    conditional_means = np.divide(successes, labeled_counts, out=np.full(successes.size, 0.5), where=labeled_counts > 0)
    return np.concatenate((probabilities * conditional_means, probabilities * (1.0 - conditional_means)))


def constrained_profile(target_mean, successes, failures, unlabeled_counts, warm_start):
    """Return a certified upper bound on the constrained maximum, or failure.

    Concavity bounds the remaining likelihood improvement by the maximum
    gradient over each fixed-mass simplex minus its value at the iterate.
    The certification tolerance is in raw log-likelihood units, not per record.
    """
    cell_count = successes.size
    total_count = float(np.sum(successes + failures + unlabeled_counts))
    if target_mean == 0.0:
        if np.sum(successes) > 0:
            return -np.inf, warm_start, True
        probabilities = (failures + unlabeled_counts) / total_count
        joint_mass = np.concatenate((np.zeros(cell_count), probabilities))
        return cell_loglik(joint_mass, successes, failures, unlabeled_counts), joint_mass, True
    if target_mean == 1.0:
        if np.sum(failures) > 0:
            return -np.inf, warm_start, True
        probabilities = (successes + unlabeled_counts) / total_count
        joint_mass = np.concatenate((probabilities, np.zeros(cell_count)))
        return cell_loglik(joint_mass, successes, failures, unlabeled_counts), joint_mass, True
    positive_start = warm_start[:cell_count] + 0.01 / cell_count
    negative_start = warm_start[cell_count:] + 0.01 / cell_count
    initial = np.concatenate((target_mean * positive_start / positive_start.sum(), (1.0 - target_mean) * negative_start / negative_start.sum()))
    total_gradient = np.ones(2 * cell_count)
    mean_gradient = np.concatenate((np.ones(cell_count), np.zeros(cell_count)))
    constraints = [
        {"type": "eq", "fun": lambda mass: float(np.sum(mass) - 1.0), "jac": lambda mass: total_gradient},
        {"type": "eq", "fun": lambda mass: profile_mean_constraint(mass, target_mean, cell_count), "jac": lambda mass: mean_gradient},
    ]
    for tolerance in (1e-13, 1e-15):
        result = minimize(
            lambda mass: -cell_loglik(mass, successes, failures, unlabeled_counts) / total_count,
            initial,
            jac=lambda mass: -cell_gradient(mass, successes, failures, unlabeled_counts) / total_count,
            bounds=[(0.0, 1.0)] * (2 * cell_count),
            constraints=constraints,
            method="SLSQP",
            options={"ftol": tolerance, "maxiter": 240},
        )
        if not np.isfinite(result.x).all() or np.min(result.x) < -1e-10:
            return -np.inf, initial, False
        joint_mass = np.maximum(result.x, 0.0)
        positive_total = float(joint_mass[:cell_count].sum())
        negative_total = float(joint_mass[cell_count:].sum())
        if positive_total <= 0.0 or negative_total <= 0.0:
            return -np.inf, initial, False
        joint_mass[:cell_count] *= target_mean / positive_total
        joint_mass[cell_count:] *= (1.0 - target_mean) / negative_total
        loglik = cell_loglik(joint_mass, successes, failures, unlabeled_counts)
        gradient = cell_gradient(joint_mass, successes, failures, unlabeled_counts)
        if np.isfinite(loglik) and np.isfinite(gradient).all():
            dual_gap = target_mean * np.max(gradient[:cell_count]) + (1.0 - target_mean) * np.max(gradient[cell_count:]) - np.dot(gradient, joint_mass)
            if result.success and -1e-5 <= dual_gap <= 0.005:
                return loglik + max(0.0, float(dual_gap)), joint_mass, True
        initial = joint_mass
    return -np.inf, initial, False


def profile_interval(successes, failures, unlabeled_counts, alpha, diagnostics=None):
    """Invert the Wilks LR test. This is asymptotic, NOT a finite-sample CI."""
    maximum_mass = joint_mle(successes, failures, unlabeled_counts)
    cell_count = successes.size
    estimate = float(maximum_mass[:cell_count].sum())
    maximum_loglik = cell_loglik(maximum_mass, successes, failures, unlabeled_counts)
    cutoff = chi2.ppf(1.0 - alpha, 1)
    warm_starts = [(estimate, maximum_mass)]
    if diagnostics is not None:
        diagnostics["optimization_failure"] = False
        diagnostics["boundary_cells"] = int(np.sum((successes == 0) | (failures == 0)))

    def likelihood_root(target_mean):
        nearest = min(warm_starts, key=lambda item: abs(item[0] - target_mean))[1]
        constrained_loglik, joint_mass, optimization_ok = constrained_profile(target_mean, successes, failures, unlabeled_counts, nearest)
        if not optimization_ok:
            raise ArithmeticError("uncertified constrained likelihood")
        if constrained_loglik > maximum_loglik + 0.006:
            raise ArithmeticError("inconsistent constrained likelihood")
        warm_starts.append((target_mean, joint_mass))
        likelihood_gap = 2.0 * (maximum_loglik - constrained_loglik) - cutoff
        return float(likelihood_gap)

    optimization_ok = np.isfinite(maximum_loglik) and np.isfinite(cutoff)
    if diagnostics is not None and not optimization_ok:
        diagnostics["optimization_failure"] = True
    if not optimization_ok: return 0.0, 1.0
    try:
        lower_gap = likelihood_root(0.0)
        upper_gap = likelihood_root(1.0)
        lower = 0.0 if lower_gap <= 0.0 else max(0.0, float(brentq(likelihood_root, 0.0, estimate, xtol=1e-7, rtol=1e-8, maxiter=64)) - 2e-7)
        upper = 1.0 if upper_gap <= 0.0 else min(1.0, float(brentq(likelihood_root, estimate, 1.0, xtol=1e-7, rtol=1e-8, maxiter=64)) + 2e-7)
        optimization_ok = np.isfinite(lower) and np.isfinite(upper) and 0.0 <= lower <= estimate <= upper <= 1.0
    except (ArithmeticError, ValueError, RuntimeError, FloatingPointError):
        optimization_ok = False
    if diagnostics is not None:
        diagnostics["optimization_failure"] = not optimization_ok
    if not optimization_ok: return 0.0, 1.0
    return lower, upper


def exact_partition_interval(successes, failures, unlabeled_counts, alpha):
    """Conditional-pilot simultaneous CP interval, never selected by width."""
    cell_count = successes.size
    labeled_counts = successes + failures
    analysis_count = int(unlabeled_counts.sum())
    if analysis_count == 0:
        return 0.0, 1.0
    component_alpha = alpha / (2 * cell_count)
    q_lower = np.empty(cell_count)
    q_upper = np.empty(cell_count)
    p_lower = np.empty(cell_count)
    p_upper = np.empty(cell_count)
    for cell_index in range(cell_count):
        q_lower[cell_index], q_upper[cell_index] = clopper_pearson(successes[cell_index], labeled_counts[cell_index], component_alpha)
        p_lower[cell_index], p_upper[cell_index] = clopper_pearson(unlabeled_counts[cell_index], analysis_count, component_alpha)
    probability_bounds = list(zip(p_lower, p_upper))
    try:
        lower_result = linprog(q_lower, A_eq=np.ones((1, cell_count)), b_eq=[1.0], bounds=probability_bounds, method="highs")
        upper_result = linprog(-q_upper, A_eq=np.ones((1, cell_count)), b_eq=[1.0], bounds=probability_bounds, method="highs")
    except (ValueError, RuntimeError):
        return 0.0, 1.0
    if not lower_result.success or not upper_result.success:
        return 0.0, 1.0
    lower_multiplier = float(lower_result.eqlin.marginals[0])
    upper_multiplier = float(upper_result.eqlin.marginals[0])
    lower_dual = lower_multiplier + np.sum(np.minimum((q_lower - lower_multiplier) * p_lower, (q_lower - lower_multiplier) * p_upper))
    upper_dual = upper_multiplier + np.sum(np.minimum((-q_upper - upper_multiplier) * p_lower, (-q_upper - upper_multiplier) * p_upper))
    lower = float(np.clip(lower_dual - 1e-8, 0.0, 1.0))
    upper = float(np.clip(-upper_dual + 1e-8, 0.0, 1.0))
    if not np.isfinite(lower + upper) or lower > upper:
        return 0.0, 1.0
    return lower, upper


def partition_profile_intervals(labels, predictions, unlabeled, alpha, seed):
    successes, failures, unlabeled_counts = partition_counts(labels, predictions, unlabeled, seed)
    maximum_mass = joint_mle(successes, failures, unlabeled_counts)
    estimate = float(maximum_mass[:successes.size].sum())
    diagnostics = {}
    lower, upper = profile_interval(successes, failures, unlabeled_counts, alpha, diagnostics)
    return {"estimate": estimate, "profile": (lower, upper), "diagnostics": diagnostics}


def partition_variance(cell_probabilities, conditional_means, labeled_count, analysis_count):
    population_mean = np.sum(cell_probabilities * conditional_means)
    within_variance = np.sum(cell_probabilities * conditional_means * (1.0 - conditional_means))
    between_variance = np.sum(cell_probabilities * (conditional_means - population_mean) ** 2)
    return within_variance / labeled_count + between_variance / (labeled_count + analysis_count)
