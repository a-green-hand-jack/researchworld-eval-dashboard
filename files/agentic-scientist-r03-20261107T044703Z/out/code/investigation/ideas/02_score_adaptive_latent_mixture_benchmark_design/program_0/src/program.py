"""Deterministic CPU masked-factor starter; single-file finite-JSON handle API.

All requests and responses are objects. No additional response keys are allowed.
Every independent episode begins with reset; reset erases uploads, fits, contexts,
and RNG. Seeds are arbitrary nonnegative integers, never workload selectors.

reset: {op:'reset', seed:int} -> {ok:true}.
train_start: {op:'train_start', rows:int<=8192, columns:int<=1024,
 column_names:list[str] of length columns, training_steps:int in [1,100],
 max_queries:int<=8} -> {ok:true}. Allocates candidate-owned RAM only.
train_chunk: {op:'train_chunk', offset:int, shape:[r,columns], dtype:'<f8',
 encoding:'base64', data:str, mask_dtype:'|u1', mask:str} -> {ok:true}.
Chunks are sequential, r<=256, at most 32 chunks. data contains row-major
little-endian float64 normalized scores in [0,1]; mask is row-major uint8 0/1.
Unobserved cells contain zero, not NaN. Decode both; masked cells are unknown.
train_commit: {op:'train_commit'} -> {ok:true}; requires all rows uploaded.
fit: {op:'fit'} -> {ok:true}; learn only from the committed historical matrix.
start: {op:'start', availability:list[list[bool]], max_queries:int} -> {ok:true}.
Creates/replaces a batch of 1..128 independent new-model contexts; each mask has
columns entries. A true entry may be purchased once; no scores are provided.
select: {op:'select'} -> {indices:list[int]}, exactly one unqueried available
column per active row. Rows have enough available columns for max_queries+1.
observe: {op:'observe', indices:list[int], values:list[float]} -> {ok:true}.
Exactly the last selections and their purchased normalized scores are supplied.
Only completed observations can affect subsequent decisions. Never pool contexts.
predict: {op:'predict'} -> {predictions:list[list[float]]}, shape [batch,columns],
all entries finite numeric (not bool); evaluator clips to [0,1] and scores only
available unpurchased entries. No diagnostics, state flags, or artifact paths.

Calls follow reset, train_start, chunks, train_commit, fit, then repeated start /
(select,observe,[predict])* trajectories. Prediction checkpoints and workload are
operation-driven, not seed-driven. Fit allowance is advisory sweeps, not telemetry.
The starter fits a regularized masked latent model, selects rank using held-out
historical cells, and uses covariance-trace information selection with conditional
ridge reconstruction. It is a reproducible starting point, not a claimed win.
No filesystem or network transport is part of this interface. Full messages,
including JSON framing, must be strictly below 64 MiB. Dependencies are preinstalled.
"""
import base64
import numpy as np

_STATE = {}


def factor_fit(values, mask, rank, steps, seed):
    mean = np.sum(values * mask, axis=0) / np.maximum(mask.sum(axis=0), 1)
    centered = values - mean
    filled = np.where(mask, centered, 0.0)
    _, singular, right = np.linalg.svd(filled, full_matrices=False)
    factors = right[:rank].T * np.sqrt(np.maximum(singular[:rank], 1e-8))
    latent = np.zeros((len(values), rank))
    regularizer = np.eye(rank) * 0.1
    for sweep in range(steps):
        for row in range(len(values)):
            selected = factors[mask[row]]
            latent[row] = np.linalg.solve(selected.T @ selected + regularizer,
                                          selected.T @ centered[row, mask[row]])
        for column in range(values.shape[1]):
            selected = latent[mask[:, column]]
            factors[column] = np.linalg.solve(selected.T @ selected + regularizer,
                                              selected.T @ centered[mask[:, column], column])
    return mean, factors


def learn(values, mask, steps, seed):
    random = np.random.default_rng(seed)
    validation = (random.random(mask.shape) < 0.1) & mask
    fitting = mask & ~validation
    best = None
    for rank in (1, 2, 4, 8):
        if rank > min(values.shape) - 1:
            continue
        mean, factors = factor_fit(values, fitting, rank, min(steps, 4), seed)
        losses = []
        for row in range(len(values)):
            selected = factors[fitting[row]]
            latent = np.linalg.solve(selected.T @ selected + np.eye(rank) * 0.1,
                                     selected.T @ (values[row, fitting[row]] - mean[fitting[row]]))
            losses.extend(np.abs((mean + factors @ latent - values[row])[validation[row]]))
        loss = float(np.mean(losses)) if losses else 1.0
        if best is None or loss < best[0]:
            best = (loss, rank)
    return factor_fit(values, mask, best[1], min(steps, 8), seed)


def handle(request):
    operation = request['op']
    if operation == 'reset':
        _STATE.clear()
        _STATE['seed'] = request['seed']
        return {'ok': True}
    if operation == 'train_start':
        _STATE.update(values=np.zeros((request['rows'], request['columns'])),
                      mask=np.zeros((request['rows'], request['columns']), dtype=bool),
                      offset=0, steps=request['training_steps'])
    elif operation == 'train_chunk':
        shape = tuple(request['shape'])
        values = np.frombuffer(base64.b64decode(request['data']), dtype='<f8').reshape(shape)
        mask = np.frombuffer(base64.b64decode(request['mask']), dtype='u1').reshape(shape).astype(bool)
        offset = request['offset']
        _STATE['values'][offset:offset + shape[0]] = values
        _STATE['mask'][offset:offset + shape[0]] = mask
        _STATE['offset'] += shape[0]
    elif operation == 'train_commit':
        if _STATE['offset'] != len(_STATE['values']):
            raise ValueError('incomplete training upload')
    elif operation == 'fit':
        mean, factors = learn(_STATE['values'], _STATE['mask'], _STATE['steps'], _STATE['seed'])
        _STATE.update(mean=mean, factors=factors)
    elif operation == 'start':
        _STATE['available'] = np.array(request['availability'], dtype=bool)
        _STATE['queried'] = np.zeros_like(_STATE['available'])
        _STATE['observed'] = np.zeros(_STATE['available'].shape)
    elif operation == 'select':
        factors = _STATE['factors']
        indices = []
        for row in range(len(_STATE['available'])):
            selected = factors[_STATE['queried'][row]]
            covariance = np.linalg.inv(selected.T @ selected + np.eye(factors.shape[1]) * 0.1)
            targets = factors[_STATE['available'][row] & ~_STATE['queried'][row]]
            reduction = np.sum((targets @ covariance @ factors.T) ** 2, axis=0)
            reduction /= 1.0 + np.sum((factors @ covariance) * factors, axis=1)
            legal = _STATE['available'][row] & ~_STATE['queried'][row]
            reduction[~legal] = -np.inf
            indices.append(int(np.argmax(reduction)))
        _STATE['pending'] = indices
        return {'indices': indices}
    elif operation == 'observe':
        if request['indices'] != _STATE['pending']:
            raise ValueError('unexpected observation')
        for row, (column, value) in enumerate(zip(request['indices'], request['values'])):
            _STATE['queried'][row, column] = True
            _STATE['observed'][row, column] = value
    elif operation == 'predict':
        mean, factors = _STATE['mean'], _STATE['factors']
        predictions = []
        for row in range(len(_STATE['available'])):
            selected = factors[_STATE['queried'][row]]
            latent = np.linalg.solve(selected.T @ selected + np.eye(factors.shape[1]) * 0.1,
                                     selected.T @ (_STATE['observed'][row, _STATE['queried'][row]]
                                                   - mean[_STATE['queried'][row]]))
            predictions.append(np.clip(mean + factors @ latent, 0, 1).tolist())
        return {'predictions': predictions}
    else:
        raise ValueError('unknown operation')
    return {'ok': True}
