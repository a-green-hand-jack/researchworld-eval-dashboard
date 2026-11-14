"""Train-only positive compositional residual-scale learner, python_rpc_v1:handle.

All requests/responses are finite JSON objects; extra response keys are forbidden.
reset: {op:'reset', seed: nonnegative int} -> {ok:true}. Clears all model/transfer
state. Any seed is accepted; seeds initialize randomness, never select a workload.
fit: {op:'fit', x:Array[n,6], residuals:Array[n], dimension:int>=2,
      scale_min:0.0001, scale_max:10000.0} -> {ok:true}.
Only training covariates and training residual norms are provided. Fits replace the
model. Prediction is read-only and requires a completed fit after reset.
predict: {op:'predict', x:Array[n,6]} -> {scales:Array[n]}.
Return strictly positive finite scales; the evaluator consistently clips them to
[0.0001,10000]. No calibration/test outcomes or later scoring feedback is given.
Array is exactly {encoding:'base64',dtype:'<f8',shape:[...],nbytes:int,data:str}.
Data is C-order little-endian float64, n<=2048 normally; no file paths are used.
Workload dimensions/settings come from fit, not reset seeds. Candidate changes may
change the scale estimator but not evaluator-owned center, geometry or calibration.

Optional bounded fallback, exercised by maximum-protocol tests, not needed for
ordinary shapes: begin {op:'begin',method:'fit'|'predict',fields:object,
arrays:{name:{shape:list,nbytes:int}},nbytes:int} -> {token:str}.
fields holds the non-array logical request fields except op. Arrays, in insertion
order, concatenate raw <f8 bytes; total <=8 MiB. upload {op:'upload',token:str,
offset:int,data:base64str} -> {ok:true}, sequential <=2 chunks of <=4 MiB.
commit {op:'commit',token:str} -> {ok:true} validates lengths and computes once.
export_start {op:'export_start',token:str} -> {nbytes:int,chunks:int}.
fetch {op:'fetch',token:str,index:int} -> {data:base64str}, sequential <=2 chunks.
Output is UTF-8 JSON for fit, raw <f8 scales for predict. release
{op:'release',token:str} -> {ok:true} destroys buffers. One live token, <=32 MiB
transfer storage; reset invalidates it. No token is a path. At most 8 calls per
logical operation (begin,2 uploads,commit,export_start,2 fetches,release).
No self-reported learning, timing or diagnostics are accepted as scientific evidence.
"""
import base64
import json
import math
import numpy as np

MODEL = None
TRANSFER = None
CHUNK = 4 * 1024 * 1024


def decode(value):
    if set(value) != {'encoding', 'dtype', 'shape', 'nbytes', 'data'}:
        raise ValueError('array schema')
    if value['encoding'] != 'base64' or value['dtype'] != '<f8':
        raise ValueError('array encoding')
    raw = base64.b64decode(value['data'], validate=True)
    if len(raw) != value['nbytes'] or len(raw) != math.prod(value['shape']) * 8:
        raise ValueError('array size')
    result = np.frombuffer(raw, dtype='<f8').reshape(value['shape'])
    if not np.isfinite(result).all():
        raise ValueError('nonfinite input')
    return result


def encode(array):
    array = np.asarray(array, dtype='<f8', order='C')
    return dict(encoding='base64', dtype='<f8', shape=list(array.shape),
                nbytes=array.nbytes, data=base64.b64encode(array.tobytes()).decode('ascii'))


def features(array):
    return np.column_stack((np.ones(len(array)), array, array * array))


def pinball_loss(residuals, quantile):
    return np.maximum(quantile * residuals, (quantile - 1.0) * residuals)


def blend_log_scales(incumbent_log_scale, tail_log_scale, tail_weight):
    return (1.0 - tail_weight) * incumbent_log_scale + tail_weight * tail_log_scale


def quantiles_from_counts(sorted_values, cumulative_counts, leaf_sizes, quantile):
    positions = quantile * (leaf_sizes - 1)
    lower_ranks = np.floor(positions)
    upper_ranks = np.ceil(positions)
    lower_indices = np.argmax(cumulative_counts > lower_ranks[:, None], axis=1)
    upper_indices = np.argmax(cumulative_counts > upper_ranks[:, None], axis=1)
    return (sorted_values[lower_indices]
            + (positions - lower_ranks)
            * (sorted_values[upper_indices] - sorted_values[lower_indices]))


def fit_quantile_stumps(features, log_norms, quantile, max_rounds, min_leaf):
    learning_rate = 0.1
    intercept = float(np.quantile(log_norms, quantile))
    model = dict(intercept=intercept, learning_rate=learning_rate, stumps=[])
    fitted_log_scale = np.full(len(log_norms), intercept)
    if len(log_norms) < 2 * min_leaf:
        return model
    splits, masks = [], []
    for feature_index in range(features.shape[1]):
        thresholds = np.unique(np.quantile(features[:, feature_index],
                                           np.linspace(0.05, 0.95, 15)))
        for threshold in thresholds:
            left_mask = features[:, feature_index] <= threshold
            left_size = int(left_mask.sum())
            if min_leaf <= left_size <= len(log_norms) - min_leaf:
                splits.append((feature_index, float(threshold)))
                masks.append(left_mask)
    if not splits:
        return model
    split_masks = np.asarray(masks, dtype=bool)
    left_sizes = split_masks.sum(axis=1)
    right_sizes = len(log_norms) - left_sizes
    observation_counts = np.arange(1, len(log_norms) + 1)
    for round_index in range(min(max_rounds, 80)):
        working_residuals = log_norms - fitted_log_scale
        sorted_indices = np.argsort(working_residuals, kind='stable')
        sorted_values = working_residuals[sorted_indices]
        left_counts = np.cumsum(split_masks[:, sorted_indices], axis=1)
        left_updates = quantiles_from_counts(sorted_values, left_counts,
                                            left_sizes, quantile)
        right_updates = quantiles_from_counts(sorted_values,
                                             observation_counts - left_counts,
                                             right_sizes, quantile)
        updates = learning_rate * np.where(split_masks, left_updates[:, None],
                                          right_updates[:, None])
        losses = pinball_loss(working_residuals[None, :] - updates, quantile).mean(axis=1)
        best_index = int(np.argmin(losses))
        current_loss = float(pinball_loss(working_residuals, quantile).mean())
        if losses[best_index] >= current_loss - 1e-12 * max(1.0, current_loss):
            break
        left_mask = split_masks[best_index]
        left_update = float(np.quantile(working_residuals[left_mask], quantile))
        right_update = float(np.quantile(working_residuals[~left_mask], quantile))
        fitted_log_scale += learning_rate * np.where(left_mask, left_update, right_update)
        feature_index, threshold = splits[best_index]
        model['stumps'].append((feature_index, threshold, left_update, right_update))
    return model


def predict_quantile_stumps(model, covariates):
    prediction = np.full(len(covariates), model['intercept'])
    for feature_index, threshold, left_update, right_update in model['stumps']:
        left_mask = covariates[:, feature_index] <= threshold
        prediction += model['learning_rate'] * np.where(left_mask, left_update, right_update)
    return prediction


def fit_incumbent(covariates, residual_norms):
    mean = covariates.mean(axis=0)
    deviation = np.maximum(covariates.std(axis=0), 1e-8)
    design = features((covariates - mean) / deviation)
    target = np.log(np.maximum(residual_norms, 1e-8))
    penalty = np.eye(design.shape[1]) * 2.0
    penalty[0, 0] = 1e-8
    coefficients = np.linalg.solve(design.T @ design + penalty, design.T @ target)
    return mean, deviation, coefficients


def predict_incumbent_log(model, covariates):
    mean, deviation, coefficients = model
    return np.clip(features((covariates - mean) / deviation) @ coefficients,
                   np.log(1e-4), np.log(1e4))


def raw_candidate_logs(incumbent, tail_model, covariates):
    incumbent_log_scale = predict_incumbent_log(incumbent, covariates)
    tail_log_scale = predict_quantile_stumps(tail_model, covariates)
    return np.column_stack((incumbent_log_scale, np.zeros(len(covariates)),
                            *(blend_log_scales(incumbent_log_scale, tail_log_scale, weight)
                              for weight in (0.25, 0.5, 0.75, 1.0))))


def align_log_scale(log_norms, fitted_log_scale, quantile):
    alignment_offset = float(np.quantile(log_norms - fitted_log_scale, quantile))
    return alignment_offset


def fit_scale_family(covariates, residual_norms, log_norms, tail_model, quantile):
    incumbent = fit_incumbent(covariates, residual_norms)
    fitted_candidates = raw_candidate_logs(incumbent, tail_model, covariates)
    offsets = np.asarray([align_log_scale(log_norms, fitted_candidates[:, index], quantile)
                          for index in range(fitted_candidates.shape[1])])
    return dict(incumbent=incumbent, tail=tail_model, alignment_offsets=offsets)


def fit_complete_incumbent(features, residual_norms):
    quantile, max_rounds = 0.9, 80
    log_norms = np.log(np.maximum(residual_norms, 1e-12))
    selected_index = 0
    if len(log_norms) >= 3:
        indices = np.random.default_rng(0).permutation(len(log_norms))
        folds = np.array_split(indices, 3)
        fold_losses = []
        for fold_index, validation_indices in enumerate(folds):
            fit_indices = np.concatenate([fold for index, fold in enumerate(folds)
                                          if index != fold_index])
            assert np.intersect1d(fit_indices, validation_indices).size == 0
            min_leaf = max(20, math.ceil(0.03 * len(fit_indices)))
            fold_tail_model = fit_quantile_stumps(features[fit_indices], log_norms[fit_indices], quantile, max_rounds, min_leaf)
            family = fit_scale_family(features[fit_indices], residual_norms[fit_indices],
                                      log_norms[fit_indices], fold_tail_model, quantile)
            held_out = raw_candidate_logs(family['incumbent'], family['tail'],
                                          features[validation_indices])
            held_out += family['alignment_offsets']
            fold_losses.append(pinball_loss(log_norms[validation_indices, None] - held_out,
                                            quantile).mean(axis=0))
        fold_losses = np.asarray(fold_losses)
        mean_losses = fold_losses.mean(axis=0)
        standard_errors = fold_losses.std(axis=0, ddof=1) / np.sqrt(len(folds))
        best_index = int(np.argmin(mean_losses))
        selection_limit = mean_losses[best_index] + standard_errors[best_index]
        simplicity_order = (0, 1, 2, 3, 4, 5)
        selected_index = next(index for index in simplicity_order if mean_losses[index] <= selection_limit)
    min_leaf = max(20, math.ceil(0.03 * len(log_norms)))
    tail_model = fit_quantile_stumps(features, log_norms, quantile, max_rounds, min_leaf)
    model = fit_scale_family(features, residual_norms, log_norms, tail_model, quantile)
    model['selected_index'] = selected_index
    return model


def predict_complete_incumbent(model, covariates):
    selected_index = model['selected_index']
    if selected_index == 1:
        raw_log_scale = np.zeros(len(covariates))
    elif selected_index == 0:
        raw_log_scale = predict_incumbent_log(model['incumbent'], covariates)
    else:
        incumbent_log_scale = predict_incumbent_log(model['incumbent'], covariates)
        tail_log_scale = predict_quantile_stumps(model['tail'], covariates)
        tail_weight = (0.25, 0.5, 0.75, 1.0)[selected_index - 2]
        raw_log_scale = blend_log_scales(incumbent_log_scale, tail_log_scale, tail_weight)
    alignment_offset = model['alignment_offsets'][selected_index]
    blended_log_scale = raw_log_scale + alignment_offset
    return np.maximum(np.exp(np.clip(blended_log_scale, -30.0, 30.0)), 1e-12)


class QuantileTreeNode:
    def __init__(self):
        self.feature_index = None
        self.threshold = None
        self.left_child = None
        self.right_child = None
        self.quantile_value = None


class HonestQuantileTree:
    def __init__(self, max_depth, quantile, min_estimation_leaf=16):
        self.max_depth = max_depth
        self.quantile = quantile
        self.min_estimation_leaf = min_estimation_leaf
        self.root = None

    def fit_structure(self, features, log_norms):
        self.min_structure_leaf = max(16, math.ceil(0.05 * len(log_norms)))
        self.root = self._grow(features, log_norms, 0)

    def _grow(self, features, log_norms, depth):
        node = QuantileTreeNode()
        if depth >= self.max_depth or len(log_norms) < 2 * self.min_structure_leaf:
            return node
        parent_quantile = float(np.quantile(log_norms, self.quantile))
        parent_loss = float(pinball_loss(log_norms - parent_quantile, self.quantile).sum())
        best_gain = 1e-12 * max(1.0, parent_loss)
        best_split = None
        sorted_indices = np.argsort(log_norms, kind='stable')
        sorted_values = log_norms[sorted_indices]
        observation_counts = np.arange(1, len(log_norms) + 1)
        for feature_index in range(features.shape[1]):
            thresholds = np.unique(np.quantile(features[:, feature_index],
                                               np.linspace(0.05, 0.95, 16)))
            split_masks = features[None, :, feature_index] <= thresholds[:, None]
            left_sizes = split_masks.sum(axis=1)
            supported = ((left_sizes >= self.min_structure_leaf)
                         & (len(log_norms) - left_sizes >= self.min_structure_leaf))
            if not supported.any():
                continue
            thresholds = thresholds[supported]
            split_masks = split_masks[supported]
            left_sizes = left_sizes[supported]
            left_counts = np.cumsum(split_masks[:, sorted_indices], axis=1)
            left_quantiles = quantiles_from_counts(sorted_values, left_counts,
                                                  left_sizes, self.quantile)
            right_quantiles = quantiles_from_counts(sorted_values,
                                                   observation_counts - left_counts,
                                                   len(log_norms) - left_sizes, self.quantile)
            left_losses = (pinball_loss(log_norms[None, :] - left_quantiles[:, None],
                                        self.quantile) * split_masks).sum(axis=1)
            right_losses = (pinball_loss(log_norms[None, :] - right_quantiles[:, None],
                                         self.quantile) * ~split_masks).sum(axis=1)
            for split_index, threshold in enumerate(thresholds):
                left_loss = float(left_losses[split_index])
                right_loss = float(right_losses[split_index])
                split_gain = parent_loss - left_loss - right_loss
                if split_gain > best_gain:
                    best_gain = split_gain
                    best_split = feature_index, float(threshold)
        if best_split is not None:
            feature_index, threshold = best_split
            left_mask = features[:, feature_index] <= threshold
            left_child = self._grow(features[left_mask], log_norms[left_mask], depth + 1)
            right_child = self._grow(features[~left_mask], log_norms[~left_mask], depth + 1)
            node.feature_index = feature_index
            node.threshold = threshold
            node.left_child = left_child
            node.right_child = right_child
        return node

    def fit_leaf_quantiles(self, features, log_norms):
        if len(log_norms) < self.min_estimation_leaf or self.root is None:
            raise ValueError('unsupported estimation root')
        root_quantile = float(np.quantile(log_norms, self.quantile))
        self._estimate(self.root, features, log_norms, root_quantile)

    def _estimate(self, node, features, node_log_norms, inherited_quantile):
        node.quantile_value = float(np.quantile(node_log_norms, self.quantile)) if node_log_norms.size >= self.min_estimation_leaf else inherited_quantile
        if node.feature_index is not None:
            left_mask = features[:, node.feature_index] <= node.threshold
            self._estimate(node.left_child, features[left_mask], node_log_norms[left_mask],
                           node.quantile_value)
            self._estimate(node.right_child, features[~left_mask], node_log_norms[~left_mask],
                           node.quantile_value)

    def predict_log(self, features):
        prediction = np.empty(len(features), dtype=np.float64)
        self._predict(self.root, features, np.arange(len(features)), prediction)
        return prediction

    def _predict(self, node, features, indices, prediction):
        if node.feature_index is None:
            prediction[indices] = node.quantile_value
            return
        left_mask = features[indices, node.feature_index] <= node.threshold
        self._predict(node.left_child, features, indices[left_mask], prediction)
        self._predict(node.right_child, features, indices[~left_mask], prediction)


class HonestQuantileEnsemble:
    def __init__(self, max_depth, n_trees=16, quantile=0.9):
        self.max_depth = max_depth
        self.n_trees = n_trees
        self.quantile = quantile
        self.trees = []

    def fit(self, features, log_norms):
        self.trees = []
        self.fallback_log_scale = float(np.quantile(log_norms, self.quantile))
        split_point = len(log_norms) // 2
        self.supported = len(log_norms) - split_point >= 16
        if not self.supported:
            return self
        for tree_index in range(self.n_trees):
            permutation = np.random.default_rng(4103 + tree_index).permutation(len(log_norms))
            structure_indices = permutation[:split_point]
            estimation_indices = permutation[split_point:]
            assert np.intersect1d(structure_indices, estimation_indices).size == 0
            assert len(structure_indices) + len(estimation_indices) == len(log_norms)
            tree = HonestQuantileTree(self.max_depth, self.quantile)
            tree.fit_structure(features[structure_indices], log_norms[structure_indices])
            tree.fit_leaf_quantiles(features[estimation_indices], log_norms[estimation_indices])
            self.trees.append(tree)
        return self

    def predict_log(self, features):
        if not self.trees:
            return np.full(len(features), self.fallback_log_scale)
        tree_log_predictions = np.asarray([tree.predict_log(features) for tree in self.trees])
        return np.mean(tree_log_predictions, axis=0)


def fit_scale(features, residual_norms):
    log_norms = np.log(np.maximum(residual_norms, 1e-12))
    folds = np.array_split(np.random.default_rng(0).permutation(len(log_norms)), 3)
    candidate_specs = [(tree_depth, blend_weight) for tree_depth in (1, 2)
                       for blend_weight in (0.25, 0.5, 1.0)]
    model = dict(selected_index=0, forest=None, alignment_offset=0.0, blend_weight=0.0)
    fitting_sizes = [len(log_norms) - len(fold) for fold in folds]
    if any(size - size // 2 < 16 for size in fitting_sizes):
        model['incumbent'] = fit_complete_incumbent(features, residual_norms)
        return model
    fold_losses = []
    for fold_index, validation_indices in enumerate(folds):
        fit_indices = np.concatenate([fold for index, fold in enumerate(folds)
                                      if index != fold_index])
        assert np.intersect1d(fit_indices, validation_indices).size == 0
        incumbent = fit_complete_incumbent(features[fit_indices], residual_norms[fit_indices])
        fitted_incumbent_log_scale = np.log(predict_complete_incumbent(incumbent, features[fit_indices]))
        incumbent_log_scale = np.log(predict_complete_incumbent(incumbent, features[validation_indices]))
        constant_log_scale = float(np.quantile(log_norms[fit_indices], 0.9))
        losses = [float(pinball_loss(log_norms[validation_indices] - incumbent_log_scale, 0.9).mean()),
                  float(pinball_loss(log_norms[validation_indices] - constant_log_scale, 0.9).mean())]
        for tree_depth in (1, 2):
            forest = HonestQuantileEnsemble(max_depth=tree_depth, n_trees=16, quantile=0.9)
            forest.fit(features[fit_indices], log_norms[fit_indices])
            assert forest.supported
            fitted_forest_log_scale = forest.predict_log(features[fit_indices])
            forest_log_scale = forest.predict_log(features[validation_indices])
            for blend_weight in (0.25, 0.5, 1.0):
                fitted_blend = ((1.0 - blend_weight) * fitted_incumbent_log_scale
                                + blend_weight * fitted_forest_log_scale)
                alignment_offset = align_log_scale(log_norms[fit_indices], fitted_blend, 0.9)
                blended_log_scale = (1.0 - blend_weight) * incumbent_log_scale + blend_weight * forest_log_scale
                blended_log_scale += alignment_offset
                validation_loss = pinball_loss(log_norms[validation_indices] - blended_log_scale, 0.9)
                losses.append(float(validation_loss.mean()))
        fold_losses.append(losses)
    fold_losses = np.asarray(fold_losses)
    mean_losses = fold_losses.mean(axis=0)
    standard_errors = fold_losses.std(axis=0, ddof=1) / np.sqrt(len(folds))
    best_index = int(np.argmin(mean_losses))
    selection_limit = mean_losses[best_index] + standard_errors[best_index]
    selected_index = next(index for index in range(len(mean_losses))
                          if mean_losses[index] <= selection_limit)
    model['incumbent'] = fit_complete_incumbent(features, residual_norms)
    model['selected_index'] = selected_index
    model['fold_losses'] = fold_losses
    if selected_index == 1:
        model['alignment_offset'] = float(np.quantile(log_norms, 0.9))
    elif selected_index >= 2:
        tree_depth, blend_weight = candidate_specs[selected_index - 2]
        forest = HonestQuantileEnsemble(max_depth=tree_depth, n_trees=16, quantile=0.9)
        forest.fit(features, log_norms)
        incumbent_log_scale = np.log(predict_complete_incumbent(model['incumbent'], features))
        forest_log_scale = forest.predict_log(features)
        blended_log_scale = (1.0 - blend_weight) * incumbent_log_scale + blend_weight * forest_log_scale
        model['alignment_offset'] = align_log_scale(log_norms, blended_log_scale, 0.9)
        model['forest'] = forest
        model['blend_weight'] = blend_weight
    return model


def predict_scale(model, covariates):
    if model['selected_index'] == 0:
        predicted_scales = predict_complete_incumbent(model['incumbent'], covariates)
    else:
        if model['selected_index'] == 1:
            selected_log_scale = np.full(len(covariates), model['alignment_offset'])
        else:
            incumbent_log_scale = np.log(predict_complete_incumbent(model['incumbent'], covariates))
            forest_log_scale = model['forest'].predict_log(covariates)
            selected_log_scale = blend_log_scales(incumbent_log_scale, forest_log_scale,
                                                 model['blend_weight']) + model['alignment_offset']
        predicted_scales = np.exp(np.clip(selected_log_scale, -30.0, 30.0))
    assert np.isfinite(predicted_scales).all() and (predicted_scales > 0.0).all()
    return predicted_scales


def compute(method, fields, arrays):
    global MODEL
    if method == 'fit':
        covariates, residuals = arrays['x'], arrays['residuals']
        if covariates.ndim != 2 or covariates.shape[1] != 6 or residuals.shape != (len(covariates),):
            raise ValueError('training shape')
        if len(covariates) == 0:
            raise ValueError('empty training data')
        MODEL = fit_scale(covariates, residuals)
        return {'ok': True}
    if method == 'predict' and MODEL is not None:
        return predict_scale(MODEL, arrays['x'])
    raise ValueError('operation/state')


def handle(request):
    global MODEL, TRANSFER
    operation = request['op']
    if operation == 'reset':
        if type(request['seed']) is not int or request['seed'] < 0:
            raise ValueError('seed')
        MODEL, TRANSFER = None, None
        return {'ok': True}
    if operation in ('fit', 'predict'):
        names = ('x', 'residuals') if operation == 'fit' else ('x',)
        result = compute(operation, request, {name: decode(request[name]) for name in names})
        return result if operation == 'fit' else {'scales': encode(result)}
    if operation == 'begin':
        if TRANSFER is not None or not 0 < request['nbytes'] <= 2 * CHUNK:
            raise ValueError('transfer bound')
        if request['method'] not in ('fit', 'predict'):
            raise ValueError('method')
        if sum(item['nbytes'] for item in request['arrays'].values()) != request['nbytes']:
            raise ValueError('transfer shape')
        TRANSFER = dict(request=request, raw=bytearray(), output=None, fetched=0)
        return {'token': 'buffer'}
    if TRANSFER is None or request['token'] != 'buffer':
        raise ValueError('transfer state')
    transfer = TRANSFER
    if operation == 'upload':
        raw = base64.b64decode(request['data'], validate=True)
        if (request['offset'] != len(transfer['raw']) or not 0 < len(raw) <= CHUNK
                or len(transfer['raw']) + len(raw) > transfer['request']['nbytes']):
            raise ValueError('chunk ordering/length')
        transfer['raw'].extend(raw)
        return {'ok': True}
    if operation == 'commit':
        specification = transfer['request']
        if len(transfer['raw']) != specification['nbytes'] or transfer['output'] is not None:
            raise ValueError('incomplete/duplicate commit')
        arrays, offset = {}, 0
        for name, metadata in specification['arrays'].items():
            count = metadata['nbytes']
            arrays[name] = np.frombuffer(transfer['raw'], dtype='<f8', count=count // 8,
                                       offset=offset).reshape(metadata['shape'])
            offset += count
        result = compute(specification['method'], specification['fields'], arrays)
        transfer['output'] = (json.dumps(result).encode() if specification['method'] == 'fit'
                              else np.asarray(result, dtype='<f8').tobytes())
        if len(transfer['output']) > 2 * CHUNK:
            raise ValueError('output bound')
        del arrays
        transfer['raw'] = bytearray()
        return {'ok': True}
    if operation == 'export_start' and transfer['output'] is not None:
        return {'nbytes': len(transfer['output']),
                'chunks': math.ceil(len(transfer['output']) / CHUNK)}
    if operation == 'fetch' and transfer['output'] is not None:
        index = request['index']
        if index != transfer['fetched'] or index * CHUNK >= len(transfer['output']):
            raise ValueError('fetch order')
        transfer['fetched'] += 1
        return {'data': base64.b64encode(transfer['output'][index * CHUNK:(index + 1) * CHUNK]).decode()}
    if operation == 'release':
        TRANSFER = None
        return {'ok': True}
    raise ValueError('transfer operation/state')
