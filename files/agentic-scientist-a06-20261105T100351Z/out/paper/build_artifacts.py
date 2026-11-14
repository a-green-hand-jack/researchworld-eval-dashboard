import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parent
plt.rcParams.update({'font.size': 9, 'axes.labelsize': 9, 'axes.titlesize': 9,
                     'xtick.labelsize': 8.5, 'ytick.labelsize': 8.5,
                     'legend.fontsize': 8.5, 'font.family': 'DejaVu Sans',
                     'axes.spines.top': False, 'axes.spines.right': False,
                     'pdf.fonttype': 42})
COLORS = ['#147D92', '#C45B26', '#635A9B']
METHODS = ['report_mse', 'reuse_mse', 'full_budget_naive_mse',
           'honest_half_mse', 'fixed_prompt_mse', 'random_prompt_mse']


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2) + '\n')


def provenance(path, kind='derived'):
    write_json(str(path) + '.prov.json', {
        'schema_name': 'scientific-evidence.artifact-manifest',
        'artifact': {'path': str(path), 'kind': kind,
                     'sha256': hashlib.sha256(Path(path).read_bytes()).hexdigest()},
        'derived_from': ['@evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]',
                         '@evidence[[source_evidence/evaluate_final.py#L746]]'],
        'generated_by': {'script_path': 'build_artifacts.py',
                         'command': ['python', 'build_artifacts.py']}})


def save_figure(figure, figure_id):
    for extension in ['pdf', 'png']:
        path = Path('figures') / (figure_id + '.' + extension)
        figure.savefig(path, dpi=300, bbox_inches='tight', pad_inches=0.025)
        provenance(path, 'figure')
    plt.close(figure)


def manifest_entry(figure_id, figure_type, panels, rows, categories, series):
    return {'figure_id': figure_id, 'figure_type': figure_type,
            'path_pdf': f'figures/{figure_id}.pdf', 'path_png': f'figures/{figure_id}.png',
            'generator': 'matplotlib', 'n_panels': panels, 'panels_per_row': rows,
            'categories_per_panel': categories, 'series_per_panel': series,
            'max_label_chars': 35, 'font_sizes': {'title': 9, 'axis': 9, 'ticks': 8.5, 'legend': 8.5},
            'uses_abbrev_labels': True, 'uses_progression': False,
            'placement': 'full_width', 'intended_latex_width_fraction': 1.0,
            'estimated_min_rendered_font_pt': 8.5,
            'source_ids': ['final.evidence.episodes']}


def main():
    Path('figures').mkdir(exist_ok=True)
    Path('tables').mkdir(exist_ok=True)
    Path('analysis').mkdir(exist_ok=True)
    # @evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]
    paper_data = json.loads(Path('paper_data.json').read_text())
    episodes = paper_data['final_evaluation']['evaluation_evidence']['episodes']
    cases = [{**case, 'seed': episode['seed']} for episode in episodes for case in episode['solution']['cases']]
    labels = [case['case'] for case in episodes[0]['solution']['cases']]
    means = {label: {metric: float(np.mean([case['metrics'][metric] for case in cases if case['case'] == label]))
                     for metric in cases[0]['metrics']} for label in labels}
    regimes = {}
    for regime in range(len(cases[0]['details'])):
        regimes[str(regime)] = {}
        for label in [label for label in labels if label.startswith('S')]:
            regimes[str(regime)][label] = {metric: float(np.mean([case['details'][regime]['metrics'][metric]
                                                                for case in cases if case['case'] == label]))
                                          for metric in cases[0]['metrics']}
    audit = [{ 'seed': case['seed'], 'case': case['case'],
               'difference': case['details'][0]['target'] - case['details'][0]['fixed'][1],
               'interval': case['details'][0]['paired_subject_bootstrap_interval'],
               'target': case['details'][0]['target'], 'fixed': case['details'][0]['fixed'][1]}
             for case in cases if case['case'].startswith('R')]
    summary = {'condition_means': means, 'regime_means': regimes, 'audit_differences': audit,
               'episode_durations_seconds': [episode['duration_seconds'] for episode in episodes],
               'duration_sum_seconds': sum(episode['duration_seconds'] for episode in episodes),
               'reductions_percent': {label: 100 * (1 - means[label]['report_mse'] / means[label]['reuse_mse'])
                                      for label in labels},
               'seed_count': len(episodes)}
    write_json('analysis/summary.json', summary)
    provenance('analysis/summary.json')
    with Path('analysis/condition_results.csv').open('w') as output:
        writer = csv.DictWriter(output, fieldnames=['seed', 'case'] + list(cases[0]['metrics']))
        writer.writeheader()
        writer.writerows({'seed': case['seed'], 'case': case['case'], **case['metrics']} for case in cases)
    provenance('analysis/condition_results.csv')
    with Path('analysis/regime_results.csv').open('w') as output:
        fields = ['seed', 'case', 'regime', 'report_mse_standard_error'] + list(cases[0]['metrics'])
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows({'seed': case['seed'], 'case': case['case'], 'regime': detail['regime'],
                         'report_mse_standard_error': detail['report_mse_standard_error'], **detail['metrics']}
                        for case in cases if case['case'].startswith('S') for detail in case['details'])
    provenance('analysis/regime_results.csv')
    figure, axes = plt.subplots(2, 2, figsize=(5.5, 3.15), sharex=True, sharey='row')
    for row, family in enumerate(['S', 'R']):
        for column, size in enumerate([64, 256]):
            axis = axes[row, column]
            for method_index, metric in enumerate(METHODS[:3]):
                offset = (method_index - 1) * 0.16
                for arm_index, arms in enumerate([1, 16]):
                    label = f'{family}{size}K{arms}'
                    observations = [case['metrics'][metric] * 1000 for case in cases if case['case'] == label]
                    axis.scatter(arm_index + offset + np.linspace(-0.025, 0.025, len(observations)), observations,
                                 color=COLORS[method_index], alpha=0.35, s=12, linewidths=0)
                    axis.plot(arm_index + offset, np.mean(observations), marker=['o', 's', 'D'][method_index],
                              color=COLORS[method_index], markersize=4.8,
                              label=['Protected', 'Selection reuse', 'Full reuse'][method_index] if arm_index == 0 else None)
            axis.set_title(f'({chr(97 + row * 2 + column)}) {"Synthetic" if family == "S" else "Real audit"}, n={size}', loc='left')
            axis.set_xticks([0, 1], ['K=1', 'K=16'])
            axis.tick_params(axis='x', labelbottom=True)
            axis.grid(axis='y', alpha=0.2)
            axis.set_xlim(-0.4, 1.4)
            axis.set_ylim(bottom=0)
            if column == 0:
                axis.set_ylabel('MSE × 10³' if family == 'S' else 'Audit error × 10³')
    handles, legend_labels = axes[0, 0].get_legend_handles_labels()
    figure.legend(handles, legend_labels, loc='upper center', ncol=3, frameon=False, bbox_to_anchor=(0.52, 1.03))
    figure.tight_layout(pad=0.6, rect=(0, 0, 1, 0.94))
    save_figure(figure, 'reporting_error_comparison')
    figure, axes = plt.subplots(1, 2, figsize=(5.5, 1.95), sharex=True, sharey=True)
    for axis, size in zip(axes, [64, 256]):
        observations = [value for value in audit if value['case'] == f'R{size}K16']
        for row, value in enumerate(observations):
            axis.plot(np.array(value['interval']) * 100, [row, row], color=COLORS[0], linewidth=1.5)
            axis.scatter(value['difference'] * 100, row, color=COLORS[0], s=20, zorder=3)
        axis.axvline(0, color='0.5', linestyle='--', linewidth=0.8)
        axis.set_title(f'n={size}, K=16')
        axis.set_yticks(range(len(observations)), [str(value['seed']) for value in observations])
        axis.set_xlabel('Selected − fixed (pp)')
        axis.set_xlim(-4.5, 9.5)
        axis.set_xticks([-4, 0, 4, 8])
        axis.grid(axis='x', alpha=0.2)
    axes[0].set_ylabel('Seed')
    axes[0].invert_yaxis()
    figure.tight_layout(pad=0.5)
    save_figure(figure, 'real_audit_accuracy_difference')
    concept = Path('figures/reporting_overview.png')
    prompt_log = Path('figures/reporting_overview.prompts.json')
    if not Path('.concept_figure_complete').exists() and not concept.exists():
        figure = plt.figure(figsize=(8, 2.3))
        figure.text(0.5, 0.5, 'Selection and reporting overview', ha='center', va='center', fontsize=14)
        figure.savefig(concept, dpi=300, facecolor='white')
        plt.close(figure)
    if not prompt_log.exists():
        write_json(prompt_log, {})
    entries = [manifest_entry('reporting_error_comparison', 'composite', 4, 2, [2]*4, [3]*4),
               manifest_entry('real_audit_accuracy_difference', 'composite', 2, 2, [5]*2, [1]*2)]
    overview = manifest_entry('reporting_overview', 'diagram', 1, 1, [6], [3])
    overview.pop('path_pdf')
    overview.update(generator='generate-concept-figure', prompt_log_path=str(prompt_log),
                    max_label_chars=38, estimated_min_rendered_font_pt=9)
    write_json('figure_manifest.json', {'figures': [overview] + entries})
    content = ['% @evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]',
               r'\begin{tabular}{llrrrrrr}\toprule',
               r'Setting & $(n,K)$ & Protected & Reuse & Full & Half & Fixed & Random\\\midrule']
    for label in labels:
        family, numbers = ('Synthetic' if label.startswith('S') else 'Real audit'), label[1:].split('K')
        content.append(f'{family} & ({numbers[0]},{numbers[1]}) & ' + ' & '.join(f'{means[label][metric]*1000:.3f}' for metric in METHODS) + r'\\')
    content.append(r'\bottomrule\end{tabular}')
    Path('tables/main_results.tex').write_text('\n'.join(content) + '\n')
    provenance('tables/main_results.tex', 'table')
    content = ['% @evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]',
               r'\begin{tabular}{llrrrr}\toprule',
               r'Truth & Coupling & Bias (pp) & Optimism (pp) & Coverage & Width\\\midrule']
    for regime in range(4):
        values = [regimes[str(regime)][label] for label in ['S64K16', 'S256K16']]
        content.append(f'{"Equal" if regime < 2 else "Graded"} & {"Low" if regime % 2 == 0 else "High"} & ' +
                       ' & '.join(f'{np.mean([value[metric] for value in values])*scale:.3f}' for metric, scale in
                                  [('report_bias', 100), ('signed_optimism', 100), ('coverage', 1), ('interval_width', 1)]) + r'\\')
    content.append(r'\bottomrule\end{tabular}')
    Path('tables/synthetic_regimes.tex').write_text('\n'.join(content) + '\n')
    provenance('tables/synthetic_regimes.tex', 'table')
    content = ['% @evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]',
               r'\begin{longtable}{rrlrrrrrr}\toprule',
               r'Seed & $n$ & Setting & $K$ & Report & Reuse & Target & Cov. & Width\\\midrule\endhead']
    for case in cases:
        label, metrics = case['case'], case['metrics']
        size, arms = label[1:].split('K')
        content.append(f'{case["seed"]} & {size} & {"Synth." if label.startswith("S") else "Real"} & {arms} & ' +
                       ' & '.join(f'{metrics[metric]*scale:.4f}' for metric, scale in [('report_mse', 1000), ('reuse_mse', 1000), ('selected_accuracy', 1), ('coverage', 1), ('interval_width', 1)]) + r'\\')
    content.append(r'\bottomrule\end{longtable}')
    Path('tables/seed_results.tex').write_text('\n'.join(content) + '\n')
    provenance('tables/seed_results.tex', 'table')
    print(json.dumps(summary['condition_means'], indent=2))


if __name__ == '__main__':
    main()
