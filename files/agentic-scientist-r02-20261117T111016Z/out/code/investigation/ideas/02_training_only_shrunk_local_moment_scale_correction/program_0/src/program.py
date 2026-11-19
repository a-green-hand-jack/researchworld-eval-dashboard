"""Deterministic training-only scaled-ILR compositional regression starter.

Interface: handle(request: dict) -> dict, finite JSON only, no extra response keys.
Keep the entrypoint self-contained in this file; native validation stages only this
file plus installed packages, with a read-only filesystem and memory-only state.
Every request has exactly the keys shown below. Seed is any int in [0,2**63);
it initializes randomness and NEVER chooses a workload. No paths are accepted.

Operations/state transitions:
  reset: {op:'reset', seed:int} -> {ok:true}; clears ALL state, enters unfitted.
  predict: {op:'predict', x:array} -> {status:'unfitted'} until fit_scale completes.
    When fitted: {center:array, scale:array}, both shape [N,K-1], finite float64;
    center is in the fixed ILR basis, abs(center)<=100; scale in [1e-4,100].
    Read-only, deterministic for equal inputs; identical rows have equal outputs.
  fit_center: {op:'fit_center', x:array, y:array, dimension:int} -> {ok:true}.
    X [N,6], Y [N,K], K in {3,8}, positive rows summing to 1, training only.
    Fits center; invalidates scale, enters center-fitted but still unfitted.
  fit_scale: {op:'fit_scale'} -> {ok:true}; requires fit_center, uses retained
    TRAINING residuals only, enters fitted. No calibration/test labels provided.

Array schema (exact keys): {encoding:'base64', dtype:'float64', byte_order:'little',
  shape:[rows,columns], data:ASCII base64 of C-order little-endian float64 bytes}.
1<=N<=4096, columns<=8, each logical array <=1 MiB. Complete request/response
including envelope and newline must be <2 MiB (and strictly <64 MiB harness cap).
No state transfer or chunk operations exist: declared maximum shapes all fit inline;
larger logical inputs are rejected, never written to disk. Live model state <64 MiB.
Additional keys, nonfinite numbers, malformed encodings, and invalid state transitions
are errors, not diagnostics. Responses contain no optional keys or internal reports.

Basis convention: column j-1 (j=1..K-1) has first j entries 1/sqrt(j*(j+1)),
entry j equal to -j/sqrt(j*(j+1)), remaining entries zero. z=log(y) @ basis.
Inverse softmax(z @ basis.T). Evaluator owns calibration and region membership:
max(abs(z-center)/scale) <= independent split-conformal order statistic, separately
at alpha=.05,.10,.20. Targets to predict are observed continuous compositions,
not labels or latent categorical probabilities. Prediction queries do not identify
calibration/test membership, alpha, case, plane, targets, scores, or baselines.

Public workload: six continuous X features; K=3 or 8; logistic-normal IID,
heteroscedastic Dirichlet IID and covariate-shift stress. Training-only fitting can
be replaced within this exact output family. Evaluator also tests constant-input,
nonidentity-permuted-input, zero-radius copy-point, and reset/unfitted controls.
No superiority or realized-coverage threshold is a search eligibility requirement.
"""

import base64
import math

import numpy as np


_state = {}


def _decode(value):
    if type(value) is not dict or set(value) != {
        'encoding', 'dtype', 'byte_order', 'shape', 'data'
    }:
        raise ValueError('invalid array schema')
    shape = value['shape']
    if (value['encoding'] != 'base64' or value['dtype'] != 'float64'
            or value['byte_order'] != 'little' or type(shape) is not list
            or len(shape) != 2 or any(type(size) is not int for size in shape)
            or not 1 <= shape[0] <= 4096 or not 1 <= shape[1] <= 8):
        raise ValueError('invalid array metadata')
    raw = base64.b64decode(value['data'], validate=True)
    if len(raw) != math.prod(shape) * 8 or len(raw) > 1024 * 1024:
        raise ValueError('invalid array size')
    result = np.frombuffer(raw, dtype='<f8').reshape(shape).copy()
    if not np.isfinite(result).all():
        raise ValueError('nonfinite array')
    return result


def _encode(array):
    array = np.ascontiguousarray(array, dtype='<f8')
    return {'encoding': 'base64', 'dtype': 'float64', 'byte_order': 'little',
            'shape': list(array.shape), 'data': base64.b64encode(array.tobytes()).decode('ascii')}


def _basis(dimension):
    basis = np.zeros((dimension, dimension - 1))
    for column in range(1, dimension):
        denominator = math.sqrt(column * (column + 1))
        basis[:column, column - 1] = 1 / denominator
        basis[column, column - 1] = -column / denominator
    return basis


def _features(features):
    return np.column_stack((np.ones(len(features)), features, features ** 2,
                            np.sin(features), features[:, 0] * features[:, 1]))


def _ridge(features, targets, penalty):
    regularizer = np.eye(features.shape[1]) * penalty
    regularizer[0, 0] = 1e-8
    return np.linalg.solve(features.T @ features + regularizer, features.T @ targets)


def handle(request):
    if type(request) is not dict:
        raise ValueError('request must be object')
    operation = request.get('op')
    keys = {'reset': {'op', 'seed'}, 'predict': {'op', 'x'},
            'fit_center': {'op', 'x', 'y', 'dimension'}, 'fit_scale': {'op'}}
    if operation not in keys or set(request) != keys[operation]:
        raise ValueError('invalid operation schema')
    if operation == 'reset':
        seed = request['seed']
        if type(seed) is not int or not 0 <= seed < 2 ** 63:
            raise ValueError('invalid seed')
        _state.clear()
        _state['rng'] = np.random.default_rng(seed)
        return {'ok': True}
    if 'rng' not in _state:
        raise ValueError('reset required')
    if operation == 'fit_center':
        dimension = request['dimension']
        features, targets = _decode(request['x']), _decode(request['y'])
        if (type(dimension) is not int or dimension not in (3, 8)
                or features.shape[1] != 6 or targets.shape != (len(features), dimension)
                or not (targets > 0).all()
                or not np.allclose(targets.sum(axis=1), 1, atol=1e-10, rtol=0)):
            raise ValueError('invalid training data')
        design = _features(features)
        transformed = np.log(targets) @ _basis(dimension)
        coefficient = _ridge(design, transformed, 1.0)
        _state.update(coefficient=coefficient, design=design,
                      residual=transformed - design @ coefficient)
        _state.pop('scale_coefficient', None)
        return {'ok': True}
    if operation == 'fit_scale':
        if 'coefficient' not in _state:
            raise ValueError('center required')
        log_residual = np.log(np.maximum(abs(_state['residual']), .02))
        _state['scale_coefficient'] = _ridge(_state['design'], log_residual, 10.0)
        return {'ok': True}
    features = _decode(request['x'])
    if features.shape[1] != 6:
        raise ValueError('invalid feature shape')
    if 'scale_coefficient' not in _state:
        return {'status': 'unfitted'}
    design = _features(features)
    center = np.clip(design @ _state['coefficient'], -100, 100)
    scale = np.clip(np.exp(np.clip(design @ _state['scale_coefficient'], math.log(1e-4), math.log(100))), 1e-4, 100)
    return {'center': _encode(center), 'scale': _encode(scale)}
