"""CPU-only frozen-predictor mean interval; finite JSON RPC v1.

All request/response fields below are mandatory; extra fields are forbidden.
reset {op:"reset",seed:int} -> {ok:true}: clears buffers, fit and RNG. Accept
any nonnegative signed-64-bit seed; seeds do not identify workloads or planes.
update/start {op:"update",phase:"start",n:int,N:int,alpha:0.05,
 label_kind:"bernoulli"|"real",dtype:"<f8",encoding:"base64",shape:[2*n+N],
 total_bytes:8*(2*n+N),chunks:ceil(total_bytes/1048576)} ->
 {ok:true,transfer_id:str}. n,N>=8; logical input <=8 MiB, at most 8 chunks.
update/chunk {op:"update",phase:"chunk",transfer_id:str,index:int,data:str}
 -> {ok:true}. data is standard base64; indices must be sequential from zero.
 Decoded chunks are 1 MiB except the last. The ID is an opaque memory token,
 1..64 ASCII alphanumeric/underscore characters, never a filename or path.
update/commit {op:"update",phase:"commit",transfer_id:str} -> {ok:true}.
 Assembled little-endian float64 array contains y[n], p[n], u[N]: labeled
 outcomes, their frozen predictions, then unlabeled frozen predictions. Values
 must be finite; Bernoulli y is 0/1. Fits once and releases transfer buffers.
infer {op:"infer"} -> {lower:float,upper:float}. Endpoints and their width must
 be finite and ordered, within [0,1] for Bernoulli. Repeated infer is identical.

One reset, one start, 1..8 chunks, one commit, two infer calls per episode.
Only one transaction per reset. Workload shape/outcome type is supplied by
start, never inferred from seeds. All responses <=64 KiB; complete JSON lines
must be <64 MiB. No paths, private targets, population labels, baseline outputs,
extra labels, predictor retraining, or cross-episode state are permitted.
Constant scores require label-only fallback. Matched score interventions and
one trailing reset replay are evaluator-owned controls, not self-report gates.

Candidate: five-fold score-only zero/affine/spline controls with training-only
paired-risk selection and offset-invariant variance. Constant/rare inputs
retain the label-only fallback (Clopper-Pearson
for Bernoulli, Student t otherwise). Infer returns an asymptotic interval, NOT
the separate conservative bounded-fold certificate computed internally for
Bernoulli data. No certificate, fitted parameters or diagnostics are exposed.
The frozen predictor is never changed. Calibration uses other folds' labels
and scores only, not the unlabeled score pool. See METHOD.md for assumptions,
oracle algebra, the scope of the certificate, and unperformed validation.
"""

import base64
import math

import numpy as np
from scipy.stats import beta, t


_state = None


def _keys(value, expected):
    if type(value) is not dict or set(value) != set(expected.split()):
        raise ValueError("invalid fields")


def _label_only(outcomes, kind, alpha):
    count = len(outcomes)
    if kind == "bernoulli":
        successes = int(outcomes.sum())
        lower = 0.0 if successes == 0 else beta.ppf(alpha / 2, successes, count - successes + 1)
        upper = 1.0 if successes == count else beta.ppf(1 - alpha / 2, successes + 1, count - successes)
    else:
        radius = t.ppf(1 - alpha / 2, count - 1) * outcomes.std(ddof=1) / math.sqrt(count)
        lower, upper = outcomes.mean() - radius, outcomes.mean() + radius
    return {"lower": float(lower), "upper": float(upper)}


class ScoreCalibrator:
    """Low-dimensional score nuisance; knots and ridge rule are prespecified."""

    def __init__(self, bounded):
        self.bounded = bounded

    def _features(self, scores):
        scaled = np.clip(scores, -self.score_scale, self.score_scale) / self.score_scale
        centered = np.clip(scaled - self.location, -3.0 * self.span, 3.0 * self.span)
        standardized = centered / self.span
        return np.column_stack([
            standardized,
            standardized ** 2,
            np.maximum(standardized + 0.5, 0.0),
            np.maximum(standardized, 0.0),
            np.maximum(standardized - 0.5, 0.0),
        ])

    def fit(self, scores, outcomes):
        self.score_scale = float(np.max(np.abs(scores))) or 1.0
        scaled = scores / self.score_scale
        lower, upper = np.quantile(scaled, [0.1, 0.9])
        if upper <= lower:
            lower, upper = float(scaled.min()), float(scaled.max())
        self.location = 0.5 * lower + 0.5 * upper
        self.span = float(0.5 * (upper - lower)) or 1.0
        features = self._features(scores)
        self.feature_mean = features.mean(axis=0)
        self.feature_scale = features.std(axis=0)
        self.feature_scale[self.feature_scale < 1e-8] = 1.0
        design = (features - self.feature_mean) / self.feature_scale
        self.outcome_mean = float(np.mean(outcomes))
        centered_outcomes = outcomes - self.outcome_mean
        penalty = np.diag([0.1, 2.0, 4.0, 4.0, 4.0])
        self.coefficients = np.linalg.solve(
            design.T @ design + penalty, design.T @ centered_outcomes
        )
        return self

    def predict(self, scores):
        features = (self._features(scores) - self.feature_mean) / self.feature_scale
        prediction = self.outcome_mean + features @ self.coefficients
        return np.clip(prediction, 0.0, 1.0) if self.bounded else prediction


class AffineCalibrator:
    """Training-only affine score calibration, with bounded outcome clipping."""

    def __init__(self, bounded):
        self.bounded = bounded

    def fit(self, scores, outcomes):
        self.score_scale = float(np.max(np.abs(scores))) or 1.0
        scaled = scores / self.score_scale
        self.location = float(np.mean(scaled))
        self.span = float(np.std(scaled)) or 1.0
        standardized = (scaled - self.location) / self.span
        self.outcome_mean = float(np.mean(outcomes))
        denominator = float(standardized @ standardized)
        self.slope = (float(standardized @ (outcomes - self.outcome_mean)) / denominator
                      if denominator > 0.0 else 0.0)
        return self

    def predict(self, scores):
        standardized = (scores / self.score_scale - self.location) / self.span
        prediction = self.outcome_mean + self.slope * standardized
        return np.clip(prediction, 0.0, 1.0) if self.bounded else prediction


class FittedControl:
    """Apply the fitted finite-N multiplier once; controls may be signed."""

    def __init__(self, calibrator=None, control_weight=0.0):
        self.calibrator = calibrator
        self.control_weight = float(control_weight)
        self.lower_bound = min(0.0, self.control_weight)
        self.upper_bound = max(0.0, self.control_weight)

    def predict(self, scores):
        if self.calibrator is None or self.control_weight == 0.0:
            return np.zeros(scores.size)
        return self.control_weight * self.calibrator.predict(scores)


def _fit_control(family, training_scores, training_y, sample_ratio, bounded):
    if family == 'zero':
        return FittedControl()
    if family == 'affine':
        calibrator = AffineCalibrator(bounded)
    elif family == 'nonlinear':
        calibrator = ScoreCalibrator(bounded)
    else:
        raise ValueError("unknown control family")
    calibrator.fit(training_scores, training_y)
    training_control = calibrator.predict(training_scores)
    weight_denominator = (1.0 + sample_ratio) * np.var(training_control, ddof=1)
    control_scale = max(float(np.max(np.abs(training_control))), np.finfo(float).tiny)
    if (not np.isfinite(weight_denominator)
            or weight_denominator / control_scale / control_scale <= np.finfo(float).eps):
        return FittedControl()
    control_weight = np.cov(training_y, training_control, ddof=1)[0, 1] / weight_denominator
    if not np.isfinite(control_weight):
        return FittedControl()
    return FittedControl(calibrator, control_weight)


def _select_control(training_scores, training_y, sample_ratio, bounded, rng):
    """Paired one-standard-error risk rule on identical inner validation folds."""
    inner_fold_count = min(3, training_y.size // 2)
    inner_order = rng.permutation(training_y.size)
    inner_folds = np.array_split(inner_order, inner_fold_count)
    all_indices = np.arange(training_y.size)
    family_risks = {}
    for family in ('zero', 'affine', 'nonlinear'):
        fold_risks = []
        for validation_indices in inner_folds:
            fitting_indices = np.setdiff1d(all_indices, validation_indices, assume_unique=True)
            control = _fit_control(
                family, training_scores[fitting_indices], training_y[fitting_indices],
                sample_ratio, bounded,
            )
            validation_y = training_y[validation_indices]
            validation_control = control.predict(training_scores[validation_indices])
            risk_by_fold = np.var(validation_y - validation_control, ddof=1) + sample_ratio * np.var(validation_control, ddof=1)
            fold_risks.append(risk_by_fold)
        family_risks[family] = np.asarray(fold_risks)
    selected_family = 'zero'
    selected_fold_risks = family_risks[selected_family]
    for family in ('affine', 'nonlinear'):
        candidate_fold_risks = family_risks[family]
        paired_excess = candidate_fold_risks - selected_fold_risks
        risk_upper = np.mean(paired_excess) + np.std(paired_excess, ddof=1) / np.sqrt(paired_excess.size)
        if risk_upper < 0.0:
            selected_family = family
            selected_fold_risks = candidate_fold_risks
    return _fit_control(selected_family, training_scores, training_y, sample_ratio, bounded)


def bounded_mean_radius(sample_values, lower_bound, upper_bound, error_probability):
    """Two-sided empirical-Bernstein bound for an iid bounded mean."""
    if sample_values.size < 2 or not 0.0 < error_probability < 1.0:
        raise ValueError("invalid bounded-mean parameters")
    if (not np.isfinite(sample_values).all() or upper_bound < lower_bound
            or np.any(sample_values < lower_bound) or np.any(sample_values > upper_bound)):
        raise ValueError("values outside specified bounds")
    log_term = np.log(4.0 / error_probability)
    radius = np.sqrt(2.0 * np.var(sample_values, ddof=1) * log_term / sample_values.size) + 7.0 * (upper_bound - lower_bound) * log_term / (3.0 * (sample_values.size - 1))
    return min(float(radius), upper_bound - lower_bound)


def _control_statistics(labeled_y, unlabeled_scores, fold_controls):
    """Offset-invariant moments for fitted or independently fixed fold controls."""
    labeled_center = 0.0
    labeled_variance = 0.0
    unlabeled_control = np.zeros(unlabeled_scores.size)
    for heldout_indices, heldout_prediction, fold_unlabeled_prediction in fold_controls:
        fold_residuals = labeled_y[heldout_indices] - heldout_prediction
        fold_weight = heldout_indices.size / labeled_y.size
        labeled_center += fold_weight * np.mean(fold_residuals)
        fold_label_variance = fold_weight ** 2 * np.var(fold_residuals, ddof=1) / heldout_indices.size
        labeled_variance += fold_label_variance
        unlabeled_control += fold_weight * fold_unlabeled_prediction
    estimate = labeled_center + np.mean(unlabeled_control)
    variance = labeled_variance + np.var(unlabeled_control, ddof=1) / unlabeled_scores.size
    return float(estimate), float(variance)


def _crossfit_controls(labeled_y, labeled_scores, unlabeled_scores, alpha, bounded, rng):
    """Fit only on training labels and scores; reuse the single unlabeled pool."""
    n_folds = min(5, labeled_y.size // 2)
    order = rng.permutation(labeled_y.size)
    all_indices = np.arange(labeled_y.size)
    sample_ratio = labeled_y.size / unlabeled_scores.size
    fold_controls = []
    certified_radius = 0.0
    fold_error_probability = alpha / (2.0 * n_folds)
    for heldout_indices in np.array_split(order, n_folds):
        training_indices = np.setdiff1d(all_indices, heldout_indices, assume_unique=True)
        assert np.intersect1d(training_indices, heldout_indices).size == 0
        control = _select_control(
            labeled_scores[training_indices], labeled_y[training_indices],
            sample_ratio, bounded, rng,
        )
        heldout_prediction = control.predict(labeled_scores[heldout_indices])
        fold_unlabeled_prediction = control.predict(unlabeled_scores)
        fold_controls.append((heldout_indices, heldout_prediction, fold_unlabeled_prediction))
        fold_weight = heldout_indices.size / labeled_y.size
        if bounded:
            fold_residuals = labeled_y[heldout_indices] - heldout_prediction
            residual_radius = bounded_mean_radius(
                fold_residuals, -control.upper_bound, 1.0 - control.lower_bound,
                fold_error_probability,
            )
            control_radius = bounded_mean_radius(
                fold_unlabeled_prediction, control.lower_bound, control.upper_bound,
                fold_error_probability,
            )
            certified_radius += fold_weight * (residual_radius + control_radius)
    estimate, variance = _control_statistics(labeled_y, unlabeled_scores, fold_controls)
    return estimate, variance, certified_radius


def _interval_from_statistics(center, variance, count, alpha, bounded):
    radius = t.ppf(1 - alpha / 2, max(2, count - 6)) * math.sqrt(max(0.0, variance))
    lower, upper = float(center - radius), float(center + radius)
    if bounded:
        lower, upper = float(np.clip(lower, 0.0, 1.0)), float(np.clip(upper, 0.0, 1.0))
    return {"lower": lower, "upper": upper}


def _fit(values, settings):
    count, unlab_count = settings["n"], settings["N"]
    outcomes, predictions, unlab = np.split(values, [count, 2 * count])
    if not np.isfinite(values).all() or len(unlab) != unlab_count:
        raise ValueError("invalid values")
    kind, alpha = settings["label_kind"], settings["alpha"]
    if kind == "bernoulli" and not np.isin(outcomes, [0, 1]).all():
        raise ValueError("invalid outcomes")
    label_only = np.all(unlab == unlab[0]) or np.all(predictions == predictions[0]) or (
        kind == "bernoulli" and min(outcomes.sum(), count - outcomes.sum()) < 10
    )
    if label_only and kind != "bernoulli":
        return _label_only(outcomes, kind, alpha)
    center, variance, certified_radius = _crossfit_controls(
        outcomes, predictions, unlab, alpha, kind == "bernoulli", _state["rng"]
    )
    if kind == "bernoulli":
        _state["certificate"] = {
            "lower": float(np.clip(center - certified_radius, 0.0, 1.0)),
            "upper": float(np.clip(center + certified_radius, 0.0, 1.0)),
        }
    if label_only:
        return _label_only(outcomes, kind, alpha)
    return _interval_from_statistics(center, variance, count, alpha, kind == "bernoulli")


def handle(request):
    """Dispatch the exact reset/update/infer protocol in the module docstring."""
    global _state
    if type(request) is not dict:
        raise ValueError("invalid request")
    operation = request.get("op")
    if operation == "reset":
        _keys(request, "op seed")
        seed = request["seed"]
        if type(seed) is not int or not 0 <= seed < 2**63:
            raise ValueError("invalid seed")
        _state = {"rng": np.random.default_rng(seed), "phase": "reset"}
        return {"ok": True}
    if _state is None:
        raise ValueError("reset required")
    if operation == "infer":
        _keys(request, "op")
        if _state["phase"] != "fitted":
            raise ValueError("commit required")
        return dict(_state["interval"])
    if operation != "update":
        raise ValueError("unsupported operation")
    phase = request.get("phase")
    if phase == "start":
        _keys(request, "op phase n N alpha label_kind dtype encoding shape total_bytes chunks")
        count, unlab_count = request["n"], request["N"]
        if any(type(value) is not int or value < 8 for value in (count, unlab_count)):
            raise ValueError("invalid shape")
        length = 8 * (2 * count + unlab_count)
        if (_state["phase"] != "reset" or length > 8 * 1024**2
                or request["dtype"] != "<f8" or request["encoding"] != "base64"
                or request["shape"] != [2 * count + unlab_count]
                or type(request["total_bytes"]) is not int or request["total_bytes"] != length
                or type(request["chunks"]) is not int or request["chunks"] != math.ceil(length / 1024**2)
                or type(request["alpha"]) not in (int, float) or request["alpha"] != 0.05
                or request["label_kind"] not in ("bernoulli", "real")):
            raise ValueError("invalid transfer")
        _state.update(phase="buffer", settings=dict(request), buffer=bytearray(), next_index=0)
        return {"ok": True, "transfer_id": "buffer"}
    if _state["phase"] != "buffer" or request.get("transfer_id") != "buffer":
        raise ValueError("invalid transfer state")
    if phase == "chunk":
        _keys(request, "op phase transfer_id index data")
        index, settings = request["index"], _state["settings"]
        if type(index) is not int or index != _state["next_index"] or index >= settings["chunks"]:
            raise ValueError("invalid index")
        if type(request["data"]) is not str or len(request["data"]) > 1398104:
            raise ValueError("invalid base64")
        decoded = base64.b64decode(request["data"], validate=True)
        expected = min(1024**2, settings["total_bytes"] - len(_state["buffer"]))
        if len(decoded) != expected:
            raise ValueError("invalid chunk length")
        _state["buffer"].extend(decoded)
        _state["next_index"] += 1
        return {"ok": True}
    if phase == "commit":
        _keys(request, "op phase transfer_id")
        settings = _state["settings"]
        if len(_state["buffer"]) != settings["total_bytes"] or _state["next_index"] != settings["chunks"]:
            raise ValueError("incomplete transfer")
        interval = _fit(np.frombuffer(_state["buffer"], dtype="<f8"), settings)
        _state.pop("buffer")
        _state.pop("settings")
        _state.update(phase="fitted", interval=interval)
        return {"ok": True}
    raise ValueError("invalid phase")
