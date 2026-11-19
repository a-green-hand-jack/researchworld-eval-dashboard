"""Genuine interventional Kernel SHAP starter; finite JSON handle(request)->response.

All responses have EXACTLY the documented keys; extra fields are forbidden. All
numeric inputs/outputs are finite. No file names, host paths, private targets,
reference answers, baseline outputs, or scoring feedback are exchanged.

reset: {op:'reset',seed:nonnegative int} -> {ok:true}. Accept arbitrary seeds;
clear models, RNG and incomplete transfers. Seeds NEVER choose workload identity.

model_start: {op,token:ASCII string,nbytes:int,sha256:64 hex chars,
 encoding:'base64',dtype:'uint8',shape:[nbytes],content_type:'application/json'}
 -> {ok:true}. Begin one in-memory JSON document, 1..16777216 bytes.
model_chunk: {op,token,index:int,data:base64 str} -> {ok:true}. Sequential
0-based chunks, each at most 1048576 decoded bytes, at most 16 chunks.
model_commit: {op,token} -> {ok:true}. Verify length/digest, decode UTF-8 JSON,
replace the active model, and discard transfer buffers. Errors clear transfers.
Only one outstanding upload is used; no file-based exchange is permitted.

The uploaded model has EXACTLY kind, dimension, background, parameters.
background: [B,d] float64-compatible rows, 1<=B<=16, d<=20. All columns
are original feature groups after evaluator-owned scalar ordinal encoding,
training-median imputation and standard scaling; no dummy columns are split.
kind='logistic': parameters={coef:[d],intercept:float}.
kind='forest': parameters={trees:[{left:[nodes],right:[nodes],feature:[nodes],
 threshold:[nodes],probability:[nodes]}]}; <=64 trees, depth<=6.
kind='affine': parameters={coef:[d],intercept:float}; these fixtures remain
in [0,1] on the permitted background-replacement domain. Probability-scale,
identity-link prediction is used for every kind, without output clipping.

explain: {op:'explain',queries:[[float]*d]*N,budget:int,
 workload:{usable_seconds:positive float,remaining_explanations:positive int}} ->
{attributions:[[float]*d]*N}, N<=16, 1<=budget<=8192. The budget is a
requested number of nontrivial sampled coalitions PER query, not a new seed
or workload selector. workload supplies the shared method's remaining usable
wall seconds (including transport and any remaining model uploads) and count of
explanation calls still scheduled, INCLUDING this call. It is advisory runtime
information, not scoring feedback: candidates can allocate time across those
calls, e.g. usable_seconds/remaining_explanations, allowing transport headroom.
The same fields occur in smoke and all episodes, including analytic controls;
no plane, seed mapping, private answers or outcome measurements are included.
These hints do not change coalition budgets or extend the enforced deadline.
State advances only its RNG and active model. Model
and background are held fixed across repetitions. Return original-coordinate
attributions, |value|<=1000000. Repeated calls use independent RNG draws;
reset and replay of identical requests must reproduce identical numbers.
Enumeration is allowed when the budget covers all nontrivial coalitions.

The evaluator varies the number of rows, calls, budgets, and model complexity
through these same plane-independent fields in smoke and production. No
internal counter, method-name flag, or state-change assertion is evidence.
Complete compact UTF-8 JSON lines, including envelopes/framing, are <2 MiB
and strictly <64 MiB. Candidate-owned assembly/cache memory stays <=64 MiB;
this starter uses at most one 16 MiB upload and one bounded model.
"""
import base64
import hashlib
import json
import math
import re

import numpy as np

from reliability import explain_fixed_game

_rng = None
_model = None
_transfer = None


def predict(model, rows):
    values = np.asarray(rows, dtype=np.float64)
    parameters = model['parameters']
    if model['kind'] in ('logistic', 'affine'):
        linear = values @ np.asarray(parameters['coef']) + parameters['intercept']
        if model['kind'] == 'affine':
            return linear
        return 1.0 / (1.0 + np.exp(-np.clip(linear, -700, 700)))
    output = np.zeros(len(values))
    forest_values = values.astype(np.float32)
    for tree in parameters['trees']:
        nodes = np.zeros(len(values), dtype=np.int64)
        left = np.asarray(tree['left'])
        right = np.asarray(tree['right'])
        features = np.asarray(tree['feature'])
        thresholds = np.asarray(tree['threshold'])
        for depth in range(7):
            active = left[nodes] >= 0
            if not active.any():
                break
            selected = nodes[active]
            branches = forest_values[active][np.arange(len(selected)), features[selected]]
            nodes[active] = np.where(branches <= thresholds[selected], left[selected], right[selected])
        output += np.asarray(tree['probability'])[nodes]
    return output / len(parameters['trees'])


def kernel_shap(model, query, budget, rng):
    dimension = model['dimension']
    background = np.asarray(model['background'], dtype=np.float64)
    empty = float(predict(model, background).mean())
    full = float(predict(model, [query])[0])
    delta = full - empty
    count = (1 << dimension) - 2
    if budget >= count:
        indices = np.arange(1, count + 1, dtype=np.uint32)
        masks = ((indices[:, None] >> np.arange(dimension)) & 1).astype(float)
        sizes = masks.sum(axis=1).astype(int)
        weights = np.array([(dimension-1)/(math.comb(dimension,int(size))*size*(dimension-size)) for size in sizes])
    else:
        sizes = np.arange(1, dimension)
        probabilities = (dimension-1)/(sizes*(dimension-sizes))
        probabilities = probabilities / probabilities.sum()
        masks = np.zeros((budget, dimension))
        for row, size in enumerate(rng.choice(sizes, size=budget, p=probabilities)):
            masks[row, rng.choice(dimension, size=int(size), replace=False)] = 1
        weights = np.ones(budget)
    coalition_values = []
    for offset in range(0, len(masks), 128):
        chunk = masks[offset:offset+128]
        hybrid = np.where(chunk[:,None,:].astype(bool), np.asarray(query), background[None,:,:])
        coalition_values.extend(predict(model, hybrid.reshape(-1, dimension)).reshape(len(chunk),len(background)).mean(axis=1))
    design = masks[:,:-1] - masks[:,-1:]
    target = np.asarray(coalition_values) - empty - masks[:,-1]*delta
    root = np.sqrt(weights)
    coefficients = np.linalg.lstsq(design*root[:,None], target*root, rcond=1e-12)[0]
    return np.append(coefficients, delta-coefficients.sum()).tolist()


def handle(request):
    global _rng, _model, _transfer
    operation = request['op']
    if operation == 'reset':
        if set(request) != {'op','seed'} or type(request['seed']) is not int or request['seed'] < 0:
            raise ValueError('invalid seed')
        _rng = np.random.default_rng(request['seed'])
        _model = None
        _transfer = None
        return {'ok': True}
    if _rng is None:
        raise ValueError('reset required')
    try:
        if operation == 'model_start':
            if set(request) != {'op','token','nbytes','sha256','encoding','dtype','shape','content_type'}:
                raise ValueError('invalid start fields')
            if not isinstance(request['token'],str) or re.fullmatch('[A-Za-z0-9_-]{1,64}',request['token']) is None:
                raise ValueError('invalid token')
            if type(request['nbytes']) is not int or not 1 <= request['nbytes'] <= 16*1024*1024:
                raise ValueError('invalid size')
            if request['encoding'] != 'base64' or request['dtype'] != 'uint8' or request['shape'] != [request['nbytes']] or request['content_type'] != 'application/json':
                raise ValueError('invalid encoding')
            if not isinstance(request['sha256'],str) or re.fullmatch('[0-9a-f]{64}',request['sha256']) is None:
                raise ValueError('invalid digest')
            _transfer = {'token':request['token'],'nbytes':request['nbytes'],'sha256':request['sha256'],'buffer':bytearray(),'index':0}
            return {'ok':True}
        if operation == 'model_chunk':
            if set(request) != {'op','token','index','data'} or _transfer is None or request['token'] != _transfer['token'] or type(request['index']) is not int or request['index'] != _transfer['index']:
                raise ValueError('invalid chunk')
            chunk = base64.b64decode(request['data'],validate=True)
            if not 1 <= len(chunk) <= 1048576 or _transfer['index'] >= 16 or len(_transfer['buffer'])+len(chunk) > _transfer['nbytes']:
                raise ValueError('chunk overflow')
            _transfer['buffer'].extend(chunk)
            _transfer['index'] += 1
            return {'ok':True}
        if operation == 'model_commit':
            if set(request) != {'op','token'} or _transfer is None or request['token'] != _transfer['token']:
                raise ValueError('invalid commit')
            raw = _transfer['buffer']
            if len(raw) != _transfer['nbytes'] or hashlib.sha256(raw).hexdigest() != _transfer['sha256']:
                raise ValueError('integrity failure')
            model = json.loads(raw)
            if set(model) != {'kind','dimension','background','parameters'} or model['kind'] not in ('logistic','forest','affine') or type(model['dimension']) is not int or not 2 <= model['dimension'] <= 20:
                raise ValueError('invalid model')
            background = np.asarray(model['background'],dtype=float)
            if background.ndim != 2 or background.shape[1] != model['dimension'] or not 1 <= len(background) <= 16 or not np.isfinite(background).all():
                raise ValueError('invalid background')
            _model = model
            _transfer = None
            return {'ok':True}
        if operation == 'explain':
            if set(request) != {'op','queries','budget','workload'} or _model is None or type(request['budget']) is not int or not 1 <= request['budget'] <= 8192:
                raise ValueError('invalid explanation request')
            workload = request['workload']
            if type(workload) is not dict or set(workload) != {'usable_seconds','remaining_explanations'}:
                raise ValueError('invalid workload')
            if type(workload['usable_seconds']) not in (float,int) or not math.isfinite(workload['usable_seconds']) or workload['usable_seconds'] <= 0:
                raise ValueError('invalid usable time')
            if type(workload['remaining_explanations']) is not int or workload['remaining_explanations'] < 1:
                raise ValueError('invalid remaining explanations')
            queries = np.asarray(request['queries'],dtype=float)
            if queries.ndim != 2 or queries.shape[1] != _model['dimension'] or not 1 <= len(queries) <= 16 or not np.isfinite(queries).all():
                raise ValueError('invalid queries')
            return {'attributions':[explain_fixed_game(_model, query, request['budget'], _rng, predict).tolist() for query in queries]}
        raise ValueError('unknown operation')
    except Exception:
        _transfer = None
        raise
