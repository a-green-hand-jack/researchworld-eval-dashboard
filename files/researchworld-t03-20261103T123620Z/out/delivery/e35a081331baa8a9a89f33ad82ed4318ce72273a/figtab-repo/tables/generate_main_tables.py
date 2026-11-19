"""Format complete analysis-owned coverage, ambiguity and compute records.

No fitted result, inference, exclusion or new reliability estimate is made.
Execution on the actual main handoff is required before accepting any output.
"""
import argparse
import json
from pathlib import Path
import platform
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'figures'))
from rendering import file_record

DATASET_NAMES = {'german': 'German', 'acs': 'ACSIncome', 'diabetes': 'Diabetes'}
MODEL_NAMES = {'logistic': 'LR', 'forest': 'RF', 'histboost': 'HGB'}


def read_frame(path):
    frame = pd.read_csv(path)
    frame['input_csv_line'] = frame.index + 2
    return frame


def emit_table(stem, caption, headings, rows, rowmap, provenance, command):
    path = ROOT / f'tables/{stem}.tex'
    label = 'tab:' + stem.replace('_', '-')
    # All dynamic labels are from the closed dictionaries above; numbers are
    # formatted below. No arbitrary data strings are inserted into TeX.
    lines = [r'\begin{table}[tb]', r'\centering', r'\caption{' + caption + '}',
             r'\label{' + label + '}', r'\small',
             r'\begin{tabular}{' + 'll' + 'r'*(len(headings)-2) + '}',
             r'\toprule', ' & '.join(headings) + r' \\', r'\midrule']
    lines += [' & '.join(row) + r' \\' for row in rows]
    lines += [r'\bottomrule', r'\end{tabular}', r'\end{table}', '']
    path.write_text('\n'.join(lines))
    manifest = dict(provenance, artifact=path.name, command=command,
                    row_mapping=rowmap, outputs=[file_record(path, ROOT)],
                    inspection='Pending actual rendering and integrated-PDF checks')
    (ROOT / f'tables/{stem}.manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')


def load_complete(results, config_path):
    config = json.loads(config_path.read_text())
    if config.get('status') != 'frozen':
        raise ValueError('Tables require the actual frozen analysis configuration')
    paths = [results / name for name in ['aggregation_manifest.json', 'panel_audit.json',
             'model_diagnostics.csv', 'assessability_counts.csv', 'job_costs.csv',
             'reference_diagnostics.csv']]
    manifest, audit = [json.loads(p.read_text()) for p in paths[:2]]
    expected = {(d, m) for d in config['datasets'] for m in config['models']}
    nrefs = len(expected) * config['n_instances']
    nruns = sum(len(config['budgets'][d]) for d in config['datasets']) * len(config['models']) * len(config['estimators']) * config['n_instances'] * config['n_repeats']
    for record in [manifest, audit]:
        if (record['status'] != 'complete' or record['n_model_cells'] != len(expected)
                or record['n_reference_inputs'] != nrefs or record['n_runs'] != nruns):
            raise ValueError('Incomplete or mismatched scientific matrix')
    if manifest['signature'] != audit['signature']:
        raise ValueError('Audit and aggregate source identities disagree')
    models, assess, jobs, refs = [read_frame(p) for p in paths[2:]]
    observed = list(models[['dataset', 'model']].itertuples(index=False, name=None))
    if len(observed) != len(expected) or set(observed) != expected:
        raise ValueError('Predictive diagnostics do not cover exactly the configured cells')
    if len(refs) != nrefs or not refs.reference_method.eq('exact_empirical_coalition_enumeration').all():
        raise ValueError('The exact-reference table description needs revision')
    if set(jobs.cell) != {f'{d}_{m}' for d, m in expected} or len(jobs) != len(expected):
        raise ValueError('Missing/duplicate completed-job accounting')
    if not jobs.status.eq('complete').all() or not jobs.n_completed.eq(config['n_instances']).all():
        raise ValueError('An incomplete job cannot be formatted as completed evidence')
    return config, paths, manifest, audit, models, assess, jobs, refs


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--results', type=Path, default=ROOT/'results')
    p.add_argument('--config', type=Path, required=True)
    p.add_argument('--analysis-revision', required=True)
    args = p.parse_args()
    revision = args.analysis_revision
    if len(revision) != 40 or any(c not in '0123456789abcdef' for c in revision):
        raise ValueError('Supply the verified full analysis revision')
    config, paths, manifest, audit, models, assess, jobs, refs = load_complete(args.results.resolve(), args.config.resolve())
    command = ('python3 tables/generate_main_tables.py --results '+str(args.results.resolve().relative_to(ROOT))+
               ' --config '+str(args.config.resolve().relative_to(ROOT))+' --analysis-revision '+revision)
    provenance = {'schema_version': 1, 'analysis_revision': revision,
                  'source_signature': manifest['signature'],
                  'inputs': [file_record(x, ROOT) for x in [*paths, args.config.resolve()]],
                  'generator': file_record(Path(__file__), ROOT),
                  'supporting_code': [file_record(ROOT/'figures/rendering.py', ROOT)],
                  'versions': {'python': platform.python_version(), 'pandas': pd.__version__}}
    coverage, ambiguity, costs = [], [], []
    covmap, ambmap, costmap = [], [], []
    stable_counts = ['n_instances', 'n_runs', 'n_exact_references', 'n_failed_runs',
                     'n_unresolved_references', 'n_top1_numerical_ties',
                     'n_topk_boundary_numerical_ties', 'n_selected_sign_ambiguous',
                     'n_low_signal', 'n_active_sign_assessable', 'primary_denominator']
    for d in config['datasets']:
        for m in config['models']:
            label = [DATASET_NAMES[d], MODEL_NAMES[m]]
            md = models[(models.dataset == d) & (models.model == m)].iloc[0]
            coverage.append(label + [str(int(md[k])) for k in ['n_train', 'n_test', 'n_features']]
                            + [format(float(md[k]), '.3f') for k in ['roc_auc', 'accuracy']])
            covmap.append({'dataset': d, 'model': m, 'file': 'model_diagnostics.csv',
                           'input_csv_line': int(md.input_csv_line),
                           'columns': ['n_train', 'n_test', 'n_features', 'roc_auc', 'accuracy'],
                           'format': 'counts as integers; quality metrics .3f'})
            ac = assess[(assess.dataset == d) & (assess.model == m)]
            expected_keys = {(e, b, config['background_size']) for e in config['estimators']
                             for b in config['budgets'][d]}
            actual_keys = list(ac[['estimator', 'budget', 'background_size']].itertuples(index=False, name=None))
            if len(actual_keys) != len(expected_keys) or set(actual_keys) != expected_keys:
                raise ValueError('Assessability grid missing/duplicated')
            if any(ac[k].nunique(dropna=False) != 1 for k in stable_counts):
                raise ValueError('Counts differ by method/budget: present those cells separately')
            ar = ac.iloc[0]
            if (ar.n_instances != config['n_instances'] or ar.n_exact_references != config['n_instances']
                    or ar.n_runs != config['n_instances']*config['n_repeats']
                    or ar.n_failed_runs != 0 or ar.n_unresolved_references != 0):
                raise ValueError('Explicit failure/unresolved reporting needs an adapted table')
            count_columns = ['n_exact_references', 'n_top1_numerical_ties',
                             'n_topk_boundary_numerical_ties', 'n_selected_sign_ambiguous',
                             'n_low_signal', 'n_active_sign_assessable']
            ambiguity.append(label + [str(int(ar[k])) for k in count_columns])
            ambmap.append({'dataset': d, 'model': m, 'file': 'assessability_counts.csv',
                           'input_csv_lines': ac.input_csv_line.astype(int).tolist(),
                           'columns': count_columns,
                           'display': 'one row only after verifying identical reference counts across budgets/estimators; none summed',
                           'primary_denominator': ar.primary_denominator})
            job = jobs[jobs.cell == f'{d}_{m}'].iloc[0]
            reference_rows = refs[(refs.dataset == d) & (refs.model == m)]
            if len(reference_rows) != config['n_instances']:
                raise ValueError('Reference cost count does not match the panel')
            ref_cpu_minutes = float(reference_rows.cpu_seconds.sum())/60
            costs.append(label + [format(float(job.process_total_cpu_seconds)/60, '.2f'),
                                  format(float(job.wall_seconds)/60, '.2f'),
                                  format(ref_cpu_minutes, '.3f'),
                                  format(float(job.peak_process_rss_kib)/1024, '.0f')])
            costmap.append({'dataset': d, 'model': m,
                            'job_csv_line': int(job.input_csv_line),
                            'reference_csv_lines': reference_rows.input_csv_line.astype(int).tolist(),
                            'columns': ['process_total_cpu_seconds', 'wall_seconds', 'cpu_seconds', 'peak_process_rss_kib'],
                            'conversions': 'job/reference seconds to minutes; per-cell reference CPU summed for accounting; KiB/1024 to MiB'})
    (ROOT/'tables').mkdir(exist_ok=True)
    scope = (f"The complete handoff contains {manifest['n_model_cells']} fitted-model cells, "
             f"{config['n_instances']} non-pilot explained inputs per cell, "
             f"{config['n_repeats']} independent runs per estimator/budget/input and "
             f"a fixed {config['background_size']}-row training background. ")
    emit_table('study_coverage', scope +
        'Predictive quality is measured on the held-out split; features are grouped raw players. '
        'LR, RF and HGB denote logistic regression, random forest and histogram gradient boosting. '
        'These fitted-model diagnostics do not estimate attribution reliability.',
        ['Dataset', 'Model', 'Train', 'Test', 'Features', 'AUROC', 'Accuracy'],
        coverage, covmap, provenance, command)
    emit_table('reference_assessability', scope +
        'Reference-defined caution counts; counts are per input and are identical across the method/budget cells, not summed across them. '
        'All exact-reference inputs remain in the primary event denominator, including ties and weak signals. '
        'Numerical top-1 and top-3-boundary ties use the supplied twice-coordinate tolerance; selected near-zero signs use the coordinate tolerance. '
        'Weak signal means reference L1 below 0.01 probability units; active-sign counts identify inputs with at least one active sign. '
        f"The declared coordinate tolerance is {config['sign_tie_tolerance']:.0e} probability units. "
        'No unresolved reference or failed final call is present in this complete handoff.',
        ['Dataset', 'Model', 'Exact', 'Top-1 ties', 'Top-3 ties', 'Near zero', 'Weak', 'Active'],
        ambiguity, ambmap, provenance, command)
    emit_table('main_compute',
        'Measured completed-job costs, separate from the initial pilot and resource projections. '
        'CPU and wall columns give the successful completion process time; reference CPU sums all saved exact-reference call timings. '
        'These scopes overlap and must not be added. A resumed process can exclude earlier work, which belongs in the full research compute ledger alongside pilots and failed attempts. '
        'Peak memory is the completion-process peak RSS. '
        f"The independent saved-panel audit records {audit['recorded_failed_attempts']} failed attempts, "
        f"{audit['warning_messages']} warning messages and {audit['exhaustive_stochastic_calls']} exhaustive calls among the nominally stochastic runs; "
        'those counts must accompany any final efficiency or stochastic-method claim. Severe execution interruptions contaminate wall times; they are preserved execution records, not deployment-latency benchmarks. Use CPU and actual rows for efficiency comparisons. Runtime excludes untracked organizational work and is not a per-call latency quantile.',
        ['Dataset', 'Model', 'CPU min', 'Wall min', 'Ref. CPU min', 'Peak MiB'],
        costs, costmap, provenance, command)
    print('Formatted measured coverage, reference caution counts and compute tables; inspect actual renders before delivery.')


if __name__ == '__main__':
    main()
