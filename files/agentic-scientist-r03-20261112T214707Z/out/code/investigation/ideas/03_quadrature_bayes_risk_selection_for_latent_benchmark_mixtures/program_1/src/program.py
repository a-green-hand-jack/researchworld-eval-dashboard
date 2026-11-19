"""Finite JSON RPC v1, handle(request)->response. No extra response fields allowed.

reset: {op:'reset', seed:nonnegative integer}; returns {ok:true}. Arbitrary seeds
initialize RNG only; clear all fit/upload/row state. Every episode begins here.
upload_start: {op, shape:[M,N], dtype:'<f4', encoding:'base64',
 mask_encoding:'uint8', total_bytes:5*M*N, max_chunks:8, chunk_bytes:4194304,
 tasks:[N opaque strings]}; returns {ok:true}. M<=220,N<=128. Matrix is
row-major little-endian float32 followed by M*N uint8 mask bytes (0/1).
Missing values have zero fill, never NaN. Entire object <=32 MiB, in memory.
upload_chunk: {op,index:0..7,offset:integer,data:base64 string}; {ok:true}.
Chunks are ordered, <=4MiB decoded, contiguous, no duplicates or empty chunks.
upload_commit: {op}; {ok:true}. Require exact assembly length and valid masks.
fit: {op,sweeps:positive integer<=30}; {ok:true}. Fit once per episode on
historical scores only. Sweeps are advisory, wall/CPU/RPC limits authoritative.
row_start: {op,row:opaque string,available:[distinct column integers],
 k_max:positive integer,checkpoints:[increasing integers ending at k_max]}.
Clear only row conditioning, retaining fit. Return {column:legal integer,
 prediction:null}. Availability discloses recorded queryable scores, not values;
unavailable and audit columns cannot be selected. Dimensions/workload come from
requests, never seed identity. Rows are independent new-model predictions.
observe: {op,column:previous selected integer,value:finite number in [0,1]}.
Append the authorized observation; return {column:next distinct available integer
or null exactly at k_max, prediction:null except at checkpoint counts}.
At each checkpoint prediction is {encoding:'base64',dtype:'<f4',shape:[N],
 data:base64 of N little-endian float32 predictions}, all finite in [0,1].
The full vector is returned, but only recorded, unqueried entries are scored.
Selecting the next column and checkpoint prediction are fused to bound RPC calls.
No targets, control labels, scores, paths, state flags or diagnostics cross RPC.
A reset invalidates buffers, fit and all row state. New row_start retains fit.
The implementation uses historical model-heldout validation, observed-data
latent-mixture EM, validation-gated quadrature absolute-risk transfer selection
and component conditioning. Without paired evidence the incumbent is retained.
Validation uses fixed target tasks excluded from probes. No external labels or
family metadata are supplied; no external experiment or superiority is claimed.
"""
import base64
import importlib.util
from pathlib import Path
import numpy as np

_MODEL_SPEC = importlib.util.spec_from_file_location(
    '_candidate_residual_covariance', Path(__file__).with_name('covariance.py'),
)
_MODEL_MODULE = importlib.util.module_from_spec(_MODEL_SPEC)
_MODEL_SPEC.loader.exec_module(_MODEL_MODULE)
_MIXTURE_SPEC = importlib.util.spec_from_file_location(
    '_candidate_latent_mixture', Path(__file__).with_name('mixture.py'),
)
_MIXTURE_MODULE = importlib.util.module_from_spec(_MIXTURE_SPEC)
_MIXTURE_SPEC.loader.exec_module(_MIXTURE_MODULE)

_STATE = {}



def handle(request):
    operation = request['op']
    if operation == 'reset':
        seed = request['seed']
        if type(seed) is not int or seed < 0:
            raise ValueError('invalid seed')
        _STATE.clear()
        _STATE['seed'] = seed
        return {'ok': True}
    if operation == 'upload_start':
        shape = request['shape']
        if len(shape) != 2 or any(type(size) is not int or size < 1 for size in shape) or shape[0] > 220 or shape[1] > 128:
            raise ValueError('invalid shape')
        if request['dtype'] != '<f4' or request['encoding'] != 'base64' or request['mask_encoding'] != 'uint8' or request['max_chunks'] != 8 or request['chunk_bytes'] != 4194304 or request['total_bytes'] != 5 * shape[0] * shape[1]:
            raise ValueError('invalid encoding')
        if len(request['tasks']) != shape[1] or any(type(token) is not str for token in request['tasks']):
            raise ValueError('invalid tasks')
        _STATE.update(shape=shape, buffer=bytearray(), chunks=0)
        return {'ok': True}
    if operation == 'upload_chunk':
        data = base64.b64decode(request['data'], validate=True)
        if not data or len(data) > 4194304 or request['index'] != _STATE['chunks'] or request['offset'] != len(_STATE['buffer']) or _STATE['chunks'] >= 8 or len(_STATE['buffer']) + len(data) > 5 * np.prod(_STATE['shape']):
            raise ValueError('invalid chunk')
        _STATE['buffer'].extend(data)
        _STATE['chunks'] += 1
        return {'ok': True}
    if operation == 'upload_commit':
        count = int(np.prod(_STATE['shape']))
        data = _STATE.pop('buffer')
        if len(data) != count * 5:
            raise ValueError('incomplete upload')
        matrix = np.frombuffer(data[:count * 4], dtype='<f4').astype(float).reshape(_STATE['shape'])
        mask = np.frombuffer(data[count * 4:], dtype='u1').reshape(_STATE['shape'])
        if not np.isfinite(matrix).all() or (matrix < 0).any() or (matrix > 1).any() or (mask > 1).any():
            raise ValueError('invalid matrix')
        _STATE.update(matrix=matrix, mask=mask.astype(bool))
        return {'ok': True}
    if operation == 'fit':
        if type(request['sweeps']) is not int or not 1 <= request['sweeps'] <= 30:
            raise ValueError('invalid sweeps')
        covariance_model = _MIXTURE_MODULE.tune_fit(_STATE['matrix'], _STATE['mask'], _STATE['seed'], request['sweeps'], _MODEL_MODULE)
        _STATE.update(offset=covariance_model.mean_, covariance_model=covariance_model)
        return {'ok': True}
    if operation == 'row_start':
        available = request['available']
        if len(set(available)) != len(available) or any(type(index) is not int or not 0 <= index < len(_STATE['offset']) for index in available) or not 1 <= request['k_max'] <= len(available):
            raise ValueError('invalid availability')
        checkpoints = request['checkpoints']
        if not checkpoints or checkpoints != sorted(set(checkpoints)) or checkpoints[-1] != request['k_max'] or checkpoints[0] < 1:
            raise ValueError('invalid checkpoints')
        row_state = _MIXTURE_MODULE.MixtureRow(_STATE['covariance_model'])
        _STATE.update(available=available, observed=row_state.observed, values=row_state.values,
                      k_max=request['k_max'], checkpoints=checkpoints, row_state=row_state)
        selected = row_state.select(available, _MODEL_MODULE)
        _STATE['pending'] = selected
        return {'column': selected, 'prediction': None}
    if operation == 'observe':
        if request['column'] != _STATE['pending'] or type(request['value']) not in (int, float) or not np.isfinite(request['value']) or not 0 <= request['value'] <= 1:
            raise ValueError('invalid observation')
        _STATE['row_state'].reveal(request['column'], float(request['value']), _MODEL_MODULE)
        count = len(_STATE['observed'])
        prediction = None
        if count in _STATE['checkpoints']:
            vector = _STATE['row_state'].predict(_MODEL_MODULE).astype('<f4')
            prediction = {'encoding': 'base64', 'dtype': '<f4', 'shape': [len(vector)], 'data': base64.b64encode(vector.tobytes()).decode('ascii')}
        selected = None if count == _STATE['k_max'] else _STATE['row_state'].select(_STATE['available'], _MODEL_MODULE)
        _STATE['pending'] = selected
        return {'column': selected, 'prediction': prediction}
    raise ValueError('unknown operation')
