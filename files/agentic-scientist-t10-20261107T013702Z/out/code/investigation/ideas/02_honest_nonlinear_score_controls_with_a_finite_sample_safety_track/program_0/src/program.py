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

Starter: two-fold cross-fitted ridge polynomial control variates (f,f^2,f^3),
training-fold GCV over fixed penalties; shared-unlabeled variance uses the average
coefficient, not independent fold variances. Small-event/constant fallback uses
exact Clopper-Pearson with the labeled mean. The selected composite procedure
is NOT asserted finite-sample valid; cross-fitting is asymptotic and Monte Carlo
nonrejection is not a proof. Negative/no-gain findings are legitimate. Fit labels
are already permitted study labels, not predictor training or active labeling.
Search eligibility has no required gain versus PPI++; evidence must be honest.
"""
import base64
import math

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
    import numpy as np
    from scipy.special import betaincinv, ndtri
    values = np.frombuffer(_state["buffer"], dtype="<f8")
    labeled_size, unlabeled_size = metadata["n"], metadata["N"]
    labels = values[:labeled_size]
    predictions = values[labeled_size:2 * labeled_size]
    unlabeled = values[2 * labeled_size:]
    if not np.isfinite(values).all() or np.any(values < 0) or np.any(values > 1) or np.any((labels != 0) & (labels != 1)):
        raise ValueError("invalid array values")
    count = int(labels.sum())
    alpha = metadata["alpha"]
    if min(count, labeled_size - count) < 5 or np.ptp(predictions) < 1e-12:
        estimate = float(labels.mean())
        lower = 0.0 if count == 0 else float(betaincinv(count, labeled_size - count + 1, alpha / 2))
        upper = 1.0 if count == labeled_size else float(betaincinv(count + 1, labeled_size - count, 1 - alpha / 2))
    else:
        basis = np.column_stack([predictions**power for power in (1, 2, 3)])
        basis_unlabeled = np.column_stack([unlabeled**power for power in (1, 2, 3)])
        folds = np.array_split(np.random.default_rng(_state["seed"]).permutation(labeled_size), 2)
        estimate = 0.0
        variance_labeled = 0.0
        average_coefficient = np.zeros(3)
        for fold_index, evaluation_indices in enumerate(folds):
            training_indices = folds[1 - fold_index]
            training_basis = basis[training_indices]
            centered = training_basis - training_basis.mean(axis=0)
            centered_labels = labels[training_indices] - labels[training_indices].mean()
            gram = centered.T @ centered / len(training_indices)
            cross = centered.T @ centered_labels / len(training_indices)
            options = []
            for penalty in (0.0001, 0.01, 1.0):
                coefficient = np.linalg.solve(gram + penalty * np.eye(3), cross)
                residuals = centered_labels - centered @ coefficient
                degrees = float(np.trace(np.linalg.solve(gram + penalty * np.eye(3), gram))) + 1
                gcv = float(np.mean(residuals**2) / (1 - degrees / len(training_indices))**2)
                options.append((gcv, coefficient))
            coefficient = min(options, key=lambda option: option[0])[1]
            weight = len(evaluation_indices) / labeled_size
            residuals = labels[evaluation_indices] - basis[evaluation_indices] @ coefficient
            estimate += weight * float(residuals.mean() + basis_unlabeled.mean(axis=0) @ coefficient)
            variance_labeled += weight**2 * float(np.var(residuals, ddof=1)) / len(evaluation_indices)
            average_coefficient += weight * coefficient
        variance = variance_labeled + float(np.var(basis_unlabeled @ average_coefficient, ddof=1)) / unlabeled_size
        radius = float(ndtri(1 - alpha / 2)) * math.sqrt(max(0.0, variance))
        lower, upper = max(0.0, min(1.0, estimate - radius)), max(0.0, min(1.0, estimate + radius))
        estimate = max(0.0, min(1.0, estimate))
    _state["done"] = True
    _state["buffer"] = bytearray()
    return {"estimate": float(estimate), "lower": lower, "upper": upper}
