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


def _rank_totals(matrix):
    result = np.zeros(matrix.shape[0], dtype=np.int64)
    for column in matrix.T:
        _, inverse, counts = np.unique(column, return_inverse=True, return_counts=True)
        below = np.cumsum(counts) - counts
        result += 2 * below[inverse] + counts[inverse] - 1
    return result


def _answer(indices):
    return {'status': 'feasible', 'tasks': sorted(int(column) for column in indices)}


def _exhaustive(original, caps, wins):
    available = np.flatnonzero(caps > original).tolist()
    for size in range(len(available) + 1):
        for subset in itertools.combinations(available, size):
            indices = list(subset)
            if wins(indices):
                return indices
    return None


def _mean_budget(original, caps, wins):
    order = np.argsort(-(caps - original), kind='stable')
    for size in range(len(order) + 1):
        selected = order[:size].tolist()
        if wins(selected):
            return selected
    return None


def _odd_median_budget(original, caps, competitor, tolerance):
    already_above = np.count_nonzero(original - competitor >= -tolerance)
    promotable = np.flatnonzero(
        (original - competitor < -tolerance) & (caps - competitor >= -tolerance)
    )
    needed = max(0, len(original) // 2 + 1 - already_above)
    if needed > len(promotable):
        return None
    return promotable[:needed].tolist()


def _even_median_budget(original, caps, competitor, tolerance, wins):
    half = len(original) // 2
    endpoints = np.unique(np.concatenate((original, caps)))
    best = None
    for lower in endpoints:
        upper_candidates = endpoints[
            (endpoints >= lower)
            & ((endpoints + lower) / 2 - competitor >= -tolerance)
        ]
        if not len(upper_candidates):
            continue
        upper = upper_candidates[0]
        low_needed = max(0, half + 1 - np.count_nonzero(original >= lower))
        high_needed = max(0, half - np.count_nonzero(original >= upper))
        shared = np.flatnonzero((original < lower) & (caps >= upper))
        low_only = np.flatnonzero(
            (original < lower) & (caps >= lower) & (caps < upper)
        )
        high_only = np.flatnonzero(
            (original >= lower) & (original < upper) & (caps >= upper)
        )
        if low_needed > len(shared) + len(low_only):
            continue
        if high_needed > len(shared) + len(high_only):
            continue
        shared_count = min(len(shared), max(low_needed, high_needed))
        selected = shared[:shared_count].tolist()
        selected += low_only[:max(0, low_needed - shared_count)].tolist()
        selected += high_only[:max(0, high_needed - shared_count)].tolist()
        if best is not None and len(selected) >= len(best):
            continue
        if wins(selected):
            best = selected
    return best


def _scalar_solve(matrix, target, rule, caps, tolerance, context):
    original = matrix[target]
    aggregate = np.mean if rule == 'mean' else np.median
    rival_scores = context[rule]
    competitor = max(rival_scores[:target].max(initial=-np.inf),
                     rival_scores[target + 1:].max(initial=-np.inf))

    def wins(indices):
        attacked = original.copy()
        attacked[indices] = caps[indices]
        return float(aggregate(attacked) - competitor) >= -tolerance

    if wins([]):
        return {'status': 'feasible', 'tasks': []}
    if not wins(list(range(len(original)))):
        return {'status': 'unattainable', 'tasks': []}
    if rule == 'mean':
        selected = _mean_budget(original, caps, wins)
    elif len(original) % 2:
        selected = _odd_median_budget(original, caps, competitor, tolerance)
    else:
        selected = _even_median_budget(original, caps, competitor, tolerance, wins)
    if len(original) <= 6:
        reference = _exhaustive(original, caps, wins)
        if selected is None or reference is None or len(selected) != len(reference):
            selected = reference
    if selected is None or not wins(selected):
        return {'status': 'unresolved', 'tasks': []}
    return _answer(selected)


def _borda_search(coefficients, deficits, budget, order, deadline):
    ordered = coefficients[:, order]
    count = len(order)
    visited = 0

    def search(position, residual, selected):
        nonlocal visited
        visited += 1
        if time.monotonic() >= deadline or visited > 20000:
            raise TimeoutError
        if np.all(residual <= 0):
            return selected
        slots = budget - len(selected)
        available = count - position
        if slots <= 0 or available < slots:
            return None
        suffix = ordered[:, position:]
        optimistic = np.partition(suffix, available - slots, axis=1)[:, -slots:].sum(axis=1)
        if np.any(optimistic < residual):
            return None
        if np.all(suffix[:, :slots].sum(axis=1) >= residual):
            return selected + order[position:position + slots].tolist()
        if available == slots:
            return None
        included = search(position + 1, residual - ordered[:, position],
                          selected + [int(order[position])])
        if included is not None:
            return included
        return search(position + 1, residual, selected)

    return search(0, deficits, [])


def _borda_solve(matrix, target, caps, tolerance, deadline, context):
    if context.get('borda') is None:
        context['borda'] = _rank_totals(matrix)
    totals = context['borda']
    denominator = 2 * (matrix.shape[0] - 1) * matrix.shape[1]
    raw_deficits = totals - totals[target]
    deficits = np.ceil(raw_deficits - tolerance * denominator).astype(np.int64)
    active = np.flatnonzero(deficits > 0)
    if not len(active):
        return _answer([])
    original = matrix[target]
    if np.array_equal(caps, original):
        return {'status': 'unattainable', 'tasks': []}
    before = 2 * (original > matrix).astype(np.int8) + (original == matrix).astype(np.int8)
    after = 2 * (caps > matrix).astype(np.int8) + (caps == matrix).astype(np.int8)
    delta = after - before
    delta[target] = 0
    gains = delta.sum(axis=0, dtype=np.int64)
    deficits = deficits[active]
    coefficients = delta[active].astype(np.int64) + gains
    if np.any(coefficients.sum(axis=1) < deficits):
        return {'status': 'unattainable', 'tasks': []}

    def wins(indices):
        return bool(np.all(coefficients[:, indices].sum(axis=1) >= deficits))

    order = np.argsort(-gains, kind='stable')
    accumulated = np.zeros(len(active), dtype=np.int64)
    selected = []
    for column in order:
        accumulated += coefficients[:, column]
        selected.append(int(column))
        if np.all(accumulated >= deficits):
            break
    for column in selected[::-1]:
        trial = [item for item in selected if item != column]
        if wins(trial):
            selected = trial
    if len(selected) <= 1 or time.monotonic() >= deadline:
        return _answer(selected)
    maximum_deficit = int(deficits.max())
    relevant = deficits > maximum_deficit - 2 * len(selected)
    reduced = coefficients[relevant]
    requirements = deficits[relevant]
    available = np.flatnonzero(gains > 0)
    reduced = reduced[:, available]
    ranked = np.sort(reduced, axis=1)[:, ::-1]
    cumulative = np.cumsum(ranked, axis=1)
    lower_bound = int(np.max(np.sum(cumulative < requirements[:, None], axis=1) + 1))
    if lower_bound >= len(selected):
        return _answer(selected)
    for budget in range(lower_bound, len(selected)):
        if time.monotonic() >= deadline:
            break
        search_order = np.argsort(-gains[available], kind='stable')
        try:
            found = _borda_search(reduced, requirements, budget, search_order, deadline)
        except TimeoutError:
            break
        if found is not None:
            trial = available[found].tolist()
            if wins(trial):
                selected = trial
                break
    return _answer(selected)


def _solve(matrix, target, rule, fraction, tolerance, deadline, context):
    original = matrix[target]
    caps = np.round(original + fraction * (1 - original), 10)
    if rule == 'borda':
        return _borda_solve(matrix, target, caps, tolerance, deadline, context)
    return _scalar_solve(matrix, target, rule, caps, tolerance, context)


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
        matrix = _state['matrix']
        context = {'mean': np.mean(matrix, axis=1), 'median': np.median(matrix, axis=1)}
        results = []
        cache = {}
        remaining_borda = len(targets) * len(request['cap_fractions'])
        for target in targets:
            for rule in request['rules']:
                for fraction in request['cap_fractions']:
                    key = (target, rule, float(fraction))
                    local_deadline = deadline
                    if rule == 'borda':
                        now = time.monotonic()
                        local_deadline = now + max(0, deadline - now) / remaining_borda
                        remaining_borda -= 1
                    if key not in cache:
                        cache[key] = _solve(matrix, target, rule, fraction,
                                            request['tolerance'], local_deadline, context)
                    results.append(cache[key])
        return {'solutions': results}
    if operation == 'release':
        assert set(request) == {'op'}
        _state.clear()
        return {'ok': True}
    raise ValueError('unsupported operation')
