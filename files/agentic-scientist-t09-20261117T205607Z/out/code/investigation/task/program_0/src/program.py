"""Deterministic endpoint plug-in ridge regression; edit handle and helpers here.

All operations use finite JSON dictionaries; additional response keys are forbidden.
There are no paths, files, scores, endpoint labels, or plane identifiers in requests.
reset: {op:'reset', seed: arbitrary nonnegative int} -> {ok:true}. Clears every
upload/model and initializes randomness. It is always the episode's first operation.
begin: {op:'begin', n:int in [2,20000], edges:int in [0,2000000],
        bytes:int in [1,50331648], chunks:int in [1,8],
        encoding:'base64', byte_order:'little',
        arrays:[{name,dtype,shape}, ...]} -> {ok:true}.
Arrays in exact order: edges <i4 [edges,2], x <f8 [n], z <f8 [n], y <f8 [n].
Concatenate their C-order raw bytes in that order, then split into chunks <=6291456
bytes. z is observed binary treatment, x a pre-treatment scalar, y an observed
experimental outcome, never an all-treated/all-control outcome. Edge indices
describe a simple undirected graph with the explicit n-node universe (isolates kept).
upload: {op:'upload', index:int, data:base64 str} -> {ok:true}; indices 0..chunks-1
are consecutive. Assembly is candidate-owned memory, bounded to 48 MiB.
fit: {op:'fit'} -> {ok:true}; commits complete upload, constructs features, fits.
predict: {op:'predict'} -> {beta:[8 finite numbers], ridge:finite number in [0,1e6],
                         endpoints:[control_mean, treated_mean], gate:finite number}.
All numeric response magnitudes are <=1e12, booleans are not numeric values.
Features in exact order: [1,z,e,z*e,e**2,x,d,x*z], where e is mean neighbor
treatment (0 at isolates), d=degree/max(1,max_degree). All-control sets z=e=0;
all-treated sets z=1 and e=1 at nonisolates, 0 at isolates. Covariates and d stay
fixed. beta solves least squares plus ridge*sum(beta[1:]**2), unpenalized intercept.
Evaluator verifies numeric fit stationarity and endpoint reconstruction independently;
a method label, diagnostics or internal-state flag is not evidence. Ridge selection
and solver are editable, but this auditable regression/feature contract is fixed.
release: {op:'release'} -> {ok:true}; drops upload/model, allowing next reset.
No other operations or optional response fields. Predict only after fit; fit only
after complete upload. Each episode uses reset/begin/uploads/fit/predict/release.
Fit stationarity tolerance is 1e-6*max(1,norm(X.T@y)); endpoint comparison uses
absolute/relative tolerances 1e-7. No fixed ridge choice or error superiority is
required. Two CPU threads, 8 GiB role memory, 512 MiB in-memory RPC-state cap;
reset has a 1s allowance and candidate fitting/transport a matched 2.5s allowance.
Request dimensions, not seeds, select workload. No adaptive feedback is required.
Every complete JSON message including framing must be strictly below 64 MiB.
"""
import base64
import numpy as np
from scipy import sparse

_state = {}


def features(edges, covariate, treatment):
    count = len(treatment)
    adjacency = sparse.coo_matrix((np.ones(2 * len(edges)),
        (np.concatenate((edges[:, 0], edges[:, 1])),
         np.concatenate((edges[:, 1], edges[:, 0])))), shape=(count, count)).tocsr()
    degree = np.asarray(adjacency.sum(axis=1)).ravel()
    exposure = adjacency @ treatment / np.maximum(degree, 1)
    scaled = degree / max(1, degree.max())
    def matrix(own, neighbor):
        return np.column_stack((np.ones(count), own, neighbor, own * neighbor,
                                neighbor ** 2, covariate, scaled, covariate * own))
    return (matrix(treatment, exposure), matrix(np.zeros(count), np.zeros(count)),
            matrix(np.ones(count), (degree > 0).astype(float)))


def handle(request):
    operation = request['op']
    if operation == 'reset':
        seed = request['seed']
        if type(seed) is not int or seed < 0:
            raise ValueError('invalid seed')
        _state.clear()
        _state['rng'] = np.random.default_rng(seed)
        return {'ok': True}
    if operation == 'begin':
        if not 1 <= request['chunks'] <= 8 or not 1 <= request['bytes'] <= 48 * 1024**2:
            raise ValueError('invalid transfer')
        _state.update(spec=request, chunks=[], uploaded=0)
        return {'ok': True}
    if operation == 'upload':
        if request['index'] != len(_state['chunks']):
            raise ValueError('unordered chunk')
        chunk = base64.b64decode(request['data'], validate=True)
        if len(chunk) > 6 * 1024**2 or _state['uploaded'] + len(chunk) > _state['spec']['bytes']:
            raise ValueError('oversized chunk')
        _state['chunks'].append(chunk)
        _state['uploaded'] += len(chunk)
        return {'ok': True}
    if operation == 'fit':
        spec = _state['spec']
        if len(_state['chunks']) != spec['chunks'] or _state['uploaded'] != spec['bytes']:
            raise ValueError('incomplete upload')
        payload = b''.join(_state.pop('chunks'))
        offset = 0
        arrays = []
        for field in spec['arrays']:
            dtype = np.dtype(field['dtype'])
            size = int(np.prod(field['shape'])) * dtype.itemsize
            arrays.append(np.frombuffer(payload, dtype=dtype, count=size // dtype.itemsize,
                                        offset=offset).reshape(field['shape']))
            offset += size
        if offset != len(payload):
            raise ValueError('invalid byte count')
        edges, covariate, treatment, outcome = arrays
        matrix, control, treated = features(edges, covariate, treatment)
        ridge = 1e-4
        penalty = np.diag([0.0] + [ridge] * 7)
        coefficient = np.linalg.solve(matrix.T @ matrix + penalty, matrix.T @ outcome)
        endpoints = [float(control.mean(axis=0) @ coefficient),
                     float(treated.mean(axis=0) @ coefficient)]
        _state['prediction'] = dict(beta=coefficient.tolist(), ridge=ridge,
                                    endpoints=endpoints, gate=endpoints[1] - endpoints[0])
        return {'ok': True}
    if operation == 'predict':
        return dict(_state['prediction'])
    if operation == 'release':
        _state.clear()
        return {'ok': True}
    raise ValueError('unsupported operation')
