"""Deterministic exposure-regression GATE starter, not a universal causal model.

Only handle(request) is public. All objects are finite JSON; no extra response
keys are allowed. No operation accepts paths. Seeds are arbitrary nonnegative
integers and initialize randomness only, never a workload or plane selector.

reset: {op:'reset', seed:int} -> {ok:true}. Clears every episode buffer/model.
ingest: {op:'ingest', index:int, total:int, n:int, p:int, m:int, layout:list,
         encoding:'base64', dtype:'packed-le', data:str} -> {ok:true}.
After reset, send 1..8 consecutive chunks, index 0..total-1, each <=4 MiB
decoded, total <=32 MiB. Repeated metadata must agree. n<=12000, 1<=p<=8,
m<=600000. Concatenate in memory; layout is edges[m,2] little-endian int32,
raw covariates[n,p] little-endian float64 row-major, treatment[n] uint8,
observed outcomes[n] little-endian float64.
The layout lists four objects in that order, each with exactly name, dtype,
shape and offset_bytes. Names: edges/covariates/treatment/observed; dtypes:
<i4/<f8/uint8/<f8; shapes: [m,2]/[n,p]/[n]/[n]; byte offsets:
0 / 8*m / (8*m+8*n*p) / (8*m+8*n*p+n). This is full-buffer metadata;
index/total describe byte chunks, not independent tensors.
Edges are unique undirected pairs u<v, no self-loops; isolates retained.
Ingest index zero starts transfer;
the last chunk commits automatically: no additional setup/commit operation.
Observed outcomes are legal training feedback; endpoint outcomes are withheld.
fit: {op:'fit'} -> {ok:true}. Exactly one dispatch after complete ingestion.
Candidate chooses its own model/regularization, using only supplied experiment.
predict: {op:'predict'} -> {encoding:'base64',dtype:'<f8',shape:[3,n],data:str}.
Exactly one dispatch after fit. Rows are node-aligned fitted outcome predictions
for observed assignment, all-treated, all-control, respectively. Finite float64
C-order payload <=4 MiB decoded, each prediction absolute value <=1e100.
No effect/score/success/state flags are used.
The evaluator computes the mean endpoint difference itself. Implementations
may use graph/covariate features and arbitrary CPU methods within role budgets.
No objective, case identifier, true GATE or private potential outcome is given.

Every case, matched constant/permuted control, and sole reset replay follows
the same operations and fit budget. Constant outcomes should produce zero
endpoint contrast (absolute tolerance 1e-6); node relabeling should commute with
predictions and reset replay reproduce them (rtol=atol=1e-6). Negative results
are eligible: correctness does not require outperforming any baseline.

The baseline uses unpenalized-intercept ridge, fixed one-hop hinges and own-
treatment/exposure interactions. Its fixed regularization is not claimed to
solve nonlinear extrapolation or omitted two-hop interference. Investigation
is offline; NumPy 1.26.4, SciPy 1.13.1, NetworkX 3.3 are installed. Use at most
two CPU cores and 8 GiB RAM; numerical threads default to one. No filesystem
exchange, candidate artifact output, network access or internal telemetry API.

The candidate tunes a quadratic exposure reference for endpoint-contrast risk.
For each fixed penalty, its risk estimate assumes a correct linear reference
and independent homoskedastic Gaussian errors. Selecting the minimum estimated
risk does not yield an unbiased post-selection risk estimate. Estimability is
checked, but does not establish endpoint support or robustness to misspecification.
Ineligible reference fits use the unchanged baseline regression instead.
"""

import base64

import numpy as np


_state = {}


def _features(assignment):
    count = _state['n']
    edges = _state['edges']
    degree = np.bincount(edges.ravel(), minlength=count)
    exposure = np.zeros(count)
    np.add.at(exposure, edges[:, 0], assignment[edges[:, 1]])
    np.add.at(exposure, edges[:, 1], assignment[edges[:, 0]])
    exposure /= np.maximum(degree, 1)
    hinges = np.maximum(exposure[:, None] - np.array([.25, .5, .75]), 0)
    return np.column_stack((np.ones(count), _state['x'], assignment, exposure,
                            hinges, assignment * exposure))


def _fit_incumbent(assignment, outcome):
    design = _features(assignment)
    penalty = np.eye(design.shape[1]) * 1e-3
    penalty[0, 0] = 0
    coefficients = np.linalg.solve(design.T @ design + penalty, design.T @ outcome)
    return {'kind': 'incumbent', 'coefficients': coefficients}


def _reference_features(assignment):
    edges = _state['edges']
    degree = np.bincount(edges.ravel(), minlength=_state['n'])
    exposure = np.zeros(_state['n'])
    np.add.at(exposure, edges[:, 0], assignment[edges[:, 1]])
    np.add.at(exposure, edges[:, 1], assignment[edges[:, 0]])
    exposure /= np.maximum(degree, 1)
    curvature = exposure * (1.0 - exposure)
    return np.column_stack((np.ones(_state['n']), _state['x'], assignment, exposure, assignment * exposure, curvature, assignment * curvature))


def _fit_endpoint_sure(assignment, outcome):
    observed_design = _reference_features(assignment)
    treated_design = _reference_features(np.ones(_state['n']))
    control_design = _reference_features(np.zeros(_state['n']))
    feature_mean = observed_design[:, 1:].mean(axis=0)
    feature_scale = observed_design[:, 1:].std(axis=0)
    feature_scale = np.where(feature_scale > 0.0, feature_scale, 1.0)
    standardized_design = (observed_design[:, 1:] - feature_mean) / feature_scale
    endpoint_contrast = (treated_design[:, 1:].mean(axis=0) - control_design[:, 1:].mean(axis=0)) / feature_scale
    outcome_mean = float(outcome.mean())
    centered_outcome = outcome - outcome_mean
    if not (np.all(np.isfinite(feature_mean))
            and np.all(np.isfinite(feature_scale))
            and np.all(np.isfinite(standardized_design))
            and np.all(np.isfinite(endpoint_contrast))
            and np.all(np.isfinite(centered_outcome))):
        return _fit_incumbent(assignment, outcome)
    try:
        left_vectors, singular_values, right_vectors = np.linalg.svd(
            standardized_design, full_matrices=False)
    except np.linalg.LinAlgError:
        return _fit_incumbent(assignment, outcome)
    if not (np.all(np.isfinite(singular_values))
            and np.all(np.isfinite(left_vectors))
            and np.all(np.isfinite(right_vectors))):
        return _fit_incumbent(assignment, outcome)
    retained = singular_values > max(standardized_design.shape) * np.finfo(np.float64).eps * singular_values[0]
    contrast_coordinates = right_vectors[retained] @ endpoint_contrast
    estimability_error = np.linalg.norm(endpoint_contrast - right_vectors[retained].T @ contrast_coordinates)
    if not np.isfinite(estimability_error):
        return _fit_incumbent(assignment, outcome)
    if estimability_error > 1e-8 * max(1.0, np.linalg.norm(endpoint_contrast)):
        return _fit_incumbent(assignment, outcome)
    if outcome.size - int(np.count_nonzero(retained)) - 1 <= 0:
        return _fit_incumbent(assignment, outcome)
    reference_weights = left_vectors[:, retained] @ (contrast_coordinates / singular_values[retained])
    projected_outcome = left_vectors[:, retained].T @ centered_outcome
    residual = centered_outcome - left_vectors[:, retained] @ projected_outcome
    noise_variance = float(residual @ residual) / (outcome.size - int(np.count_nonzero(retained)) - 1)
    reference_effect = float(reference_weights @ centered_outcome)
    if not (np.all(np.isfinite(reference_weights))
            and np.isfinite(noise_variance) and np.isfinite(reference_effect)):
        return _fit_incumbent(assignment, outcome)
    penalties = outcome.size * np.array([0.0, 1e-6, 1e-4, 1e-2, 1.0])
    risk_scores = []
    with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
        for penalty in penalties:
            contrast_weights = left_vectors[:, retained] @ (singular_values[retained] * contrast_coordinates / (singular_values[retained] ** 2 + penalty))
            risk_score = float((contrast_weights @ centered_outcome - reference_effect) ** 2 + 2.0 * noise_variance * (contrast_weights @ reference_weights) - noise_variance * (reference_weights @ reference_weights))
            risk_scores.append(risk_score if np.isfinite(risk_score) else np.inf)
    if not np.any(np.isfinite(risk_scores)):
        return _fit_incumbent(assignment, outcome)
    selected_index = int(np.argmin(risk_scores))
    penalty = penalties[selected_index]
    coefficients = right_vectors[retained].T @ (
        singular_values[retained] * projected_outcome
        / (singular_values[retained] ** 2 + penalty))
    if not np.all(np.isfinite(coefficients)):
        return _fit_incumbent(assignment, outcome)
    return {'kind': 'endpoint_sure', 'coefficients': coefficients,
            'feature_mean': feature_mean, 'feature_scale': feature_scale,
            'outcome_mean': outcome_mean}


def _predict_endpoint_sure(assignment, model):
    if model['kind'] == 'incumbent':
        return _features(assignment) @ model['coefficients']
    design = _reference_features(assignment)
    standardized_design = (design[:, 1:] - model['feature_mean']) / model['feature_scale']
    return model['outcome_mean'] + standardized_design @ model['coefficients']


def handle(request):
    operation = request['op']
    if operation == 'reset':
        _state.clear()
        _state['seed'] = request['seed']
        _state['chunks'] = []
        return {'ok': True}
    if operation == 'ingest':
        metadata = tuple(request[name] for name in ('n', 'p', 'm', 'total'))
        count, width, edge_count, total = metadata
        if not (0 < count <= 12000 and 0 < width <= 8 and 0 <= edge_count <= 600000
                and 0 < total <= 8 and request['index'] == len(_state['chunks'])):
            raise ValueError('invalid ingestion')
        if 'metadata' in _state and _state['metadata'] != metadata:
            raise ValueError('metadata changed')
        _state['metadata'] = metadata
        chunk = base64.b64decode(request['data'], validate=True)
        if len(chunk) > 4 * 1024 * 1024:
            raise ValueError('chunk too large')
        _state['chunks'].append(chunk)
        if len(_state['chunks']) == total:
            packed = b''.join(_state.pop('chunks'))
            expected = 8 * edge_count + 8 * count * width + 9 * count
            if len(packed) != expected or expected > 32 * 1024 * 1024:
                raise ValueError('invalid data length')
            _state['n'] = count
            _state['edges'] = np.frombuffer(packed, '<i4', 2 * edge_count).reshape(-1, 2)
            _state['x'] = np.frombuffer(packed, '<f8', count * width, 8 * edge_count).reshape(count, width)
            _state['z'] = np.frombuffer(packed, 'u1', count, 8 * edge_count + 8 * count * width).astype(float)
            _state['y'] = np.frombuffer(packed, '<f8', count, 8 * edge_count + 8 * count * width + count)
        return {'ok': True}
    if operation == 'fit':
        _state['constant_outcome'] = bool(np.all(_state['y'] == _state['y'][0]))
        if _state['constant_outcome']:
            _state['model'] = None
        else:
            _state['model'] = _fit_endpoint_sure(_state['z'], _state['y'])
        return {'ok': True}
    if operation == 'predict':
        if _state['constant_outcome']:
            predictions = np.full((3, _state['n']), float(_state['y'][0]), dtype=np.float64)
        else:
            predictions = np.stack([_predict_endpoint_sure(assignment, _state['model']) for assignment in (_state['z'], np.ones(_state['n']), np.zeros(_state['n']))])
        return {'encoding': 'base64', 'dtype': '<f8', 'shape': [3, _state['n']],
                'data': base64.b64encode(predictions.astype('<f8').tobytes()).decode('ascii')}
    raise ValueError('unsupported operation')
