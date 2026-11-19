"""Deterministic, lightweight source-response anchors and ridge reconstruction.

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
from sklearn.cluster import KMeans
from threadpoolctl import threadpool_limits

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
        groups = np.array(_state['config']['item_groups'])
        representatives = np.unique(groups, return_index=True)[1]
        count = min(_state['config']['max_budget'], len(representatives))
        clustering = KMeans(n_clusters=count, n_init=1, max_iter=40,
                            random_state=int(_state['seed'] % (2**32 - 1)))
        clustering.fit(matrix.T)
        chosen = []
        for center in clustering.cluster_centers_:
            eligible = [int(index) for index in representatives if groups[index] not in {groups[item] for item in chosen}]
            distances = np.sum((matrix[:, eligible].T - center) ** 2, axis=1)
            chosen.append(eligible[int(np.argmin(distances))])
        _state['chosen'] = chosen
    elif operation == 'select':
        return {'items': _state['chosen'][:request['budget']]}
    elif operation == 'observe':
        _state['items'] = request['items']
        _state['observed'] = np.asarray(request['values'], dtype=float)
    elif operation == 'update':
        matrix = _state['matrix'].astype(float)
        items = _state['items']
        weights = np.asarray(_state['config']['source_weights'])
        features = matrix[:, items]
        means = weights @ features
        scores = matrix.mean(axis=1)
        prior = float(weights @ scores)
        centered = features - means
        regularization = 1.0
        coefficients = np.linalg.solve(centered.T @ (weights[:, None] * centered)
                                       + regularization * np.eye(len(items)),
                                       centered.T @ (weights * (scores - prior)))
        estimates = prior + (_state['observed'] - means) @ coefficients
        _state['predictions'] = np.clip(estimates, 0, 1).tolist()
    elif operation == 'predict':
        return {'predictions': _state['predictions']}
    elif operation == 'close':
        _state = {}
    else:
        raise ValueError('unknown operation')
    return {'ok': True}
