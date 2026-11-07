"""Entry point: configuration, hyperparameters and experiment runner."""
import json

import numpy as np

from experiments import run_experiment
from experiment_config import CONDITIONS

HYPERPARAMETERS = {
    'seeds': [0, 1, 2],
    'time_budget_sec': 3600,
    'time_guard_frac': 0.80,
    'top_m': 8,                     # adjacent pairs among top-m ranked participants
    'bt_l2': 1e-4,
    'bt_max_iter': 40,
    'bt_tol': 1e-6,
    'n_bootstrap': 30,              # iid bootstrap replicates
    'random_flip_reps': 3,          # reps for random-flip budget
    'random_grid_points': 10,
    'max_budget_frac': 0.40,        # never edit more than this fraction of N
    'adv_batch_small': 1,
    'adv_k_exact_max': 10,
    'adv_batch_large': 10,
    'subsample_fracs': [0.5, 1.0],
    'tost_margin_log': 0.35,
    'rho_threshold_h2': 0.7,
    'mag_miscal_threshold_h2': 5.0,
    'adv_vs_rand_ratio_threshold_h2': 10.0,
    'h3_ratio_A_over_B': 3.0,
    'h3_ratio_C_over_B': 5.0,
    'h3_design_effect': 3.0,
    'h3_cluster_ci_ratio': 1.3,
    'min_pairs': 12,
    'min_comparisons_per_model': 20,
    'use_real_data': True,
    'data_dir': './data',
    'h3_reps': 12,
    'tie_handling': 'half',
    'nba_year_min': 2005,
    'nba_year_max': 2015,
    'nba_home_advantage': True,
    # total budget is split evenly over (dataset, condition, seed) runs; this is
    # the maximum any single run may take, a floor keeps tiny runs meaningful.
    'per_run_cap_sec': 40,
    'per_run_floor_sec': 4,
    # cap on records per dataset used in the flip-budget search (CPU budget)
    'max_records_search': 3000,
    # maximum number of adjacent pairs evaluated per run (<= top_m - 1)
    'max_pairs_per_run': 7,
}


def _jsonable(obj):
    """Recursively convert numpy types / non-finite floats into JSON-safe values."""
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return _jsonable(obj.tolist())
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, (float, np.floating)):
        v = float(obj)
        return v if np.isfinite(v) else None
    return obj


def _report_success_diagnostics(results):
    """Print per-condition success-rate diagnostics (fraction of pairs flipped within cap)."""
    print('\nSuccess-rate diagnostics (fraction of adjacent pairs flipped within cap):')
    for cond in CONDITIONS:
        agg = results.get('agg', {}).get(cond)
        if agg is None:
            continue
        print('  %-45s success_rate_mean=%.3f n_runs=%d'
              % (cond, agg['success_rate'], agg['n']))
        per_ds = results.get('success', {}).get(cond, {})
        for dname, vals in per_ds.items():
            finite = [v for v in vals if v is not None and np.isfinite(v)]
            if finite:
                print('      %-22s %.3f' % (dname, float(np.mean(finite))))


def main():
    results = run_experiment(HYPERPARAMETERS)
    print('\nDataset status:')
    for k, v in results['status'].items():
        print('  %-22s %s' % (k, v))
    _report_success_diagnostics(results)
    print('\nElapsed: %.1fs  stopped_early=%s' % (results['elapsed_sec'],
                                                  results['stopped_early']))
    with open('results.json', 'w') as fh:
        json.dump(_jsonable(results), fh, indent=2)
    print('Wrote results.json')


if __name__ == '__main__':
    main()