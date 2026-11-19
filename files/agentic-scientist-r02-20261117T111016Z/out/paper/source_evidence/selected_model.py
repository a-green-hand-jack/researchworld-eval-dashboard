"""Deterministic training-only rank-selected local-moment ILR regression.

The incumbent centers and base scales are unchanged. Three outer training folds
select the existing scalar scale correction using nested residual tables and
swapped held-out pseudo-calibration/evaluation halves. Selection minimizes a
row-weighted, alpha-averaged log arithmetic mean ILR-box volume, not simplex
volume. Unavailable finite-sample ranks or invalid radii fall back to the original
Gaussian selector for the entire fit. Fewer than five training rows retain its
exact neutral correction. Independent evaluator calibration is untouched; no
conditional or covariate-shift coverage guarantee is added.

Interface: handle(request: dict) -> dict, finite JSON only, no extra response keys.
Keep the entrypoint self-contained in this file; native validation stages only this
file plus installed packages, with a read-only filesystem and memory-only state.
Every request has exactly the keys shown below. Seed is any int in [0,2**63);
it initializes randomness and NEVER chooses a workload. No paths are accepted.

Operations/state transitions:
  reset: {op:'reset', seed:int} -> {ok:true}; clears ALL state, enters unfitted.
  predict: {op:'predict', x:array} -> {status:'unfitted'} until fit_scale completes.
    When fitted: {center:array, scale:array}, both shape [N,K-1], finite float64;
    center is in the fixed ILR basis, abs(center)<=100; scale in [1e-4,100].
    Read-only, deterministic for equal inputs; identical rows have equal outputs.
  fit_center: {op:'fit_center', x:array, y:array, dimension:int} -> {ok:true}.
    X [N,6], Y [N,K], K in {3,8}, positive rows summing to 1, training only.
    Fits center; invalidates scale, enters center-fitted but still unfitted.
  fit_scale: {op:'fit_scale'} -> {ok:true}; requires fit_center, uses retained
    TRAINING residuals only, enters fitted. No calibration/test labels provided.

Array schema (exact keys): {encoding:'base64', dtype:'float64', byte_order:'little',
  shape:[rows,columns], data:ASCII base64 of C-order little-endian float64 bytes}.
1<=N<=4096, columns<=8, each logical array <=1 MiB. Complete request/response
including envelope and newline must be <2 MiB (and strictly <64 MiB harness cap).
No state transfer or chunk operations exist: declared maximum shapes all fit inline;
larger logical inputs are rejected, never written to disk. Live model state <64 MiB.
Additional keys, nonfinite numbers, malformed encodings, and invalid state transitions
are errors, not diagnostics. Responses contain no optional keys or internal reports.

Basis convention: column j-1 (j=1..K-1) has first j entries 1/sqrt(j*(j+1)),
entry j equal to -j/sqrt(j*(j+1)), remaining entries zero. z=log(y) @ basis.
Inverse softmax(z @ basis.T). Evaluator owns calibration and region membership:
max(abs(z-center)/scale) <= independent split-conformal order statistic, separately
at alpha=.05,.10,.20. Targets to predict are observed continuous compositions,
not labels or latent categorical probabilities. Prediction queries do not identify
calibration/test membership, alpha, case, plane, targets, scores, or baselines.

Public workload: six continuous X features; K=3 or 8; logistic-normal IID,
heteroscedastic Dirichlet IID and covariate-shift stress. Training-only fitting can
be replaced within this exact output family. Evaluator also tests constant-input,
nonidentity-permuted-input, zero-radius copy-point, and reset/unfitted controls.
No superiority or realized-coverage threshold is a search eligibility requirement.
"""

import base64
import math

import numpy as np


_state = {}


def _decode(value):
    if type(value) is not dict or set(value) != {
        'encoding', 'dtype', 'byte_order', 'shape', 'data'
    }:
        raise ValueError('invalid array schema')
    shape = value['shape']
    if (value['encoding'] != 'base64' or value['dtype'] != 'float64'
            or value['byte_order'] != 'little' or type(shape) is not list
            or len(shape) != 2 or any(type(size) is not int for size in shape)
            or not 1 <= shape[0] <= 4096 or not 1 <= shape[1] <= 8):
        raise ValueError('invalid array metadata')
    raw = base64.b64decode(value['data'], validate=True)
    if len(raw) != math.prod(shape) * 8 or len(raw) > 1024 * 1024:
        raise ValueError('invalid array size')
    result = np.frombuffer(raw, dtype='<f8').reshape(shape).copy()
    if not np.isfinite(result).all():
        raise ValueError('nonfinite array')
    return result


def _encode(array):
    array = np.ascontiguousarray(array, dtype='<f8')
    return {'encoding': 'base64', 'dtype': 'float64', 'byte_order': 'little',
            'shape': list(array.shape), 'data': base64.b64encode(array.tobytes()).decode('ascii')}


def _basis(dimension):
    basis = np.zeros((dimension, dimension - 1))
    for column in range(1, dimension):
        denominator = math.sqrt(column * (column + 1))
        basis[:column, column - 1] = 1 / denominator
        basis[column, column - 1] = -column / denominator
    return basis


def _features(features):
    return np.column_stack((np.ones(len(features)), features, features ** 2,
                            np.sin(features), features[:, 0] * features[:, 1]))


def _ridge(features, targets, penalty):
    regularizer = np.eye(features.shape[1]) * penalty
    regularizer[0, 0] = 1e-8
    return np.linalg.solve(features.T @ features + regularizer, features.T @ targets)


def _training_folds(sample_count):
    indices = np.random.default_rng(0).permutation(sample_count)
    return np.array_split(indices, 3)


def _fit_incumbent(train_features, train_targets):
    design = _features(train_features)
    ilr_targets = np.log(train_targets) @ _basis(train_targets.shape[1])
    coefficient = _ridge(design, ilr_targets, 1.0)
    residual = ilr_targets - design @ coefficient
    log_residual = np.log(np.maximum(abs(residual), .02))
    scale_coefficient = _ridge(design, log_residual, 10.0)
    return coefficient, scale_coefficient


def _incumbent_predictions(model, features):
    coefficient, scale_coefficient = model
    design = _features(features)
    base_centers = np.clip(design @ coefficient, -100, 100)
    base_scales = np.clip(np.exp(np.clip(design @ scale_coefficient,
                                        math.log(1e-4), math.log(100))), 1e-4, 100)
    return base_centers, base_scales


def build_oof_residual_table(train_features, train_targets):
    ilr_targets = np.log(train_targets) @ _basis(train_targets.shape[1])
    oof_centers = np.empty_like(ilr_targets)
    oof_scales = np.empty_like(ilr_targets)
    all_indices = np.arange(len(train_features))
    for valid_indices in _training_folds(len(train_features)):
        fit_indices = np.setdiff1d(all_indices, valid_indices)
        assert np.intersect1d(fit_indices, valid_indices).size == 0
        model = _fit_incumbent(train_features[fit_indices], train_targets[fit_indices])
        oof_centers[valid_indices], oof_scales[valid_indices] = _incumbent_predictions(
            model, train_features[valid_indices])
    scale_floor = 1e-4
    standardized_residuals = (ilr_targets - oof_centers) / np.maximum(oof_scales, scale_floor)
    relative_squared_residuals = np.mean(standardized_residuals ** 2, axis=1)
    location = np.mean(train_features, axis=0)
    spread = np.maximum(np.std(train_features, axis=0), 1e-8)
    return {'features': (train_features - location) / spread,
            'location': location, 'spread': spread,
            'relative_squared_residuals': relative_squared_residuals}


def _local_moment_ratio(residual_table, query_features, bandwidth, prior_mass):
    assert bandwidth > 0.0 and prior_mass > 0.0
    reference_features = residual_table['features']
    relative_squared_residuals = residual_table['relative_squared_residuals']
    reference_norms = np.sum(reference_features ** 2, axis=1)
    ratios = np.empty(len(query_features), dtype=np.float64)
    for start in range(0, len(query_features), 128):
        query = ((query_features[start:start + 128] - residual_table['location'])
                 / residual_table['spread'])
        squared_distances = np.maximum(
            np.sum(query ** 2, axis=1)[:, None] + reference_norms[None, :]
            - 2.0 * (query @ reference_features.T), 0.0)
        weights = np.exp(-0.5 * squared_distances / (bandwidth ** 2))
        moment_ratio = (weights @ relative_squared_residuals + prior_mass) / (weights.sum(axis=1) + prior_mass)
        ratios[start:start + len(query)] = moment_ratio
    return ratios


def apply_scale_correction(base_scales, moment_ratio, blend):
    if blend == 0.0: return base_scales.copy()
    correction = np.exp(0.5 * blend * np.log(np.clip(moment_ratio, 0.25, 4.0)))
    lower_factor = np.max(1e-4 / base_scales, axis=1)
    upper_factor = np.min(100.0 / base_scales, axis=1)
    correction = np.clip(correction, lower_factor, upper_factor)
    below_floor = np.any(base_scales * correction[:, None] < 1e-4, axis=1)
    above_ceiling = np.any(base_scales * correction[:, None] > 100.0, axis=1)
    correction[below_floor] = np.nextafter(lower_factor[below_floor], np.inf)
    correction[above_ceiling] = np.nextafter(upper_factor[above_ceiling], 0.0)
    adjusted_scales = base_scales * correction[:, None]
    assert np.all(np.isfinite(adjusted_scales)) and np.all(adjusted_scales > 0.0)
    assert np.all(adjusted_scales >= 1e-4) and np.all(adjusted_scales <= 100.0)
    return adjusted_scales


def _select_correction_gaussian(train_features, train_targets):
    candidate_blends = (0.0, 0.5, 1.0)
    feature_dimension = train_features.shape[1]
    candidate_bandwidths = (0.5 * math.sqrt(feature_dimension), math.sqrt(feature_dimension))
    candidate_results = [
        {'blend': blend, 'bandwidth': bandwidth, 'prior_mass': prior_mass,
         'validation_loss': 0.0}
        for blend in candidate_blends for bandwidth in candidate_bandwidths
        for prior_mass in (10.0, 50.0)]
    if len(train_features) < 5:
        return candidate_results[0], None
    all_indices = np.arange(len(train_features))
    for outer_valid_indices in _training_folds(len(train_features)):
        outer_train_indices = np.setdiff1d(all_indices, outer_valid_indices)
        assert np.intersect1d(outer_train_indices, outer_valid_indices).size == 0
        outer_residual_table = build_oof_residual_table(train_features[outer_train_indices], train_targets[outer_train_indices])
        model = _fit_incumbent(train_features[outer_train_indices],
                               train_targets[outer_train_indices])
        validation_centers, base_scales = _incumbent_predictions(
            model, train_features[outer_valid_indices])
        validation_targets = (np.log(train_targets[outer_valid_indices])
                              @ _basis(train_targets.shape[1]))
        ratio_cache = {}
        for setting in candidate_results:
            blend = setting['blend']
            cache_key = (setting['bandwidth'], setting['prior_mass'])
            if blend == 0.0:
                moment_ratio = np.ones(len(outer_valid_indices))
            else:
                if cache_key not in ratio_cache:
                    ratio_cache[cache_key] = _local_moment_ratio(
                        outer_residual_table, train_features[outer_valid_indices],
                        setting['bandwidth'], setting['prior_mass'])
                moment_ratio = ratio_cache[cache_key]
            validation_scales = apply_scale_correction(base_scales, moment_ratio, blend)
            validation_residuals = (validation_targets - validation_centers) / validation_scales
            validation_loss = np.mean(np.log(validation_scales) + 0.5 * validation_residuals ** 2)
            setting['validation_loss'] += (float(validation_loss)
                                           * len(outer_valid_indices) / len(train_features))
        assert np.allclose(apply_scale_correction(base_scales, moment_ratio, 0.0), base_scales)
    selected_setting = min(candidate_results, key=lambda setting: (setting['validation_loss'], setting['blend']))
    residual_table = build_oof_residual_table(train_features, train_targets)
    distant_query = residual_table['location'][None, :] + 1e6 * residual_table['spread'][None, :]
    assert np.allclose(_local_moment_ratio(residual_table, distant_query,
                                          selected_setting['bandwidth'],
                                          selected_setting['prior_mass']), 1.0)
    return selected_setting, residual_table


def _conformal_radius(calibration_scores, alpha):
    rank = math.ceil((len(calibration_scores) + 1) * (1.0 - alpha))
    if rank > len(calibration_scores): return None
    if not np.isfinite(calibration_scores).all(): return None
    radius = np.partition(calibration_scores, rank - 1)[rank - 1]
    if not np.isfinite(radius) or radius <= 0.0: return None
    return float(radius)


def _log_mean_box_volume(validation_scales, radius):
    coordinate_count = validation_scales.shape[1]
    log_box_volume = coordinate_count * np.log(2.0 * radius) + np.sum(np.log(validation_scales), axis=1)
    volume_shift = np.max(log_box_volume)
    log_mean_volume = volume_shift + np.log(np.mean(np.exp(log_box_volume - volume_shift)))
    return float(log_mean_volume)


def _assert_rank_selection_controls(calibration_scores, calibration_scales,
                                    validation_scales, selection_alphas):
    assert _conformal_radius(np.ones(18), 0.05) is None
    assert _conformal_radius(np.ones(19), 0.05) == 1.0
    assert _conformal_radius(np.zeros(19), 0.05) is None
    assert _conformal_radius(np.full(19, np.inf), 0.05) is None
    if (np.any(calibration_scales <= 1e-4) or np.any(calibration_scales >= 50.0)
            or np.any(validation_scales <= 1e-4) or np.any(validation_scales >= 50.0)):
        return
    for alpha in selection_alphas:
        radius = _conformal_radius(calibration_scores, alpha)
        rescaled_radius = _conformal_radius(calibration_scores / 2.0, alpha)
        assert radius is not None and rescaled_radius is not None
        assert np.allclose(radius * validation_scales,
                           rescaled_radius * (2.0 * validation_scales),
                           rtol=1e-12, atol=1e-12)
        assert np.isclose(_log_mean_box_volume(validation_scales, radius),
                          _log_mean_box_volume(2.0 * validation_scales, rescaled_radius),
                          rtol=1e-12, atol=1e-12)


def _select_correction(train_features, train_targets):
    selection_alphas = (0.05, 0.10, 0.20)
    outer_folds = _training_folds(len(train_features))
    rank_selection_available = all(
        math.ceil((len(half) + 1) * (1.0 - alpha)) <= len(half)
        for fold in outer_folds for half in np.array_split(fold, 2)
        for alpha in selection_alphas)
    if not rank_selection_available: return _select_correction_gaussian(train_features, train_targets)
    candidate_blends = (0.0, 0.5, 1.0)
    feature_dimension = train_features.shape[1]
    candidate_bandwidths = (0.5 * math.sqrt(feature_dimension), math.sqrt(feature_dimension))
    candidate_results = [
        {'blend': blend, 'bandwidth': bandwidth, 'prior_mass': prior_mass,
         'selection_loss': 0.0}
        for blend in candidate_blends for bandwidth in candidate_bandwidths
        for prior_mass in (10.0, 50.0)]
    all_indices = np.arange(len(train_features))
    for outer_valid_indices in outer_folds:
        outer_train_indices = np.setdiff1d(all_indices, outer_valid_indices)
        assert np.intersect1d(outer_train_indices, outer_valid_indices).size == 0
        half_positions = np.array_split(np.arange(len(outer_valid_indices)), 2)
        pseudo_splits = []
        for split_index in range(2):
            calibration_positions = half_positions[split_index]
            evaluation_positions = half_positions[1 - split_index]
            pseudo_calibration_indices = outer_valid_indices[calibration_positions]
            pseudo_evaluation_indices = outer_valid_indices[evaluation_positions]
            assert np.intersect1d(outer_train_indices, pseudo_calibration_indices).size == 0
            assert np.intersect1d(outer_train_indices, pseudo_evaluation_indices).size == 0
            assert np.intersect1d(pseudo_calibration_indices, pseudo_evaluation_indices).size == 0
            pseudo_splits.append((calibration_positions, evaluation_positions))
        outer_residual_table = build_oof_residual_table(train_features[outer_train_indices], train_targets[outer_train_indices])
        model = _fit_incumbent(train_features[outer_train_indices],
                               train_targets[outer_train_indices])
        heldout_centers, base_scales = _incumbent_predictions(
            model, train_features[outer_valid_indices])
        heldout_targets = (np.log(train_targets[outer_valid_indices])
                           @ _basis(train_targets.shape[1]))
        ratio_cache = {}
        for setting in candidate_results:
            blend = setting['blend']
            cache_key = (setting['bandwidth'], setting['prior_mass'])
            if blend == 0.0:
                moment_ratio = np.ones(len(outer_valid_indices))
            else:
                if cache_key not in ratio_cache:
                    ratio_cache[cache_key] = _local_moment_ratio(
                        outer_residual_table, train_features[outer_valid_indices],
                        setting['bandwidth'], setting['prior_mass'])
                moment_ratio = ratio_cache[cache_key]
            heldout_scales = apply_scale_correction(base_scales, moment_ratio, blend)
            assert np.array_equal(apply_scale_correction(base_scales, moment_ratio, 0.0), base_scales)
            for calibration_positions, evaluation_positions in pseudo_splits:
                calibration_targets = heldout_targets[calibration_positions]
                calibration_centers = heldout_centers[calibration_positions]
                calibration_scales = heldout_scales[calibration_positions]
                validation_scales = heldout_scales[evaluation_positions]
                calibration_scores = np.max(np.abs(calibration_targets - calibration_centers) / calibration_scales, axis=1)
                alpha_log_mean_volumes = []
                for alpha in selection_alphas:
                    radius = _conformal_radius(calibration_scores, alpha)
                    rank_selection_available = radius is not None
                    if not rank_selection_available: return _select_correction_gaussian(train_features, train_targets)
                    log_mean_volume = _log_mean_box_volume(validation_scales, radius)
                    rank_selection_available = np.isfinite(log_mean_volume)
                    if not rank_selection_available: return _select_correction_gaussian(train_features, train_targets)
                    alpha_log_mean_volumes.append(log_mean_volume)
                if setting is candidate_results[0]:
                    _assert_rank_selection_controls(calibration_scores, calibration_scales,
                                                    validation_scales, selection_alphas)
                fold_weight = len(evaluation_positions) / len(train_features)
                setting['selection_loss'] += fold_weight * float(np.mean(alpha_log_mean_volumes))
    selected_setting = min(candidate_results, key=lambda setting: (setting['selection_loss'], setting['blend']))
    residual_table = build_oof_residual_table(train_features, train_targets)
    distant_query = residual_table['location'][None, :] + 1e6 * residual_table['spread'][None, :]
    assert np.allclose(_local_moment_ratio(residual_table, distant_query,
                                          selected_setting['bandwidth'],
                                          selected_setting['prior_mass']), 1.0)
    return selected_setting, residual_table


def _corrected_predictions(features):
    model = (_state['coefficient'], _state['scale_coefficient'])
    base_centers, base_scales = _incumbent_predictions(model, features)
    original_centers = base_centers.copy()
    setting = _state['correction_setting']
    if setting['blend'] == 0.0:
        moment_ratio = np.ones(len(features))
    else:
        moment_ratio = _local_moment_ratio(_state['residual_table'], features,
                                           setting['bandwidth'], setting['prior_mass'])
    adjusted_scales = apply_scale_correction(base_scales, moment_ratio, setting['blend'])
    assert np.array_equal(base_centers, original_centers)
    assert adjusted_scales.shape == base_scales.shape == base_centers.shape
    assert np.all(np.isfinite(adjusted_scales)) and np.all(adjusted_scales > 0.0)
    return base_centers, adjusted_scales


def handle(request):
    if type(request) is not dict:
        raise ValueError('request must be object')
    operation = request.get('op')
    keys = {'reset': {'op', 'seed'}, 'predict': {'op', 'x'},
            'fit_center': {'op', 'x', 'y', 'dimension'}, 'fit_scale': {'op'}}
    if operation not in keys or set(request) != keys[operation]:
        raise ValueError('invalid operation schema')
    if operation == 'reset':
        seed = request['seed']
        if type(seed) is not int or not 0 <= seed < 2 ** 63:
            raise ValueError('invalid seed')
        _state.clear()
        _state['rng'] = np.random.default_rng(seed)
        return {'ok': True}
    if 'rng' not in _state:
        raise ValueError('reset required')
    if operation == 'fit_center':
        dimension = request['dimension']
        features, targets = _decode(request['x']), _decode(request['y'])
        if (type(dimension) is not int or dimension not in (3, 8)
                or features.shape[1] != 6 or targets.shape != (len(features), dimension)
                or not (targets > 0).all()
                or not np.allclose(targets.sum(axis=1), 1, atol=1e-10, rtol=0)):
            raise ValueError('invalid training data')
        design = _features(features)
        transformed = np.log(targets) @ _basis(dimension)
        coefficient = _ridge(design, transformed, 1.0)
        _state.update(coefficient=coefficient, design=design,
                      residual=transformed - design @ coefficient,
                      train_features=features, train_targets=targets)
        _state.pop('scale_coefficient', None)
        _state.pop('correction_setting', None)
        _state.pop('residual_table', None)
        return {'ok': True}
    if operation == 'fit_scale':
        if 'coefficient' not in _state:
            raise ValueError('center required')
        log_residual = np.log(np.maximum(abs(_state['residual']), .02))
        scale_coefficient = _ridge(_state['design'], log_residual, 10.0)
        setting, residual_table = _select_correction(_state['train_features'],
                                                     _state['train_targets'])
        _state.update(scale_coefficient=scale_coefficient,
                      correction_setting=setting, residual_table=residual_table)
        return {'ok': True}
    features = _decode(request['x'])
    if features.shape[1] != 6:
        raise ValueError('invalid feature shape')
    if 'scale_coefficient' not in _state:
        return {'status': 'unfitted'}
    center, scale = _corrected_predictions(features)
    response = {'center': _encode(center), 'scale': _encode(scale)}
    assert set(response) == {'center', 'scale'}
    assert response['center']['shape'] == response['scale']['shape'] == [len(features), center.shape[1]]
    return response
