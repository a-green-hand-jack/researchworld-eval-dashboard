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

Contender selection is deterministic and uses only the clean fit. For every
nonleader, construct its required influence order and three exact prefixes.
Using the clean Hessian, predict the full score displacement for each prefix,
including the mean-loss regularization correction. Maximize, lexicographically,
the sum of predicted leader rank drops, the number of predicted target reversals,
and the sum of target-gap closure fractions clipped to [0,2]. Break ties by
clean rank. Predictions are only a selection heuristic, not verified refits or
uncertainty estimates. Never refine the selected order after this selection.
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
    observed = np.flatnonzero(pair_counts)
    first, second = observed // players, observed % players
    counts, wins = pair_counts[observed], pair_wins[observed]
    total_rows = len(rows)
    theta = np.zeros(players)

    def quantities(scores):
        margin = scores[first] - scores[second]
        probability = expit(margin)
        residual = (counts * probability - wins) / total_rows
        gradient = np.bincount(first, residual, minlength=players) - np.bincount(second, residual, minlength=players) + regularization * scores
        weight = counts * probability * (1 - probability) / total_rows
        hessian = np.diag(np.bincount(first, weight, minlength=players) + np.bincount(second, weight, minlength=players) + regularization)
        np.add.at(hessian, (first, second), -weight)
        np.add.at(hessian, (second, first), -weight)
        objective = np.sum(counts * np.logaddexp(0, margin) - wins * margin) / total_rows + regularization * np.dot(scores, scores) / 2
        return objective, gradient, hessian

    for iteration in range(iterations):
        objective, gradient, hessian = quantities(theta)
        if np.max(np.abs(gradient)) < 1e-11:
            break
        step = cho_solve(cho_factor(hessian, lower=True, check_finite=False), gradient, check_finite=False)
        rate = 1.0
        for attempt in range(30):
            trial = theta - rate * step
            trial -= np.mean(trial)
            trial_objective, trial_gradient, unused_hessian = quantities(trial)
            sufficient_decrease = trial_objective <= objective - 1e-4 * rate * np.dot(gradient, step)
            roundoff_descent = trial_objective <= objective + 8 * np.finfo(float).eps * max(1.0, abs(objective)) and np.max(np.abs(trial_gradient)) < np.max(np.abs(gradient))
            if sufficient_decrease or roundoff_descent:
                theta = trial
                break
            rate *= 0.5
        else:
            break
    unused_objective, gradient, hessian = quantities(theta)
    if not np.isfinite(theta).all() or np.max(np.abs(gradient)) > 1e-9:
        raise RuntimeError('Bradley-Terry fit did not converge')
    return theta, hessian


def select_contender(rows, theta, hessian, regularization, fractions):
    players = len(theta)
    total_rows = len(rows)
    ranking = np.lexsort((np.arange(players), -np.round(theta, 8)))
    leader = int(ranking[0])
    contenders = ranking[1:]
    contrasts = np.zeros((players, len(contenders)))
    contrasts[leader, :] = 1.0
    contrasts[contenders, np.arange(len(contenders))] = -1.0
    factor = cho_factor(hessian, lower=True, check_finite=False)
    directions = cho_solve(factor, contrasts, check_finite=False)
    inverse_hessian = cho_solve(factor, np.eye(players), check_finite=False)
    first, second = rows[:, 0].astype(int), rows[:, 1].astype(int)
    residual = expit(theta[first] - theta[second]) - rows[:, 2]
    budgets = [int(fraction * total_rows) for fraction in fractions]
    best_score = None
    best_selection = None
    for position, contender_value in enumerate(contenders):
        contender = int(contender_value)
        direction = directions[:, position]
        influence = residual * (direction[first] - direction[second])
        order = np.lexsort((rows[:, 3], np.round(influence, 10)))
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
        if best_score is None or score > best_score:
            best_score = score
            best_selection = (contender, direction.copy(), influence.copy(), order.copy())
    return best_selection


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
        theta, hessian = fit(rows, metadata['n_players'], metadata['regularization'], request['max_iterations'])
        contender, direction, influence, order = select_contender(rows, theta, hessian, metadata['regularization'], request['fractions'])
        result = {'theta':theta.tolist(),'contender':contender,'direction':direction.tolist(),'influence':influence.tolist(),
                  'deletions':[[int(key) for key in rows[order[:int(fraction*len(rows))],3]] for fraction in request['fractions']]}
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
