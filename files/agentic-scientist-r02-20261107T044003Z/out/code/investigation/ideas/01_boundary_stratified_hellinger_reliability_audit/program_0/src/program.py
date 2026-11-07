"""Training-only adaptive ILR ellipsoid predictor, finite JSON RPC v1.

All operations return EXACTLY the keys described here; extra keys are forbidden.
No paths, metrics, test targets, calibration responses, or plane identity are inputs.
Seeds initialize randomness only; accept any nonnegative signed-64-bit integer seed.
reset {op,seed} -> {ok:true}: discard model and both in-memory transfer buffers.

fit_start {op,n_rows,composition_dim,ilr_basis,alpha,nbytes,chunks} -> {ok:true}:
one training phase per reset; 1<=n_rows<=4096, K=composition_dim in {3,8},
alpha=0.1, ilr_basis is K by K-1 orthonormal contrast matrix. Training consists
of row-major float64 X[n_rows,5], then Y[n_rows,K] (positive, row sums one).
nbytes=8*n_rows*(5+K), chunks=ceil(nbytes/1048576), at most four chunks.
fit_chunk {op,index,block} -> {ok:true}: consecutive zero-based indices only.
fit_commit {op} -> {ok:true}: require all bytes; fit actual predictor, free upload.
All training inputs are authorized; calibration is performed by the evaluator.

predict_start {op,x:block} -> {n_rows,dimension,nbytes,chunks,encoding,dtype,shape}:
requires committed fit and no live prediction. X has shape [N,5], 1<=N<=5952.
Return dimension d=K-1; buffer is row-major float64 [N,d+d*d], location first,
then a FULL row-major lower triangular Cholesky factor of a positive shape.
shape=[N,d+d*d], encoding='base64', dtype='<f8', nbytes=8*N*(d+d*d),
chunks=ceil(nbytes/1048576)<=4. A prediction must be a fixed row-wise function
of X after fit: no test-time updating, batch position, or batch-size dependence.
predict_chunk {op,index} -> {block}: ordered chunks of flattened output.
predict_release {op} -> {ok:true}: requires all chunks read; erase output buffer.
The evaluator performs three prediction transfers: full authorized query batch,
reordered query subset, and another subset, without revealing partition boundaries.

Every block has EXACT keys {encoding,dtype,shape,nbytes,data}: base64 ASCII data,
encoding='base64', dtype='<f8', shape a positive integer list, nbytes=8*prod(shape).
Chunk blocks use shape [number_of_float64_values], at most 1048576 raw bytes.
All numeric values must be finite. Location and factor magnitudes <=1e6;
factor diagonals >=1e-8; singular-value condition number <=1e10.
At most 4 MiB per logical buffer, 512 MiB total candidate-owned memory allowed;
complete framed UTF-8 JSON messages <8 MiB (and always <64 MiB). No disk exchange.
No optional response keys or candidate diagnostics are supported. Errors are protocol
failures, not a channel for scientific self-reports. Reset is the only restart.
Evaluator controls include matched constant inputs, genuine training derangement,
actual point-copy singleton/full-simplex membership, query invariance, and replay.
Neither nominal coverage nor superiority is an eligibility gate: negative results
are valid when execution and required instrumentation are valid. Search utility is
1 - .8*max(0,.9-coverage)/.9 - .2*normalized_volume, equally weighted case then seed.
"""
import base64
import math
import numpy as np

CHUNK = 1048576
STATE = {}


def decode(block):
    if set(block) != {'encoding', 'dtype', 'shape', 'nbytes', 'data'}:
        raise ValueError('invalid block')
    if block['encoding'] != 'base64' or block['dtype'] != '<f8':
        raise ValueError('invalid encoding')
    shape = block['shape']
    if not isinstance(shape, list) or not shape or any(type(size) is not int or size < 1 for size in shape):
        raise ValueError('invalid shape')
    size = math.prod(shape) * 8
    if size != block['nbytes'] or size > 4 * CHUNK:
        raise ValueError('invalid size')
    raw = base64.b64decode(block['data'], validate=True)
    if len(raw) != size:
        raise ValueError('invalid byte count')
    array = np.frombuffer(raw, dtype='<f8').reshape(shape)
    if not np.isfinite(array).all():
        raise ValueError('nonfinite')
    return array


def encode(array):
    array = np.asarray(array, dtype='<f8', order='C')
    return {'encoding': 'base64', 'dtype': '<f8', 'shape': list(array.shape),
            'nbytes': array.nbytes, 'data': base64.b64encode(array.tobytes()).decode('ascii')}


def features(covariates):
    columns = [np.ones(len(covariates))]
    columns.extend(covariates[:, index] for index in range(5))
    columns.extend(covariates[:, index] ** 2 for index in range(5))
    columns.extend(covariates[:, first] * covariates[:, second]
                   for first in range(5) for second in range(first))
    return np.column_stack(columns)


def ridge(design, targets, penalty):
    return np.linalg.solve(design.T @ design + penalty * np.eye(design.shape[1]), design.T @ targets)


def fit_model(covariates, responses, basis):
    transformed = np.log(responses) @ basis
    design = features(covariates)
    cut = 3 * len(covariates) // 4
    location = ridge(design[:cut], transformed[:cut], 0.01)
    residuals = transformed[cut:] - design[cut:] @ location
    variance = ridge(design[cut:], np.log(residuals ** 2 + 0.02), 5.0)
    return location, variance


def handle(request):
    operation = request['op']
    if operation == 'reset':
        if set(request) != {'op', 'seed'} or type(request['seed']) is not int or not 0 <= request['seed'] < 2**63:
            raise ValueError('invalid reset')
        STATE.clear()
        STATE['rng'] = np.random.default_rng(request['seed'])
        return {'ok': True}
    if 'rng' not in STATE:
        raise ValueError('reset required')
    if operation == 'fit_start':
        if 'upload' in STATE or 'model' in STATE:
            raise ValueError('one fit per reset')
        rows, size = request['n_rows'], request['composition_dim']
        if type(rows) is not int or not 1 <= rows <= 4096 or size not in (3, 8):
            raise ValueError('invalid training shape')
        raw_size = rows * (5 + size) * 8
        if request['nbytes'] != raw_size or request['chunks'] != math.ceil(raw_size / CHUNK):
            raise ValueError('invalid transfer')
        basis = np.asarray(request['ilr_basis'], dtype=float)
        if basis.shape != (size, size - 1) or not np.allclose(basis.T @ basis, np.eye(size - 1)):
            raise ValueError('invalid basis')
        STATE.update(upload=bytearray(), metadata=dict(request), basis=basis, upload_index=0)
        return {'ok': True}
    if operation == 'fit_chunk':
        if 'upload' not in STATE or request['index'] != STATE['upload_index']:
            raise ValueError('invalid upload order')
        block = decode(request['block'])
        expected = min(CHUNK, STATE['metadata']['nbytes'] - len(STATE['upload']))
        if block.ndim != 1 or block.nbytes != expected or expected < 1:
            raise ValueError('invalid upload length')
        STATE['upload'].extend(block.tobytes())
        STATE['upload_index'] += 1
        return {'ok': True}
    if operation == 'fit_commit':
        metadata = STATE['metadata']
        if len(STATE['upload']) != metadata['nbytes'] or STATE['upload_index'] != metadata['chunks']:
            raise ValueError('incomplete upload')
        rows, size = metadata['n_rows'], metadata['composition_dim']
        flat = np.frombuffer(STATE['upload'], dtype='<f8')
        covariates = flat[:rows * 5].reshape(rows, 5)
        responses = flat[rows * 5:].reshape(rows, size)
        STATE['model'] = fit_model(covariates, responses, STATE['basis'])
        STATE['dimension'] = size - 1
        del flat, covariates, responses
        del STATE['upload']
        return {'ok': True}
    if operation == 'predict_start':
        if 'prediction' in STATE or 'model' not in STATE:
            raise ValueError('invalid prediction state')
        covariates = decode(request['x'])
        if covariates.ndim != 2 or covariates.shape[1] != 5 or not 1 <= len(covariates) <= 5952:
            raise ValueError('invalid query shape')
        design = features(covariates)
        location, variance = STATE['model']
        dimension = STATE['dimension']
        means = design @ location
        scales = np.exp(0.5 * np.clip(design @ variance, -6, 5))
        factors = np.zeros((len(covariates), dimension, dimension))
        indices = np.arange(dimension)
        factors[:, indices, indices] = scales
        output = np.concatenate((means, factors.reshape(len(covariates), -1)), axis=1).astype('<f8')
        STATE['prediction'] = output.tobytes()
        STATE['prediction_index'] = 0
        return {'n_rows': len(covariates), 'dimension': dimension, 'nbytes': output.nbytes,
                'chunks': math.ceil(output.nbytes / CHUNK), 'encoding': 'base64',
                'dtype': '<f8', 'shape': list(output.shape)}
    if operation == 'predict_chunk':
        if request['index'] != STATE['prediction_index']:
            raise ValueError('invalid download order')
        start = request['index'] * CHUNK
        raw = STATE['prediction'][start:start + CHUNK]
        if not raw:
            raise ValueError('invalid download index')
        STATE['prediction_index'] += 1
        return {'block': encode(np.frombuffer(raw, dtype='<f8'))}
    if operation == 'predict_release':
        if STATE['prediction_index'] != math.ceil(len(STATE['prediction']) / CHUNK):
            raise ValueError('incomplete download')
        del STATE['prediction']
        return {'ok': True}
    raise ValueError('unknown operation')
