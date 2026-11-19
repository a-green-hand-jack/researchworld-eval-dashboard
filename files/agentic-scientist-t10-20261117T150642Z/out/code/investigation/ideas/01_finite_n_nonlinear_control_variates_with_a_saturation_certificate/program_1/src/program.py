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

Candidate: five-fold score-only spline/ridge control variates with finite-N
shrinkage. Constant/rare inputs retain the label-only fallback (Clopper-Pearson
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


def _crossfit_controls(labeled_y, labeled_scores, unlabeled_scores, alpha, bounded, rng):
    """Reuse one unlabeled pool; do not treat fold-specific means as independent."""
    n_folds = min(5, labeled_y.size // 2)
    order = rng.permutation(labeled_y.size)
    all_indices = np.arange(labeled_y.size)
    shrinkage = unlabeled_scores.size / (labeled_scores.size + unlabeled_scores.size)
    heldout_residuals = np.empty(labeled_y.size)
    unlabeled_control = np.zeros(unlabeled_scores.size)
    certified_radius = 0.0
    fold_error_probability = alpha / (2.0 * n_folds)
    for heldout_indices in np.array_split(order, n_folds):
        training_indices = np.setdiff1d(all_indices, heldout_indices, assume_unique=True)
        assert np.intersect1d(training_indices, heldout_indices).size == 0
        calibrator = ScoreCalibrator(bounded=bounded)
        calibrator.fit(labeled_scores[training_indices], labeled_y[training_indices])
        if bounded:
            heldout_calibration = np.clip(calibrator.predict(labeled_scores[heldout_indices]), 0.0, 1.0)
            fold_unlabeled_prediction = np.clip(calibrator.predict(unlabeled_scores), 0.0, 1.0)
        else:
            heldout_calibration = calibrator.predict(labeled_scores[heldout_indices])
            fold_unlabeled_prediction = calibrator.predict(unlabeled_scores)
        heldout_residuals[heldout_indices] = labeled_y[heldout_indices] - shrinkage * heldout_calibration
        fold_weight = heldout_indices.size / labeled_y.size
        unlabeled_control += fold_weight * shrinkage * fold_unlabeled_prediction
        if bounded:
            fold_residuals = heldout_residuals[heldout_indices]
            residual_radius = bounded_mean_radius(fold_residuals, -shrinkage, 1.0, fold_error_probability)
            control_radius = bounded_mean_radius(shrinkage * fold_unlabeled_prediction, 0.0, shrinkage, fold_error_probability)
            certified_radius += fold_weight * (residual_radius + control_radius)
    estimate = np.mean(heldout_residuals) + np.mean(unlabeled_control)
    variance = np.var(heldout_residuals, ddof=1) / labeled_y.size + np.var(unlabeled_control, ddof=1) / unlabeled_scores.size
    return float(estimate), float(variance), certified_radius


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
    radius = t.ppf(1 - alpha / 2, max(2, count - 6)) * math.sqrt(max(0.0, variance))
    lower, upper = float(center - radius), float(center + radius)
    if kind == "bernoulli":
        lower, upper = float(np.clip(lower, 0.0, 1.0)), float(np.clip(upper, 0.0, 1.0))
    return {"lower": lower, "upper": upper}


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
