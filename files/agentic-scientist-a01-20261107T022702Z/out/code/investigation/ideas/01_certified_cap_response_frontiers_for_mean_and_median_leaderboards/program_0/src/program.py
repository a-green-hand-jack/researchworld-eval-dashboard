"""Deterministic counterfactual allocation solver; no training or external files.

Protocol: handle(dict) -> finite JSON dict. Extra request/response keys are forbidden.
Every episode starts with reset, clearing all arrays, transfer buffers and RNG.
Seeds are arbitrary nonnegative integers and initialize RNG only, not workloads.

reset: {op:'reset', seed:int} -> {ok:true}.
upload_start: {op, encoding:'base64', dtype:'<f8', shape:[models,tasks],
 byte_length:int, chunk_count:int, sha256:64-char hex, task_ids:[str,...]}
 -> {ok:true}. Models 2..100000, tasks 2..100, bytes exactly models*tasks*8,
 logical limit 16 MiB; chunk_count=ceil(bytes/1048576), in 1..16.
upload_chunk: {op, index:int, data:base64 str} -> {ok:true}; contiguous zero-based
 indices, each decoded block <=1048576 bytes, all except last full-sized.
upload_commit: {op} -> {ok:true}; checks digest, finite [0,1] scores and shape.
 All buffering is candidate-owned memory; no host filenames or shared files.
solve: {op, targets:[distinct row int,...], rules:['mean','median','borda'],
 cap_fractions:[float,float], tolerance:1e-10, work_seconds:positive float}
 -> {solutions:[{status:str,tasks:[distinct column int,...]},...]}. At most
 eight targets; decisions are target-major, then rule-major, then cap-major.
 A selected coordinate is set to score + fraction*(1-score), fraction in [0,1].
 Both fractions can be zero for no-update experiments. Costs are one per
 selected coordinate, divided by task count for reported investment.
 Input scores/caps round to 10 decimal places before evaluation. Mean and
 median use float64; Borda is average pairwise win credit (ties half), updated
 competitors included. Co-first allows an aggregate deficit <= tolerance.
 status is 'feasible' (tasks witness), 'unattainable' (tasks=[]; full caps
 cannot win), or 'unresolved' (tasks=[]; honest bounded solver uncertainty).
 No optimality or internal-state self-report is accepted. Evaluator independently
 checks witnesses, ranks, unattainability and controls; no answers are returned.
 After one solve, release {op:'release'} -> {ok:true} clears episode buffers.
 No additional response fields, logs on stdout, file paths, polling, retries,
 state transfers, candidate-chosen objectives or hidden telemetry are supported.
 Maximum response: 48 decisions with at most 100 integer indices each, <64 KiB.
 reset -> upload_start -> upload_chunk(s) -> upload_commit -> solve -> release.
 A method may replace the solver below while preserving this exact interface.
"""

import base64
import hashlib
import itertools
import math
import random
import time

import numpy as np

_state = {}


def _ranks(matrix):
    result = np.zeros(matrix.shape[0])
    for column in matrix.T:
        _, inverse, counts = np.unique(column, return_inverse=True, return_counts=True)
        below = np.cumsum(counts) - counts
        result += (below[inverse] + (counts[inverse] - 1) / 2) / (len(column) - 1)
    return result / matrix.shape[1]


def _solve(matrix, target, rule, fraction, tolerance, deadline):
    original = matrix[target]
    caps = np.round(original + fraction * (1 - original), 10)
    if rule == 'borda':
        initial = _ranks(matrix)
        before = (original > matrix).astype(float) + .5 * (original == matrix)
        after = (caps > matrix).astype(float) + .5 * (caps == matrix)
        delta = after - before
        delta[target] = 0
        gains = delta.sum(axis=0)
        coefficients = (delta + gains) / ((matrix.shape[0] - 1) * matrix.shape[1])
        def gap(indices):
            updated = initial[target] - initial + coefficients[:, indices].sum(axis=1)
            return float(updated.min())
    else:
        aggregate = np.mean if rule == 'mean' else np.median
        competitors = np.delete(aggregate(matrix, axis=1), target).max()
        def gap(indices):
            value = original.copy()
            value[indices] = caps[indices]
            return float(aggregate(value) - competitors)
    count = matrix.shape[1]
    if gap([]) >= -tolerance:
        return {'status': 'feasible', 'tasks': []}
    if gap(list(range(count))) < -tolerance:
        return {'status': 'unattainable', 'tasks': []}
    if count <= 6:
        for size in range(1, count + 1):
            for subset in itertools.combinations(range(count), size):
                if time.monotonic() >= deadline:
                    return {'status': 'unresolved', 'tasks': []}
                indices = list(subset)
                if gap(indices) >= -tolerance:
                    return {'status': 'feasible', 'tasks': indices}
    selected = []
    remaining = set(range(count))
    while gap(selected) < -tolerance:
        if time.monotonic() >= deadline:
            return {'status': 'feasible', 'tasks': list(range(count))}
        best = max(sorted(remaining), key=lambda column: gap(selected + [column]))
        selected.append(best)
        remaining.remove(best)
    for column in selected.copy():
        trial = [item for item in selected if item != column]
        if gap(trial) >= -tolerance:
            selected = trial
    return {'status': 'feasible', 'tasks': sorted(selected)}


def handle(request):
    operation = request['op']
    if operation == 'reset':
        assert set(request) == {'op', 'seed'}
        assert type(request['seed']) is int and request['seed'] >= 0
        _state.clear()
        _state['rng'] = random.Random(request['seed'])
        return {'ok': True}
    if operation == 'upload_start':
        assert set(request) == {'op', 'encoding', 'dtype', 'shape', 'byte_length', 'chunk_count', 'sha256', 'task_ids'}
        models, tasks = request['shape']
        size = request['byte_length']
        assert 2 <= models <= 100000 and 2 <= tasks <= 100
        assert request['dtype'] == '<f8' and request['encoding'] == 'base64'
        assert size == models * tasks * 8 and 0 < size <= 16 * 1048576
        assert request['chunk_count'] == math.ceil(size / 1048576)
        assert len(request['task_ids']) == tasks
        _state['meta'] = request.copy()
        _state['buffer'] = bytearray()
        _state['next'] = 0
        return {'ok': True}
    if operation == 'upload_chunk':
        assert set(request) == {'op', 'index', 'data'}
        assert request['index'] == _state['next']
        block = base64.b64decode(request['data'], validate=True)
        remaining = _state['meta']['byte_length'] - len(_state['buffer'])
        assert len(block) == min(1048576, remaining) and remaining > 0
        _state['buffer'].extend(block)
        _state['next'] += 1
        return {'ok': True}
    if operation == 'upload_commit':
        assert set(request) == {'op'}
        meta = _state['meta']
        assert _state['next'] == meta['chunk_count']
        assert hashlib.sha256(_state['buffer']).hexdigest() == meta['sha256']
        matrix = np.frombuffer(_state.pop('buffer'), dtype='<f8').copy().reshape(meta['shape'])
        assert np.isfinite(matrix).all() and (matrix >= 0).all() and (matrix <= 1).all()
        _state['matrix'] = np.round(matrix, 10)
        return {'ok': True}
    if operation == 'solve':
        assert set(request) == {'op', 'targets', 'rules', 'cap_fractions', 'tolerance', 'work_seconds'}
        assert request['rules'] == ['mean', 'median', 'borda']
        assert len(request['cap_fractions']) == 2 and all(0 <= item <= 1 for item in request['cap_fractions'])
        targets = request['targets']
        assert 1 <= len(targets) <= 8 and len(set(targets)) == len(targets)
        assert all(type(item) is int and 0 <= item < len(_state['matrix']) for item in targets)
        assert request['tolerance'] == 1e-10 and 0 < request['work_seconds'] <= 60
        deadline = time.monotonic() + request['work_seconds'] * .9
        results = [_solve(_state['matrix'], target, rule, fraction, request['tolerance'], deadline)
                   for target in targets for rule in request['rules'] for fraction in request['cap_fractions']]
        return {'solutions': results}
    if operation == 'release':
        assert set(request) == {'op'}
        _state.clear()
        return {'ok': True}
    raise ValueError('unsupported operation')
