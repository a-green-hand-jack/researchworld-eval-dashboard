"""Source-trained frozen low-rank reconstruction with randomized residual audits.

Only handle(request) is public. All requests/responses are finite inline JSON
objects; extra response keys are forbidden. Errors raise exceptions, not JSON.
No paths, artifacts, filenames, metrics, or unqueried target data are exchanged.
All binary data are C-order uint8, with encoding='base64' and byte_order='na'.
Reset accepts arbitrary nonnegative integer seeds (not bool); seeds only set RNG.

Episode transitions, in order:
  reset {op, seed} -> {ok: true}; discard ALL episode state.
  upload_start {op, shape: [source_rows, items], dtype:'uint8',
    encoding:'base64', byte_order:'na', total_bytes:int, chunks:int,
    item_groups:[int]*items, source_weights:[float]*source_rows,
    source_groups:[int]*source_rows,
    target_count:int, max_budget:int} -> {ok:true}.
    Bounds: 1..512 source rows, 25..65536 items, <=32MiB total,
    1..11 chunks <=3MiB each, <=513 targets, max_budget<=25.
    item_groups identify equal-content items (anonymous, consecutive integers).
    source_weights sum to one; they equalize source lineage groups.
    source_groups are anonymous episode-local lineage IDs, for source-only CV.
  upload_chunk {op, index:int, offset:int, data:str} -> {ok:true}.
    Sequential chunks fill candidate-owned memory only; exact total size.
  upload_commit {op} -> {ok:true}; validate assembled binary source matrix.
  fit {op, training_steps:int, cv_settings:int} -> {ok:true}.
    Advisory source-only optimization allowances, not attested work counters.
  select {op, budget:int} -> {items:[int]*budget}.
    A nested prefix of distinct content groups; one common subset for all
    anonymous targets. Budgets increase (production 5,10,25; smoke 2,5).
  observe {op, items:[int]*budget, values:[[0|1]*budget]*target_count}
    -> {ok:true}. Complete cumulative queried histories only; never infer
    workload identity from zero observations or reset seeds.
  update {op} -> {ok:true}; optional internal adaptation from legal observations.
  predict {op} -> {predictions:[float]*target_count}, finite in [0,1].
    Equal observed histories must yield equal predictions, regardless of row
    position. target_count includes an anonymous duplicate-history probe.
  close {op} -> {ok:true}; release episode-owned memory.

The same interface applies to smoke, search and final. No self-reported state,
flags, diagnostics or timing are accepted. Deterministic replay uses a fresh
reset with identical inputs. Zero-observation and independently permuted-source
controls exercise this actual implementation, not alternative method aliases.
Implementations may replace this starter algorithm, including nonadaptive
methods; all fitting/tuning must use source data only. No comparative accuracy
threshold is an eligibility gate. Full-score truth and baselines stay private.
"""

import base64
import numpy as np
from threadpoolctl import threadpool_limits

from surrogate import (combine_prediction, estimate_parts, fit_surrogate,
                       make_design, make_validation_folds, tune_configuration,
                       uniform_predictions)

_state = {}


def handle(request):
    global _state
    operation = request['op']
    if operation == 'reset':
        seed = request['seed']
        if type(seed) is not int or seed < 0:
            raise ValueError('invalid seed')
        _state = {'rng': np.random.default_rng(seed), 'seed': seed}
        return {'ok': True}
    if operation == 'upload_start':
        rows, columns = request['shape']
        if not (1 <= rows <= 512 and 25 <= columns <= 65536
                and rows * columns == request['total_bytes'] <= 33554432
                and 1 <= request['chunks'] <= 11
                and request['dtype'] == 'uint8' and request['encoding'] == 'base64'
                and request['byte_order'] == 'na'):
            raise ValueError('invalid upload')
        _state.update(config=request, buffer=bytearray(), chunk_index=0)
    elif operation == 'upload_chunk':
        data = base64.b64decode(request['data'], validate=True)
        if (request['offset'] != len(_state['buffer'])
                or request['index'] != _state['chunk_index'] or len(data) > 3145728
                or len(_state['buffer']) + len(data) > _state['config']['total_bytes']):
            raise ValueError('invalid chunk')
        _state['buffer'].extend(data)
        _state['chunk_index'] += 1
    elif operation == 'upload_commit':
        config = _state['config']
        if len(_state['buffer']) != config['total_bytes'] or _state['chunk_index'] != config['chunks']:
            raise ValueError('incomplete upload')
        matrix = np.frombuffer(_state.pop('buffer'), dtype=np.uint8).reshape(config['shape']).copy()
        if np.any(matrix > 1):
            raise ValueError('nonbinary matrix')
        _state['matrix'] = matrix
    elif operation == 'fit':
        threadpool_limits(1)
        matrix = _state['matrix'].astype(float)
        config = _state['config']
        weights = np.asarray(config['source_weights'], dtype=float)
        source_groups = np.asarray(config['source_groups'])
        _state['item_groups'] = np.asarray(config['item_groups'])
        _state['model'] = fit_surrogate(matrix, weights)
        _state['folds'] = make_validation_folds(
            matrix, weights, source_groups, _state['seed'] + 104729)
        _state.pop('chosen', None)
        _state.pop('observed', None)
        _state.pop('predictions', None)
        _state['last_budget'] = 0
    elif operation == 'select':
        budget = request['budget']
        groups = _state['item_groups']
        maximum = min(_state['config']['max_budget'], np.unique(groups).size)
        if type(budget) is not int or not (0 <= budget <= maximum):
            raise ValueError('invalid budget')
        if budget < _state['last_budget']:
            raise ValueError('budgets must increase')
        if budget == 0:
            return {'items': []}
        if 'chosen' not in _state:
            _, sizes = np.unique(groups, return_counts=True)
            pilot_maximum = min(budget - 1, 12, int(np.sum(sizes == 1)))
            _state['uniform_mode'] = budget <= 2 or not _state['folds']
            candidates = [0, min(pilot_maximum, max(1, budget // 2)), pilot_maximum]
        else:
            candidates = [_state['tuning']['pilot_size']]
        if _state['uniform_mode']:
            tuning = dict(pilot_size=0, rank=0, ridge=0.25, correction_weight=1.0)
        else:
            tuning = tune_configuration(_state['folds'], groups, budget, candidates,
                                        _state['seed'] + 65537)
        _state['tuning'] = tuning
        if 'chosen' not in _state:
            _state['chosen'] = make_design(
                _state['model'][1], groups, tuning['pilot_size'], maximum,
                _state['seed'] + 15485863).tolist()
        _state['last_budget'] = budget
        return {'items': _state['chosen'][:budget]}
    elif operation == 'observe':
        if request['items'] != _state.get('chosen', [])[:_state['last_budget']]:
            raise ValueError('observation items do not match selection')
        _state['items'] = request['items']
        values = np.asarray(request['values'], dtype=float)
        if (values.shape != (_state['config']['target_count'], len(request['items']))
                or not np.all((values == 0) | (values == 1))):
            raise ValueError('invalid observations')
        _state['observed'] = values
    elif operation == 'update':
        indices = np.asarray(_state['items'], dtype=int)
        groups = _state['item_groups']
        observed = _state['observed']
        if indices.size == 0:
            predictions = [float(_state['model'][0].mean())] * observed.shape[0]
        elif indices.size == groups.size:
            predictions = observed.mean(axis=1).tolist()
        elif _state['uniform_mode']:
            predictions = uniform_predictions(observed, indices, groups).tolist()
        else:
            tuning = _state['tuning']
            item_means, loadings = _state['model']
            predictions = []
            for answers in observed:
                plugin_score, residual_correction = estimate_parts(
                    item_means, loadings[:, :tuning['rank']], indices,
                    tuning['pilot_size'], answers, tuning['ridge'], groups)
                predictions.append(combine_prediction(
                    plugin_score, residual_correction, tuning['correction_weight']))
        _state['predictions'] = predictions
    elif operation == 'predict':
        return {'predictions': _state['predictions']}
    elif operation == 'close':
        _state = {}
    else:
        raise ValueError('unknown operation')
    return {'ok': True}
