"""Optional synthetic study; never imported or run by the candidate RPC."""
import argparse
import hashlib
import json
import platform
from pathlib import Path
import time

import numpy as np
import scipy
from scipy.stats import binom

from program import (coupled_endpoint_check, endpoint_contrast_diagnostic,
                     features, synthetic_response_pair, validate_endpoint_diagnostic)


def make_graph(family, count, degree, graph_seed):
    import networkx as nx

    labels = np.arange(count) * 20 // count
    if family == 'regular':
        graph = nx.random_regular_graph(degree, count, seed=graph_seed)
    elif family == 'ba':
        graph = nx.barabasi_albert_graph(count, max(1, degree // 2), seed=graph_seed)
    else:
        sizes = np.bincount(labels).tolist()
        probabilities = []
        for block, size in enumerate(sizes):
            within = 0.75 * degree / (size - 1)
            between = 0.25 * degree / (count - size)
            probabilities.append([within if other == block else between
                                  for other in range(len(sizes))])
        if max(map(max, probabilities)) > 1.0:
            raise ValueError('SBM requested degree exceeds block support')
        graph = nx.stochastic_block_model(sizes, probabilities, seed=graph_seed)
    edges = np.asarray(list(graph.edges()), dtype=np.int32).reshape(-1, 2)
    degrees = np.array([graph.degree(node) for node in range(count)])
    return edges, degrees, labels


def support_bound(degrees, threshold=0.8, probability=0.5):
    positive = degrees > 0
    cutoff = np.floor(threshold * degrees[positive]).astype(int)
    expected_active = float(probability * np.sum(
        binom.sf(cutoff, degrees[positive], probability)))
    expected_active += float(np.count_nonzero(~positive) * probability)
    event_lower_bound = max(0.0, 1.0 - expected_active)
    return {'expected_active': expected_active, 'event_probability_lower_bound': event_lower_bound,
            'two_world_max_mse_lower_bound': event_lower_bound / 4.0,
            'assumption': 'Bernoulli independent unit assignment; bump size one'}


def study_outcomes(matrix, covariate, shocks):
    base, hidden, _ = synthetic_response_pair(
        matrix[:, 1], matrix[:, 2], covariate, shocks, matrix[:, 6] == 0)
    return {'linear': base, 'hidden_bump': hidden,
            'quadratic_control': base + 0.5 * matrix[:, 2] ** 2}


def bump_column(matrix):
    exposure = np.where(matrix[:, 6] == 0, matrix[:, 1], matrix[:, 2])
    return matrix[:, 1] * np.maximum((exposure - 0.8) / 0.2, 0.0) ** 2


def solve_ridge(design, outcome, ridge):
    if ridge == 0.0:
        relative_tolerance = np.finfo(float).eps * max(design.shape)
        return np.linalg.lstsq(design, outcome, rcond=relative_tolerance)[0]
    penalty = np.diag(np.r_[0.0, np.repeat(ridge, design.shape[1] - 1)])
    return np.linalg.solve(design.T @ design + penalty, design.T @ outcome)


def fitted_record(design, outcome, control, treated, folds, tune=False):
    contrast = treated.mean(axis=0) - control.mean(axis=0)
    grid = (0.0, 1e-4, 0.01, 0.1, 1.0, 10.0, 100.0) if tune else (0.0,)
    losses = []
    for ridge in grid:
        squared_error = 0.0
        for fold in range(3):
            training = folds != fold
            validation = ~training
            beta = solve_ridge(design[training], outcome[training], ridge)
            squared_error += float(np.sum((outcome[validation] - design[validation] @ beta) ** 2))
        losses.append(squared_error / len(outcome))
    selected = int(np.argmin(losses))
    ridge = grid[selected]
    beta = solve_ridge(design, outcome, ridge)
    estimate = float(contrast @ beta)
    diagnostic = endpoint_contrast_diagnostic(design, contrast)
    variance = diagnostic['noise_variance']
    assumption = 'known-sigma iid outcome noise; fixed-population coverage is empirical'
    if ridge > 0.0:
        penalty = np.diag(np.r_[0.0, np.repeat(ridge, design.shape[1] - 1)])
        weights = design @ np.linalg.solve(design.T @ design + penalty, contrast)
        variance = float(weights @ weights)
        assumption = 'known-sigma noise only; ignores shrinkage and model bias'
    half_length = 1.959963984540054 * np.sqrt(variance) if variance is not None else None
    return {'estimate': estimate, 'ridge': float(ridge), 'validation_mse': losses[selected],
            'interval_lower': estimate - half_length if half_length is not None else None,
            'interval_upper': estimate + half_length if half_length is not None else None,
            'interval_assumption': assumption, 'diagnostic': diagnostic}


def summarize(records):
    completed = [record for record in records if record['status'] == 'completed']
    if not completed:
        return {'attempted': len(records), 'completed': 0, 'failure_rate': 1.0}
    estimates = np.asarray([record['estimate'] for record in completed])
    true_gate = completed[0]['true_gate']
    np.testing.assert_allclose([record['true_gate'] for record in completed], true_gate)
    estimation_errors = estimates - true_gate
    rmse = np.sqrt(np.mean(estimation_errors ** 2))
    if estimates.size > 1:
        bias_mcse = np.std(estimation_errors, ddof=1) / np.sqrt(estimates.size)
    else:
        bias_mcse = None
    interval_lower = np.array([record['interval_lower'] if record['interval_lower'] is not None
                               else np.nan for record in completed])
    interval_upper = np.array([record['interval_upper'] if record['interval_upper'] is not None
                               else np.nan for record in completed])
    coverage = np.mean((interval_lower <= true_gate) & (true_gate <= interval_upper))
    coverage_mcse = np.sqrt(coverage * (1.0 - coverage) / estimates.size)
    if estimates.size > 1:
        rmse_mcse = float(np.std(estimation_errors ** 2, ddof=1)
                          / (2.0 * rmse * np.sqrt(estimates.size))) if rmse > 0 else 0.0
    else:
        rmse_mcse = None
    lengths = interval_upper - interval_lower
    defined = np.isfinite(lengths)
    bias = float(np.mean(estimation_errors))
    return {
        'attempted': len(records), 'completed': len(completed),
        'failure_rate': 1.0 - len(completed) / len(records),
        'true_gate': float(true_gate), 'bias': bias,
        'bias_mcse': float(bias_mcse) if bias_mcse is not None else None,
        'bias_mc_interval': [bias - 1.96 * bias_mcse, bias + 1.96 * bias_mcse] if bias_mcse is not None else None,
        'rmse': float(rmse), 'rmse_mcse_delta': rmse_mcse,
        'rmse_mc_interval_delta': [max(0.0, rmse - 1.96 * rmse_mcse), rmse + 1.96 * rmse_mcse] if rmse_mcse is not None else None,
        'coverage': float(coverage), 'coverage_mcse': float(coverage_mcse),
        'interval_defined_rate': float(np.mean(defined)),
        'mean_interval_length_when_defined': float(np.mean(lengths[defined])) if np.any(defined) else None,
        'nonestimable_rate': float(np.mean([
            record['diagnostic']['status'] != 'estimable' for record in completed])),
        'no_bump_event_rate': float(np.mean([record['pair']['identical_observed_pair'] for record in completed])),
        'mean_active_bump_count': float(np.mean([record['pair']['active_bump_count'] for record in completed])),
        'mean_validation_mse': float(np.mean([record['validation_mse'] for record in completed])),
        'scope': 'conditional on this graph, covariates and fixed shocks; failed fits excluded from error means',
    }


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--n', type=int, default=2000)
    parser.add_argument('--degrees', type=int, nargs='+', default=[8, 32, 128])
    parser.add_argument('--graph-seeds', type=int, nargs='+', default=[1103, 2207, 3301])
    parser.add_argument('--repetitions', type=int, default=200)
    parser.add_argument('--families', nargs='+', choices=['regular', 'sbm', 'ba'], default=['regular'])
    parser.add_argument('--cluster', action='store_true', help='Also run SBM with 20 assignment clusters')
    arguments = parser.parse_args()
    if arguments.n < 60 or arguments.repetitions < 2:
        parser.error('n >= 60 and repetitions >= 2 are required')
    if 'sbm' in arguments.families and arguments.n % 20:
        parser.error('SBM requires n divisible by 20 for equal symmetric blocks')
    arguments.output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    write_json(arguments.output / 'diagnostic_checks.json', validate_endpoint_diagnostic())
    groups = {}
    graph_records = []
    family_codes = {'regular': 1, 'sbm': 2, 'ba': 3}
    with (arguments.output / 'replicates.jsonl').open('w') as stream:
        for family in arguments.families:
            for degree in arguments.degrees:
                for graph_seed in arguments.graph_seeds:
                    edges, degrees, labels = make_graph(family, arguments.n, degree, graph_seed)
                    population_seed = [graph_seed, degree, arguments.n, family_codes[family], 771]
                    rng = np.random.default_rng(np.random.SeedSequence(population_seed))
                    covariate = rng.normal(size=arguments.n)
                    shocks = rng.normal(size=arguments.n)
                    folds = rng.permutation(np.arange(arguments.n)) % 3
                    graph_records.append({'family': family, 'degree_target': degree, 'graph_seed': graph_seed,
                                          'n': arguments.n, 'edges': len(edges),
                                          'mean_degree': float(degrees.mean()),
                                          'edge_sha256': hashlib.sha256(edges.tobytes()).hexdigest(),
                                          'population_seed_sequence': population_seed,
                                          'bernoulli_support_bound': support_bound(degrees)})
                    designs = ['bernoulli', 'cluster'] if family == 'sbm' and arguments.cluster else ['bernoulli']
                    for assignment_design in designs:
                        for repetition in range(arguments.repetitions):
                            seed_material = [graph_seed, degree, arguments.n, family_codes[family],
                                             repetition, 1 if assignment_design == 'bernoulli' else 2]
                            assignment_seed = int(np.random.SeedSequence(seed_material).generate_state(1, dtype=np.uint64)[0])
                            rng = np.random.default_rng(assignment_seed)
                            treatment = (rng.binomial(1, 0.5, size=arguments.n) if assignment_design == 'bernoulli'
                                         else rng.binomial(1, 0.5, size=20)[labels]).astype(float)
                            matrix, control, treated = features(edges, covariate, treatment)
                            pair = coupled_endpoint_check(matrix, covariate, shocks)
                            observed = study_outcomes(matrix, covariate, shocks)
                            controls = study_outcomes(control, covariate, shocks)
                            treateds = study_outcomes(treated, covariate, shocks)
                            columns = {'dim': [0, 1], 'linear_ols': [0, 1, 2, 3, 5, 6, 7],
                                       'quadratic_ols': list(range(8)), 'cv_ridge': list(range(8))}
                            models = {method: tuple(array[:, indices] for array in (matrix, control, treated))
                                      for method, indices in columns.items()}
                            models['oracle_bump'] = tuple(np.column_stack((array, bump_column(array)))
                                                          for array in (matrix, control, treated))
                            for world, outcome in observed.items():
                                for method, (design, endpoint_control, endpoint_treated) in models.items():
                                    replicate_record = {'family': family, 'degree_target': degree,
                                                        'assignment_design': assignment_design, 'world': world,
                                                        'method': method, 'repetition': repetition,
                                                        'true_gate': float(np.mean(treateds[world] - controls[world])),
                                                        'pair': pair, 'n': arguments.n,
                                                        'treated_count': int(treatment.sum()),
                                                        'independent_assignment_units': arguments.n if assignment_design == 'bernoulli' else 20}
                                    replicate_record['graph_seed'] = graph_seed
                                    replicate_record['assignment_seed'] = assignment_seed
                                    try:
                                        if method == 'dim' and np.unique(treatment).size != 2:
                                            raise ValueError('difference in means requires both arms')
                                        replicate_record.update(fitted_record(design, outcome, endpoint_control,
                                                                             endpoint_treated, folds,
                                                                             tune=method == 'cv_ridge'))
                                        replicate_record['status'] = 'completed'
                                    except (ValueError, np.linalg.LinAlgError, FloatingPointError) as error:
                                        replicate_record.update(status='failed', error=str(error))
                                    stream.write(json.dumps(replicate_record, allow_nan=False) + '\n')
                                    key = (family, degree, graph_seed, assignment_design, world, method)
                                    groups.setdefault(key, []).append(replicate_record)
                            stream.flush()
    summaries = []
    for key, records in groups.items():
        cell = dict(zip(['family', 'degree_target', 'graph_seed', 'assignment_design', 'world', 'method'], key))
        cell.update(summarize(records))
        summaries.append(cell)
    write_json(arguments.output / 'summary.json', summaries)
    import networkx as nx
    sources = {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
               for name in ['program.py', 'study.py', 'STUDY.md']}
    write_json(arguments.output / 'provenance.json', {
        'arguments': {key: str(value) if isinstance(value, Path) else value
                      for key, value in vars(arguments).items()},
        'versions': {'python': platform.python_version(), 'numpy': np.__version__,
                     'scipy': scipy.__version__, 'networkx': nx.__version__},
        'elapsed_seconds': time.perf_counter() - started, 'source_sha256': sources,
        'graphs': graph_records,
        'limitations': ['No public graph or paper generation in this optional runner.',
                        'Known-sigma intervals are not certified fixed-population randomization intervals.',
                        'Validation folds are node-wise, not independent network experiments.',
                        'RMSE Monte Carlo intervals use a delta approximation; coverage MCSE is binomial plug-in.',
                        'Graph seeds are separate fixed-population cells, not pooled independent node samples.']})


if __name__ == '__main__':
    main()
