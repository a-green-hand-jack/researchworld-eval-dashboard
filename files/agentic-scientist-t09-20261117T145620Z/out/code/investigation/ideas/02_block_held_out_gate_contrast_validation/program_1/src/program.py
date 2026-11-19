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
candidate-controlled; whole-block contrast validation selects among eight
recipes, with augmented ridge 0.1 as the fallback.
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


def fit_coefficients(selected_features, outcomes, ridge):
    column_count = selected_features.shape[1]
    penalty = np.sqrt(ridge) * np.eye(column_count)
    penalty[0, 0] = 0.0
    stacked_features = np.vstack((selected_features, penalty))
    stacked_outcomes = np.concatenate((outcomes, np.zeros(column_count)))
    coefficients = np.linalg.lstsq(stacked_features, stacked_outcomes, rcond=1e-12)[0]
    return coefficients


def select_recipe(full_features, outcomes, blocks, contrast):
    recipes = [(basis, ridge) for basis in ("linear", "augmented")
               for ridge in (0.0, 0.01, 0.1, 1.0)]
    default_recipe_index = recipes.index(("augmented", 0.1))
    fallback = recipes[default_recipe_index]
    block_labels, block_indices, block_sizes = np.unique(
        blocks, return_inverse=True, return_counts=True)
    if len(block_labels) < 10:
        return fallback
    if not (np.isfinite(full_features).all() and np.isfinite(contrast).all()):
        return fallback
    fold_count = 5
    fold_sizes = np.zeros(fold_count, dtype=np.int64)
    block_folds = np.empty(len(block_labels), dtype=np.int64)
    for block_index in np.argsort(-block_sizes, kind="stable"):
        fold_index = int(np.argmin(fold_sizes))
        block_folds[block_index] = fold_index
        fold_sizes[fold_index] += block_sizes[block_index]
    node_folds = block_folds[block_indices]
    fold_losses = np.empty((fold_count, len(recipes)))
    for fold_index in range(fold_count):
        validation_indices = np.flatnonzero(node_folds == fold_index)
        training_indices = np.flatnonzero(node_folds != fold_index)
        if validation_indices.size < 12 or training_indices.size < 12:
            return fallback
        assert not np.intersect1d(blocks[training_indices], blocks[validation_indices]).size
        validation_features = full_features[validation_indices, :12]
        left_vectors, singular_values, right_vectors = np.linalg.svd(validation_features, full_matrices=False)
        if not np.isfinite(singular_values).all() or singular_values[0] <= 0.0:
            return fallback
        retained = singular_values > 1e-12 * singular_values[0]
        contrast_coordinates = right_vectors[retained] @ contrast
        unrepresented_contrast = contrast - right_vectors[retained].T @ contrast_coordinates
        reference_estimable = np.linalg.norm(unrepresented_contrast) <= 1e-9 * max(1.0, np.linalg.norm(contrast))
        if not reference_estimable:
            return fallback
        validation_weights = left_vectors[:, retained] @ (contrast_coordinates / singular_values[retained])
        if not np.isfinite(validation_weights).all():
            return fallback
        validation_target = float(validation_weights @ outcomes[validation_indices])
        if not np.isfinite(validation_target):
            return fallback
        training_outcomes = outcomes[training_indices]
        for recipe_index, (basis, ridge) in enumerate(recipes):
            column_count = 8 if basis == "linear" else 12
            training_features = full_features[training_indices, :column_count]
            training_coefficients = fit_coefficients(training_features, training_outcomes, ridge)
            if not np.isfinite(training_coefficients).all():
                return fallback
            fold_gate = float(contrast[:column_count] @ training_coefficients)
            fold_losses[fold_index, recipe_index] = (fold_gate - validation_target) ** 2
    if not np.isfinite(fold_losses).all():
        return fallback
    paired_losses = fold_losses - fold_losses[:, [default_recipe_index]]
    paired_mean = paired_losses.mean(axis=0)
    paired_se = paired_losses.std(axis=0, ddof=1) / np.sqrt(fold_losses.shape[0])
    if not (np.isfinite(paired_mean).all() and np.isfinite(paired_se).all()):
        return fallback
    eligible = np.flatnonzero(paired_mean + paired_se < 0.0)
    if not eligible.size:
        return fallback
    selected_recipe_index = int(eligible[np.argmin(paired_mean[eligible])])
    return recipes[selected_recipe_index]


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
        blocks = arrays["blocks"]
        try:
            with np.errstate(over="raise", invalid="raise", divide="raise"):
                basis, ridge = select_recipe(full_features, outcomes, blocks, contrast)
        except (np.linalg.LinAlgError, FloatingPointError, OverflowError):
            basis, ridge = "augmented", 0.1
        column_count = 8 if basis == "linear" else 12
        selected_features = full_features[:, :column_count]
        coefficients = fit_coefficients(selected_features, outcomes, ridge)
        gate = float(contrast[:column_count] @ coefficients)
        _state["phase"] = "fit"
        return {"basis": basis, "ridge": ridge, "coefficients": coefficients.tolist(), "gate": gate}
    if operation == "release":
        require(set(request) == {"op"} and _state.get("phase") == "fit")
        _state = {"phase": "released"}
        return {"ok": True}
    raise ValueError("unknown operation")
