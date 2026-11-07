"""Prepare condition, tolerance and instance views from complete main evidence.

Consumes analysis-owned estimates and intervals. No new interval, test, fitted
result or empirical adequacy classification is calculated here. ECDFs only sort
and count the supplied per-instance observed success rates.
"""
import argparse
from pathlib import Path
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import LogLocator, LogFormatterSciNotation
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_main import (ROOT, KEYS, DATASET_NAMES, MODEL_NAMES, load_evidence,
                           verify_metric, truth, join_cost)
from rendering import WIDTH_IN, METHOD_STYLE, paper_style, export_figure

STRATA = [('near_top1_tie', 'separated_top1'), ('low_signal', 'nonlow_signal')]
FLOORS = [.001, .01, .05]
SENSITIVITIES = [
    ('L1 cutoff', [('joint_success_0p1', '0.10'), ('joint_success_0p2', '0.20 (primary)'),
                   ('joint_success_0p4', '0.40')]),
    ('Selection rule', [('joint_success_0p2', 'Signed 2 of 3'),
                        ('strict_joint_success_0p2', 'Signed 3 of 3'),
                        ('tie_aware_joint_success_0p2', 'Tie-aware 2 of 3')]),
]
LINE_STYLES = ['-', '--', ':']


def read_csv(path):
    frame = pd.read_csv(path)
    frame['input_csv_line'] = frame.index + 2
    return frame


def verify_strata(frame, config):
    f = frame.loc[frame.metric == 'joint_success_0p2'].copy()
    expected = {(d, m, e, b, config['background_size'], s)
                for d in config['datasets'] for m in config['models']
                for e in config['estimators'] for b in config['budgets'][d]
                for pair in STRATA for s in pair}
    actual = list(f[KEYS + ['stratum']].itertuples(index=False, name=None))
    if len(actual) != len(expected) or set(actual) != expected:
        raise ValueError('Incomplete/duplicated prespecified stratum grid')
    for _, g in f.groupby(KEYS, sort=False):
        for pair in STRATA:
            subset = g[g.stratum.isin(pair)]
            if subset.n_instances.sum() != config['n_instances']:
                raise ValueError('Strata do not partition the explained inputs')
    for _, g in f.groupby(['dataset', 'model', 'stratum'], sort=False):
        if g.n_instances.nunique() != 1:
            raise ValueError('Reference-defined stratum n varies by budget/method')
    for _, row in f.iterrows():
        n = row.n_instances
        if n < 0 or n > config['n_instances'] or row.n_repeats != config['n_repeats']:
            raise ValueError('Unexpected stratum denominator')
        vals = np.array([row.estimate, row.ci_low, row.ci_high], float)
        if n == 0:
            if not np.isnan(vals).all():
                raise ValueError('Empty stratum must be unavailable, not zero')
        elif n == 1:
            if not np.isfinite(vals[0]) or not np.isnan(vals[1:]).all():
                raise ValueError('Singleton estimate requires unavailable interval')
        elif not (np.isfinite(vals).all() and vals[1] <= vals[0] <= vals[2]):
            raise ValueError('Invalid supplied stratum interval')
        elif row.n_metric_instances != n:
            raise ValueError('Stratum metric denominator differs from stratum n')
        if n and not 0 <= row.estimate <= 1:
            raise ValueError('Invalid stratum success rate')
    return f


def verify_instances(frame, config):
    key = KEYS + ['instance']
    expected = {(d, m, e, b, config['background_size'], i)
                for d in config['datasets'] for m in config['models']
                for e in config['estimators'] for b in config['budgets'][d]
                for i in range(config['n_instances'])}
    actual = list(frame[key].itertuples(index=False, name=None))
    if len(actual) != len(expected) or set(actual) != expected:
        raise ValueError('Incomplete/duplicated instance-success grid')
    if (not frame.n_repeats.eq(config['n_repeats']).all()
            or not frame.successes.between(0, config['n_repeats']).all()
            or not np.equal(frame.successes, np.floor(frame.successes)).all()
            or not np.allclose(frame.success_rate, frame.successes/frame.n_repeats)):
        raise ValueError('Instance-success denominator/count mismatch')
    for _, g in frame.groupby(['dataset', 'model', 'instance'], sort=False):
        if g.source_id.nunique() != 1:
            raise ValueError('Source identity changed across repetitions/budgets')
    return frame


def load_diagnostics(results, config_path):
    config, manifest, paths, metrics = load_evidence(results, config_path)
    paths.update({name: results/name for name in ['stratified_metrics.csv',
                  'floor_sensitivity.csv', 'instance_success.csv']})
    strata = verify_strata(read_csv(paths['stratified_metrics.csv']), config)
    instances = verify_instances(read_csv(paths['instance_success.csv']), config)
    agg = pd.read_csv(paths['aggregate_metrics.csv'])
    for _, specs in SENSITIVITIES:
        for name, _ in specs:
            if name not in metrics:
                metrics[name] = verify_metric(agg, name, config, repeats=config['n_repeats'])
    # Components retain their meaning: magnitude-only pass versus joint pass;
    # average overlaps are explicitly different from pass probabilities.
    for name in ['error_success_0p2', 'signed_topk_overlap', 'topk_overlap', 'absolute_l1_error']:
        metrics[name] = verify_metric(agg, name, config, repeats=config['n_repeats'])
    floor_frame = pd.read_csv(paths['floor_sensitivity.csv'])
    if set(floor_frame.normalization_floor) != set(FLOORS):
        raise ValueError('Unexpected normalization-floor scenarios')
    floors = {floor: verify_metric(floor_frame[floor_frame.normalization_floor == floor],
               'joint_success_0p2', config, repeats=config['n_repeats']) for floor in FLOORS}
    return config, paths, metrics, strata, instances, floors


def axes_grid(config, dataset, labels):
    fig, axes = plt.subplots(len(labels), len(config['models']),
        figsize=(WIDTH_IN, 1.72*len(labels)+.95), squeeze=False)
    for ri, label in enumerate(labels):
        for ci, model in enumerate(config['models']):
            ax = axes[ri, ci]
            ax.set_title(f'{MODEL_NAMES[model]} · {label}', fontsize=8.5)
            ax.grid(axis='y', color='.88', linewidth=.5)
            if ci:
                ax.tick_params(labelleft=False)
    bottom = .28 if len(labels)==1 else .17
    fig.get_layout_engine().set(rect=(0, bottom, 1, .88-bottom))
    fig.suptitle(DATASET_NAMES[dataset], fontsize=10, y=.97)
    return fig, axes


def log_cost_axes(axes):
    for ax in axes.flat:
        ax.set_xscale('log')
        ax.xaxis.set_major_locator(LogLocator(numticks=3))
        ax.xaxis.set_major_formatter(LogFormatterSciNotation())
        ax.minorticks_off()


def rate_axes(axes):
    for ax in axes.flat:
        ax.set_ylim(-.025, 1.025)
        ax.set_yticks([0, .5, 1])


def method_handles(config):
    return [Line2D([], [], color=METHOD_STYLE[e]['color'], marker=METHOD_STYLE[e]['marker'],
                   linestyle='none', label=e.title()) for e in config['estimators']]


def draw(ax, data, x, style):
    """Draw supplied intervals, leaving absent/singleton intervals absent."""
    data = data.sort_values('budget')
    xx = data[x].to_numpy(float)
    yy = data.estimate.to_numpy(float)
    available = data.n_instances.to_numpy() > 0
    if np.any(xx <= 0):
        raise ValueError('Log-axis cost/budget must be positive')
    # NaN is retained as a break in a line; never interpolate an empty stratum.
    ax.plot(xx, yy, **style)
    has_ci = available & data.ci_low.notna().to_numpy() & data.ci_high.notna().to_numpy()
    if has_ci.any():
        lo = yy[has_ci] - data.ci_low.to_numpy(float)[has_ci]
        hi = data.ci_high.to_numpy(float)[has_ci] - yy[has_ci]
        ax.errorbar(xx[has_ci], yy[has_ci], yerr=np.vstack([lo, hi]),
                    fmt='none', ecolor=style['color'], capsize=2, elinewidth=.8)
    flags = np.array([False if pd.isna(v) else truth(v) for v in data.boundary_adjusted])
    if flags.any():
        ax.plot(xx[flags], yy[flags], '+', color='black', markersize=6, linestyle='none', zorder=6)


def mapping(data, panel, file, x, **extra):
    return dict(panel=panel, file=str(file.relative_to(ROOT)),
        input_csv_lines=data.input_csv_line.astype(int).tolist(),
        keys=data[KEYS].to_dict(orient='records'), x_column=x,
        y_columns=['estimate', 'ci_low', 'ci_high'],
        n_instances=data.n_instances.astype(int).tolist(),
        interval=data.interval.fillna('unavailable').tolist(),
        **extra)


def export(fig, stem, caption, mappings, paths, config_path, revision, command):
    from generate_main import readable_cost_ticks
    for ax in fig.axes:
        if ax.get_xscale() == 'log' and not stem.startswith('conditions_'):
            readable_cost_ticks(ax)
    caption_path = ROOT/f'figures/{stem}.caption.txt'
    caption_path.write_text(caption+'\n')
    export_figure(fig, ROOT/f'figures/{stem}', root=ROOT, inputs=[*paths.values(), config_path, ROOT/'figures/generate_main.py'],
        analysis_revision=revision, generator=Path(__file__), command=command,
        panels=mappings, caption_path=caption_path)
    plt.close(fig)


def render_conditions(config, paths, strata, config_path, revision, command):
    for d in config['datasets']:
        fig, axes = axes_grid(config, d, ['Top-1 gap', 'Reference signal'])
        rate_axes(axes)
        mappings = []
        for ri, pair in enumerate(STRATA):
            for ci, m in enumerate(config['models']):
                ax = axes[ri, ci]
                counts = []
                for si, s in enumerate(pair):
                    cell = strata[(strata.dataset == d) & (strata.model == m) & (strata.stratum == s)]
                    counts.append(int(cell.n_instances.iloc[0]))
                    for e in config['estimators']:
                        frame = cell[cell.estimator == e].copy()
                        # Insufficient n rows deliberately have no boundary flag.
                        if 'boundary_adjusted' not in frame:
                            frame['boundary_adjusted'] = False
                        style = dict(METHOD_STYLE[e], linestyle=LINE_STYLES[si])
                        draw(ax, frame, 'budget', style)
                        mappings.append(mapping(frame, f'{d}/{m}/{s}/{e}', paths['stratified_metrics.csv'],
                            'budget (requested; not equal actual work)', stratum=s))
                ax.text(.03, .04, f'n: {counts[0]} / {counts[1]}', transform=ax.transAxes,
                        fontsize=8, bbox=dict(facecolor='white', edgecolor='none', alpha=.85))
                ax.set_xscale('log')
                ax.set_xticks(config['budgets'][d], [str(b) for b in config['budgets'][d]])
                ax.minorticks_off()
        handles = method_handles(config) + [
            Line2D([], [], color='.25', linestyle='-', label='Near tie / low signal'),
            Line2D([], [], color='.25', linestyle='--', label='Separated / other signal')]
        fig.legend(handles=handles, loc='lower center', bbox_to_anchor=(.5, .045), ncol=2, frameon=False)
        fig.supxlabel('Requested coalition-work budget (actual costs shown separately)', fontsize=8.5, y=.01)
        fig.supylabel('Observed one-run adequacy rate', fontsize=9)
        caption = (f'Reference-defined conditions for {DATASET_NAMES[d]}. Upper row: near-top-1 tie versus '
            'separated, using (largest minus second-largest absolute reference attribution)/max(reference L1,0.01) <=0.02. '
            'Lower row: low signal (reference L1 <0.01 probability units) versus other signal. '
            'Each panel labels independent-input counts in solid/dashed order; counts do not multiply across runs or budgets. '
            'Empty strata have no estimate; singleton strata show the observed estimate without an interval. '
            'Adequacy requires normalized L1 <=0.20 and signed top-3 overlap >=2/3. '
            'These descriptive strata are fixed by the exact reference, not selected using explanation performance. '
            'No main input has low signal, so that empty stratum is untested rather than a zero-success finding. Requested work labels do not compare equal actual work. '+interval_caption(config))
        export(fig, f'conditions_{d}', caption, mappings, paths, config_path, revision, command)


def interval_caption(config):
    return (f"Each input has {config['n_repeats']} independent runs per estimator/budget; the fixed "
        f"{config['background_size']}-row empirical interventional probability game uses grouped raw features. "
        'Bars are analysis-supplied pointwise 95% instance-cluster percentile intervals, conditional on the fitted '
        'model, split and background. Black plus markers denote observed all-zero/all-one panels using the supplied '
        'two-sided 95% bounded-instance Hoeffding interval instead. Interior intervals are descriptive approximations. '
        'No population >=0.95 or individual-input certification follows from the plotted rates.')


def render_sensitivity(config, paths, metrics, floors, config_path, revision, command):
    for d in config['datasets']:
        labels = ['L1 cutoff', 'Selection rule', 'Normalization floor']
        fig, axes = axes_grid(config, d, labels)
        rate_axes(axes)
        log_cost_axes(axes)
        mappings = []
        for ri, label in enumerate(labels):
            scenarios = SENSITIVITIES[ri][1] if ri < 2 else [(f, f'{f:g}') for f in FLOORS]
            for ci, m in enumerate(config['models']):
                ax = axes[ri, ci]
                for si, (metric, _) in enumerate(scenarios):
                    source = metrics[metric] if ri < 2 else floors[metric]
                    for e in config['estimators']:
                        select = lambda f: f[(f.dataset == d) & (f.model == m) & (f.estimator == e)]
                        frame = join_cost(select(source), select(metrics['prediction_rows']))
                        draw(ax, frame, 'x_estimate', dict(METHOD_STYLE[e], linestyle=LINE_STYLES[si]))
                        mappings.append(mapping(frame, f'{d}/{m}/{e}/{label}/{metric}',
                            paths['aggregate_metrics.csv' if ri < 2 else 'floor_sensitivity.csv'],
                            'estimate in matched prediction_rows aggregate', scenario=str(metric),
                            x_input_csv_lines=frame.x_input_csv_line.astype(int).tolist(),
                            x_file=str(paths['aggregate_metrics.csv'].relative_to(ROOT))))
                if ci == 0:
                    h = [Line2D([], [], color='.25', linestyle=LINE_STYLES[i], label=name)
                         for i, (_, name) in enumerate(scenarios)]
                    ax.legend(handles=h, loc='lower left', fontsize=7, framealpha=.85, handlelength=2)
        fig.legend(handles=method_handles(config), loc='lower center', bbox_to_anchor=(.5, .045), ncol=2, frameon=False)
        fig.supxlabel('Mean actual prediction rows per call', fontsize=9, y=.01)
        fig.supylabel('Observed adequacy rate for declared scenario', fontsize=9)
        caption = (f'Predeclared adequacy scenarios for {DATASET_NAMES[d]}; no scenario is selected after seeing the rates. '
            'Top row varies the normalized L1 cutoff (0.10/0.20/0.40), retaining signed top-3 overlap >=2/3 and floor 0.01. '
            'Middle row fixes cutoff 0.20/floor 0.01 and compares signed overlap >=2/3 (primary), all three matching signed '
            'features, and the analysis-defined 1e-6 probability-unit tie-aware selection rule. '
            'Bottom row varies normalization floor (0.001/0.01/0.05 probability units) in max(reference L1,floor), '
            'retaining cutoff 0.20 and the same primary signed-top-3 event. These floors change the metric, not the target '
            'or explanation calls. All main reference norms exceed 0.05, so these floor curves coincide; weak-signal behavior is untested. Curves use the same runs and are correlated. '+interval_caption(config))
        export(fig, f'metric_sensitivity_{d}', caption, mappings, paths, config_path, revision, command)


def render_components(config, paths, metrics, config_path, revision, command):
    specs = [
        ('Magnitude / joint pass', [('error_success_0p2', 'Magnitude only'),
                                    ('joint_success_0p2', 'Joint event')]),
        ('Mean top-3 overlap', [('topk_overlap', 'Unsigned'),
                               ('signed_topk_overlap', 'Signed')]),
        ('Absolute L1 error', [('absolute_l1_error', 'Reference error')]),
    ]
    for d in config['datasets']:
        fig, axes = axes_grid(config, d, [name for name, _ in specs])
        log_cost_axes(axes)
        mappings = []
        for ri, (label, curves) in enumerate(specs):
            upper = 0.
            for ci, m in enumerate(config['models']):
                ax = axes[ri, ci]
                for si, (metric, _) in enumerate(curves):
                    for e in config['estimators']:
                        select = lambda f: f[(f.dataset == d) & (f.model == m) & (f.estimator == e)]
                        frame = join_cost(select(metrics[metric]), select(metrics['prediction_rows']))
                        draw(ax, frame, 'x_estimate', dict(METHOD_STYLE[e], linestyle=LINE_STYLES[si]))
                        upper = max(upper, float(frame.ci_high.max()))
                        mappings.append(mapping(frame, f'{d}/{m}/{e}/{metric}',
                            paths['aggregate_metrics.csv'], 'estimate in matched prediction_rows aggregate',
                            metric=metric, x_input_csv_lines=frame.x_input_csv_line.astype(int).tolist(),
                            x_file=str(paths['aggregate_metrics.csv'].relative_to(ROOT))))
                if ci == 0 and len(curves) > 1:
                    ax.legend(handles=[Line2D([], [], color='.25', linestyle=LINE_STYLES[i], label=name)
                        for i, (_, name) in enumerate(curves)], loc='lower left', fontsize=7, framealpha=.85)
            # Common scale across fitted models within each row; absolute errors
            # remain in probability units rather than being rescaled to rates.
            for ax in axes[ri, :]:
                if ri < 2:
                    ax.set_ylim(-.025, 1.025)
                    ax.set_yticks([0, .5, 1])
                else:
                    ax.set_ylim(0, max(upper*1.08, 1e-6))
        axes[0, 0].set_ylabel('Observed rate')
        axes[1, 0].set_ylabel('Mean overlap')
        axes[2, 0].set_ylabel('Probability units')
        fig.legend(handles=method_handles(config), loc='lower center', bbox_to_anchor=(.5, .045), ncol=2, frameon=False)
        fig.supxlabel('Mean actual prediction rows per call', fontsize=9, y=.01)
        caption = (f'Accuracy components for {DATASET_NAMES[d]}. Upper row compares the normalized-magnitude '
            'pass probability (L1/max(reference L1,0.01) <=0.20) with the primary joint event, which additionally '
            'requires signed top-3 overlap >=2/3. Middle row gives mean unsigned and signed top-3 overlap '
            '(matching features or feature-sign tokens, divided by three); these are average overlaps, not pass '
            'probabilities. Lower row shows mean absolute L1 error against the exact reference in probability units, '
            'without division by the attribution norm. '+interval_caption(config))
        export(fig, f'accuracy_components_{d}', caption, mappings, paths, config_path, revision, command)


def render_instances(config, paths, instances, config_path, revision, command):
    for d in config['datasets']:
        fig, axes = axes_grid(config, d, ['Observed input rates'])
        mappings = []
        for ci, m in enumerate(config['models']):
            ax = axes[0, ci]
            for e in config['estimators']:
                for bi, b in enumerate(config['budgets'][d]):
                    frame = instances[(instances.dataset == d) & (instances.model == m)
                                      & (instances.estimator == e) & (instances.budget == b)]
                    vals = np.sort(frame.success_rate.to_numpy())
                    # Explicit domain endpoints make masses at zero and one visible.
                    xs = np.unique(np.r_[0., vals, 1.])
                    ys = np.searchsorted(vals, xs, side='right')/len(vals)
                    ax.step(xs, ys, where='post', color=METHOD_STYLE[e]['color'],
                            linestyle=LINE_STYLES[bi], linewidth=1.25)
                    ax.plot(xs, ys, linestyle='none', marker=METHOD_STYLE[e]['marker'],
                            markersize=3, color=METHOD_STYLE[e]['color'],
                            markevery=max(1, len(xs)//5))
                    ax.plot([0, 0], [0, ys[0]], color=METHOD_STYLE[e]['color'],
                            linestyle=LINE_STYLES[bi], linewidth=1.25)
                    mappings.append(dict(panel=f'{d}/{m}/{e}/{b}',
                        file=str(paths['instance_success.csv'].relative_to(ROOT)),
                        input_csv_lines=frame.input_csv_line.astype(int).tolist(),
                        source_ids=frame.source_id.astype(int).tolist(),
                        x_column='success_rate = successes / n_repeats',
                        y_transform='empirical fraction of input rates <= x, including endpoint masses',
                        n_instances=len(frame), n_repeats=config['n_repeats']))
            ax.set_xlim(-.02, 1.02)
            ax.set_ylim(-.025, 1.025)
            ax.set_xticks([0, .5, 1])
            ax.set_yticks([0, .5, 1])
        handles = method_handles(config)
        handles += [Line2D([], [], color='.25', linestyle=LINE_STYLES[i], label=f'Budget {b}')
                    for i, b in enumerate(config['budgets'][d])]
        fig.legend(handles=handles, loc='lower center', bbox_to_anchor=(.5, .045), ncol=3, frameon=False, fontsize=8)
        fig.supxlabel('Observed successes / independent runs for each input', fontsize=8.5, y=.01)
        fig.supylabel('Fraction of inputs at or below x', fontsize=9)
        caption = (f'Per-input heterogeneity for {DATASET_NAMES[d]}: empirical cumulative distribution of the '
            f"observed primary-event success fractions among {config['n_instances']} inputs per fitted model, "
            f"each measured with {config['n_repeats']} independent runs per estimator/budget. "
            'The event requires L1/max(exact-reference L1,0.01) <=0.20 and signed top-3 overlap >=2/3. '
            'Each input contributes once to each curve; vertical masses at zero/one are retained. '
            'Curves describe observed finite-run fractions, not the distribution of known true per-input success probabilities. '
            'There are no confidence bands or individual-input certifications: even no observed failures in these runs '
            'does not establish a 0.95 success probability. Budget labels are requested work, with actual-work/time '
            f"comparisons supplied separately. The fixed B={config['background_size']} empirical interventional "
            'probability game uses grouped raw features; split/model/background remain fixed.')
        export(fig, f'instance_distribution_{d}', caption, mappings, paths, config_path, revision, command)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--results', type=Path, default=ROOT/'results')
    p.add_argument('--config', type=Path, required=True)
    p.add_argument('--analysis-revision', required=True)
    args = p.parse_args()
    if len(args.analysis_revision) != 40 or any(c not in '0123456789abcdef' for c in args.analysis_revision):
        raise ValueError('Supply the verified full analysis revision')
    config_path, results = args.config.resolve(), args.results.resolve()
    config, paths, metrics, strata, instances, floors = load_diagnostics(results, config_path)
    command = ('python3 figures/generate_diagnostics.py --results '+str(results.relative_to(ROOT))+
               ' --config '+str(config_path.relative_to(ROOT))+' --analysis-revision '+args.analysis_revision)
    with paper_style():
        render_conditions(config, paths, strata, config_path, args.analysis_revision, command)
        render_sensitivity(config, paths, metrics, floors, config_path, args.analysis_revision, command)
        render_instances(config, paths, instances, config_path, args.analysis_revision, command)
        render_components(config, paths, metrics, config_path, args.analysis_revision, command)
    print('Rendered main condition, scenario and observed-input views; visual inspection is still required.')


if __name__ == '__main__':
    main()
