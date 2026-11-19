"""Deterministic exposure-regression GATE candidate, not a universal causal model.

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

Six bases use linear, quadratic or hinge exposure terms, with or without
nonbacktracking two-hop augmentation, selected by centered/scaled ridge GCV.
Two-hop exposure is multiplicity-weighted walk exposure, not distinct distance-
two-neighbor exposure; triangles can contribute. GCV is a predictive heuristic,
not endpoint-optimal selection or a dependent-data confidence interval.
Concentrated exposures, correlated residuals, threshold spillovers and graph
misspecification can undermine endpoint extrapolation. Investigation is offline;
NumPy 1.26.4, SciPy 1.13.1, NetworkX 3.3 are installed. Use at most
two CPU cores and 8 GiB RAM; numerical threads default to one. No filesystem
exchange, candidate artifact output, network access or internal telemetry API.
"""

import base64

import numpy as np
from scipy.sparse import csr_matrix


_state = {}


def _prepare_graph():
    count = _state['n']
    edges = _state['edges']
    sources = np.concatenate((edges[:, 0], edges[:, 1]))
    targets = np.concatenate((edges[:, 1], edges[:, 0]))
    adjacency = csr_matrix((np.ones(sources.size), (sources, targets)),
                           shape=(count, count))
    degree = np.asarray(adjacency.sum(axis=1)).ravel()
    two_hop_denominator = adjacency @ degree - degree
    _state['adjacency'] = adjacency
    _state['degree'] = degree
    _state['two_hop_denominator'] = two_hop_denominator


def _exposures(assignment):
    adjacency = _state['adjacency']
    degree = _state['degree']
    two_hop_denominator = _state['two_hop_denominator']
    neighbor_sum = adjacency @ assignment
    neighbor_exposure = neighbor_sum / np.maximum(degree, 1)
    two_hop_numerator = adjacency @ neighbor_sum - degree * assignment
    two_hop_exposure = np.divide(two_hop_numerator, two_hop_denominator, out=np.zeros_like(assignment, dtype=float), where=two_hop_denominator > 0)
    return neighbor_exposure, two_hop_exposure


def _features(assignment, family, include_two_hop, exposures):
    neighbor_exposure, two_hop_exposure = exposures
    columns = [_state['x'], np.log1p(_state['degree']), assignment,
               neighbor_exposure, assignment * neighbor_exposure]
    if family == 'quadratic':
        columns.append(neighbor_exposure ** 2)
    elif family == 'hinge':
        columns.append(np.maximum(neighbor_exposure[:, None] -
                                  np.array([.25, .5, .75]), 0))
    if include_two_hop:
        columns.extend((two_hop_exposure, assignment * two_hop_exposure))
        if family == 'quadratic':
            columns.append(two_hop_exposure ** 2)
    return np.column_stack(columns)


def _fit_multihop_gcv(assignment, outcome):
    centered_outcome = outcome - outcome.mean()
    penalties = outcome.size * np.array([1e-8, 1e-6, 1e-4, 1e-2, 1.0])
    bases = (('linear', False), ('quadratic', False), ('linear', True),
             ('hinge', False), ('quadratic', True), ('hinge', True))
    exposures = _exposures(assignment)
    best_model = None
    best_gcv = np.inf
    for family, include_two_hop in bases:
        design = _features(assignment, family, include_two_hop, exposures)
        retained = np.ptp(design, axis=0) > 0
        design = design[:, retained]
        center = design.mean(axis=0)
        centered_design = design - center
        scale = np.sqrt(np.mean(centered_design ** 2, axis=0))
        standardized_design = centered_design / scale
        left_vectors, singular_values, right_vectors = np.linalg.svd(standardized_design, full_matrices=False)
        projected_outcome = left_vectors.T @ centered_outcome
        for penalty in penalties:
            shrinkage = singular_values ** 2 / (singular_values ** 2 + penalty)
            fitted_centered = left_vectors @ (shrinkage * (left_vectors.T @ centered_outcome))
            effective_df = 1.0 + float(np.sum(shrinkage))
            gcv = float(np.mean((centered_outcome - fitted_centered) ** 2) / max(1.0 - effective_df / outcome.size, 1e-8) ** 2)
            if best_model is None or gcv < best_gcv - 1e-12 * max(1.0, abs(best_gcv)):
                coefficients = right_vectors.T @ (
                    singular_values / (singular_values ** 2 + penalty) *
                    projected_outcome)
                best_gcv = gcv
                best_model = {'family': family, 'include_two_hop': include_two_hop,
                              'retained': retained, 'center': center, 'scale': scale,
                              'coefficients': coefficients,
                              'intercept': float(outcome.mean())}
    return best_model


def _predict_multihop(assignment, model):
    design = _features(assignment, model['family'], model['include_two_hop'],
                       _exposures(assignment))
    standardized_design = (design[:, model['retained']] - model['center']) / model['scale']
    return model['intercept'] + standardized_design @ model['coefficients']


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
        outcome = _state['y']
        _state['constant_outcome'] = bool(np.all(outcome == outcome[0]))
        _state['constant_value'] = float(outcome[0])
        if not _state['constant_outcome']:
            _prepare_graph()
            _state['model'] = _fit_multihop_gcv(_state['z'], _state['y'])
        return {'ok': True}
    if operation == 'predict':
        if _state['constant_outcome']:
            predictions = np.full((3, _state['n']), _state['constant_value'], dtype=np.float64)
        else:
            predictions = np.stack([_predict_multihop(assignment, _state['model']) for assignment in (_state['z'], np.ones(_state['n']), np.zeros(_state['n']))])
        return {'encoding': 'base64', 'dtype': '<f8', 'shape': [3, _state['n']],
                'data': base64.b64encode(predictions.astype('<f8').tobytes()).decode('ascii')}
    raise ValueError('unsupported operation')
