"""CPU influence-guided comparison deletion; finite JSON handle(request) protocol.

Every request is a dict with op below. Responses have EXACTLY the documented
keys; no additional fields. No paths or external state are accepted or returned.
All seeds are arbitrary nonnegative integers; they select RNG, never workload.

reset {seed:int} -> {ok:true}: clear ALL buffers, certificates and tokens.
export_chunk {token:str,index:int} -> {error:'unknown_token'} for unknown tokens,
or {data:str(base64)} for a live output token and valid zero-based chunk index.
This same operation probes stale exported state immediately after each reset.
import_start {n_rows:int<=100000,n_players:int in [2,256],regularization:float>0,
 dtype:'<f8',shape:[n_rows,4],encoding:'base64',byte_order:'little',
 nbytes:int<=67108864,chunks:int in [1,8]} -> {ok:true}.
It replaces the input staging buffer, not RNG; no solve before commit.
import_chunk {index:int,data:str(base64)} -> {ok:true}: ordered chunks, each
at most 8388608 decoded bytes. No shared files. At most 128 MiB staging.
import_commit {} -> {ok:true}: validate byte count and decode C-order float64
rows [participant_a,participant_b,observed_a_win_fraction,row_key]. Endpoints
are distinct integers in [0,n_players), outcomes are 0,0.5,1; keys are unique
nonnegative exact integers <=2**53. Rows are observed analysis inputs, not
hidden prediction labels. n_players, regularization and row count configure
workload independently of seed. No scores or references are supplied.
solve {fractions:[0.001,0.005,0.01],max_iterations:100} -> {ok:true}.
Fit mean pair logloss + regularization/2 * sum(theta**2), zero-sum theta.
Choose any clean nonleader contender, solve H direction=e_leader-e_contender,
influence_i=(sigmoid(theta_a-theta_b)-outcome_i)*(direction_a-direction_b).
Sort ascending influence rounded to 10 decimals, then ascending stable row key.
Rank participants by descending logits rounded to 8 decimals, then ascending
integer identity. Deletion sets must
be nested EXACT prefixes of this order at floor(fraction*n_rows) budgets.
Changing contender is allowed; undisclosed post-selection refinement is not.
The exported certificate is UTF-8 finite JSON with exactly theta:[m floats],
contender:int, direction:[m floats], influence:[n floats], deletions:[3 lists
of integer row keys]. Evaluator recomputes residuals, selection and refits;
these numbers are untrusted certificates, never scores or validity flags.
export_start {} -> {token:str<=80 ASCII,nbytes:int<=67108864,chunks:int<=8,
 encoding:'base64',dtype:'json',shape:[],byte_order:'none'}; output divided
into fixed 8388608-byte chunks (last may be shorter).
release {} -> {ok:true}: erase input staging; keep exported state live until
next reset so stale-state tests can exercise the actual exported data.

Each JSON request/response including envelope/framing must be <64 MiB. Maximum
logical input/output is 64 MiB, at most 8 chunks; wire chunks are ~10.7 MiB.
No candidate timing/state-change report is requested. No scoring feedback is
given. Native CLI is JSON-lines for local debugging; production uses handle.

Contender screening is deterministic and uses only the clean fit. For every
nonleader, construct its required influence order and three exact prefixes.
Using the clean Hessian, predict the full score displacement for each prefix,
including the mean-loss regularization correction. Shortlist at most six,
including the screening winner and clean runner-up. A pool of at most 24 uses
one centered retained-Hessian Newton step at each frozen prefix to nominate at
most six extra contenders. Keep every original finalist regardless of proxy
quality. Compare finalists' frozen prefixes using converged retained-data
mean-loss ridge refits. Maximize the sum
of original-leader rank drops, target reversals, and clipped gap closure, then
prefer clean rank. Failed or incomplete candidates are excluded; if none remain,
use the screening winner. Refit scores stay internal. Export only clean-fit
certificates, never refine an order, and never infer metadata from row keys.
"""
import base64
import hashlib
import json
import math
import sys

import numpy as np
from scipy.linalg import cho_factor, cho_solve
from scipy.special import expit

STATE = {}
CHUNK = 8 * 1024 * 1024


def fit(rows, players, regularization, iterations):
    first = rows[:, 0].astype(int)
    second = rows[:, 1].astype(int)
    outcome = rows[:, 2]
    pair_index = first * players + second
    pair_counts = np.bincount(pair_index, minlength=players * players)
    pair_wins = np.bincount(pair_index, weights=outcome, minlength=players * players)
    theta, hessian = fit_aggregates(pair_counts, pair_wins, regularization,
                                    iterations=iterations, return_hessian=True)
    return theta, hessian, pair_counts, pair_wins


def fit_aggregates(retained_counts, retained_wins, regularization,
                   initial_theta=None, iterations=100, return_hessian=False):
    players = math.isqrt(len(retained_counts))
    retained_rows = int(retained_counts.sum())
    if retained_rows <= 0:
        raise RuntimeError('No retained comparisons')
    observed = np.flatnonzero(retained_counts)
    first, second = observed // players, observed % players
    retained_counts, retained_wins = retained_counts[observed], retained_wins[observed]
    scores = np.zeros(players) if initial_theta is None else initial_theta.copy()
    scores -= np.mean(scores)

    def quantities(scores):
        margin = scores[first] - scores[second]
        probability = expit(margin)
        pair_residual = (retained_counts * probability - retained_wins) / retained_rows
        data_gradient = np.bincount(first, pair_residual, minlength=players) - np.bincount(second, pair_residual, minlength=players)
        gradient = data_gradient + regularization * scores
        weight = retained_counts * probability * (1 - probability) / retained_rows
        hessian = np.diag(np.bincount(first, weight, minlength=players) + np.bincount(second, weight, minlength=players) + regularization)
        np.add.at(hessian, (first, second), -weight)
        np.add.at(hessian, (second, first), -weight)
        data_loss = np.sum(retained_counts * np.logaddexp(0, margin) - retained_wins * margin)
        objective = data_loss / retained_rows + 0.5 * regularization * np.dot(scores, scores)
        return objective, gradient, hessian

    for iteration in range(iterations):
        objective, gradient, hessian = quantities(scores)
        if np.max(np.abs(gradient)) < 1e-11:
            break
        step = cho_solve(cho_factor(hessian, lower=True, check_finite=False), gradient, check_finite=False)
        rate = 1.0
        for attempt in range(30):
            trial = scores - rate * step
            trial -= np.mean(trial)
            trial_objective, trial_gradient, unused_hessian = quantities(trial)
            sufficient_decrease = trial_objective <= objective - 1e-4 * rate * np.dot(gradient, step)
            roundoff_descent = trial_objective <= objective + 8 * np.finfo(float).eps * max(1.0, abs(objective)) and np.max(np.abs(trial_gradient)) < np.max(np.abs(gradient))
            if sufficient_decrease or roundoff_descent:
                scores = trial
                break
            rate *= 0.5
        else:
            break
    unused_objective, gradient, hessian = quantities(scores)
    if not np.isfinite(gradient).all():
        raise RuntimeError("Bradley-Terry fit did not converge")
    if not np.isfinite(scores).all() or np.max(np.abs(gradient)) > 1e-9:
        raise RuntimeError("Bradley-Terry fit did not converge")
    if return_hessian:
        return scores, hessian
    return scores


def shortlist_contenders(screen_records, incumbent_contender, runner_up, limit=6):
    shortlist = []
    ordered = [incumbent_contender, runner_up]
    ordered.extend(record['contender'] for record in sorted(screen_records, key=lambda record: record['score'], reverse=True))
    for contender in ordered:
        if contender not in shortlist:
            shortlist.append(contender)
        if len(shortlist) >= limit:
            break
    return shortlist


def bounded_proxy_pool(screen_records, baseline_shortlist, limit=24):
    pool = list(baseline_shortlist)
    if len(pool) > limit:
        raise ValueError('Baseline shortlist exceeds proxy limit')
    for record in sorted(screen_records, key=lambda record: record['score'], reverse=True):
        if len(pool) >= limit:
            break
        if record['contender'] not in pool:
            pool.append(record['contender'])
    return pool


def select_curvature_extras(curvature_records, baseline_shortlist, limit=6):
    eligible = [record for record in curvature_records
                if record['complete'] and np.isfinite(record['score']).all()
                and record['contender'] not in baseline_shortlist]
    ordered = sorted(eligible, key=lambda record: record['score'], reverse=True)
    return [record['contender'] for record in ordered[:limit]]


def clean_selection(rows, first, second, residual, clean_factor, leader, contender):
    contrast = np.zeros(clean_factor[0].shape[0])
    contrast[leader] = 1.0
    contrast[contender] = -1.0
    direction = cho_solve(clean_factor, contrast, check_finite=False)
    influence = residual * (direction[first] - direction[second])
    order = np.lexsort((rows[:, 3], np.round(influence, 10)))
    return contender, direction, influence, order


def retained_curvature_proxy(retained_counts, retained_wins, regularization, theta):
    players = len(theta)
    retained_rows = int(retained_counts.sum())
    if retained_rows <= 0:
        raise RuntimeError('No retained comparisons')
    observed = np.flatnonzero(retained_counts)
    first, second = observed // players, observed % players
    retained_counts, retained_wins = retained_counts[observed], retained_wins[observed]
    probability = expit(theta[first] - theta[second])
    pair_residual = (retained_counts * probability - retained_wins) / retained_rows
    data_gradient = np.bincount(first, pair_residual, minlength=players) - np.bincount(second, pair_residual, minlength=players)
    retained_gradient = data_gradient + regularization * theta
    weight = retained_counts * probability * (1 - probability) / retained_rows
    retained_hessian = np.diag(np.bincount(first, weight, minlength=players) + np.bincount(second, weight, minlength=players) + regularization)
    np.add.at(retained_hessian, (first, second), -weight)
    np.add.at(retained_hessian, (second, first), -weight)
    if not np.isfinite(retained_gradient).all() or not np.isfinite(retained_hessian).all():
        raise RuntimeError('Nonfinite retained-curvature proxy inputs')
    proxy_theta = theta - cho_solve(cho_factor(retained_hessian, lower=True, check_finite=False), retained_gradient, check_finite=False)
    proxy_theta -= np.mean(proxy_theta)
    if not np.isfinite(proxy_theta).all():
        raise RuntimeError('Nonfinite retained-curvature proxy')
    return proxy_theta


def refit_prefix(pair_counts, pair_wins, removed_counts, removed_wins,
                 regularization, theta):
    retained_counts = pair_counts - removed_counts
    retained_wins = pair_wins - removed_wins
    trial_theta = fit_aggregates(retained_counts, retained_wins, regularization, initial_theta=theta)
    return trial_theta


def select_contender(rows, theta, hessian, regularization, fractions,
                     pair_counts, pair_wins):
    players = len(theta)
    total_rows = len(rows)
    ranking = np.lexsort((np.arange(players), -np.round(theta, 8)))
    leader = int(ranking[0])
    contenders = ranking[1:]
    runner_up = int(ranking[1])
    clean_factor = cho_factor(hessian, lower=True, check_finite=False)
    inverse_hessian = cho_solve(clean_factor, np.eye(players), check_finite=False)
    first, second = rows[:, 0].astype(int), rows[:, 1].astype(int)
    residual = expit(theta[first] - theta[second]) - rows[:, 2]
    budgets = [int(fraction * len(rows)) for fraction in fractions]
    best_score = None
    best_selection = None
    screen_records = []
    for position, contender_value in enumerate(contenders):
        contender = int(contender_value)
        selection = clean_selection(rows, first, second, residual, clean_factor, leader, contender)
        contender, direction, influence, order = selection
        rank_drop_sum = 0
        target_reversals = 0
        gap_closure_sum = 0.0
        original_gap = theta[leader] - theta[contender]
        for budget in budgets:
            if budget == 0:
                continue
            selected = order[:budget]
            removed_gradient = np.bincount(first[selected], residual[selected], minlength=players) - np.bincount(second[selected], residual[selected], minlength=players)
            displacement = np.einsum('ij,j->i', inverse_hessian, removed_gradient + budget * regularization * theta, optimize=False) / (total_rows - budget)
            predicted_theta = theta + displacement
            predicted_ranking = np.lexsort((np.arange(players), -np.round(predicted_theta, 8)))
            rank_drop_sum += int(np.flatnonzero(predicted_ranking == leader)[0])
            predicted_gap = predicted_theta[leader] - predicted_theta[contender]
            target_reversals += int(predicted_gap < -1e-8)
            gap_closure_sum += float(np.clip((original_gap - predicted_gap) / max(original_gap, 1e-8), 0.0, 2.0))
        score = (rank_drop_sum, target_reversals, gap_closure_sum, -position)
        screen_records.append({'contender': contender, 'score': score, 'clean_rank': position + 1})
        if best_score is None or score > best_score:
            best_score = score
            best_selection = selection
    incumbent_selection = best_selection
    incumbent_contender = incumbent_selection[0]
    baseline_shortlist = shortlist_contenders(screen_records, incumbent_contender, runner_up, limit=6)
    clean_ranks = {record['contender']: record['clean_rank'] for record in screen_records}
    pair_index = first * players + second
    proxy_pool = list(baseline_shortlist)
    extras = []
    if len(screen_records) > len(baseline_shortlist):
        try:
            proxy_pool = bounded_proxy_pool(screen_records, baseline_shortlist, limit=24)
            curvature_records = []
            for contender in proxy_pool:
                selection = clean_selection(rows, first, second, residual, clean_factor, leader, contender)
                order = selection[3]
                removed_counts = np.zeros_like(pair_counts)
                removed_wins = np.zeros_like(pair_wins)
                previous_budget = 0
                proxy_cache = {0: theta}
                rank_drop_sum = 0
                target_reversals = 0
                gap_closure_sum = 0.0
                original_gap = theta[leader] - theta[contender]
                complete = True
                for budget in budgets:
                    removed = order[previous_budget:budget]
                    removed_counts += np.bincount(pair_index[removed], minlength=players * players)
                    removed_wins += np.bincount(pair_index[removed], weights=rows[removed, 2], minlength=players * players)
                    previous_budget = budget
                    if budget not in proxy_cache:
                        retained_counts = pair_counts - removed_counts
                        retained_wins = pair_wins - removed_wins
                        try:
                            proxy_cache[budget] = retained_curvature_proxy(retained_counts, retained_wins, regularization, theta)
                        except (RuntimeError, np.linalg.LinAlgError, ValueError, FloatingPointError):
                            complete = False
                            break
                    proxy_theta = proxy_cache[budget]
                    if not np.isfinite(proxy_theta).all():
                        complete = False
                        break
                    proxy_ranking = np.lexsort((np.arange(players), -np.round(proxy_theta, 8)))
                    rank_drop_sum += int(np.flatnonzero(proxy_ranking == leader)[0])
                    proxy_gap = proxy_theta[leader] - proxy_theta[contender]
                    target_reversals += int(proxy_gap < -1e-8)
                    gap_closure_sum += float(np.clip((original_gap - proxy_gap) / max(original_gap, 1e-8), 0.0, 2.0))
                if complete:
                    clean_rank = clean_ranks[contender]
                    candidate_score = (rank_drop_sum, target_reversals, gap_closure_sum, -clean_rank)
                    curvature_records.append({'contender': contender, 'score': candidate_score, 'complete': True})
            extras = select_curvature_extras(curvature_records, baseline_shortlist, limit=6)
        except Exception:
            proxy_pool = list(baseline_shortlist)
            extras = []
    shortlist = baseline_shortlist + extras
    assert set(baseline_shortlist).issubset(shortlist)
    assert len(proxy_pool) <= 24 and len(shortlist) <= 12
    assert set(extras).isdisjoint(baseline_shortlist)
    refit_cache = {(): theta}
    exact_candidates = []
    for contender in shortlist:
        selection = clean_selection(rows, first, second, residual, clean_factor, leader, contender)
        contender, direction, influence, order = selection
        removed_counts = np.zeros_like(pair_counts)
        removed_wins = np.zeros_like(pair_wins)
        previous_budget = 0
        warm_theta = theta
        rank_drop_sum = 0
        target_reversals = 0
        gap_closure_sum = 0.0
        original_gap = theta[leader] - theta[contender]
        complete = True
        for budget in budgets:
            removed = order[previous_budget:budget]
            removed_counts += np.bincount(pair_index[removed], minlength=players * players)
            removed_wins += np.bincount(pair_index[removed], weights=rows[removed, 2], minlength=players * players)
            previous_budget = budget
            cache_key = tuple(sorted(order[:budget].tolist()))
            if cache_key not in refit_cache:
                try:
                    refit_cache[cache_key] = refit_prefix(pair_counts, pair_wins, removed_counts,
                                                         removed_wins, regularization, warm_theta)
                except (RuntimeError, np.linalg.LinAlgError, ValueError, FloatingPointError):
                    refit_cache[cache_key] = None
            trial_theta = refit_cache[cache_key]
            if trial_theta is None:
                complete = False
                break
            warm_theta = trial_theta
            trial_ranking = np.lexsort((np.arange(players), -np.round(trial_theta, 8)))
            rank_drop_sum += int(np.flatnonzero(trial_ranking == leader)[0])
            trial_gap = trial_theta[leader] - trial_theta[contender]
            target_reversals += int(trial_gap < -1e-8)
            gap_closure_sum += float(np.clip((original_gap - trial_gap) / max(original_gap, 1e-8), 0.0, 2.0))
        if complete:
            clean_rank = clean_ranks[contender]
            candidate_score = (rank_drop_sum, target_reversals, gap_closure_sum, -clean_rank)
            exact_candidates.append({'score': candidate_score, 'contender': contender})
    if not exact_candidates:
        return incumbent_selection
    selected = max(exact_candidates, key=lambda candidate: candidate["score"])
    return clean_selection(rows, first, second, residual, clean_factor, leader, selected['contender'])


def handle(request):
    operation = request['op']
    if operation == 'reset':
        if type(request['seed']) is not int or request['seed'] < 0:
            raise ValueError('invalid seed')
        STATE.clear()
        STATE['rng'] = np.random.default_rng(request['seed'])
        return {'ok': True}
    if operation == 'export_chunk':
        if request['token'] != STATE.get('token'):
            return {'error': 'unknown_token'}
        index = request['index']
        if type(index) is not int or not 0 <= index < math.ceil(len(STATE['output']) / CHUNK):
            raise ValueError('invalid chunk index')
        return {'data': base64.b64encode(STATE['output'][index*CHUNK:(index+1)*CHUNK]).decode('ascii')}
    if operation == 'import_start':
        count, players = request['n_rows'], request['n_players']
        if not (type(count) is int and 1 <= count <= 100000 and type(players) is int and 2 <= players <= 256):
            raise ValueError('invalid shape')
        if (request['dtype'], request['shape'], request['encoding'], request['byte_order'],request['nbytes']) != ('<f8',[count,4],'base64','little',count*32):
            raise ValueError('invalid input metadata')
        if type(request['chunks']) is not int or not math.ceil(count*32/CHUNK)<=request['chunks']<=8:
            raise ValueError('invalid chunk count')
        if not 0 < request['regularization'] <= 1:
            raise ValueError('invalid regularization')
        STATE.update(metadata=request, staging=bytearray(), next_chunk=0)
        return {'ok': True}
    if operation == 'import_chunk':
        if request['index'] != STATE['next_chunk'] or STATE['next_chunk']>=STATE['metadata']['chunks']:
            raise ValueError('unordered chunk')
        chunk = base64.b64decode(request['data'], validate=True)
        if len(chunk)>CHUNK or len(STATE['staging'])+len(chunk)>STATE['metadata']['nbytes']:
            raise ValueError('oversize chunk')
        STATE['staging'].extend(chunk)
        STATE['next_chunk'] += 1
        return {'ok': True}
    if operation == 'import_commit':
        metadata = STATE['metadata']
        if len(STATE['staging']) != metadata['nbytes'] or STATE['next_chunk'] != metadata['chunks']:
            raise ValueError('incomplete input')
        rows = np.frombuffer(STATE['staging'], dtype='<f8').reshape(metadata['shape']).copy()
        if not np.isfinite(rows).all():
            raise ValueError('nonfinite input')
        STATE['rows'] = rows
        return {'ok': True}
    if operation == 'solve':
        if request['fractions'] != [0.001,0.005,0.01] or request['max_iterations'] != 100:
            raise ValueError('invalid solve settings')
        rows = STATE['rows']; metadata = STATE['metadata']
        theta, hessian, pair_counts, pair_wins = fit(rows, metadata['n_players'], metadata['regularization'], request['max_iterations'])
        fractions = request['fractions']
        contender, direction, influence, order = select_contender(rows, theta, hessian, metadata['regularization'], fractions, pair_counts, pair_wins)
        budgets = [int(fraction * len(rows)) for fraction in fractions]
        deletions = [[int(key) for key in rows[order[:budget], 3]] for budget in budgets]
        result = {"theta": theta.tolist(), "contender": int(contender), "direction": direction.tolist(), "influence": influence.tolist(), "deletions": deletions}
        output = json.dumps(result,allow_nan=False,separators=(',',':')).encode()
        if len(output)>64*1024*1024:
            raise ValueError('oversize output')
        STATE['output'] = output
        STATE['token'] = hashlib.sha256(output).hexdigest()
        return {'ok':True}
    if operation == 'export_start':
        return {'token':STATE['token'],'nbytes':len(STATE['output']),'chunks':math.ceil(len(STATE['output'])/CHUNK),
                'encoding':'base64','dtype':'json','shape':[],'byte_order':'none'}
    if operation == 'release':
        for key in ('rows','staging','metadata','next_chunk'):
            STATE.pop(key,None)
        return {'ok':True}
    raise ValueError('unknown operation')


if __name__ == '__main__':
    for line in sys.stdin:
        print(json.dumps(handle(json.loads(line)),allow_nan=False,separators=(',',':')),flush=True)
