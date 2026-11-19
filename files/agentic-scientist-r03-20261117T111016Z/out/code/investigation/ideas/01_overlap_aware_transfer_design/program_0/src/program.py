"""CPU score-matrix prediction starter; only handle(request) is public.

All requests/responses are finite JSON objects. Additional response keys are forbidden.
All indices are zero-based, episode-local and opaque; no filenames or model IDs are used.
reset accepts ANY nonnegative integer seed and returns exactly {"ok": true}; it clears
all state. Seeds initialize randomness, never choose a workload or evaluation plane.

History upload (one per episode): upload_start fields shape=[M,N], dtype="float64",
byteorder="little", mask_dtype="uint8", encoding="base64", layout="values_then_mask",
nbytes=9*M*N, chunks=C. Bounds: 1<=M,N<=4096, 1<=C<=64, <=256 MiB logical data.
Returns {"ok": true}. upload_chunk fields index (sequential 0..C-1) and data (base64
string, <=4 MiB decoded). Returns {"ok": true}. upload_commit has no other fields,
returns {"ok": true}. Bytes are contiguous little-endian float64 [M,N] values then
uint8 [M,N] observed mask, row major. Missing entries are zero with mask=0. Scores
have already been normalized by public metric ranges to [0,1]. Buffers are private
memory, never shared files. At most one upload is live; outstanding transfer <=512 MiB.

fit fields rank (positive integer <=16), sweeps (positive integer <=50), ridge
(positive float). Returns {"ok": true}. These are requested settings, not scientific
evidence of internal computation. Training uses history only. Fit/preprocessing must
remain immutable until reset; no observations from new models may enter history.

begin fields trajectory (nonnegative int), queryable (distinct integer indices in
0..N-1, at least eight), budget=8. Returns {"ok": true}. Clears only the current
new-model observations, never fitted history. select has no other fields; returns
exactly {"index": int}, an available not-yet-selected queryable index. observe fields
index (the most recently selected index) and value (finite [0,1] score); returns
{"ok": true}. Only that score is authorized feedback. select/observe repeats eight
times; predict is called after 1,2,4,8 observations and returns exactly
{"predictions": [N finite floats in [0,1]]}. Predictions cover ALL N columns, including
unobserved ones; target membership and masks are never disclosed. Predict must not
consume future observations. A new begin discards the preceding trajectory state.

The same operations/settings apply in reduced smoke and all production workloads.
Evaluator-owned constant-history, independent-column permutation, constant/copy
baselines, and reset replay test this actual implementation under matched budgets.
Controls have no required direction of error change; null findings are legitimate.
No state flags, self-reported metrics, file outputs or undocumented response keys.
No adaptivity restriction: selection may be nonadaptive; inference uses observations.
Each complete JSON message must be strictly below 64 MiB (chunks target below 8 MiB).
"""
import base64
import math

import numpy as np


_state = {}


def handle(request):
    operation = request['op']
    if operation == 'reset':
        seed = request['seed']
        if type(seed) is not int or seed < 0:
            raise ValueError('invalid seed')
        _state.clear()
        _state['rng'] = np.random.default_rng(seed)
        return {'ok': True}
    if operation == 'upload_start':
        rows, columns = request['shape']
        if (any(type(count) is not int or not 1 <= count <= 4096 for count in [rows, columns])
                or request['nbytes'] != 9 * rows * columns or request['nbytes'] > 256 * 1024**2
                or not 1 <= request['chunks'] <= 64
                or [request[key] for key in ['dtype', 'byteorder', 'mask_dtype', 'encoding', 'layout']]
                != ['float64', 'little', 'uint8', 'base64', 'values_then_mask']):
            raise ValueError('invalid upload')
        _state['upload'] = bytearray()
        _state['metadata'] = dict(request)
        _state['next_chunk'] = 0
        return {'ok': True}
    if operation == 'upload_chunk':
        metadata = _state['metadata']
        if request['index'] != _state['next_chunk'] or request['index'] >= metadata['chunks']:
            raise ValueError('invalid chunk order')
        decoded = base64.b64decode(request['data'], validate=True)
        if len(decoded) > 4 * 1024**2 or len(_state['upload']) + len(decoded) > metadata['nbytes']:
            raise ValueError('invalid chunk size')
        _state['upload'].extend(decoded)
        _state['next_chunk'] += 1
        return {'ok': True}
    if operation == 'upload_commit':
        metadata = _state['metadata']
        if len(_state['upload']) != metadata['nbytes'] or _state['next_chunk'] != metadata['chunks']:
            raise ValueError('incomplete upload')
        rows, columns = metadata['shape']
        count = rows * columns
        _state['values'] = np.frombuffer(_state['upload'], dtype='<f8', count=count).reshape(rows, columns).copy()
        _state['mask'] = np.frombuffer(_state['upload'], dtype='u1', offset=8*count).reshape(rows, columns).copy()
        if (not np.isfinite(_state['values']).all() or not np.isin(_state['mask'], [0, 1]).all()
                or np.any((_state['values'] < 0) | (_state['values'] > 1))):
            raise ValueError('invalid history')
        del _state['upload']
        return {'ok': True}
    if operation == 'fit':
        values, mask = _state['values'], _state['mask'].astype(bool)
        rank = min(int(request['rank']), *values.shape)
        ridge = float(request['ridge'])
        sweeps = int(request['sweeps'])
        if not 1 <= rank <= 16 or not 1 <= sweeps <= 50 or not math.isfinite(ridge) or ridge <= 0:
            raise ValueError('invalid fitting settings')
        counts = mask.sum(axis=0)
        means = np.divide((values * mask).sum(axis=0), counts,
                          out=np.full(values.shape[1], 0.5), where=counts > 0)
        centered = values - means
        factors = _state['rng'].normal(0, .1, size=(values.shape[1], rank))
        latent = np.zeros((values.shape[0], rank))
        identity = ridge * np.eye(rank)
        for sweep in range(sweeps):
            for row in range(values.shape[0]):
                design = factors[mask[row]]
                latent[row] = np.linalg.solve(identity + design.T @ design, design.T @ centered[row, mask[row]])
            for column in range(values.shape[1]):
                design = latent[mask[:, column]]
                factors[column] = np.linalg.solve(identity + design.T @ design, design.T @ centered[mask[:, column], column])
        _state.update(means=means, factors=factors, ridge=ridge)
        return {'ok': True}
    if operation == 'begin':
        _state['available'] = sorted(request['queryable'])
        _state['observed'] = []
        _state['scores'] = []
        _state['pending'] = None
        return {'ok': True}
    if operation == 'select':
        factors = _state['factors']
        observed = _state['observed']
        available = [index for index in _state['available'] if index not in observed]
        covariance = np.linalg.inv(_state['ridge'] * np.eye(factors.shape[1]) + factors[observed].T @ factors[observed])
        cross = factors @ covariance @ factors[available].T
        denominator = 1 + np.sum((factors[available] @ covariance) * factors[available], axis=1)
        gains = np.sum(cross * cross, axis=0) / denominator
        chosen = int(available[int(np.argmax(gains))])
        _state['pending'] = chosen
        return {'index': chosen}
    if operation == 'observe':
        if request['index'] != _state['pending']:
            raise ValueError('observation without selection')
        _state['observed'].append(request['index'])
        _state['scores'].append(float(request['value']))
        _state['pending'] = None
        return {'ok': True}
    if operation == 'predict':
        factors, means = _state['factors'], _state['means']
        observed = _state['observed']
        design = factors[observed]
        latent = np.linalg.solve(_state['ridge'] * np.eye(factors.shape[1]) + design.T @ design,
                                 design.T @ (np.asarray(_state['scores']) - means[observed]))
        return {'predictions': np.clip(means + factors @ latent, 0, 1).tolist()}
    raise ValueError('unsupported operation')
