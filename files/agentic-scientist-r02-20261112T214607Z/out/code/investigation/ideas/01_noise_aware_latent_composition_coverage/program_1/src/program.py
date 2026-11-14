"""Train-only positive compositional residual-scale learner, python_rpc_v1:handle.

All requests/responses are finite JSON objects; extra response keys are forbidden.
reset: {op:'reset', seed: nonnegative int} -> {ok:true}. Clears all model/transfer
state. Any seed is accepted; seeds initialize randomness, never select a workload.
fit: {op:'fit', x:Array[n,6], residuals:Array[n], dimension:int>=2,
      scale_min:0.0001, scale_max:10000.0} -> {ok:true}.
Only training covariates and training residual norms are provided. Fits replace the
model. Prediction is read-only and requires a completed fit after reset.
predict: {op:'predict', x:Array[n,6]} -> {scales:Array[n]}.
Return strictly positive finite scales; the evaluator consistently clips them to
[0.0001,10000]. No calibration/test outcomes or later scoring feedback is given.
Array is exactly {encoding:'base64',dtype:'<f8',shape:[...],nbytes:int,data:str}.
Data is C-order little-endian float64, n<=2048 normally; no file paths are used.
Workload dimensions/settings come from fit, not reset seeds. Candidate changes may
change the scale estimator but not evaluator-owned center, geometry or calibration.

Optional bounded fallback, exercised by maximum-protocol tests, not needed for
ordinary shapes: begin {op:'begin',method:'fit'|'predict',fields:object,
arrays:{name:{shape:list,nbytes:int}},nbytes:int} -> {token:str}.
fields holds the non-array logical request fields except op. Arrays, in insertion
order, concatenate raw <f8 bytes; total <=8 MiB. upload {op:'upload',token:str,
offset:int,data:base64str} -> {ok:true}, sequential <=2 chunks of <=4 MiB.
commit {op:'commit',token:str} -> {ok:true} validates lengths and computes once.
export_start {op:'export_start',token:str} -> {nbytes:int,chunks:int}.
fetch {op:'fetch',token:str,index:int} -> {data:base64str}, sequential <=2 chunks.
Output is UTF-8 JSON for fit, raw <f8 scales for predict. release
{op:'release',token:str} -> {ok:true} destroys buffers. One live token, <=32 MiB
transfer storage; reset invalidates it. No token is a path. At most 8 calls per
logical operation (begin,2 uploads,commit,export_start,2 fetches,release).
No self-reported learning, timing or diagnostics are accepted as scientific evidence.

Candidate scope: the proposed multinomial latent-coverage bridge is not available
through this interface. Neither count depths nor observed/latent compositions are
provided, and calibration and region construction are not candidate operations.
The starter scale estimator is intentionally unchanged; no latent-coverage claim
or experimental result is made. See IDEA_LIMITATIONS.md for the scope assessment.
"""
import base64
import json
import math
import numpy as np

MODEL = None
TRANSFER = None
CHUNK = 4 * 1024 * 1024


def decode(value):
    if set(value) != {'encoding', 'dtype', 'shape', 'nbytes', 'data'}:
        raise ValueError('array schema')
    if value['encoding'] != 'base64' or value['dtype'] != '<f8':
        raise ValueError('array encoding')
    raw = base64.b64decode(value['data'], validate=True)
    if len(raw) != value['nbytes'] or len(raw) != math.prod(value['shape']) * 8:
        raise ValueError('array size')
    result = np.frombuffer(raw, dtype='<f8').reshape(value['shape'])
    if not np.isfinite(result).all():
        raise ValueError('nonfinite input')
    return result


def encode(array):
    array = np.asarray(array, dtype='<f8', order='C')
    return dict(encoding='base64', dtype='<f8', shape=list(array.shape),
                nbytes=array.nbytes, data=base64.b64encode(array.tobytes()).decode('ascii'))


def features(array):
    return np.column_stack((np.ones(len(array)), array, array * array))


def compute(method, fields, arrays):
    global MODEL
    if method == 'fit':
        covariates, residuals = arrays['x'], arrays['residuals']
        if covariates.ndim != 2 or covariates.shape[1] != 6 or residuals.shape != (len(covariates),):
            raise ValueError('training shape')
        mean = covariates.mean(axis=0)
        deviation = np.maximum(covariates.std(axis=0), 1e-8)
        design = features((covariates - mean) / deviation)
        target = np.log(np.maximum(residuals, 1e-8))
        penalty = np.eye(design.shape[1]) * 2.0
        penalty[0, 0] = 1e-8
        coefficients = np.linalg.solve(design.T @ design + penalty, design.T @ target)
        MODEL = (mean, deviation, coefficients)
        return {'ok': True}
    if method == 'predict' and MODEL is not None:
        mean, deviation, coefficients = MODEL
        return np.clip(np.exp(np.clip(features((arrays['x'] - mean) / deviation)
                                         @ coefficients, -20, 20)), 1e-4, 1e4)
    raise ValueError('operation/state')


def handle(request):
    global MODEL, TRANSFER
    operation = request['op']
    if operation == 'reset':
        if type(request['seed']) is not int or request['seed'] < 0:
            raise ValueError('seed')
        MODEL, TRANSFER = None, None
        return {'ok': True}
    if operation in ('fit', 'predict'):
        names = ('x', 'residuals') if operation == 'fit' else ('x',)
        result = compute(operation, request, {name: decode(request[name]) for name in names})
        return result if operation == 'fit' else {'scales': encode(result)}
    if operation == 'begin':
        if TRANSFER is not None or not 0 < request['nbytes'] <= 2 * CHUNK:
            raise ValueError('transfer bound')
        if request['method'] not in ('fit', 'predict'):
            raise ValueError('method')
        if sum(item['nbytes'] for item in request['arrays'].values()) != request['nbytes']:
            raise ValueError('transfer shape')
        TRANSFER = dict(request=request, raw=bytearray(), output=None, fetched=0)
        return {'token': 'buffer'}
    if TRANSFER is None or request['token'] != 'buffer':
        raise ValueError('transfer state')
    transfer = TRANSFER
    if operation == 'upload':
        raw = base64.b64decode(request['data'], validate=True)
        if (request['offset'] != len(transfer['raw']) or not 0 < len(raw) <= CHUNK
                or len(transfer['raw']) + len(raw) > transfer['request']['nbytes']):
            raise ValueError('chunk ordering/length')
        transfer['raw'].extend(raw)
        return {'ok': True}
    if operation == 'commit':
        specification = transfer['request']
        if len(transfer['raw']) != specification['nbytes'] or transfer['output'] is not None:
            raise ValueError('incomplete/duplicate commit')
        arrays, offset = {}, 0
        for name, metadata in specification['arrays'].items():
            count = metadata['nbytes']
            arrays[name] = np.frombuffer(transfer['raw'], dtype='<f8', count=count // 8,
                                       offset=offset).reshape(metadata['shape'])
            offset += count
        result = compute(specification['method'], specification['fields'], arrays)
        transfer['output'] = (json.dumps(result).encode() if specification['method'] == 'fit'
                              else np.asarray(result, dtype='<f8').tobytes())
        if len(transfer['output']) > 2 * CHUNK:
            raise ValueError('output bound')
        del arrays
        transfer['raw'] = bytearray()
        return {'ok': True}
    if operation == 'export_start' and transfer['output'] is not None:
        return {'nbytes': len(transfer['output']),
                'chunks': math.ceil(len(transfer['output']) / CHUNK)}
    if operation == 'fetch' and transfer['output'] is not None:
        index = request['index']
        if index != transfer['fetched'] or index * CHUNK >= len(transfer['output']):
            raise ValueError('fetch order')
        transfer['fetched'] += 1
        return {'data': base64.b64encode(transfer['output'][index * CHUNK:(index + 1) * CHUNK]).decode()}
    if operation == 'release':
        TRANSFER = None
        return {'ok': True}
    raise ValueError('transfer operation/state')
