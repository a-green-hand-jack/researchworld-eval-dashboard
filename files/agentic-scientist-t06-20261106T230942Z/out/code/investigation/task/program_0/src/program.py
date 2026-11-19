"""Influence-guided binary outcome flips; CPU float64, deterministic and seed-independent workload.

The entrypoint is self-contained Python (installed NumPy/SciPy are available); native
validation copies only this entrypoint into its private sandbox, not adjacent files.
Only handle(request)->finite JSON response is public. Extra response keys are forbidden.
A reset accepts ANY nonnegative integer seed (not bool) and returns exactly {"ok":true};
it clears all buffers, results and prior tokens. It does not choose dataset or workload.
Immediately after reset, analyze({"op":"analyze","token":"input"}) must return
exactly {"error":"no_data"}; no data or prior proposal may survive reset.

Upload protocol (all data inline; never paths):
 upload_start: token="input", dtype="<f8", shape=[n,4], byte_length=32*n,
 chunks=ceil(byte_length/1048576), participants=p, home=boolean. Response {"ok":true}.
 n<=524288, p in [2,256], chunks<=16; at most 16MiB decoded in-memory input.
 upload_chunk: token="input", index=0..chunks-1, encoding="base64", data=ASCII base64.
 Each chunk <=1048576 decoded bytes, in order. Response {"ok":true}.
 upload_commit: token="input". Response {"ok":true}. Columns are participant indices
 a,b (integers represented as float64), observed y in {0,.5,1}, home covariate z in
 {-1,0,1}. No home nuisance is fitted if home=false. Ties fit as fractional outcomes
 but cannot be flipped. Inputs are observed comparisons, not held-out targets.
 analyze: token="input", counts=[k1,k2,k3] positive nondecreasing exact edit budgets,
 audit_rows=list of 8 legal row indices, ridge=1.0, iterations=positive integer.
 The estimator minimizes SUM(logaddexp(0,x*theta)-y*x*theta)+ridge/2*||theta||^2,
 where x=e_a-e_b plus optional home coordinate z. Participant scores are centered.
 Returns {"token":"result","dtype":"<f8","shape":[L],"byte_length":8*L,"chunks":c}.
 download_chunk: token="result", index=0..c-1. Returns exactly
 {"index":index,"encoding":"base64","data":ASCII base64}, <=1MiB decoded/chunk.

Result layout, concatenated little-endian float64 (d=p+int(home)):
 fitted theta[d]; directional row influences[n]; audit derivatives[8,d] row-major;
 ordered distinct selected binary row indices[max(counts)] as exact integer-valued
 floats; predicted shifts[3,d] row-major for the nested prefixes of those indices.
 L=d+n+8*d+max(counts)+3*d. No other diagnostics or fields are accepted.
 Target contrast t=e_lower-e_upper: sort participant scores decreasing with index as
 tie-break, among adjacent pairs in top min(10,p) choose smallest score gap (first
 gap breaks ties). Influence for row r is (1-2*y_r)*x_r @ inverse(H) @ t;
 audit derivative is inverse(H) @ x_r (UNIT outcome change, including ties).
 H is exact regularized Hessian at fitted theta. Predictions sum signed row
 derivatives for each selected prefix. Selection may improve on the starter's greedy
 priorities; actual refits, not claimed sensitivities, determine score. Exact influence
 arithmetic is audited independently; nonlinear approximation error is reported, not
 an advantage threshold. No claim of superiority is necessary for search eligibility.
 No objective, reference fit, baseline output or control feedback is returned.

Operation order: reset, stale analyze, upload_start, chunks, upload_commit, analyze,
 download chunks. No export/import of persistent state, replay, filesystem sharing,
 or additional resets. All messages <64MiB including JSON/framing (local 8MiB cap).
 The runner owns resource limits. Internal iteration counts are advisory only.
"""
import base64
import math
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit

_state = {}


def handle(request):
    global _state
    operation = request["op"]
    if operation == "reset":
        if type(request["seed"]) is not int or request["seed"] < 0:
            raise ValueError("invalid seed")
        _state = {"seed": request["seed"]}
        return {"ok": True}
    if operation == "upload_start":
        if request["dtype"] != "<f8" or request["shape"][1] != 4 or not 0 < request["byte_length"] <= 16 * 1048576:
            raise ValueError("invalid upload")
        _state.update(meta=dict(request), buffer=bytearray(), ordinal=0)
        return {"ok": True}
    if operation == "upload_chunk":
        if request["index"] != _state["ordinal"] or request["encoding"] != "base64":
            raise ValueError("chunk order")
        block = base64.b64decode(request["data"], validate=True)
        if len(block) > 1048576 or len(_state["buffer"]) + len(block) > _state["meta"]["byte_length"]:
            raise ValueError("chunk bounds")
        _state["buffer"].extend(block)
        _state["ordinal"] += 1
        return {"ok": True}
    if operation == "upload_commit":
        metadata = _state["meta"]
        if len(_state["buffer"]) != metadata["byte_length"] or _state["ordinal"] != metadata["chunks"]:
            raise ValueError("incomplete upload")
        _state["data"] = np.frombuffer(bytes(_state.pop("buffer")), dtype="<f8").reshape(metadata["shape"])
        return {"ok": True}
    if operation == "analyze":
        if "data" not in _state or request["token"] != "input":
            return {"error": "no_data"}
        data = _state["data"]
        metadata = _state["meta"]
        participants = metadata["participants"]
        dimension = participants + int(metadata["home"])
        endpoints = data[:, :2].astype(int)
        groups, inverse = np.unique(data[:, [0, 1, 3]], axis=0, return_inverse=True)
        design = np.zeros((len(groups), dimension))
        design[np.arange(len(groups)), groups[:, 0].astype(int)] = 1
        design[np.arange(len(groups)), groups[:, 1].astype(int)] = -1
        if metadata["home"]:
            design[:, -1] = groups[:, 2]
        multiplicity = np.bincount(inverse).astype(float)
        wins = np.bincount(inverse, weights=data[:, 2])
        ridge = request["ridge"]

        def objective(theta):
            logits = design @ theta
            value = np.sum(multiplicity * np.logaddexp(0, logits) - wins * logits) + ridge * np.dot(theta, theta) / 2
            gradient = design.T @ (multiplicity * expit(logits) - wins) + ridge * theta
            return value, gradient

        fitted = minimize(objective, np.zeros(dimension), jac=True, method="L-BFGS-B",
                          options={"maxiter": request["iterations"], "gtol": 1e-8, "ftol": 1e-15, "maxls": 40})
        theta = fitted.x
        theta[:participants] -= theta[:participants].mean()
        probability = expit(design @ theta)
        hessian = design.T @ ((multiplicity * probability * (1 - probability))[:, None] * design) + ridge * np.eye(dimension)
        rank = np.lexsort((np.arange(participants), -theta[:participants]))
        adjacent = rank[:min(10, participants)]
        position = int(np.argmin(theta[adjacent[:-1]] - theta[adjacent[1:]]))
        contrast = np.zeros(dimension)
        contrast[adjacent[position + 1]] = 1
        contrast[adjacent[position]] = -1
        direction = np.linalg.solve(hessian, contrast)
        row_design = np.zeros((len(data), dimension))
        row_design[np.arange(len(data)), endpoints[:, 0]] = 1
        row_design[np.arange(len(data)), endpoints[:, 1]] = -1
        if metadata["home"]:
            row_design[:, -1] = data[:, 3]
        influences = (1 - 2 * data[:, 2]) * (row_design @ direction)
        eligible = np.flatnonzero(data[:, 2] != .5)
        selected = eligible[np.lexsort((eligible, -influences[eligible]))][:max(request["counts"])]
        audits = np.linalg.solve(hessian, row_design[request["audit_rows"]].T).T
        predictions = []
        for count in request["counts"]:
            subset = selected[:count]
            gradient = row_design[subset].T @ (1 - 2 * data[subset, 2])
            predictions.append(np.linalg.solve(hessian, gradient))
        result = np.concatenate([theta, influences, audits.ravel(), selected.astype(float), np.asarray(predictions).ravel()]).astype("<f8").tobytes()
        if len(result) > 16 * 1048576:
            raise ValueError("result too large")
        _state["result"] = result
        return {"token": "result", "dtype": "<f8", "shape": [len(result) // 8], "byte_length": len(result), "chunks": math.ceil(len(result) / 1048576)}
    if operation == "download_chunk":
        index = request["index"]
        result = _state["result"]
        return {"index": index, "encoding": "base64", "data": base64.b64encode(result[index * 1048576:(index + 1) * 1048576]).decode("ascii")}
    raise ValueError("unknown operation")
