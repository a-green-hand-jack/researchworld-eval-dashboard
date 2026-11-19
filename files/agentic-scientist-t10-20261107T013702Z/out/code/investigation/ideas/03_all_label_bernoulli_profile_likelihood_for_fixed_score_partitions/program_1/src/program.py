"""Frozen-predictor Bernoulli population-mean inference, CPU/binary64 only.

RPC v1: handle(request) returns a finite JSON object. Only the exact documented
keys are accepted in responses; do not return diagnostics, paths, or state flags.
The predictor and samples are immutable. Fit inference-side transforms only.
Never pool labels across episodes. No external files, network, or extra labels.

reset: {"op":"reset","seed":nonnegative integer}, response {"ok":true}.
Accept arbitrary seeds; they initialize RNG, never identify a workload/plane.
Clears all arrays, coefficients, results and randomness. Exactly once per episode.

input: {"op":"input","n":integer>=2,"N":integer>=2,"alpha":0.05,
"dtype":"<f8","encoding":"base64","shape":[2*n+N],
"total_bytes":8*(2*n+N),"chunk_count":integer in [1,4],
"chunk_index":integer in [0,chunk_count),"offset":integer,"data":base64 string}.
The logical byte stream concatenates Y_L[n],f_L[n],f_U[N] in this order.
Each scalar is finite in [0,1]; Y_L is binary. n,N,alpha and metadata are
plane-independent workload settings. No true mean, unlabeled labels, case name,
baseline, score, feedback or resource paths are supplied. Chunks are contiguous,
ordered, nonempty, at most 1 MiB decoded each, at most 4 MiB total. First input
sets metadata; all later inputs repeat it exactly. No separate setup RPC is
needed: input #0 performs setup. Response {"ok":true,"received_bytes":integer}.
All four input calls are budgeted even when the actual value fits one chunk.
Assembly is exclusively in candidate-owned RAM. No spill or shared paths.

infer: {"op":"infer"}, only after every input chunk, exactly once per episode.
Commits the input stream and fits the actual method in one operation. Response
{"estimate":finite number,"lower":finite number,"upper":finite number}, with
0<=lower<=upper<=1 and 0<=estimate<=1. Closed intervals target E[Y] at 1-alpha.
No additional response fields. Endpoints need not contain the point estimate.
After infer only reset is legal. No state export/import or extra probes exist.
Every complete message including envelope/framing must be <64 MiB (design cap
8 MiB; endpoint/ack responses <16 KiB); keep input logical total <=4 MiB.

Candidate: all-label joint-cell observed-data Bernoulli profile likelihood.
Cuts use an independent unlabeled pilot, excluded from likelihood counts.
The RPC returns a Wilks-calibrated profile interval for n>=16 and the unchanged
labeled-only exact interval for n<16, a size-only rule. The separately callable
exact partition safety track is NOT substituted, intersected or width-selected.
Wilks coverage is only asymptotic under interior, regular fixed-cell conditions.
No empirical coverage, finite-sample profile guarantee or gain is asserted.
"""
import base64
import math

import numpy as np

from partition import partition_profile_intervals

_state = None


class ScoreCalibrator:
    """Small ridge linear-spline family, tuned exclusively on its fit sample."""

    def __init__(self, nonlinear=True):
        self.nonlinear = nonlinear

    def fit(self, scores, outcomes):
        train_scores = np.asarray(scores, dtype=float).reshape(-1)
        train_outcomes = np.asarray(outcomes, dtype=float).reshape(-1)
        self.intercept = float(np.mean(train_outcomes))
        self.knots = np.empty(0)
        self.coefficients = np.empty(0)
        self.feature_mean = np.empty(0)
        self.feature_scale = np.empty(0)
        sample_count = train_scores.size
        if sample_count < 4 or np.ptp(train_scores) < 1e-12:
            return self
        centered_outcomes = train_outcomes - self.intercept
        best_gcv = float(np.mean(centered_outcomes**2) / (1.0 - 1.0 / sample_count)**2)
        knot_families = [np.empty(0)]
        if self.nonlinear and sample_count >= 16:
            knot_families.append(np.unique(np.quantile(train_scores, [0.25, 0.5, 0.75])))
        if self.nonlinear and sample_count >= 64:
            knot_families.append(np.unique(np.quantile(train_scores, np.linspace(0.125, 0.875, 7))))
        for knots in knot_families:
            features = self._basis(train_scores, knots)
            feature_mean = features.mean(axis=0)
            feature_scale = features.std(axis=0)
            feature_scale = np.maximum(feature_scale, 1e-8)
            centered_features = (features - feature_mean) / feature_scale
            gram = centered_features.T @ centered_features / sample_count
            cross = centered_features.T @ centered_outcomes / sample_count
            identity = np.eye(gram.shape[0])
            for penalty in (0.001, 0.01, 0.1, 1.0, 10.0):
                coefficient = np.linalg.solve(gram + penalty * identity, cross)
                residuals = centered_outcomes - centered_features @ coefficient
                degrees = 1.0 + float(np.trace(np.linalg.solve(gram + penalty * identity, gram)))
                denominator = max(1.0 - degrees / sample_count, 1.0 / sample_count)
                gcv = float(np.mean(residuals**2) / denominator**2)
                if gcv < best_gcv:
                    best_gcv = gcv
                    self.knots = knots.copy()
                    self.coefficients = coefficient
                    self.feature_mean = feature_mean
                    self.feature_scale = feature_scale
        return self

    @staticmethod
    def _basis(scores, knots):
        return np.column_stack((scores, np.maximum(scores[:, None] - knots[None, :], 0.0)))

    def predict(self, scores):
        scores = np.asarray(scores, dtype=float).reshape(-1)
        if not self.coefficients.size:
            return np.full(scores.size, self.intercept)
        features = (self._basis(scores, self.knots) - self.feature_mean) / self.feature_scale
        return self.intercept + features @ self.coefficients


def fit_score_calibrator(train_scores, train_outcomes):
    calibrator = ScoreCalibrator()
    calibrator.fit(train_scores.reshape(-1, 1), train_outcomes)
    return calibrator


def bounded_eb_radius(sample, lower_bound, upper_bound, delta):
    """Conservative two-sided empirical Bernstein radius for bounded iid data."""
    sample = np.asarray(sample, dtype=float)
    if not 0.0 < delta < 1.0 or lower_bound > upper_bound:
        raise ValueError("invalid empirical-Bernstein parameters")
    if sample.size < 2:
        return float(upper_bound - lower_bound)
    log_term = np.log(4.0 / delta)
    radius = np.sqrt(2.0 * np.var(sample, ddof=1) * log_term / sample.size) + 7.0 * (upper_bound - lower_bound) * log_term / (3.0 * (sample.size - 1))
    return float(min(upper_bound - lower_bound, radius))


def honest_score_intervals(outcomes, scores, unlabeled_scores, alpha, seed, affine=False):
    """Separate Wald and finite-sample tracks; no selection between intervals."""
    from scipy.special import ndtri

    labeled_count = outcomes.size
    unlabeled_count = unlabeled_scores.size
    rho = unlabeled_count / (labeled_count + unlabeled_count)
    n_folds = 2
    component_delta = alpha / (2 * n_folds)
    generator = np.random.default_rng(seed)
    labeled_folds = np.array_split(generator.permutation(labeled_count), n_folds)
    unlabeled_folds = np.array_split(generator.permutation(unlabeled_count), n_folds)
    fold_weights = np.asarray([fold.size / labeled_count for fold in labeled_folds])
    fold_estimates = []
    fold_lowers = []
    fold_uppers = []
    oof_residuals = np.empty(labeled_count)
    oof_controls = np.empty(unlabeled_count)
    for fold_index in range(n_folds):
        training_indices = labeled_folds[1 - fold_index]
        heldout_indices = labeled_folds[fold_index]
        unlabeled_indices = unlabeled_folds[fold_index]
        train_scores = scores[training_indices]
        train_outcomes = outcomes[training_indices]
        heldout_scores = scores[heldout_indices]
        heldout_outcomes = outcomes[heldout_indices]
        heldout_unlabeled_scores = unlabeled_scores[unlabeled_indices]
        if affine:
            calibrator = fit_affine_calibrator(train_scores, train_outcomes)
        else:
            calibrator = fit_score_calibrator(train_scores, train_outcomes)
        calibrated_labeled = np.clip(calibrator.predict(heldout_scores.reshape(-1, 1)), 0.0, 1.0)
        calibrated_unlabeled = np.clip(calibrator.predict(heldout_unlabeled_scores.reshape(-1, 1)), 0.0, 1.0)
        fold_estimate = np.mean(heldout_outcomes - rho * calibrated_labeled) + rho * np.mean(calibrated_unlabeled)
        oof_residuals[heldout_indices] = heldout_outcomes - rho * calibrated_labeled
        oof_controls[unlabeled_indices] = rho * calibrated_unlabeled
        residual_radius = bounded_eb_radius(heldout_outcomes - rho * calibrated_labeled, -rho, 1.0, component_delta)
        prediction_radius = bounded_eb_radius(rho * calibrated_unlabeled, 0.0, rho, component_delta)
        fold_lower = fold_estimate - residual_radius - prediction_radius
        fold_upper = fold_estimate + residual_radius + prediction_radius
        fold_estimates.append(fold_estimate)
        fold_lowers.append(fold_lower)
        fold_uppers.append(fold_upper)
    estimate = float(np.dot(fold_weights, fold_estimates))
    wald_variance = np.var(oof_residuals, ddof=1) / labeled_count + np.var(oof_controls, ddof=1) / unlabeled_count
    critical = float(ndtri(1.0 - alpha / 2.0))
    boundary_adjustment = critical**2 / labeled_count
    wald_center = (estimate + boundary_adjustment / 2.0) / (1.0 + boundary_adjustment)
    radius = critical * math.sqrt(max(0.0, float(wald_variance)) + critical**2 / (4.0 * labeled_count**2)) / (1.0 + boundary_adjustment)
    wald_lower = float(np.clip(wald_center - radius, 0.0, 1.0))
    wald_upper = float(np.clip(wald_center + radius, 0.0, 1.0))
    safe_lower = max(0.0, float(np.dot(fold_weights, fold_lowers)))
    safe_upper = min(1.0, float(np.dot(fold_weights, fold_uppers)))
    if safe_lower > safe_upper:
        safe_lower, safe_upper = 0.0, 1.0
    return {
        "estimate": float(np.clip(estimate, 0.0, 1.0)),
        "wald": (wald_lower, wald_upper),
        "finite_sample": (safe_lower, safe_upper),
    }


def fit_affine_calibrator(train_scores, train_outcomes):
    """Matched ridge/GCV ablation with the same clipping but no spline knots."""
    calibrator = ScoreCalibrator(nonlinear=False)
    calibrator.fit(train_scores.reshape(-1, 1), train_outcomes)
    return calibrator


def handle(request):
    global _state
    operation = request.get("op")
    if operation == "reset":
        if set(request) != {"op", "seed"} or type(request["seed"]) is not int or request["seed"] < 0:
            raise ValueError("invalid reset")
        _state = {"seed": request["seed"], "buffer": bytearray(), "chunks": 0, "meta": None, "done": False}
        return {"ok": True}
    if _state is None or _state["done"]:
        raise ValueError("reset required")
    if operation == "input":
        keys = {"op", "n", "N", "alpha", "dtype", "encoding", "shape", "total_bytes", "chunk_count", "chunk_index", "offset", "data"}
        if set(request) != keys:
            raise ValueError("invalid input schema")
        labeled_size, unlabeled_size = request["n"], request["N"]
        total = request["total_bytes"]
        if any(type(request[key]) is not int for key in ("n", "N", "total_bytes", "chunk_count", "chunk_index", "offset")):
            raise ValueError("integer metadata required")
        if min(labeled_size, unlabeled_size) < 2 or total != 8 * (2 * labeled_size + unlabeled_size) or not 0 < total <= 4 * 1024**2:
            raise ValueError("invalid size")
        if request["dtype"] != "<f8" or request["encoding"] != "base64" or request["shape"] != [2 * labeled_size + unlabeled_size] or request["alpha"] != 0.05:
            raise ValueError("invalid metadata")
        if not 1 <= request["chunk_count"] <= 4 or request["chunk_index"] != _state["chunks"] or request["chunk_index"] >= request["chunk_count"] or request["offset"] != len(_state["buffer"]):
            raise ValueError("invalid chunk sequence")
        metadata = {key: request[key] for key in ("n", "N", "alpha", "dtype", "encoding", "shape", "total_bytes", "chunk_count")}
        if _state["meta"] is not None and _state["meta"] != metadata:
            raise ValueError("metadata changed")
        if not isinstance(request["data"], str) or len(request["data"]) > 1398104:
            raise ValueError("oversized chunk")
        raw = base64.b64decode(request["data"], validate=True)
        if not 0 < len(raw) <= 1024**2 or len(_state["buffer"]) + len(raw) > total:
            raise ValueError("invalid chunk size")
        _state["meta"] = metadata
        _state["buffer"].extend(raw)
        _state["chunks"] += 1
        return {"ok": True, "received_bytes": len(_state["buffer"])}
    if operation != "infer" or set(request) != {"op"}:
        raise ValueError("invalid operation")
    metadata = _state["meta"]
    if metadata is None or _state["chunks"] != metadata["chunk_count"] or len(_state["buffer"]) != metadata["total_bytes"]:
        raise ValueError("incomplete input")
    from scipy.special import betaincinv
    values = np.frombuffer(_state["buffer"], dtype="<f8")
    labeled_size, unlabeled_size = metadata["n"], metadata["N"]
    labels = values[:labeled_size]
    predictions = values[labeled_size:2 * labeled_size]
    unlabeled = values[2 * labeled_size:]
    if not np.isfinite(values).all() or np.any(values < 0) or np.any(values > 1) or np.any((labels != 0) & (labels != 1)):
        raise ValueError("invalid array values")
    count = int(labels.sum())
    alpha = metadata["alpha"]
    if labeled_size < 16:
        estimate = float(labels.mean())
        lower = 0.0 if count == 0 else float(betaincinv(count, labeled_size - count + 1, alpha / 2))
        upper = 1.0 if count == labeled_size else float(betaincinv(count + 1, labeled_size - count, 1 - alpha / 2))
    else:
        intervals = partition_profile_intervals(labels, predictions, unlabeled, alpha, _state["seed"])
        estimate = intervals["estimate"]
        lower, upper = intervals["profile"]
    _state["done"] = True
    _state["buffer"] = bytearray()
    return {"estimate": float(estimate), "lower": lower, "upper": upper}
