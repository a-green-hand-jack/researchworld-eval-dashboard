"""Source-response diversity anchors with grouped ridge/shrinkage calibration.

Finite JSON RPC, handle(request)->dict; extra response fields are forbidden.
Every episode: reset, source_chunk (1..2 calls), fit, observe (8,16,32), release.
No files, target IDs, benchmark identities, or private target scores are provided.
Seeds initialize randomness only; arbitrary nonnegative integer seeds are valid.

reset: {op:'reset',seed:int} -> {ok:true}. Clears all buffers and fitted state.
source_chunk: {op,encoding:'base64',dtype:'uint8',shape:[S,N],offset:int,
total_bytes:S*N,chunk_count:int,data:str} -> {ok:true}. C-order contiguous bytes,
in order, at most two chunks, each <=4194304 decoded bytes; S<=512,N<=16384.
The first chunk allocates candidate-owned RAM; no filesystem exchange exists.
fit: {op,mode:'primary'|'no_diversity'|'no_calibration',budgets:[8,16,32],
source_groups:[int]*S} -> {anchors:[int]*32}. Requires complete source bytes.
Anchors are distinct indices in [0,N), ordered nested prefixes for each budget.
Opaque source groups permit source-only grouped CV; target data never calibrates.
observe: {op,budget:int,encoding:'base64',dtype:'uint8',shape:[T,budget],
data:str} -> {encoding:'base64',dtype:'<f8',shape:[T],data:str}.
Input contains ONLY cumulative queried target correctness bits, C-order. Each
checkpoint supplies the complete legal prefix (not additional target queries).
Prediction bytes are finite little-endian float64 probabilities in [0,1].
Targets have no persistent identities: identical queried rows must receive equal
predictions. Evaluator may supply matched constant/copied/permuted observations.
No response flag or internal-state claim contributes to scientific validity.
release: {op:'release'} -> {ok:true}. Releases source and fit RAM. No other ops.

The editable directory may contain method/paper sources. Research conclusions,
PDF/template compliance, genuine ablation interpretation and novelty require
human-readable evidence beyond these operational prediction metrics. Search is
development-only: no comparative baseline threshold is an eligibility gate.
"""

import base64
import numpy as np

STATE = {}


def select_anchors(source, seed, uniform=False):
    random = np.random.default_rng(seed)
    if uniform:
        return random.permutation(source.shape[1])[:32]
    centered = source.astype(float) - source.mean(axis=1, keepdims=True)
    values, vectors = np.linalg.eigh(centered @ centered.T)
    embedding = (centered.T @ vectors[:, -min(8, len(values)):])
    scale = np.sqrt(np.maximum(values[-embedding.shape[1]:], 1e-8))
    embedding /= scale
    first = int(random.integers(source.shape[1]))
    chosen = []
    distance = np.full(source.shape[1], np.inf)
    current = first
    for step in range(32):
        chosen.append(current)
        distance = np.minimum(distance, np.sum((embedding - embedding[current]) ** 2, axis=1))
        distance[chosen] = -1
        current = int(np.argmax(distance))
    return np.asarray(chosen)


def ridge_fit(features, target, strength):
    center = features.mean(axis=0)
    mean = float(target.mean())
    centered = features - center
    coefficient = np.linalg.solve(centered.T @ centered + strength * np.eye(features.shape[1]), centered.T @ (target - mean))
    return center, mean, coefficient


def fit_models(source, anchors, groups):
    target = source.mean(axis=1)
    unique = sorted(set(groups))
    folds = np.asarray([unique.index(group) % 3 for group in groups])
    models = {}
    for budget in (8, 16, 32):
        features = source[:, anchors[:budget]].astype(float)
        best = None
        for strength in (0.1, 1.0, 10.0):
            predictions = np.empty(len(source))
            for fold in range(3):
                train, valid = folds != fold, folds == fold
                center, mean, coefficient = ridge_fit(features[train], target[train], strength)
                predictions[valid] = mean + (features[valid] - center) @ coefficient
            for shrinkage in (0.0, 0.5, 1.0):
                loss = float(np.mean((target - (shrinkage * predictions + (1 - shrinkage) * target.mean())) ** 2))
                key = (loss, strength, shrinkage)
                if best is None or key < best:
                    best = key
        _, strength, shrinkage = best
        models[budget] = (*ridge_fit(features, target, strength), shrinkage)
    return models


def handle(request):
    operation = request['op']
    if operation == 'reset':
        if type(request['seed']) is not int or request['seed'] < 0:
            raise ValueError('invalid seed')
        STATE.clear()
        STATE['seed'] = request['seed']
        STATE['received'] = 0
        return {'ok': True}
    if operation == 'source_chunk':
        shape = request['shape']
        total = request['total_bytes']
        if request['offset'] != STATE['received'] or total != int(np.prod(shape)) or total > 8388608:
            raise ValueError('invalid source transfer')
        if request['offset'] == 0:
            STATE['buffer'] = bytearray(total)
            STATE['shape'] = shape
        chunk = base64.b64decode(request['data'], validate=True)
        offset = STATE['received']
        if not chunk or len(chunk) > 4194304 or offset + len(chunk) > total:
            raise ValueError('invalid chunk')
        STATE['buffer'][offset:offset + len(chunk)] = chunk
        STATE['received'] += len(chunk)
        return {'ok': True}
    if operation == 'fit':
        source = np.frombuffer(STATE['buffer'], dtype=np.uint8).reshape(STATE['shape'])
        if STATE['received'] != source.size or not np.isin(source, [0, 1]).all():
            raise ValueError('incomplete or invalid source')
        anchors = select_anchors(source, STATE['seed'], request['mode'] == 'no_diversity')
        STATE['anchors'] = anchors
        STATE['models'] = fit_models(source, anchors, request['source_groups'])
        STATE['mode'] = request['mode']
        return {'anchors': anchors.tolist()}
    if operation == 'observe':
        budget = request['budget']
        observations = np.frombuffer(base64.b64decode(request['data'], validate=True), dtype=np.uint8).reshape(request['shape']).astype(float)
        if STATE['mode'] == 'no_calibration':
            predictions = observations.mean(axis=1)
        else:
            center, mean, coefficient, shrinkage = STATE['models'][budget]
            predictions = mean + shrinkage * ((observations - center) @ coefficient)
        predictions = np.clip(predictions, 0, 1).astype('<f8')
        return {'encoding': 'base64', 'dtype': '<f8', 'shape': [len(predictions)], 'data': base64.b64encode(predictions.tobytes()).decode('ascii')}
    if operation == 'release':
        STATE.clear()
        return {'ok': True}
    raise ValueError('unknown operation')
