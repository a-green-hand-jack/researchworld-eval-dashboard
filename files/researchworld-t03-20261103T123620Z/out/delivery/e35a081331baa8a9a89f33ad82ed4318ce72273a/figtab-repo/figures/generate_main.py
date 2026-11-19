"""Render main evidence after a complete analysis handoff; never uses pilot rows.

No analysis, interval calculation or result imputation occurs here. The script
requires the analysis-owned aggregate schema and complete aggregation manifest.
"""
import argparse
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import LogLocator, LogFormatterSciNotation, FixedLocator, FuncFormatter
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rendering import WIDTH_IN, METHOD_STYLE, paper_style, export_figure

ROOT = Path(__file__).resolve().parents[1]
KEYS = ['dataset', 'model', 'estimator', 'budget', 'background_size']
DATASET_NAMES = {'german': 'German', 'acs': 'ACSIncome', 'diabetes': 'Diabetes'}
MODEL_NAMES = {'logistic': 'LR', 'forest': 'RF', 'histboost': 'HGB'}


def truth(value):
    if value is True or value == 'True' or value == 'true' or value == 1:
        return True
    if value is False or value == 'False' or value == 'false' or value == 0:
        return False
    raise ValueError(f'Not an explicit boolean: {value!r}')


def verify_metric(frame, metric, config, *, repeats):
    required = set(KEYS + ['metric', 'estimate', 'ci_low', 'ci_high',
                          'n_instances', 'n_metric_instances', 'n_repeats',
                          'interval', 'boundary_adjusted'])
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f'Missing aggregate columns: {sorted(missing)}')
    selected = frame.loc[frame['metric'] == metric].copy()
    expected = {(d, m, e, b, config['background_size'])
                for d in config['datasets'] for m in config['models']
                for e in config['estimators'] for b in config['budgets'][d]}
    keys = list(selected[KEYS].itertuples(index=False, name=None))
    if len(set(keys)) != len(keys) or set(keys) != expected:
        raise ValueError(f'Duplicate/missing/extra configured cells for {metric}')
    if not ((selected['n_instances'] == config['n_instances']).all()
            and (selected['n_metric_instances'] == config['n_instances']).all()
            and (selected['n_repeats'] == repeats).all()):
        raise ValueError(f'Unresolved or changed metric denominator for {metric}; adapt display explicitly')
    values = selected[['estimate', 'ci_low', 'ci_high']].to_numpy(float)
    if not np.isfinite(values).all():
        raise ValueError(f'Nonfinite evidence for {metric}')
    if ((selected['ci_low'] > selected['estimate'])
            | (selected['ci_high'] < selected['estimate'])).any():
        raise ValueError(f'Intervals do not bracket displayed estimates for {metric}')
    # Retain the original CSV line number for panel-level traceability.
    selected['input_csv_line'] = selected.index + 2
    return selected


def load_evidence(results, config_path):
    paths = {name: results / name for name in ['aggregate_metrics.csv',
             'aggregate_repeatability.csv', 'aggregation_manifest.json',
             'reference_diagnostics.csv', 'run_metrics.parquet']}
    config = json.loads(config_path.read_text())
    if config.get('status') != 'frozen':
        raise ValueError('Main plotting requires the analysis-owned frozen configuration')
    manifest = json.loads(paths['aggregation_manifest.json'].read_text())
    n_cells = len(config['datasets']) * len(config['models'])
    n_refs = n_cells * config['n_instances']
    n_runs = sum(len(config['budgets'][d]) for d in config['datasets']) * len(config['models']) * len(config['estimators']) * config['n_instances'] * config['n_repeats']
    if (manifest['status'] != 'complete' or manifest['n_runs'] != n_runs
            or manifest['n_reference_inputs'] != n_refs or manifest['n_model_cells'] != n_cells
            or manifest['failed_runs_in_denominator'] != 0):
        raise ValueError('Main handoff is partial, inconsistent or needs explicit failure handling')
    if config['normalization_floor'] != .01 or config['primary_l1_cutoff'] != .2 or not np.isclose(config['primary_signed_topk_overlap'], 2/3):
        raise ValueError('Primary definition changed: revise captions before rendering')
    if not set(config['estimators']).issubset(METHOD_STYLE):
        raise ValueError('Unknown estimator requires a deliberate encoding')
    for d in config['datasets']:
        if d not in DATASET_NAMES:
            raise ValueError('Unknown dataset requires a display label')
    for m in config['models']:
        if m not in MODEL_NAMES:
            raise ValueError('Unknown fitted model requires a display label')
    refs = pd.read_csv(paths['reference_diagnostics.csv'])
    if (len(refs) != n_refs
            or not refs['reference_method'].eq('exact_empirical_coalition_enumeration').all()
            or not all(truth(v) for v in refs['exhaustive'])):
        raise ValueError('Exact-reference caption does not match the reference handoff')
    raw_status = pd.read_parquet(paths['run_metrics.parquet'],
                                 columns=['dataset', 'model', 'estimator', 'budget', 'repeat', 'exhaustive', 'status'])
    if len(raw_status) != n_runs or not raw_status['status'].eq('ok').all():
        raise ValueError('Run-status denominator disagrees with complete successful evidence')
    if any(truth(v) for v in raw_status['exhaustive']):
        raise ValueError('Main contains exhaustive calls: add explicit mixed/exact cell annotations before rendering')
    agg = pd.read_csv(paths['aggregate_metrics.csv'])
    pairs = pd.read_csv(paths['aggregate_repeatability.csv'])
    metrics = {metric: verify_metric(agg, metric, config, repeats=config['n_repeats'])
               for metric in ['joint_success_0p2', 'nl1_error', 'prediction_rows', 'cpu_seconds', 'wall_seconds']}
    metrics['pairwise_normalized_l1'] = verify_metric(pairs, 'pairwise_normalized_l1', config, repeats=1)
    return config, manifest, paths, metrics


def facet_figure(config, ylabel):
    nr, nc = len(config['datasets']), len(config['models'])
    fig, axes = plt.subplots(nr, nc, figsize=(WIDTH_IN, 1.55*nr + .7),
                             sharey=True, squeeze=False)
    for ri, dataset in enumerate(config['datasets']):
        for ci, model in enumerate(config['models']):
            ax = axes[ri, ci]
            ax.set_title(f'{DATASET_NAMES[dataset]} · {MODEL_NAMES[model]}', fontsize=9)
            ax.set_xscale('log')
            ax.xaxis.set_major_locator(LogLocator(numticks=3))
            ax.xaxis.set_major_formatter(LogFormatterSciNotation())
            ax.minorticks_off()
            ax.grid(axis='y', color='.88', linewidth=.5)
    fig.supylabel(ylabel, fontsize=9)
    return fig, axes


def readable_cost_ticks(ax):
    low, high = ax.dataLim.intervalx
    if low <= 0 or not np.isfinite([low, high]).all():
        raise ValueError('Invalid cost coordinate range')
    ticks = [low, high] if high/low < 4 else np.geomspace(low, high, 3)
    def label(v, pos):
        if v >= 1000:
            return f'{v/1000:.2g}k'
        return f'{v:.0f}' if v >= 1 else f'{v:.2g}'
    ax.xaxis.set_major_locator(FixedLocator(ticks))
    ax.xaxis.set_major_formatter(FuncFormatter(label))


def draw_series(ax, data, *, style, boundary=False):
    x = data['x_estimate'].to_numpy(float)
    y = data['estimate'].to_numpy(float)
    if np.any(x <= 0):
        raise ValueError('Actual log-axis cost must be strictly positive')
    error = np.vstack([y-data['ci_low'].to_numpy(float), data['ci_high'].to_numpy(float)-y])
    ax.errorbar(x, y, yerr=error, capsize=2, elinewidth=.8, **style)
    flags = np.array([truth(v) for v in data['boundary_adjusted']])
    if flags.any():
        if not boundary:
            raise ValueError('Boundary adjustment unexpectedly applied to unbounded error metric')
        ax.plot(x[flags], y[flags], '+', color='black', markersize=6, linestyle='none', zorder=6)


def map_rows(data, *, panel, file, xfile, metric):
    return {'panel': panel, 'metric': metric, 'file': file,
            'input_csv_lines': data['input_csv_line'].astype(int).tolist(),
            'x_file': xfile, 'x_input_csv_lines': data['x_input_csv_line'].astype(int).tolist(),
            'keys': data[KEYS].to_dict(orient='records'),
            'x_column': 'estimate (analysis-supplied mean actual cost)',
            'y_columns': ['estimate', 'ci_low', 'ci_high'],
            'interval_labels': data['interval'].tolist(),
            'boundary_adjusted': [truth(v) for v in data['boundary_adjusted']],
            'n_metric_instances': data['n_metric_instances'].astype(int).tolist(),
            'n_repeats': data['n_repeats'].astype(int).tolist()}


def join_cost(y, x):
    costs = x[KEYS + ['estimate', 'input_csv_line']].rename(columns={
        'estimate': 'x_estimate', 'input_csv_line': 'x_input_csv_line'})
    return y.merge(costs, on=KEYS, validate='one_to_one').sort_values('budget')


def render(config, paths, metrics, config_path, revision, command):
    n, r, b = config['n_instances'], config['n_repeats'], config['background_size']
    common = (f'For each fixed fitted model, {n} held-out inputs and {r} independent '
              f'runs per input, estimator and requested budget; background B={b}. '
              'The target is positive-class probability for the fixed empirical '
              'interventional game over grouped raw features. Estimates average '
              'equally over inputs and runs. Bars are analysis-supplied pointwise '
              '95% instance-cluster percentile intervals, conditional on the fitted '
              'model, split and background. Black plus markers identify observed '
              'all-zero/all-one panels whose displayed bars instead use the supplied '
              'two-sided 95% bounded-instance Hoeffding interval. These are observed '
              'rates and descriptive intervals, not population 95% adequacy certification. ')
    primary = ('One-run adequacy: normalized L1 error <=0.20 and signed top-3 overlap '
               '>=2/3 against the exact finite-game reference. L1 normalization is '
               'max(reference L1,0.01 probability units). ')
    specs = [
        ('one_run_budget', 'prediction_rows', 'Mean actual prediction rows per call',
         'One-run adequacy rate', [('joint_success_0p2', 'Reference adequacy')],
         primary + common + 'Horizontal positions are mean measured prediction rows; nominal budget equality does not imply equal actual work.'),
        ('budget_cpu', 'cpu_seconds', 'Mean measured CPU seconds per call',
         'One-run adequacy rate', [('joint_success_0p2', 'Reference adequacy')],
         primary + common + 'Horizontal positions are mean measured per-call process CPU time, excluding training and reference computation. CPU is the main timing comparison because recorded wall time contains severe execution interruptions.'),
        ('budget_time', 'wall_seconds', 'Recorded mean wall seconds per call (interrupted execution)',
         'One-run adequacy rate', [('joint_success_0p2', 'Reference adequacy')],
         primary + common + 'Horizontal positions are mean measured per-call wall time, excluding training and reference computation. Severe execution interruptions and shared-host scheduling are retained. These are execution records, not deployment-latency benchmarks or latency quantiles; use CPU/actual-row curves for efficiency comparison.'),
        ('error_repeatability', 'prediction_rows', 'Mean actual prediction rows per call',
         'Mean normalized L1 distance', [('nl1_error', 'Run versus reference'),
                                      ('pairwise_normalized_l1', 'Two-run disagreement')],
         'Run-reference error and two-run disagreement use the same denominator, max(exact-reference L1,0.01 probability units). '
         f'Run-reference distances average {r} runs per input; two-run distances average all distinct run pairs once per input, '
         f'then equally over {n} independent inputs. Supplied pointwise 95% instance-cluster percentile intervals are conditional '
         'on the fitted model, split and background. Two-run disagreement is not single-run accuracy; equality of the curves '
         'does not validate an explanation. Horizontal positions are mean measured prediction rows per single call. Both methods '
         f'target the same empirical interventional probability game over grouped raw features with B={b}.'),
    ]
    for stem, xmetric, xlabel, ylabel, curves, caption in specs:
        fig, axes = facet_figure(config, ylabel)
        mappings = []
        for ri, d in enumerate(config['datasets']):
            for ci, m in enumerate(config['models']):
                ax = axes[ri, ci]
                for ei, e in enumerate(config['estimators']):
                    for curve_index, (metric, _) in enumerate(curves):
                        frame = metrics[metric]
                        subset = frame[(frame.dataset == d) & (frame.model == m) & (frame.estimator == e)]
                        costs = metrics[xmetric]
                        subset = join_cost(subset, costs[(costs.dataset == d) & (costs.model == m) & (costs.estimator == e)])
                        style = dict(METHOD_STYLE[e])
                        if len(curves) > 1:
                            style['linestyle'] = '-' if curve_index == 0 else '--'
                        draw_series(ax, subset, style=style, boundary=len(curves) == 1)
                        mappings.append(map_rows(subset, panel=f'{d}/{m}/{e}',
                            file=str(paths['aggregate_repeatability.csv' if metric.startswith('pairwise_') else 'aggregate_metrics.csv'].relative_to(ROOT)),
                            xfile=str(paths['aggregate_metrics.csv'].relative_to(ROOT)), metric=metric))
                if len(curves) == 1:
                    ax.set_ylim(-.025, 1.025)
                    ax.set_yticks([0, .5, 1])
        for ax in axes.flat:
            readable_cost_ticks(ax)
        fig.supxlabel(xlabel, fontsize=9)
        handles = [Line2D([], [], label=e.title(), **METHOD_STYLE[e]) for e in config['estimators']]
        if len(curves) > 1:
            # Color/shape distinguish method, while line style distinguishes the distance.
            handles = [Line2D([], [], color=METHOD_STYLE[e]['color'], marker=METHOD_STYLE[e]['marker'],
                              linestyle='none', label=e.title()) for e in config['estimators']]
            handles += [Line2D([], [], color='.25', linestyle='-' if i == 0 else '--', label=name)
                        for i, (_, name) in enumerate(curves)]
        fig.legend(handles=handles, loc='outside upper center', ncol=2, frameon=False)
        caption_path = ROOT / f'figures/{stem}.caption.txt'
        # Plain caption source: the report owns the LaTeX wrapper and escaping.
        caption_path.write_text(caption+'\n')
        export_figure(fig, ROOT / f'figures/{stem}', root=ROOT,
                      inputs=[*paths.values(), config_path], analysis_revision=revision,
                      generator=Path(__file__), command=command,
                      panels=mappings, caption_path=caption_path)
        plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', type=Path, default=ROOT/'results')
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--analysis-revision', required=True)
    args = parser.parse_args()
    # Missing evidence fails before any output file is created.
    config, manifest, paths, metrics = load_evidence(args.results.resolve(), args.config.resolve())
    command = ('python3 figures/generate_main.py --results '+str(args.results.resolve().relative_to(ROOT))+
               ' --config '+str(args.config.resolve().relative_to(ROOT))+
               ' --analysis-revision '+args.analysis_revision)
    with paper_style():
        render(config, paths, metrics, args.config.resolve(), args.analysis_revision, command)
    print('Rendered main adequacy/work, adequacy/time and reference/repeatability displays from complete evidence.')


if __name__ == '__main__':
    main()
