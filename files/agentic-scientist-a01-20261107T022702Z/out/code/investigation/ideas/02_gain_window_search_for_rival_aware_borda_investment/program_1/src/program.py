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


def _borda_totals(matrix):
    result = np.zeros(matrix.shape[0], dtype=np.int64)
    for column in matrix.T:
        _, inverse, counts = np.unique(column, return_inverse=True, return_counts=True)
        below = np.cumsum(counts) - counts
        result += 2 * below[inverse] + counts[inverse] - 1
    return result


def _borda_trim(coefficients, deficits, selected, deadline):
    selected = list(selected)
    achieved = coefficients[:, selected].sum(axis=1)
    order = sorted(selected, key=lambda column: int(coefficients[:, column].sum()))
    for column in order:
        if time.monotonic() >= deadline:
            break
        trial_coverage = achieved - coefficients[:, column]
        if np.all(trial_coverage >= deficits):
            selected.remove(column)
            achieved = trial_coverage
    return selected


def _borda_greedy(coefficients, deficits, deadline, variant):
    residual = deficits.copy()
    selected = []
    available = np.ones(coefficients.shape[1], dtype=bool)
    while np.any(residual > 0):
        if time.monotonic() >= deadline:
            return None
        coverage = np.minimum(coefficients, np.maximum(residual, 0)[:, None]).sum(axis=0)
        if variant == 0:
            priority = coverage
        else:
            clipped = np.minimum(coefficients, np.maximum(residual, 0)[:, None])
            weights = 1.0 / np.maximum(deficits if variant == 1 else residual, 1)
            weights[residual <= 0] = 0
            priority = weights @ clipped
        priority = np.where(available, priority, -1)
        column = int(np.argmax(priority))
        if priority[column] <= 0:
            return None
        selected.append(column)
        available[column] = False
        residual -= coefficients[:, column]
    return _borda_trim(coefficients, deficits, selected, deadline)


def _borda_exchange_descent(coefficients, deficits, selected, deadline):
    selected = _borda_trim(coefficients, deficits, selected, deadline)
    while len(selected) >= 2 and time.monotonic() < deadline:
        achieved = coefficients[:, selected].sum(axis=1)
        available = np.ones(coefficients.shape[1], dtype=bool)
        available[selected] = False
        if not np.any(available):
            return selected
        improved = False
        for first, second in itertools.combinations(selected, 2):
            if time.monotonic() >= deadline:
                return selected
            residual = deficits - achieved + coefficients[:, first] + coefficients[:, second]
            screening_rows = np.flatnonzero(residual > 0)[:16]
            possible = available.copy()
            if len(screening_rows):
                possible &= np.all(coefficients[screening_rows] >= residual[screening_rows, None], axis=0)
            removed = {first, second}
            for replacement in np.flatnonzero(possible).tolist():
                if time.monotonic() >= deadline:
                    return selected
                trial = [column for column in selected if column not in removed] + [replacement]
                if len(trial) < len(selected) and np.all(coefficients[:, trial].sum(axis=1) >= deficits):
                    selected = _borda_trim(coefficients, deficits, trial, deadline)
                    improved = True
                    break
            if improved:
                break
        if not improved:
            break
    return selected


class _BordaSearchInterrupted(Exception):
    pass


def _borda_budget_search(coefficients, deficits, task_gains, budget, deadline):
    maximum_deficit = int(deficits.max())
    common_gain_floor = max(0, maximum_deficit - 2 * budget)
    relevant = deficits > maximum_deficit - 2 * budget
    maximum_common_gain = np.sort(task_gains)[::-1][:budget].sum()
    if maximum_common_gain < common_gain_floor:
        return None, True
    if time.monotonic() >= deadline:
        return None, False
    order = np.argsort(-task_gains, kind='stable')
    completion_gains = np.empty(len(order), dtype=np.int64)
    completion_gains[:budget] = maximum_common_gain
    completion_gains[budget:] = task_gains[order[:budget - 1]].sum() + task_gains[order[budget:]]
    order = order[completion_gains >= common_gain_floor]
    count = len(order)
    if count < budget:
        return None, True
    gains = task_gains[order]
    remaining_coefficients = coefficients[relevant][:, order]
    required = deficits[relevant]
    suffix_gain_bound = np.full((count + 1, budget + 1), -10**18, dtype=np.int64)
    suffix_gain_bound[:, 0] = 0
    for position in range(count - 1, -1, -1):
        suffix_gain_bound[position, 1:] = np.maximum(
            suffix_gain_bound[position + 1, 1:],
            gains[position] + suffix_gain_bound[position + 1, :-1])
    row_count = len(required)
    suffix_cover_bound = None
    suffix_ones = None
    suffix_twos = None
    if row_count <= 32:
        suffix_cover_bound = np.full((row_count, count + 1, budget + 1), -10**18, dtype=np.int64)
        suffix_cover_bound[:, :, 0] = 0
        for position in range(count - 1, -1, -1):
            if time.monotonic() >= deadline:
                return None, False
            suffix_cover_bound[:, position, 1:] = np.maximum(
                suffix_cover_bound[:, position + 1, 1:],
                remaining_coefficients[:, position, None] + suffix_cover_bound[:, position + 1, :-1])
    else:
        corrections = remaining_coefficients - gains
        suffix_ones = np.zeros((row_count, count + 1), dtype=np.int16)
        suffix_twos = np.zeros_like(suffix_ones)
        suffix_ones[:, :count] = np.cumsum((corrections[:, ::-1] >= 1), axis=1, dtype=np.int16)[:, ::-1]
        suffix_twos[:, :count] = np.cumsum((corrections[:, ::-1] == 2), axis=1, dtype=np.int16)[:, ::-1]
    chosen = []

    def visit(position, slots, selected_gain, residual):
        if time.monotonic() >= deadline:
            raise _BordaSearchInterrupted
        if count - position < slots:
            return None
        if selected_gain + suffix_gain_bound[position, slots] < common_gain_floor:
            return None
        if slots == 0:
            return chosen.copy() if np.all(residual <= 0) else None
        if suffix_cover_bound is not None:
            optimistic = suffix_cover_bound[:, position, slots]
        else:
            optimistic = (suffix_gain_bound[position, slots]
                          + np.minimum(slots, suffix_ones[:, position])
                          + np.minimum(slots, suffix_twos[:, position]))
        if np.any(residual > optimistic):
            return None
        if np.all(residual <= 0):
            return chosen + order[position:position + slots].tolist()
        if count - position == slots:
            if np.all(remaining_coefficients[:, position:].sum(axis=1) >= residual):
                return chosen + order[position:].tolist()
            return None
        chosen.append(int(order[position]))
        result = visit(position + 1, slots - 1, selected_gain + int(gains[position]),
                       residual - remaining_coefficients[:, position])
        chosen.pop()
        if result is not None:
            return result
        return visit(position + 1, slots, selected_gain, residual)

    try:
        result = visit(0, budget, 0, required)
    except _BordaSearchInterrupted:
        return None, False
    if result is not None:
        assert np.all(coefficients[:, result].sum(axis=1) >= deficits)
    return result, True


def _solve_borda(matrix, totals, target, fraction, tolerance, deadline):
    original = matrix[target]
    caps = np.round(original + fraction * (1 - original), 10)
    credit_denominator = 2 * (matrix.shape[0] - 1) * matrix.shape[1]
    deficits = np.ceil(totals - totals[target] - tolerance * credit_denominator).astype(np.int64)
    active = np.flatnonzero(deficits > 0)
    if len(active) == 0:
        return {'status': 'feasible', 'tasks': []}
    before = 2 * (original > matrix).astype(np.int8) + (original == matrix).astype(np.int8)
    after = 2 * (caps > matrix).astype(np.int8) + (caps == matrix).astype(np.int8)
    pair_delta = after - before
    pair_delta[target] = 0
    task_gains = pair_delta.sum(axis=0, dtype=np.int64)
    coefficients = pair_delta[active].astype(np.int64) + task_gains
    deficits = deficits[active]
    if np.any(coefficients.sum(axis=1) < deficits):
        return {'status': 'unattainable', 'tasks': []}
    started = time.monotonic()
    available_time = max(0.0, deadline - started)
    greedy_deadline = started + available_time * .30
    exchange_deadline = started + available_time * .50
    order = np.argsort(-task_gains, kind='stable')
    cumulative = np.cumsum(coefficients[:, order], axis=1)
    prefix_size = int(np.flatnonzero(np.all(cumulative >= deficits[:, None], axis=0))[0]) + 1
    selected = order[:prefix_size].tolist()
    selected = _borda_trim(coefficients, deficits, selected, greedy_deadline)
    for variant in range(3):
        if time.monotonic() >= greedy_deadline:
            break
        portfolio_deadline = time.monotonic() + max(0.0, greedy_deadline - time.monotonic()) / (3 - variant)
        trial = _borda_greedy(coefficients, deficits, portfolio_deadline, variant)
        if trial is not None and len(trial) < len(selected) and np.all(coefficients[:, trial].sum(axis=1) >= deficits):
            selected = trial
    selected = _borda_exchange_descent(coefficients, deficits, selected, exchange_deadline)
    maximum_deficit = int(deficits.max())
    gain_prefix = np.cumsum(np.sort(task_gains)[::-1])
    lower_bound = 1
    while lower_bound < len(selected) and gain_prefix[lower_bound - 1] + 2 * lower_bound < maximum_deficit:
        lower_bound += 1
    while lower_bound < len(selected):
        if time.monotonic() >= deadline:
            break
        budget = len(selected) - 1
        trial, exhausted = _borda_budget_search(coefficients, deficits, task_gains, budget, deadline)
        if trial is not None:
            selected = trial
        elif exhausted:
            lower_bound = budget + 1
        else:
            break
    assert np.all(coefficients[:, selected].sum(axis=1) >= deficits)
    return {'status': 'feasible', 'tasks': sorted(selected)}


def _solve(matrix, target, rule, fraction, tolerance, deadline):
    original = matrix[target]
    caps = np.round(original + fraction * (1 - original), 10)
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
        fractions = [float(np.round(fraction, 10)) for fraction in request['cap_fractions']]
        decisions = [(target, rule, fraction) for target in targets
                     for rule in request['rules'] for fraction in fractions]
        cap_keys = {(target, fraction): np.round(
            _state['matrix'][target] + fraction * (1 - _state['matrix'][target]), 10).tobytes()
                    for target in targets for fraction in fractions}
        remaining = len({(target, rule, cap_keys[target, fraction]) for target, rule, fraction in decisions})
        cache = {}
        totals = None
        results = []
        for target, rule, fraction in decisions:
            key = (target, rule, cap_keys[target, fraction])
            if key not in cache:
                now = time.monotonic()
                decision_deadline = now + max(0.0, deadline - now) / remaining
                if rule == 'borda':
                    if totals is None:
                        totals = _borda_totals(_state['matrix'])
                    result = _solve_borda(_state['matrix'], totals, target, fraction,
                                          request['tolerance'], decision_deadline)
                else:
                    result = _solve(_state['matrix'], target, rule, fraction,
                                    request['tolerance'], decision_deadline)
                cache[key] = result
                remaining -= 1
            results.append(cache[key])
        return {'solutions': results}
    if operation == 'release':
        assert set(request) == {'op'}
        _state.clear()
        return {'ok': True}
    raise ValueError('unsupported operation')
