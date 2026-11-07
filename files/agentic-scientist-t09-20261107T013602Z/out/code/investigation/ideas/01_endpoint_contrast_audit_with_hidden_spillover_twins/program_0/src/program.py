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
        design = _features(_state['z'])
        penalty = np.eye(design.shape[1]) * 1e-3
        penalty[0, 0] = 0
        _state['coef'] = np.linalg.solve(design.T @ design + penalty, design.T @ _state['y'])
        return {'ok': True}
    if operation == 'predict':
        predictions = np.stack([_features(assignment) @ _state['coef'] for assignment in
                                (_state['z'], np.ones(_state['n']), np.zeros(_state['n']))])
        return {'encoding': 'base64', 'dtype': '<f8', 'shape': [3, _state['n']],
                'data': base64.b64encode(predictions.astype('<f8').tobytes()).decode('ascii')}
    raise ValueError('unsupported operation')
