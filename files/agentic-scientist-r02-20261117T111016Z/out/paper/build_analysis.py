import datetime
import hashlib
import importlib.metadata
import json
import platform
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / 'figures'
METHODS = ('scaled_ilr', 'unscaled_ilr', 'simplex_linf', 'bonferroni')
LABELS = ('Scaled ILR', 'Unscaled ILR', 'Simplex max', 'Bonferroni')
REGIMES = ('LN_IID', 'DIR_IID', 'DIR_SHIFT')
REGIME_LABELS = ('Logistic-normal IID', 'Dirichlet IID', 'Dirichlet shift')
COLORS = ('#2864A0', '#169587', '#BF5938')
ALPHA_COLORS = ('#4D376B', '#8B68AC', '#BCA7CE')


def sidecar(path, kind='figure', notes='Derived only from retained final evaluation; no new research experiment.'):
    payload = {
        'schema_name': 'scientific-evidence.artifact-manifest',
        'artifact': {'path': str(path.relative_to(ROOT)), 'kind': kind,
                     'sha256': hashlib.sha256(path.read_bytes()).hexdigest()},
        'derived_from': ['@evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]',
                         '@evidence[[build_analysis.py]]'],
        'generated_by': {'script_path': 'build_analysis.py', 'command': ['python', 'build_analysis.py']},
        'notes': notes}
    Path(str(path) + '.prov.json').write_text(json.dumps(payload, indent=2))


def save_figure(figure, stem):
    figure.savefig(OUTPUT / (stem + '.pdf'), bbox_inches='tight')
    figure.savefig(OUTPUT / (stem + '.png'), bbox_inches='tight', dpi=300)
    for suffix in ('.pdf', '.png'):
        sidecar(OUTPUT / (stem + suffix))
    plt.close(figure)


def interval(values, indices):
    return np.quantile(np.asarray(values)[indices].mean(axis=1), [.025, .975], axis=0)


def main():
    OUTPUT.mkdir(exist_ok=True)
    Path('analysis').mkdir(exist_ok=True)
    payload = json.loads((ROOT / 'paper_data.json').read_text())
    evidence_anchor = '@evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]'
    episodes = payload['final_evaluation']['evaluation_evidence']['episodes']
    uncertainty = episodes[0]['solution']['seed_block_uncertainty']
    assert all(episode['solution']['seed_block_uncertainty'] == uncertainty for episode in episodes)
    cases = [case['case'] for case in episodes[0]['solution']['cases']]
    alphas = [record['alpha'] for record in episodes[0]['solution']['cases'][0]['methods']['scaled_ilr']]
    records = {(episode['seed'], case['case']): case for episode in episodes for case in episode['solution']['cases']}
    seeds = [episode['seed'] for episode in episodes]
    assert len(records) == len(seeds) * len(cases)
    assert all(case['complete'] for case in records.values())
    bootstrap_seed = 20261117
    indices = np.random.default_rng(bootstrap_seed).integers(0, len(seeds), size=(20000, len(seeds)))
    coverage = {case: np.array([[record['coverage'] for record in records[seed, case]['methods']['scaled_ilr']]
                                for seed in seeds]) for case in cases}
    summary = {'source': evidence_anchor, 'seeds': seeds, 'alphas': alphas, 'cases': cases,
               'bootstrap_seed': bootstrap_seed, 'bootstrap_draws': len(indices),
               'qualification': {key: payload['final_evaluation'][key] for key in ('status', 'outcome', 'correct')},
               'coverage': {}, 'methods': {}, 'paired_overall': {}}
    for case in cases:
        mean = coverage[case].mean(0)
        bounds = interval(coverage[case], indices)
        summary['coverage'][case] = [dict(alpha=alpha, mean=float(mean[index]),
                                         ci95=bounds[:, index].tolist()) for index, alpha in enumerate(alphas)]
    per_seed_utility = {}
    table = [r'\begin{tabular}{lrrrr}', r'\toprule',
             r'Method & IID error & Shift error & Mass & Utility [95\% interval] \\', r'\midrule']
    for method, label in zip(METHODS, LABELS):
        data = np.array([[[[record[field] for field in ('coverage_error', 'volume', 'utility')]
                            for record in records[seed, case]['methods'][method]] for case in cases] for seed in seeds])
        iid_indices = [index for index, case in enumerate(cases) if 'SHIFT' not in case]
        shift_indices = [index for index, case in enumerate(cases) if 'SHIFT' in case]
        values = dict(iid_error=float(data[:, iid_indices, :, 0].mean()),
                      shift_error=float(data[:, shift_indices, :, 0].mean()),
                      mass=float(data[:, :, :, 1].mean()), utility=float(data[:, :, :, 2].mean()))
        per_seed_utility[method] = data[:, :, :, 2].mean((1, 2))
        bounds = interval(per_seed_utility[method], indices).tolist()
        values['utility_ci95'] = bounds
        summary['methods'][method] = values
        table.append(f"{label} & {values['iid_error']:.4f} & {values['shift_error']:.4f} & {values['mass']:.4f} & "
                     f"{values['utility']:.4f} [{bounds[0]:.4f}, {bounds[1]:.4f}] " + r'\\')
    table.extend([r'\bottomrule', r'\end{tabular}'])
    Path('analysis/main_table.tex').write_text('\n'.join(table) + '\n')
    sidecar(ROOT / 'analysis/main_table.tex', 'table')
    for baseline in METHODS[1:]:
        difference = per_seed_utility['scaled_ilr'] - per_seed_utility[baseline]
        summary['paired_overall'][baseline] = {'mean': float(difference.mean()), 'ci95': interval(difference, indices).tolist()}
    summary['retained_uncertainty'] = uncertainty
    plt.rcParams.update({'font.size': 9, 'axes.titlesize': 10, 'axes.labelsize': 9,
                         'xtick.labelsize': 9, 'ytick.labelsize': 9,
                         'legend.fontsize': 8.5, 'axes.spines.top': False, 'axes.spines.right': False,
                         'pdf.fonttype': 42})
    figure, axes = plt.subplots(1, 2, figsize=(5.5, 2.55), sharex=True, sharey=True)
    order = np.argsort(1 - np.asarray(alphas))
    targets = 1 - np.asarray(alphas)
    for axis, dimension in zip(axes, (3, 8)):
        axis.plot([.79, .96], [.79, .96], '--', color='#999999', lw=1, label='Target')
        for regime, label, color in zip(REGIMES, REGIME_LABELS, COLORS):
            data = coverage[f'{regime}_K{dimension}']
            mean = data.mean(0)
            bounds = interval(data, indices)
            axis.errorbar(targets[order], mean[order], yerr=np.maximum(0, np.array([mean-bounds[0], bounds[1]-mean]))[:, order],
                          marker='o', markersize=4, capsize=2, color=color, label=label, lw=1.4)
        axis.set(title=f'$K={dimension}$', xlabel='Nominal coverage', xticks=[.8, .9, .95], ylim=(.57, .98))
        axis.grid(alpha=.18)
    axes[0].set_ylabel('Observed coverage (truncated axis)')
    handles, labels = axes[1].get_legend_handles_labels()
    figure.legend(handles, labels, loc='lower center', ncol=2, frameon=False, bbox_to_anchor=(.52, -.03))
    figure.tight_layout(rect=(0, .16, 1, 1))
    save_figure(figure, 'coverage_by_regime')
    figure, axes = plt.subplots(2, 2, figsize=(5.5, 4.2), sharex='col')
    for row, dimension in enumerate((3, 8)):
        for column, (field, bound_field, label) in enumerate((
            ('utility_difference', 'paired_seed_bootstrap95', r'$\Delta$ utility (positive favors ILR)'),
            ('volume_difference', 'paired_volume_bootstrap95', r'$\Delta$ mass (negative is smaller)'))):
            axis = axes[row, column]
            axis.axvline(0, color='#777777', lw=.8)
            for alpha_index, (alpha, color, marker) in enumerate(zip(alphas, ALPHA_COLORS, ('o', 's', '^'))):
                for regime_index, regime in enumerate(REGIMES):
                    result = uncertainty[f'{regime}_K{dimension}']['paired_baselines']['simplex_linf'][alpha_index]
                    mean = result[field]
                    low, high = result[bound_field]
                    axis.errorbar(mean, regime_index + (alpha_index-1)*.19,
                                  xerr=[[max(0, mean-low)], [max(0, high-mean)]], color=color, marker=marker,
                                  capsize=2, markersize=4, label=rf'$\alpha={alpha:.2f}$' if regime_index==0 else None)
            axis.set(yticks=range(3), yticklabels=['LN IID', 'Dir IID', 'Dir shift'], title=f'$K={dimension}$', xlabel=label)
            axis.invert_yaxis()
            axis.grid(axis='x', alpha=.18)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    figure.legend(handles, labels, loc='lower center', ncol=3, frameon=False, bbox_to_anchor=(.52, -.01))
    figure.tight_layout(rect=(0, .06, 1, 1), h_pad=1.0, w_pad=1.1)
    save_figure(figure, 'paired_region_tradeoffs')
    figure, axes = plt.subplots(1, 2, figsize=(5.5, 2.8), sharey=True)
    groups_summary = {}
    alpha_index = alphas.index(.1)
    for axis, dimension in zip(axes, (3, 8)):
        for group, color, label in ((0, '#815AAB', '$x_0>0$'), (1, '#71863B', r'$x_0\leq0$')):
            means, lows, highs = [], [], []
            for regime in REGIMES:
                case = f'{regime}_K{dimension}'
                data = np.array([records[seed, case]['methods']['scaled_ilr'][alpha_index]['subgroups'][group]['coverage'] for seed in seeds])
                mean = data.mean()
                low, high = interval(data, indices)
                means.append(mean); lows.append(mean-low); highs.append(high-mean)
                groups_summary[f'{case}_group{group}'] = {'mean': float(mean), 'ci95': [float(low), float(high)]}
            axis.errorbar(np.arange(3)+(group-.5)*.15, means, yerr=[lows, highs], color=color, marker='o',
                          capsize=2, lw=0, elinewidth=1.2, label=label)
        axis.axhline(.9, color='#999999', ls='--', lw=1)
        axis.set(title=f'$K={dimension}$', xticks=range(3), xticklabels=['LN IID', 'Dir IID', 'Dir shift'], ylim=(.5, 1))
        axis.tick_params(axis='x', rotation=15)
    axes[0].set_ylabel('Group coverage at nominal 0.90')
    handles, labels = axes[0].get_legend_handles_labels()
    figure.legend(handles, labels, loc='lower center', ncol=2, frameon=False)
    figure.tight_layout(rect=(0, .1, 1, 1))
    save_figure(figure, 'feature_group_reliability')
    summary['feature_groups_alpha_010'] = groups_summary
    Path('analysis/summary.json').write_text(json.dumps(summary, indent=2))
    sidecar(ROOT / 'analysis/summary.json', 'derived')
    extended = []
    for baseline, title in zip(METHODS[1:], LABELS[1:]):
        extended.extend([r'\begin{table}[p]', r'\centering\scriptsize',
                         r'\caption{Scaled ILR minus ' + title + r'. Descriptive paired 95\% intervals and adjusted utility endpoints are supplied by the evaluator. Mass intervals are unadjusted.}',
                         r'\begin{tabular}{llrrrrr}', r'\toprule',
                         r'Condition & $\alpha$ & $\Delta U$ & 95\% interval & Adjusted interval & $\Delta M$ & 95\% interval \\', r'\midrule'])
        for case in cases:
            case_label = case.replace('LN_IID_', 'LN ').replace('DIR_IID_', 'Dir ').replace('DIR_SHIFT_', 'Shift ')
            for result in uncertainty[case]['paired_baselines'][baseline]:
                bounds = result['paired_seed_bootstrap95']; adjusted = result['bonferroni54_bootstrap_interval']; mass = result['paired_volume_bootstrap95']
                extended.append(f"{case_label} & {result['alpha']:.2f} & {result['utility_difference']:+.3f} & [{bounds[0]:+.3f},{bounds[1]:+.3f}] & "
                                f"[{adjusted[0]:+.3f},{adjusted[1]:+.3f}] & {result['volume_difference']:+.3f} & [{mass[0]:+.3f},{mass[1]:+.3f}] " + r'\\')
        extended.extend([r'\bottomrule', r'\end{tabular}', r'\end{table}'])
    Path('analysis/complete_comparisons.tex').write_text('\n'.join(extended)+'\n')
    sidecar(ROOT / 'analysis/complete_comparisons.tex', 'table')
    coverage_table = [r'\begin{table}[p]', r'\centering\small',
                      r'\caption{Scaled-ILR results by condition. Coverage intervals resample seed blocks; mass and utility are empirical means.}',
                      r'\begin{tabular}{llrrrr}', r'\toprule',
                      r'Condition & $\alpha$ & Coverage & 95\% interval & Mass & Utility \\', r'\midrule']
    for case in cases:
        for alpha_index, alpha in enumerate(alphas):
            result = summary['coverage'][case][alpha_index]
            mass = np.mean([records[seed, case]['methods']['scaled_ilr'][alpha_index]['volume'] for seed in seeds])
            utility = np.mean([records[seed, case]['methods']['scaled_ilr'][alpha_index]['utility'] for seed in seeds])
            label = case.replace('LN_IID_', 'LN ').replace('DIR_IID_', 'Dir ').replace('DIR_SHIFT_', 'Shift ')
            coverage_table.append(f"{label} & {alpha:.2f} & {result['mean']:.4f} & [{result['ci95'][0]:.4f},{result['ci95'][1]:.4f}] & {mass:.4f} & {utility:.4f} " + r'\\')
    coverage_table.extend([r'\bottomrule', r'\end{tabular}', r'\end{table}'])
    Path('analysis/coverage_table.tex').write_text('\n'.join(coverage_table)+'\n')
    sidecar(ROOT / 'analysis/coverage_table.tex', 'table')
    concept = OUTPUT / 'composition_reliability_overview.png'
    prompt_log = OUTPUT / 'composition_reliability_overview.prompts.json'
    rendered = (ROOT / '.concept_figure_complete').exists() or (prompt_log.exists() and prompt_log.read_text().strip() not in ('', '{}'))
    if not rendered and not concept.exists():
        placeholder = Image.new('RGB', (1650, 440), 'white')
        draw = ImageDraw.Draw(placeholder)
        draw.text((100, 195), 'Conceptual overview: training-only fitting | independent calibration | reliability and reference mass', fill='#444444')
        placeholder.save(concept)
        prompt_log.write_text('{}\n')
    figures = []
    configurations = [
        ('composition_reliability_overview', 'diagram', 3, 'generate-concept-figure'),
        ('coverage_by_regime', 'composite', 2, 'matplotlib'),
        ('paired_region_tradeoffs', 'composite', 4, 'matplotlib'),
        ('feature_group_reliability', 'composite', 2, 'matplotlib')]
    for stem, kind, panels, generator in configurations:
        entry = {'figure_id': stem, 'figure_type': kind,
                 'files': {'png': f'figures/{stem}.png'}, 'panel_count': panels,
                 'panels': [{'panel_id': str(index+1), 'category_count': 3,
                             'series_count': (1 if generator == 'generate-concept-figure' else
                                              4 if stem == 'coverage_by_regime' else
                                              2 if stem == 'feature_group_reliability' else 3)} for index in range(panels)],
                 'uses_progression': False, 'generator': generator,
                 'source_ids': ['final.evidence.episodes'], 'placement': 'full_width',
                 'intended_latex_width_fraction': .98, 'estimated_min_rendered_font_pt': 8.2,
                 'min_font_size_pt': 9 if generator == 'generate-concept-figure' else 8.5}
        if generator == 'matplotlib':
            entry['files']['pdf'] = f'figures/{stem}.pdf'
        else:
            entry['prompt_log_path'] = f'figures/{stem}.prompts.json'
        figures.append(entry)
    Path('figure_manifest.json').write_text(json.dumps({'figures': figures}, indent=2))
    environment = {'python': sys.version, 'numpy': np.__version__, 'matplotlib': matplotlib.__version__,
                   'platform': platform.platform(), 'analysis_timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    versions = {package: importlib.metadata.version(package) for package in
                ('numpy', 'matplotlib', 'pillow', 'requests', 'jsonschema', 'pymupdf')}
    environment['dependencies'] = versions
    Path('analysis/environment.json').write_text(json.dumps(environment, indent=2))
    Path('analysis/requirements.txt').write_text(''.join(package+'=='+version+'\n' for package, version in versions.items()))
    print(json.dumps({'methods': summary['methods'], 'paired_overall': summary['paired_overall'],
                      'coverage': summary['coverage'], 'groups': groups_summary}, indent=2))


if __name__ == '__main__':
    main()
