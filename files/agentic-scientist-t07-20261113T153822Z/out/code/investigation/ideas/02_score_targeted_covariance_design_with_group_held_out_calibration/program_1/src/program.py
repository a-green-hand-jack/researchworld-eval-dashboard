"""Score-targeted covariance prefixes with source-group-held-out calibration.

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
import os
import sys

for variable in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'BLIS_NUM_THREADS'):
    os.environ[variable] = '1'

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from score_design import fit_candidate

STATE = {}


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
        budgets = tuple(request['budgets'])
        predictor, calibration, diagnostics = fit_candidate(
            source, request['source_groups'], budgets, STATE['seed'], request['mode'])
        STATE['anchors'] = predictor.anchors
        STATE['predictor'] = predictor
        STATE['calibration'] = calibration
        STATE['diagnostics'] = diagnostics
        STATE['mode'] = request['mode']
        return {'anchors': predictor.anchors.tolist()}
    if operation == 'observe':
        budget = request['budget']
        observations = np.frombuffer(base64.b64decode(request['data'], validate=True), dtype=np.uint8).reshape(request['shape']).astype(float)
        if budget not in STATE['predictor'].budgets or observations.shape[1] != budget or not np.isin(observations, [0, 1]).all():
            raise ValueError('invalid queried prefix')
        predictions = np.asarray([STATE['predictor'].predict_row(row, budget, STATE['calibration'])
                                  for row in observations], dtype='<f8')
        return {'encoding': 'base64', 'dtype': '<f8', 'shape': [len(predictions)], 'data': base64.b64encode(predictions.tobytes()).decode('ascii')}
    if operation == 'release':
        STATE.clear()
        return {'ok': True}
    raise ValueError('unknown operation')
