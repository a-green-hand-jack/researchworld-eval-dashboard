"""Independent executable validation, written for a later authorized run.

Run from the candidate directory: python src/validate_logistic_fourier.py
These small synthetic games validate arithmetic, not public-data reliability.
"""

import base64
import hashlib
import json
import math
from unittest.mock import patch

import numpy as np

import logistic_fourier
import program
import reliability
from logistic_fourier import logistic_fourier_shapley


def make_model(coefficients, intercept, background):
    return {
        'kind': 'logistic',
        'dimension': len(coefficients),
        'parameters': {'coef': list(coefficients), 'intercept': intercept},
        'background': [list(row) for row in background],
    }


def scalar_probability(model, row):
    parameters = model['parameters']
    logit = sum(float(value) * float(coefficient)
                for value, coefficient in zip(row, parameters['coef']))
    logit += parameters['intercept']
    return 1.0 / (1.0 + math.exp(-max(-700.0, min(700.0, logit))))


def enumerate_game(model, query):
    feature_count = len(query)
    background = model['background']
    values = []
    for coalition_mask in range(1 << feature_count):
        predictions = []
        for background_row in background:
            hybrid = [query[feature_index] if coalition_mask & (1 << feature_index)
                      else background_row[feature_index]
                      for feature_index in range(feature_count)]
            predictions.append(scalar_probability(model, hybrid))
        values.append(sum(predictions) / len(predictions))
    enumerated_phi = np.zeros(feature_count)
    for feature_index in range(feature_count):
        for coalition_mask in range(1 << feature_count):
            if coalition_mask & (1 << feature_index):
                continue
            coalition_size = coalition_mask.bit_count()
            weight = (math.factorial(coalition_size)
                      * math.factorial(feature_count - coalition_size - 1)
                      / math.factorial(feature_count))
            enumerated_phi[feature_index] += weight * (
                values[coalition_mask | (1 << feature_index)] - values[coalition_mask])
    return enumerated_phi, values[-1] - values[0]


def fixtures():
    yield make_model(
        [1.3, -0.7, 0.0, 2.1, -1.2, 0.4], -0.25,
        [[0.0] * 6, [0.4, -0.6, 1.2, 0.5, -0.3, 0.8],
         [-1.0, 0.2, -0.5, 0.1, 0.6, -0.2]]), [0.7, -0.8, 1.0, 0.3, 0.4, -0.5]
    for intercept in (30.0, -30.0):
        yield make_model(
            [12.0, -9.0, 4.0, 0.0], intercept,
            [[0.0] * 4, [0.5, 0.5, -0.5, 2.0]]), [1.0, 1.0, 1.0, -2.0]
    yield make_model([math.pi, -math.pi], 0.3, [[0.0, 0.0]]), [1.0, 1.0]
    yield make_model([1.0, 1.0 + 1e-10, -1.0, 0.0], -0.5,
                     [[0.0] * 4, [0.0] * 4]), [1.0, 1.0, 1.0, 2.0]
    yield make_model([0.0] * 4, 0.2, [[0.0] * 4, [1.0] * 4]), [2.0] * 4
    yield make_model([0.8, -1.1, 0.2, 0.0, 0.5], -0.6,
                     [[0.0] * 5, [0.2] * 5]), [1.0, 0.4, -0.5, 0.9, 1.2]
    identical_row = [0.4, -0.2, 0.8, 0.0]
    yield make_model([0.7, -1.3, 0.0, 0.5], 0.3,
                     [identical_row, identical_row]), identical_row


def check_probability_games():
    case_count = 0
    for model, query in fixtures():
        coefficients = np.asarray(model['parameters']['coef'])
        enumerated_phi, endpoint_difference = enumerate_game(model, query)
        integrated_phi = logistic_fourier_shapley(model, query)
        assert integrated_phi is not None
        assert np.allclose(integrated_phi, enumerated_phi, atol=2e-8, rtol=2e-8)
        assert np.isclose(integrated_phi.sum(), endpoint_difference, atol=2e-8, rtol=2e-8)
        rowwise_phi = []
        for background_row in model['background']:
            row_model = make_model(coefficients.tolist(), model['parameters']['intercept'],
                                   [background_row])
            row_phi = logistic_fourier_shapley(row_model, query)
            assert row_phi is not None
            rowwise_phi.append(row_phi)
        rowwise_phi = np.asarray(rowwise_phi)
        assert np.allclose(integrated_phi, rowwise_phi.mean(axis=0), atol=2e-8, rtol=2e-8)
        assert np.allclose(integrated_phi[coefficients == 0.0], 0.0, atol=1e-12, rtol=0.0)
        first_repeat = logistic_fourier_shapley(model, query)
        second_repeat = logistic_fourier_shapley(model, query)
        assert np.array_equal(first_repeat, second_repeat)
        case_count += 1
    return case_count


def check_zero_mixture_and_origin():
    increments = np.array([math.pi, -math.pi])
    frequencies = np.array([1.0])
    inclusion_nodes = np.array([0.5])
    inclusion_weights = np.array([1.0])
    phase_steps = np.exp(1j * frequencies[:, None] * increments[None, :])
    assert np.max(np.abs(0.5 + 0.5 * phase_steps)) < 1e-14
    actual = logistic_fourier._frequency_marginals(
        frequencies, 0.3, increments, inclusion_nodes, inclusion_weights)[0]
    expected = []
    for feature_index in range(2):
        other_index = 1 - feature_index
        marginal = 0.5 * (math.sin(0.3 + increments[feature_index]) - math.sin(0.3))
        marginal += 0.5 * (math.sin(0.3 + increments.sum())
                           - math.sin(0.3 + increments[other_index]))
        expected.append(marginal / math.sinh(math.pi))
    assert np.all(np.isfinite(actual))
    assert np.allclose(actual, expected, atol=1e-14, rtol=0.0)
    near_origin = logistic_fourier._frequency_marginals(
        np.array([1e-9]), 0.3, increments, inclusion_nodes, inclusion_weights)[0]
    assert np.allclose(near_origin, increments / np.pi, atol=1e-12, rtol=0.0)


def incumbent_sample(model, query, budget, rng):
    game = reliability.FrozenProbabilityGame(model, query, program.predict)
    path_count = budget // (4 * (game.dimension - 1))
    path_masks = np.empty(0, dtype=np.uint32)
    path_estimate = None
    certified = False
    if path_count >= 2:
        path_marginals, path_masks = reliability.independent_paths(game, path_count, rng)
        path_estimate, radius, certified = reliability.simultaneous_certificate(path_marginals)
    kernel_masks = reliability.sampled_kernel_masks(game.dimension, budget - len(path_masks), rng)
    masks = np.concatenate((path_masks, kernel_masks))
    if certified:
        return path_estimate
    return reliability.kernel_regression(game, masks, len(path_masks))


def no_predictions(model, rows):
    raise AssertionError('resolved integration must not predict coalitions')


def check_dispatch_and_fallback():
    model, query = next(fixtures())
    rng = np.random.default_rng(1729)
    before_state = json.dumps(rng.bit_generator.state, sort_keys=True)
    actual = reliability.explain_fixed_game(model, query, 1, rng, no_predictions)
    assert np.array_equal(actual, logistic_fourier_shapley(model, query))
    assert json.dumps(rng.bit_generator.state, sort_keys=True) == before_state
    with patch.object(reliability, 'logistic_fourier_shapley', side_effect=AssertionError):
        exact_phi = reliability.explain_fixed_game(model, query, 62, rng, program.predict)
    enumerated_phi, endpoint_difference = enumerate_game(model, query)
    assert np.allclose(exact_phi, enumerated_phi, atol=2e-8, rtol=2e-8)
    for budget in (1, 41):
        for force_rejection in (False, True):
            fallback_model = (model if force_rejection else
                              make_model([1000.0, -800.0, 300.0, 200.0, -100.0, 0.0],
                                         0.0, [[0.0] * 6]))
            if not force_rejection:
                assert logistic_fourier_shapley(fallback_model, query) is None
            fallback_rng = np.random.default_rng(2718)
            incumbent_rng = np.random.default_rng(2718)
            if force_rejection:
                with patch.object(reliability, 'logistic_fourier_shapley', return_value=None):
                    fallback_phi = reliability.explain_fixed_game(
                        fallback_model, query, budget, fallback_rng, program.predict)
            else:
                fallback_phi = reliability.explain_fixed_game(
                    fallback_model, query, budget, fallback_rng, program.predict)
            incumbent_phi = incumbent_sample(fallback_model, query, budget, incumbent_rng)
            assert np.array_equal(fallback_phi, incumbent_phi)
            assert json.dumps(fallback_rng.bit_generator.state, sort_keys=True) == json.dumps(
                incumbent_rng.bit_generator.state, sort_keys=True)


def check_rejection_and_work_caps():
    zero_model = make_model([0.0] * 4, 0.0, [[0.0] * 4])
    with patch.object(logistic_fourier, '_frequency_mesh',
                      wraps=logistic_fourier._frequency_mesh) as mesh_calls:
        with patch.object(logistic_fourier, '_frequency_marginals',
                          wraps=logistic_fourier._frequency_marginals) as block_calls:
            assert logistic_fourier_shapley(zero_model, [0.0] * 4) is not None
    assert mesh_calls.call_count == 3
    assert all(call.args[5] * len(call.args[6]) <= 2048
               for call in mesh_calls.call_args_list)
    assert all(0 < len(call.args[0]) <= 32 for call in block_calls.call_args_list)
    with patch.object(logistic_fourier, '_frequency_mesh', return_value=np.full(4, np.nan)):
        assert logistic_fourier_shapley(zero_model, [0.0] * 4) is None
    with patch.object(logistic_fourier, '_frequency_mesh', return_value=np.ones(4)):
        assert logistic_fourier_shapley(zero_model, [0.0] * 4) is None
    mesh_index = [0]

    def disagreeing_mesh(*args):
        mesh_index[0] += 1
        return np.array([1.0, -1.0, 0.0, 0.0]) * (-1.0) ** mesh_index[0]

    with patch.object(logistic_fourier, '_frequency_mesh', side_effect=disagreeing_mesh):
        assert logistic_fourier_shapley(zero_model, [0.0] * 4) is None
    extreme_model = make_model([1.0, 0.0], 0.0, [[-1e308, 0.0]])
    assert logistic_fourier_shapley(extreme_model, [1e308, 0.0]) is None


def upload_model(model):
    payload = json.dumps(model, separators=(',', ':')).encode('utf-8')
    response = program.handle({
        'op': 'model_start', 'token': 'validation', 'nbytes': len(payload),
        'sha256': hashlib.sha256(payload).hexdigest(), 'encoding': 'base64',
        'dtype': 'uint8', 'shape': [len(payload)], 'content_type': 'application/json',
    })
    assert response == {'ok': True}
    assert program.handle({'op': 'model_chunk', 'token': 'validation', 'index': 0,
                           'data': base64.b64encode(payload).decode('ascii')}) == {'ok': True}
    assert program.handle({'op': 'model_commit', 'token': 'validation'}) == {'ok': True}


def check_rpc_replay():
    model, query = next(fixtures())
    request = {'op': 'explain', 'queries': [query], 'budget': 1,
               'workload': {'usable_seconds': 10.0, 'remaining_explanations': 2}}
    replies = []
    for replay_index in range(2):
        assert program.handle({'op': 'reset', 'seed': 1729}) == {'ok': True}
        upload_model(model)
        first = program.handle(request)
        second = program.handle(request)
        assert set(first) == {'attributions'}
        assert type(first['attributions']) is list
        assert len(first['attributions']) == 1
        assert len(first['attributions'][0]) == model['dimension']
        assert all(type(value) is float and math.isfinite(value)
                   for value in first['attributions'][0])
        assert first == second
        replies.append(first)
    assert replies[0] == replies[1]


def main():
    case_count = check_probability_games()
    check_zero_mixture_and_origin()
    check_dispatch_and_fallback()
    check_rejection_and_work_caps()
    check_rpc_replay()
    print(f'Validated {case_count} enumerated games, numerical guards, dispatch and RPC replay.')


if __name__ == '__main__':
    main()
