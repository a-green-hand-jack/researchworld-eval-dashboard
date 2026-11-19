"""Exposure regression GATE starter: handle(request) -> finite JSON response.

All responses have EXACTLY the keys below; no optional/extra fields.
Seeds are arbitrary nonnegative integers, not booleans, for RNG only.
There is no cross-episode learning requirement, no feedback callback, and no
seed-to-workload mapping. Workload is conveyed by begin, uniformly in all runs.

reset {op:'reset', seed:int} -> {ok:true}; clear ALL episode state.
begin {op:'begin', n:int, arrays:[{name,dtype,shape,offset,nbytes}],
       total_bytes:int, chunks:int, sha256:str} -> {ok:true}.
  n=2..11586. Ordered arrays, C order, explicit little-endian dtype:
  edges '<i8' [m,2], x '<f8' [n,2], z '|u1' [n], y '<f8' [n],
  blocks '<i8' [n]. Contiguous byte offsets starting at zero.
  Edges are sorted unique undirected pairs 0<=left<right<n, no loops.
  x/y finite, z binary with both arms nonempty, blocks nonnegative integers.
  Logical input <=64 MiB; chunks=ceil(total_bytes/(8 MiB)), 1..8.
upload {op:'upload', index:int, encoding:'base64', data:str, sha256:str}
  -> {ok:true}. Zero-based ordered chunks, 8 MiB decoded except last;
  SHA-256 of decoded bytes. State is bounded candidate-owned RAM, never paths.
fit {op:'fit'} -> {basis:'linear'|'augmented', ridge:0|0.01|0.1|1,
                  coefficients:[float,...], gate:float}.
  Commits only after all chunks and whole-input SHA-256 verify.
  coefficients length 8 (linear) or 12 (augmented), abs<=1e6; abs(gate)<=1e6.
  Fit minimizes sum (y-F beta)^2 + ridge*sum(beta[1:]^2).
  Intercept is unpenalized; ridge=0 uses minimum norm, rcond=1e-12.
  e is mean neighbor treatment (zero for isolates); d is centered log1p(degree).
  Linear columns [1,z,x0,x1,d,z*x0,z*x1,e]; augmented appends
  [e^2,z*e,x0*e,x1*e]. No further feature standardization.
  gate = mean F(all-treated) beta - mean F(all-control) beta, recomputing
  exposure at endpoints with fixed x/topology. Isolated e remains zero.
  Independent evaluator fit/contrast tolerances atol=rtol=2e-6.
release {op:'release'} -> {ok:true}; release all input/model buffers.

Exactly reset, begin, ordered uploads, fit, release per episode. Each complete
framed JSON message is strictly below 64 MiB; fit response at most 1 MiB.
No hidden endpoint truth, mechanism coefficients, baseline outputs, scoring
metadata, host paths or plane identifiers are supplied. Recipe selection is
candidate-controlled; default recipe is augmented ridge 0.1.
Evaluator constructs block-sandwich intervals, not candidate-reported evidence.
"""

import base64
import hashlib
import math

import numpy as np


_state = {}
CHUNK = 8 * 1024 * 1024


def require(condition):
    if not condition:
        raise ValueError("invalid request")


def features(edges, covariates, treatment):
    count = len(treatment)
    degree = np.bincount(edges.ravel(), minlength=count).astype(float)
    neighbor = np.zeros(count)
    np.add.at(neighbor, edges[:, 0], treatment[edges[:, 1]])
    np.add.at(neighbor, edges[:, 1], treatment[edges[:, 0]])
    exposure = neighbor / np.maximum(degree, 1)
    centered = np.log1p(degree)
    centered -= centered.mean()
    first, second = covariates.T
    return np.column_stack([np.ones(count), treatment, first, second, centered,
                            treatment * first, treatment * second, exposure,
                            exposure ** 2, treatment * exposure,
                            first * exposure, second * exposure])


def handle(request):
    """Dispatch the documented finite JSON operation sequence."""
    global _state
    require(type(request) is dict)
    operation = request.get("op")
    if operation == "reset":
        require(set(request) == {"op", "seed"})
        require(type(request["seed"]) is int and request["seed"] >= 0)
        _state = {"rng": np.random.default_rng(request["seed"]), "phase": "reset"}
        return {"ok": True}
    if operation == "begin":
        require(_state.get("phase") == "reset")
        require(set(request) == {"op", "n", "arrays", "total_bytes", "chunks", "sha256"})
        count, total, chunks = request["n"], request["total_bytes"], request["chunks"]
        require(type(count) is int and 2 <= count <= 11586)
        require(type(total) is int and 0 < total <= 8 * CHUNK)
        require(type(chunks) is int and chunks == math.ceil(total / CHUNK))
        specifications = request["arrays"]
        require(type(specifications) is list and len(specifications) == 5)
        offset = 0
        for descriptor, name, dtype in zip(specifications,
                                           ["edges", "x", "z", "y", "blocks"],
                                           ["<i8", "<f8", "|u1", "<f8", "<i8"]):
            require(set(descriptor) == {"name", "dtype", "shape", "offset", "nbytes"})
            require(descriptor["name"] == name and descriptor["dtype"] == dtype)
            shape = descriptor["shape"]
            require(type(shape) is list and all(type(size) is int and size >= 0 for size in shape))
            if name == "edges":
                require(len(shape) == 2 and shape[1] == 2 and shape[0] <= count * (count - 1) // 2)
            else:
                require(shape == ([count, 2] if name == "x" else [count]))
            size = math.prod(shape) * np.dtype(dtype).itemsize
            require(descriptor["offset"] == offset and descriptor["nbytes"] == size)
            offset += size
        require(offset == total and type(request["sha256"]) is str and len(request["sha256"]) == 64)
        _state.update(phase="upload", header=request, buffer=bytearray(), next_chunk=0)
        return {"ok": True}
    if operation == "upload":
        require(set(request) == {"op", "index", "encoding", "data", "sha256"})
        require(_state.get("phase") == "upload" and request["encoding"] == "base64")
        require(type(request["index"]) is int and request["index"] == _state["next_chunk"])
        require(type(request["data"]) is str and len(request["data"]) <= 4 * math.ceil(CHUNK / 3))
        decoded = base64.b64decode(request["data"], validate=True)
        remaining = _state["header"]["total_bytes"] - len(_state["buffer"])
        require(0 < len(decoded) == min(CHUNK, remaining))
        require(hashlib.sha256(decoded).hexdigest() == request["sha256"])
        _state["buffer"].extend(decoded)
        _state["next_chunk"] += 1
        return {"ok": True}
    if operation == "fit":
        require(set(request) == {"op"} and _state.get("phase") == "upload")
        header, buffer = _state["header"], _state["buffer"]
        require(_state["next_chunk"] == header["chunks"] and len(buffer) == header["total_bytes"])
        require(hashlib.sha256(buffer).hexdigest() == header["sha256"])
        arrays = {}
        for descriptor in header["arrays"]:
            arrays[descriptor["name"]] = np.frombuffer(
                buffer, dtype=descriptor["dtype"], count=math.prod(descriptor["shape"]),
                offset=descriptor["offset"]).reshape(descriptor["shape"])
        edges, covariates, treatment = arrays["edges"], arrays["x"], arrays["z"]
        require(all(np.isfinite(values).all() for values in arrays.values()))
        require(np.all((treatment == 0) | (treatment == 1)) and 0 < treatment.sum() < len(treatment))
        require(np.all(edges[:, 0] < edges[:, 1]) and np.all(edges >= 0) and np.all(edges < len(treatment)))
        full_features = features(edges, covariates, treatment)
        treated_features = features(edges, covariates, np.ones(len(treatment)))
        control_features = features(edges, covariates, np.zeros(len(treatment)))
        contrast = treated_features.mean(axis=0) - control_features.mean(axis=0)
        outcomes = arrays["y"]
        basis, ridge = select_recipe(full_features, contrast, outcomes, arrays["blocks"])
        column_count = 8 if basis == 'linear' else 12
        selected_features = full_features[:, :column_count]
        coefficients = fit_coefficients(selected_features, outcomes, ridge)
        gate = float(contrast[:column_count] @ coefficients)
        _state["phase"] = "fit"
        return {'basis': basis, 'ridge': ridge, 'coefficients': coefficients.tolist(), 'gate': gate}
    if operation == "release":
        require(set(request) == {"op"} and _state.get("phase") == "fit")
        _state = {"phase": "released"}
        return {"ok": True}
    raise ValueError("unknown operation")


def fit_coefficients(selected_features, outcomes, ridge):
    column_count = selected_features.shape[1]
    penalty = np.sqrt(ridge) * np.eye(column_count)
    penalty[0, 0] = 0.0
    stacked_features = np.vstack((selected_features, penalty))
    stacked_outcomes = np.concatenate((outcomes, np.zeros(column_count)))
    coefficients = np.linalg.lstsq(stacked_features, stacked_outcomes, rcond=1e-12)[0]
    return coefficients


def select_recipe(full_features, contrast, outcomes, blocks):
    """Use a predictive stability heuristic, not an identified GATE-risk estimate.

    Weights and folds depend only on the observed design, never outcome values.
    Frozen full-graph features retain all neighbors and population centering.
    Squared representer weights omit cross-node residual products; clipping and
    uniform mixing further separate this criterion from endpoint estimation risk.
    Blocks need not be independent, and training folds overlap, so the block
    standard error is not a valid confidence interval or a coverage guarantee.
    """
    recipes = [(basis, ridge) for basis in ('linear', 'augmented') for ridge in (0.0, 0.01, 0.1, 1.0)]
    default_recipe_index = recipes.index(('augmented', 0.1))
    default_recipe = recipes[default_recipe_index]
    block_labels, block_indices, block_counts = np.unique(
        blocks, return_inverse=True, return_counts=True)
    if len(block_labels) < 10 or len(outcomes) < 2 * full_features.shape[1]:
        return default_recipe
    if not np.isfinite(full_features).all() or not np.isfinite(contrast).all():
        return default_recipe

    node_weights = np.full(len(outcomes), 1.0 / len(outcomes))
    try:
        with np.errstate(over='raise', invalid='raise', divide='raise'):
            target_penalty = np.sqrt(0.1) * np.eye(full_features.shape[1])
            target_penalty[0, 0] = 0.0
            target_stack = np.vstack((full_features, target_penalty))
            target_weights = np.linalg.lstsq(target_stack.T, contrast, rcond=1e-12)[0][:len(outcomes)]
            squared_weights = target_weights ** 2
            capped_weights = np.minimum(squared_weights, np.quantile(squared_weights, 0.95))
            if np.isfinite(capped_weights).all() and capped_weights.sum() > 0.0:
                node_weights = 0.5 / len(outcomes) + 0.5 * capped_weights / capped_weights.sum()
        if not np.isfinite(node_weights).all() or not np.isclose(node_weights.sum(), 1.0):
            node_weights = np.full(len(outcomes), 1.0 / len(outcomes))
    except (np.linalg.LinAlgError, FloatingPointError, ValueError, OverflowError):
        node_weights = np.full(len(outcomes), 1.0 / len(outcomes))

    fold_loads = np.zeros(5, dtype=np.int64)
    block_folds = np.empty(len(block_labels), dtype=np.int64)
    for block_index in np.argsort(-block_counts, kind='stable'):
        fold_index = int(np.argmin(fold_loads))
        block_folds[block_index] = fold_index
        fold_loads[fold_index] += block_counts[block_index]
    node_folds = block_folds[block_indices]
    out_of_fold_predictions = np.full((len(outcomes), len(recipes)), np.nan)
    try:
        with np.errstate(over='raise', invalid='raise', divide='raise'):
            for fold_index in range(5):
                validation_indices = np.flatnonzero(node_folds == fold_index)
                training_indices = np.flatnonzero(node_folds != fold_index)
                if not len(validation_indices) or len(training_indices) < 2 * full_features.shape[1]:
                    return default_recipe
                assert not np.intersect1d(blocks[training_indices], blocks[validation_indices]).size
                for recipe_index, (basis, ridge) in enumerate(recipes):
                    column_count = 8 if basis == 'linear' else 12
                    training_features = full_features[training_indices, :column_count]
                    training_coefficients = fit_coefficients(training_features, outcomes[training_indices], ridge)
                    if not np.isfinite(training_coefficients).all():
                        return default_recipe
                    out_of_fold_predictions[validation_indices, recipe_index] = full_features[validation_indices, :column_count] @ training_coefficients
            if not np.isfinite(out_of_fold_predictions).all():
                return default_recipe
            squared_errors = (outcomes[:, None] - out_of_fold_predictions) ** 2
            paired_node_losses = squared_errors - squared_errors[:, [default_recipe_index]]
            weighted_node_losses = node_weights[:, None] * paired_node_losses
            block_losses = np.zeros((len(block_labels), len(recipes)))
            np.add.at(block_losses, block_indices, weighted_node_losses)
            block_losses *= len(block_labels)
            paired_mean = block_losses.mean(axis=0)
            paired_se = block_losses.std(axis=0, ddof=1) / np.sqrt(len(block_labels))
            if not np.isfinite(paired_mean).all() or not np.isfinite(paired_se).all():
                return default_recipe
            if not np.allclose(paired_mean, weighted_node_losses.sum(axis=0), rtol=1e-10, atol=1e-12):
                return default_recipe
            selected_recipe_index = int(np.argmin(paired_mean + paired_se)) if np.min(paired_mean + paired_se) < 0.0 else default_recipe_index
    except (np.linalg.LinAlgError, FloatingPointError, ValueError, OverflowError):
        return default_recipe
    return recipes[selected_recipe_index]
