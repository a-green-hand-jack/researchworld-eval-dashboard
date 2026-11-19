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


def _borda_totals(matrix):
    if matrix is _state.get('matrix') and 'borda_totals' in _state:
        return _state['borda_totals']
    totals = np.zeros(matrix.shape[0], dtype=np.int64)
    for column in matrix.T:
        _, inverse, counts = np.unique(column, return_inverse=True, return_counts=True)
        below = np.cumsum(counts) - counts
        totals += 2 * below[inverse] + counts[inverse] - 1
    if matrix is _state.get('matrix'):
        _state['borda_totals'] = totals
    return totals


def _borda_trim(coefficients, deficits, selected, deadline):
    selected = list(selected)
    coverage = coefficients[:, selected].sum(axis=1)
    order = sorted(selected, key=lambda column: int(coefficients[:, column].max()))
    for column in order:
        if time.monotonic() >= deadline:
            break
        if np.all(coverage - coefficients[:, column] >= deficits):
            coverage -= coefficients[:, column]
            selected.remove(column)
    return selected


def _borda_mixture_certificate(weights, coefficients, deficits, budget):
    assert weights.dtype == np.int64
    assert np.all(weights >= 0) and int(weights.sum()) <= 1048576
    mass = int(weights.sum())
    limit = int(np.iinfo(np.int64).max)
    coefficient_bound = int(coefficients.max(initial=0))
    deficit_bound = int(np.abs(deficits).max(initial=0))
    if mass * max(deficit_bound, coefficient_bound * coefficients.shape[1]) > limit:
        return False, None
    weighted_scores = weights @ coefficients
    weighted_deficit = int(weights @ deficits)
    top_budget_bound = int(np.sort(weighted_scores)[-budget:].sum()) if budget else 0
    if top_budget_bound < weighted_deficit:
        return True, top_budget_bound - weighted_deficit
    return False, top_budget_bound - weighted_deficit


def _borda_dual_directions(coefficients, deficits, budget, deadline):
    rival_count = len(deficits)
    largest = int(np.argmax(deficits))
    concentrated = np.zeros(rival_count, dtype=np.float64)
    concentrated[largest] = 1.0
    initializations = [np.full(rival_count, 1.0 / rival_count), concentrated,
                       deficits.astype(np.float64) / float(deficits.sum())]
    scale = max(1, int(deficits.max()))
    for initialization in initializations:
        dual_weights = initialization.copy()
        for iteration in range(32):
            if time.monotonic() >= deadline:
                return
            top_indices = np.argsort(-(dual_weights @ coefficients), kind='stable')[:budget]
            violation = deficits - coefficients[:, top_indices].sum(axis=1)
            if iteration % 4 == 0 or np.all(violation <= 0):
                yield dual_weights.copy(), top_indices
            step_size = 1.0 / (scale * math.sqrt(iteration + 1))
            dual_weights = np.maximum(0.0, dual_weights + step_size * violation)
            mass = float(dual_weights.sum())
            if mass == 0:
                dual_weights = initialization.copy()
            else:
                dual_weights /= mass


def _borda_discover(coefficients, deficits, budget, selected, deadline):
    count = len(deficits)
    residual = deficits - coefficients[:, selected[:budget]].sum(axis=1)
    single_capacity = np.sort(coefficients, axis=1)[:, -budget:].sum(axis=1) if budget else np.zeros(count, dtype=np.int64)
    priorities = [deficits, residual, deficits - single_capacity]
    working = sorted(set(int(index) for priority in priorities
                         for index in np.argsort(-priority, kind='stable')[:16]))
    working_coefficients = coefficients[working]
    working_deficits = deficits[working]
    records = []
    seen = set()
    rejected = False
    proposal = None
    for direction, top_indices in _borda_dual_directions(
            working_coefficients, working_deficits, budget, deadline):
        if np.all(coefficients[:, top_indices].sum(axis=1) >= deficits):
            proposal = [int(column) for column in top_indices]
            break
        weights = np.floor(direction / float(direction.sum()) * 1048576).astype(np.int64)
        mass = int(weights.sum())
        if mass > 1048576:
            weights[int(np.argmax(weights))] -= mass - 1048576
        if not np.any(weights):
            continue
        key = tuple(int(weight) for weight in weights)
        if key in seen:
            continue
        seen.add(key)
        impossible, slack = _borda_mixture_certificate(
            weights, working_coefficients, working_deficits, budget)
        if slack is None:
            continue
        records.append((slack, weights))
        records.sort(key=lambda record: record[0])
        records = records[:12]
        if impossible:
            rejected = True
            break
    cut_weights = np.zeros((len(records), count), dtype=np.int64)
    for index, (_, weights) in enumerate(records):
        cut_weights[index, working] = weights
    return proposal, cut_weights, rejected


def _borda_budget_search(coefficients, deficits, gains, budget, cut_weights, deadline):
    if time.monotonic() >= deadline:
        return None, False
    order = np.argsort(-gains, kind='stable')
    ordered_coefficients = coefficients[:, order]
    ordered_gains = gains[order]
    count = len(order)
    mass = max((int(weights.sum()) for weights in cut_weights), default=0)
    bound = max(int(deficits.max(initial=0)), int(coefficients.max(initial=0)) * count)
    if mass * bound > int(np.iinfo(np.int64).max):
        cut_weights = np.zeros((0, len(deficits)), dtype=np.int64)
    cut_scores = cut_weights @ ordered_coefficients
    suffix_cut_bound = np.full((len(cut_weights), count + 1, budget + 1), -1, dtype=np.int64)
    suffix_cut_bound[:, :, 0] = 0
    for position in range(count - 1, -1, -1):
        if time.monotonic() >= deadline:
            return None, False
        for slots in range(1, min(budget, count - position) + 1):
            previous = suffix_cut_bound[:, position + 1, slots - 1]
            with_task = np.where(previous >= 0, previous + cut_scores[:, position], -1)
            suffix_cut_bound[:, position, slots] = np.maximum(
                suffix_cut_bound[:, position + 1, slots], with_task)
    suffix_maximum = np.maximum.accumulate(ordered_coefficients[:, ::-1], axis=1)[:, ::-1]
    gain_prefix = np.concatenate((np.zeros(1, dtype=np.int64), np.cumsum(ordered_gains)))
    nodes = 0

    def visit(position, slots, residual, chosen):
        nonlocal nodes
        nodes += 1
        if nodes % 32 == 1 and time.monotonic() >= deadline:
            raise TimeoutError
        if np.all(residual <= 0):
            return chosen
        if slots == 0 or count - position < slots:
            return None
        gain_bound = int(gain_prefix[position + slots] - gain_prefix[position]) + 2 * slots
        if int(residual.max()) > gain_bound:
            return None
        weighted_residual = cut_weights @ residual
        if np.any(weighted_residual > suffix_cut_bound[:, position, slots]):
            return None
        if np.any(residual > suffix_maximum[:, position] * slots):
            return None
        if count - position == slots:
            if np.all(ordered_coefficients[:, position:].sum(axis=1) >= residual):
                return chosen + [int(column) for column in order[position:]]
            return None
        if slots == 1:
            feasible = np.all(ordered_coefficients[:, position:] >= residual[:, None], axis=0)
            matches = np.flatnonzero(feasible)
            return chosen + [int(order[position + matches[0]])] if len(matches) else None
        found = visit(position + 1, slots - 1,
                      residual - ordered_coefficients[:, position], chosen + [int(order[position])])
        if found is not None:
            return found
        return visit(position + 1, slots, residual, chosen)

    try:
        return visit(0, budget, deficits.copy(), []), True
    except TimeoutError:
        return None, False


def _solve_borda(matrix, target, caps, tolerance, deadline):
    count = matrix.shape[1]
    totals = _borda_totals(matrix)
    scale = 2 * (matrix.shape[0] - 1) * count
    deficits = totals - totals[target] - math.floor(tolerance * scale)
    active = np.flatnonzero(deficits > 0)
    if not len(active):
        return {'status': 'feasible', 'tasks': []}
    original = matrix[target]
    before = 2 * (original > matrix).astype(np.int8) + (original == matrix)
    after = 2 * (caps > matrix).astype(np.int8) + (caps == matrix)
    delta = after - before
    delta[target] = 0
    gains = delta.sum(axis=0, dtype=np.int64)
    coefficients = delta[active].astype(np.int64) + gains
    deficits = deficits[active]
    if np.any(coefficients.sum(axis=1) < deficits):
        return {'status': 'unattainable', 'tasks': []}
    order = np.argsort(-gains, kind='stable')
    selected = []
    coverage = np.zeros(len(active), dtype=np.int64)
    for column in order:
        if np.all(coverage >= deficits):
            break
        selected.append(int(column))
        coverage += coefficients[:, column]
    remaining_time = max(0.0, deadline - time.monotonic())
    greedy_deadline = min(deadline, time.monotonic() + remaining_time * .15)
    selected = _borda_trim(coefficients, deficits, selected, greedy_deadline)
    greedy = []
    available = np.ones(count, dtype=bool)
    coverage = np.zeros(len(active), dtype=np.int64)
    while len(greedy) < len(selected) and time.monotonic() < greedy_deadline:
        merits = (coverage[:, None] + coefficients - deficits[:, None]).min(axis=0)
        merits[~available] = np.iinfo(np.int64).min
        column = int(np.argmax(merits))
        greedy.append(column)
        available[column] = False
        coverage += coefficients[:, column]
        if np.all(coverage >= deficits):
            selected = _borda_trim(coefficients, deficits, greedy, greedy_deadline)
            break
    assert np.all(coefficients[:, selected].sum(axis=1) >= deficits)
    if time.monotonic() < deadline:
        independent_prefix = np.cumsum(np.sort(coefficients, axis=1)[:, ::-1], axis=1)
        lower_bound = int(np.argmax(np.all(independent_prefix >= deficits[:, None], axis=0))) + 1
    else:
        lower_bound = 1
    while len(selected) > lower_bound and time.monotonic() < deadline:
        budget = len(selected) - 1
        discovery_deadline = min(deadline, time.monotonic() + max(0.0, deadline - time.monotonic()) * .25)
        proposal, cut_weights, rejected = _borda_discover(
            coefficients, deficits, budget, selected, discovery_deadline)
        if rejected:
            break
        if proposal is not None:
            selected = _borda_trim(coefficients, deficits, proposal, deadline)
            continue
        rejected = False
        for weights in cut_weights:
            impossible, _ = _borda_mixture_certificate(weights, coefficients, deficits, budget)
            if impossible:
                rejected = True
                break
        if rejected:
            break
        proposal, completed = _borda_budget_search(
            coefficients, deficits, gains, budget, cut_weights, deadline)
        if proposal is not None and np.all(coefficients[:, proposal].sum(axis=1) >= deficits):
            selected = _borda_trim(coefficients, deficits, proposal, deadline)
        elif completed:
            break
        else:
            break
    assert np.all(coefficients[:, selected].sum(axis=1) >= deficits)
    return {'status': 'feasible', 'tasks': sorted(selected)}


def _solve(matrix, target, rule, fraction, tolerance, deadline):
    original = matrix[target]
    caps = np.round(original + fraction * (1 - original), 10)
    if rule == 'borda':
        return _solve_borda(matrix, target, caps, tolerance, deadline)
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
        results = []
        remaining_borda = len(targets) * len(request['cap_fractions'])
        for target in targets:
            for rule in request['rules']:
                for fraction in request['cap_fractions']:
                    solve_deadline = deadline
                    if rule == 'borda':
                        now = time.monotonic()
                        solve_deadline = min(deadline, now + max(0.0, deadline - now) / remaining_borda)
                        remaining_borda -= 1
                    results.append(_solve(_state['matrix'], target, rule, fraction,
                                          request['tolerance'], solve_deadline))
        return {'solutions': results}
    if operation == 'release':
        assert set(request) == {'op'}
        _state.clear()
        return {'ok': True}
    raise ValueError('unsupported operation')
