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
candidate-controlled; selection uses observed contrast risk, with augmented
ridge 0.1 as the conservative fallback.
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


def contrast_certificate(features, treated_features, control_features,
                         noise_variance=1.0):
    """Conditional linear-model geometry, not a misspecification certificate.

    The variance is exact only for a fixed, correctly specified feature map
    with independent homoskedastic noise of the supplied variance. The RPC
    does not supply that variance; recipe selection uses unit-noise geometry
    and a separate empirical covariance estimate. Unsupported contrasts have
    no reported finite variance, even though a pseudoinverse still exists.
    """
    contrast = treated_features.mean(axis=0) - control_features.mean(axis=0)
    left_vectors, singular_values, right_vectors = np.linalg.svd(features, full_matrices=False)
    singular_tolerance = 1e-12 * singular_values[0]
    retained = singular_values > singular_tolerance
    contrast_coordinates = right_vectors[retained] @ contrast
    null_component = contrast - right_vectors[retained].T @ contrast_coordinates
    estimability_tolerance = 1e-9 * max(1.0, float(np.linalg.norm(contrast)))
    contrast_estimable = np.linalg.norm(null_component) <= estimability_tolerance
    contrast_variance = noise_variance * np.sum((contrast_coordinates / singular_values[retained]) ** 2)
    feature_pinv = ((right_vectors[retained].T / singular_values[retained])
                    @ left_vectors[:, retained].T)
    sensitivity = []
    for multiplier in (0.1, 1.0, 10.0):
        alternate = singular_values > multiplier * singular_tolerance
        coordinates = right_vectors[alternate] @ contrast
        remainder = contrast - right_vectors[alternate].T @ coordinates
        sensitivity.append({
            "rank": int(alternate.sum()),
            "estimable": bool(np.linalg.norm(remainder) <= estimability_tolerance),
            "variance_factor": float(np.sum((coordinates / singular_values[alternate]) ** 2))
            if np.linalg.norm(remainder) <= estimability_tolerance else None,
        })
    stable = all(item["rank"] == int(retained.sum()) for item in sensitivity)
    return {
        "contrast": contrast,
        "pinv": feature_pinv,
        "rank": int(retained.sum()),
        "estimable": bool(contrast_estimable),
        "variance": float(contrast_variance) if contrast_estimable else None,
        "null_norm": float(np.linalg.norm(null_component)),
        "rank_stable": stable,
        "sensitivity": sensitivity,
        "leverage": np.sum(left_vectors[:, retained] ** 2, axis=1),
    }


def fit_recipe(design, outcome, contrast, ridge, certificate):
    """Return the mandated least-squares fit and its outcome-linear weights."""
    if ridge == 0:
        inverse = certificate["pinv"]
    else:
        penalty = np.eye(design.shape[1]) * math.sqrt(ridge)
        penalty[0, 0] = 0
        penalized = np.vstack([design, penalty])
        left, singular, right = np.linalg.svd(penalized, full_matrices=False)
        retained = singular > 1e-12 * singular[0]
        inverse = ((right[retained].T / singular[retained])
                   @ left[:len(outcome), retained].T)
    coefficients = inverse @ outcome
    weights = contrast @ inverse
    return coefficients, weights


def select_recipe(design, treated_features, control_features, outcome, blocks):
    """Focused risk selection among exactly the permitted eight recipes.

    An estimable augmented OLS contrast is a noisy reference, never endpoint
    truth. For outcome weights a and reference weights b, the criterion is
    ((a-b)'y)^2 - Var((a-b)'y) + Var(a'y). This is an unbiased MSE criterion
    only with an unbiased reference and a known noise covariance. Here an
    HC2-adjusted block sandwich is plugged in, so selection is a heuristic,
    not an uncertainty guarantee. A one-standard-error improvement over the
    starter is required, and unsupported/unstable reference fits fall back.
    """
    recipes = []
    certificates = {}
    for basis, columns in (("linear", 8), ("augmented", 12)):
        observed = design[:, :columns]
        certificate = contrast_certificate(observed, treated_features[:, :columns],
                                           control_features[:, :columns])
        certificates[basis] = certificate
        for ridge in (0, 0.01, 0.1, 1):
            coefficients, weights = fit_recipe(observed, outcome,
                                               certificate["contrast"], ridge,
                                               certificate)
            estimated_gate = float(certificate["contrast"] @ coefficients)
            valid = bool(np.isfinite(coefficients).all()
                         and np.max(np.abs(coefficients)) <= 1e6
                         and np.isfinite(estimated_gate) and abs(estimated_gate) <= 1e6)
            recipes.append({"basis": basis, "ridge": ridge,
                            "coefficients": coefficients, "gate": estimated_gate,
                            "weights": weights, "valid": valid,
                            "supported": certificate["estimable"]})
    default_index, reference_index = 6, 4
    selected_index = default_index
    reference = certificates["augmented"]
    diagnostics = {
        "status": "regularized_fallback",
        "geometry": {basis: {key: value for key, value in certificate.items()
                              if key not in ("pinv", "leverage", "contrast")}
                     for basis, certificate in certificates.items()},
    }
    count = len(outcome)
    _, membership = np.unique(blocks, return_inverse=True)
    group_count = int(membership.max()) + 1
    residual_df = count - reference["rank"]
    diagnostics.update(block_count=group_count, residual_df=residual_df)
    if (reference["estimable"] and reference["rank_stable"] and residual_df > 0
            and group_count >= 4 and recipes[reference_index]["valid"]):
        residual = outcome - design @ recipes[reference_index]["coefficients"]
        leverage_margin = 1.0 - reference["leverage"]
        if np.min(leverage_margin) > 1e-8:
            adjusted_residual = residual / np.sqrt(leverage_margin)
            weights = np.column_stack([recipe["weights"] for recipe in recipes])
            contributions = weights * adjusted_residual[:, None]
            grouped = np.zeros((group_count, len(recipes)))
            np.add.at(grouped, membership, contributions)
            covariance = (group_count / (group_count - 1)) * (grouped.T @ grouped)
            reference_covariance = covariance[:, reference_index]
            delta_covariance = (covariance - reference_covariance[:, None]
                                - reference_covariance[None, :]
                                + covariance[reference_index, reference_index])
            delta_variance = np.maximum(np.diag(delta_covariance), 0.0)
            estimates = np.array([recipe["gate"] for recipe in recipes])
            differences = estimates - estimates[reference_index]
            risk = differences ** 2 - delta_variance + np.diag(covariance)
            signal = np.sign(differences) * np.sqrt(np.maximum(
                differences ** 2 - delta_variance, 0.0))
            for candidate_index, recipe in enumerate(recipes):
                if not recipe["valid"] or not recipe["supported"]:
                    continue
                cross_covariance = delta_covariance[candidate_index, default_index]
                candidate_variance = delta_variance[candidate_index]
                default_variance = delta_variance[default_index]
                risk_difference_variance = 2.0 * (
                    candidate_variance ** 2 + default_variance ** 2
                    - 2.0 * cross_covariance ** 2) + 4.0 * (
                        signal[candidate_index] ** 2 * candidate_variance
                        + signal[default_index] ** 2 * default_variance
                        - 2.0 * signal[candidate_index] * signal[default_index]
                        * cross_covariance)
                risk_margin = math.sqrt(max(0.0, float(risk_difference_variance)))
                if (risk[candidate_index] < risk[selected_index]
                        and risk[candidate_index] + risk_margin < risk[default_index]):
                    selected_index = candidate_index
            diagnostics.update(status="empirical_focused_selection",
                               risk=risk.tolist(),
                               variance=np.diag(covariance).tolist())
    if not recipes[selected_index]["valid"]:
        available = [index for index, recipe in enumerate(recipes) if recipe["valid"]]
        require(bool(available))
        selected_index = min(available, key=lambda index: (
            -recipes[index]["ridge"], recipes[index]["basis"] != "augmented"))
        diagnostics["status"] = "finite_fit_fallback"
    diagnostics["selected_index"] = selected_index
    selected = recipes[selected_index]
    selected_design = design[:, :len(selected["coefficients"])]
    penalty = np.eye(selected_design.shape[1]) * math.sqrt(selected["ridge"])
    penalty[0, 0] = 0
    coefficients = np.linalg.lstsq(
        np.vstack([selected_design, penalty]),
        np.concatenate([outcome, np.zeros(selected_design.shape[1])]),
        rcond=1e-12)[0]
    estimated_gate = float(certificates[selected["basis"]]["contrast"] @ coefficients)
    require(np.isfinite(coefficients).all() and np.max(np.abs(coefficients)) <= 1e6)
    require(np.isfinite(estimated_gate) and abs(estimated_gate) <= 1e6)
    response = {"basis": selected["basis"], "ridge": selected["ridge"],
                "coefficients": coefficients.tolist(), "gate": estimated_gate}
    return response, diagnostics


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
        design = features(edges, covariates, treatment)
        treated_features = features(edges, covariates, np.ones(len(treatment)))
        control_features = features(edges, covariates, np.zeros(len(treatment)))
        response, diagnostics = select_recipe(design, treated_features, control_features,
                                               arrays["y"], arrays["blocks"])
        degree = np.bincount(edges.ravel(), minlength=len(treatment))
        nonisolated = degree > 0
        observed_exposure = design[nonisolated, 7]
        diagnostics["nonisolated_count"] = int(nonisolated.sum())
        diagnostics["observed_tail_fraction"] = (float(np.mean(
            (observed_exposure < 0.25) | (observed_exposure > 0.75)))
            if observed_exposure.size else None)
        _state["diagnostics"] = diagnostics
        _state["phase"] = "fit"
        return response
    if operation == "release":
        require(set(request) == {"op"} and _state.get("phase") == "fit")
        _state = {"phase": "released"}
        return {"ok": True}
    raise ValueError("unknown operation")
