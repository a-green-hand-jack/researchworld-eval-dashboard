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

Candidate: exact hypergeometric score-partition portfolio for the realized
pooled sample, extended to the documented E[Y] target by a binomial envelope.
Finite-sample coverage requires iid labeled/unlabeled pairs from a common
population and a frozen, independently trained predictor. The RPC alone cannot
establish these sampling assumptions. No finite-pool target is substituted for
E[Y]. See METHOD.md for the proof, alpha allocation and unrun experiment plans.
No universal width improvement or measured performance is claimed.
"""
import base64
import numpy as np
from scipy.special import betaincinv
from scipy.stats import hypergeom


def hypergeometric_total_interval(population_size, sample_size, observed_successes, alpha):
    """Invert inclusive tails; exclude totals with either tail <= alpha/2."""
    if any(type(value) is not int for value in (population_size, sample_size, observed_successes)):
        raise ValueError("integer counts required")
    if not 0 <= observed_successes <= sample_size <= population_size or not 0 < alpha < 1:
        raise ValueError("invalid counts or error budget")
    if sample_size == 0: return 0, population_size
    if sample_size == population_size: return observed_successes, observed_successes
    feasible_lower = observed_successes
    feasible_upper = population_size - sample_size + observed_successes
    left, right = feasible_lower, feasible_upper
    while left < right:
        candidate_total = (left + right) // 2
        tail = hypergeom.sf(observed_successes - 1, population_size, candidate_total, sample_size)
        if not np.isfinite(tail):
            raise ArithmeticError("nonfinite hypergeometric survival probability")
        if tail > alpha / 2:
            right = candidate_total
        else:
            left = candidate_total + 1
    lower_total = left
    left, right = feasible_lower, feasible_upper
    while left < right:
        candidate_total = (left + right + 1) // 2
        tail = hypergeom.cdf(observed_successes, population_size, candidate_total, sample_size)
        if not np.isfinite(tail):
            raise ArithmeticError("nonfinite hypergeometric cumulative probability")
        if tail > alpha / 2:
            left = candidate_total
        else:
            right = candidate_total - 1
    return lower_total, left


def score_partitions(scores):
    """Freeze distinct, tie-respecting pooled-score quantile partitions."""
    scores = np.asarray(scores, dtype=np.float64)
    if scores.ndim != 1 or scores.size == 0 or not np.isfinite(scores).all():
        raise ValueError("finite nonempty score vector required")
    partitions = []
    seen = set()
    for requested_bins in (1, 2, 4, 8):
        if requested_bins == 1:
            assignment = np.zeros(scores.size, dtype=np.int8)
            population_counts = np.array([scores.size], dtype=np.int64)
        else:
            cuts = np.unique(np.quantile(scores, np.arange(1, requested_bins) / requested_bins))
            raw_assignment = np.searchsorted(cuts, scores, side="right")
            _, assignment, population_counts = np.unique(raw_assignment, return_inverse=True, return_counts=True)
            assignment = assignment.astype(np.int8)
        signature = assignment.tobytes()
        if signature not in seen:
            seen.add(signature)
            partitions.append((assignment, population_counts))
    return partitions


def exact_score_portfolio(scores, labeled_indices, labeled_outcomes, alpha=0.05):
    """Fixed-pool binary mean CI; validity requires SRS without replacement.

    Outcomes outside labeled_indices are never accepted by this function.
    Population-empty strata are removed; sample-empty strata retain [0, M_k].
    """
    partitions = score_partitions(scores)
    population_size = len(scores)
    labeled_indices = np.asarray(labeled_indices)
    labeled_outcomes = np.asarray(labeled_outcomes, dtype=np.float64)
    if labeled_indices.ndim != 1 or labeled_indices.dtype.kind not in "iu":
        raise ValueError("integer labeled-index vector required")
    if labeled_outcomes.shape != labeled_indices.shape or not np.isfinite(labeled_outcomes).all():
        raise ValueError("one finite outcome per labeled index required")
    if np.any((labeled_outcomes != 0) & (labeled_outcomes != 1)):
        raise ValueError("binary outcomes required")
    if np.any(labeled_indices < 0) or np.any(labeled_indices >= population_size):
        raise ValueError("labeled index outside score pool")
    if np.unique(labeled_indices).size != labeled_indices.size or not 0 < alpha < 1:
        raise ValueError("distinct labeled indices and valid alpha required")
    partition_alpha = alpha / len(partitions)
    candidate_intervals = []
    for assignment, population_counts in partitions:
        stratum_alpha = partition_alpha / len(population_counts)
        labeled_strata = assignment[labeled_indices]
        sample_counts = np.bincount(labeled_strata, minlength=len(population_counts))
        success_counts = np.bincount(labeled_strata, weights=labeled_outcomes, minlength=len(population_counts))
        stratum_lower_totals = []
        stratum_upper_totals = []
        for stratum_index, stratum_size in enumerate(population_counts):
            lower_total, upper_total = hypergeometric_total_interval(
                int(stratum_size), int(sample_counts[stratum_index]),
                int(success_counts[stratum_index]), stratum_alpha,
            )
            stratum_lower_totals.append(lower_total)
            stratum_upper_totals.append(upper_total)
        candidate_lower = float(np.sum(stratum_lower_totals) / population_size)
        candidate_upper = float(np.sum(stratum_upper_totals) / population_size)
        candidate_intervals.append((candidate_lower, candidate_upper))
    portfolio_lower = max(interval[0] for interval in candidate_intervals)
    portfolio_upper = min(interval[1] for interval in candidate_intervals)
    if portfolio_lower > portfolio_upper: return 0.0, 1.0
    return portfolio_lower, portfolio_upper


def iid_population_interval(labels, predictions, unlabeled, alpha=0.05):
    """Protect E[Y], not just the realized pooled-sample prevalence.

    Assumption: all labeled/unlabeled pairs are iid from one distribution,
    with the frozen predictor independent of these pairs. Conditional on the
    unordered full pool, the labeled positions are a uniform subset. The
    unobserved full-pool binary total is marginally Binomial(M, E[Y]).
    """
    labels = np.asarray(labels, dtype=np.float64)
    predictions = np.asarray(predictions, dtype=np.float64)
    unlabeled = np.asarray(unlabeled, dtype=np.float64)
    if labels.ndim != 1 or predictions.shape != labels.shape or unlabeled.ndim != 1:
        raise ValueError("invalid paired arrays")
    scores = np.concatenate((predictions, unlabeled))
    population_size = len(scores)
    population_alpha = alpha / 10
    pooled_lower, pooled_upper = exact_score_portfolio(
        scores, np.arange(labels.size), labels, alpha=alpha - population_alpha,
    )
    lower_total = int(round(population_size * pooled_lower))
    upper_total = int(round(population_size * pooled_upper))
    lower = 0.0 if lower_total == 0 else float(betaincinv(
        lower_total, population_size - lower_total + 1, population_alpha / 2,
    ))
    upper = 1.0 if upper_total == population_size else float(betaincinv(
        upper_total + 1, population_size - upper_total, 1 - population_alpha / 2,
    ))
    estimate = float(labels.mean())
    if not np.isfinite(lower) or not np.isfinite(upper) or lower > upper:
        return estimate, 0.0, 1.0
    return estimate, lower, upper

_state = None


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
    values = np.frombuffer(_state["buffer"], dtype="<f8")
    labeled_size, unlabeled_size = metadata["n"], metadata["N"]
    labels = values[:labeled_size]
    predictions = values[labeled_size:2 * labeled_size]
    unlabeled = values[2 * labeled_size:]
    if not np.isfinite(values).all() or np.any(values < 0) or np.any(values > 1) or np.any((labels != 0) & (labels != 1)):
        raise ValueError("invalid array values")
    estimate, lower, upper = iid_population_interval(
        labels, predictions, unlabeled, alpha=metadata["alpha"],
    )
    _state["done"] = True
    _state["buffer"] = bytearray()
    return {"estimate": float(estimate), "lower": lower, "upper": upper}
