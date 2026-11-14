import datetime
import hashlib
import json
import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


ROOT = pathlib.Path(__file__).resolve().parent
FIGURES = ROOT / 'figures'
FIGURES.mkdir(exist_ok=True)
COLORS = {'latent': '#2166ac', 'greedy_ridge': '#c55a11', 'random_lowrank': '#5b8c46'}
METHODS = list(COLORS)
LABELS = {'latent': 'Latent', 'greedy_ridge': 'Ridge', 'random_lowrank': 'Rand-LR'}
CONDITIONS = ['model_group', 'family_disjoint']
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9.5,
                     'axes.labelsize': 10, 'xtick.labelsize': 9.5,
                     'ytick.labelsize': 9.5, 'legend.fontsize': 9.5,
                     'pdf.fonttype': 42, 'ps.fonttype': 42,
                     'axes.spines.top': False, 'axes.spines.right': False})


def provenance(path, inputs, outputs=None):
    payload = {'schema_name': 'scientific-evidence.artifact-manifest',
               'artifact': {'path': str(path.relative_to(ROOT)), 'kind': 'figure' if path.suffix in ('.pdf', '.png') else 'derived',
                            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()},
               'derived_from': inputs,
               'generated_by': {'script_path': 'build_paper_figures.py',
                                'command': [sys.executable, 'build_paper_figures.py']}}
    if outputs is not None:
        payload['named_outputs'] = outputs
    path.with_name(path.name + '.prov.json').write_text(json.dumps(payload, indent=2) + '\n')


def average_rows(records, families, condition, key='audit_mae'):
    values = {record['row']: record[key] for record in records}
    if condition == 'family_disjoint':
        return float(np.mean([np.mean([values[row] for row in values if families[row] == family])
                              for family in sorted(set(families))]))
    return float(np.mean(list(values.values())))


def export(figure, stem):
    for suffix in ('.pdf', '.png'):
        path = FIGURES / (stem + suffix)
        figure.savefig(path, dpi=300, facecolor='white')
        provenance(path, ['@evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]',
                          '@evidence[[derived_results.json]]'])
    plt.close(figure)


def placeholder():
    if (ROOT / '.concept_figure_complete').exists():
        return
    prompt_path = FIGURES / 'problem_and_evidence_overview.prompts.json'
    if prompt_path.exists() and json.loads(prompt_path.read_text()):
        return
    if (FIGURES / 'problem_and_evidence_overview.png').exists():
        return
    figure = plt.figure(figsize=(8, 2.0))
    figure.text(0.5, 0.5, 'Concept overview reserved for orchestrator rendering',
                ha='center', va='center', fontsize=15, color='#555555')
    figure.savefig(FIGURES / 'problem_and_evidence_overview.png', dpi=300, facecolor='white')
    plt.close(figure)
    prompt_path.write_text('{}\n')


def main():
    # @evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]
    paper = json.loads((ROOT / 'paper_data.json').read_text())
    episodes = paper['final_evaluation']['evaluation_evidence']['episodes']
    cases = []
    curves = []
    for episode_index, episode in enumerate(episodes):
        for case_index, case in enumerate(episode['solution']['cases']):
            if case['replay']:
                continue
            pointer = f'/final_evaluation/evaluation_evidence/episodes/{episode_index}/solution/cases/{case_index}'
            row = {'seed': episode['seed'], 'condition': case['case'], 'arm': case['arm'], 'pointer': pointer,
                   'remaining': dict(zip(['latent', 'historical_mean', 'score_average', 'random_lowrank', 'greedy_ridge'], case['losses'])),
                   'audit': {'latent': case['audit_mae'], 'random_lowrank': case['baseline_audit'][0],
                             'greedy_ridge': case['baseline_audit'][1]}}
            row['audit']['historical_mean'] = float(np.mean([
                average_rows([record for record in case['observations'] if record['k'] == budget],
                             case['families'], case['case'], 'mean_audit_mae')
                for budget in sorted({record['k'] for record in case['observations']})]))
            cases.append(row)
            for method in METHODS:
                records = case['observations'] if method == 'latent' else case['baselines'][method]
                for budget in sorted({record['k'] for record in records}):
                    selected = [record for record in records if record['k'] == budget]
                    curves.append({'seed': episode['seed'], 'condition': case['case'], 'arm': case['arm'],
                                   'method': method, 'k': budget,
                                   'mae': average_rows(selected, case['families'], case['case']), 'pointer': pointer})
    original = [case for case in cases if case['arm'] == 'original']
    aggregate = {target: {method: float(np.mean([case[target][method] for case in original]))
                          for method in original[0][target]} for target in ['remaining', 'audit']}
    for method, metric in [('latent', 'candidate_mae'), ('random_lowrank', 'random_lowrank_mae'), ('greedy_ridge', 'greedy_ridge_mae')]:
        assert np.isclose(aggregate['remaining'][method], paper['final_evaluation']['metrics'][metric], rtol=0, atol=1e-12)
    results = {'source_ids': ['final.evidence.episodes'], 'cases': cases, 'audit_budget_curves': curves,
               'aggregate_original': aggregate,
               'qualification': {key: paper['grounding_sources']['final.qualification.' + key]['value'] for key in ['status', 'outcome']}}
    output = ROOT / 'derived_results.json'
    output.write_text(json.dumps(results, indent=2) + '\n')
    provenance(output, ['@evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]'])
    for condition in CONDITIONS:
        figure, axis = plt.subplots(figsize=(2.68, 2.12))
        figure.subplots_adjust(left=.22, right=.98, bottom=.25, top=.98)
        for method_index, method in enumerate(METHODS):
            values = [row for row in curves if row['condition'] == condition and row['arm'] == 'original' and row['method'] == method]
            budgets = sorted({row['k'] for row in values})
            means = [np.mean([row['mae'] for row in values if row['k'] == budget]) for budget in budgets]
            for budget in budgets:
                split_values = [row['mae'] for row in values if row['k'] == budget]
                axis.scatter([budget + (method_index - 1) * .045] * len(split_values), split_values,
                             color=COLORS[method], alpha=.6, s=11, zorder=3)
            axis.plot(budgets, means, color=COLORS[method], marker=['o', 's', '^'][method_index],
                      markersize=4, linewidth=1.7, label=LABELS[method])
        axis.set_xticks([1, 2, 4, 8])
        axis.set_xlabel('Queried benchmarks, $k$')
        axis.set_ylabel('Fixed-audit MAE')
        axis.set_ylim(.012, .058)
        axis.set_yticks([.02, .03, .04, .05])
        axis.grid(axis='y', color='#dddddd', linewidth=.5)
        export(figure, 'common_target_budget_comparison_' + condition)
    for condition in CONDITIONS:
        figure, axis = plt.subplots(figsize=(2.68, 2.12))
        figure.subplots_adjust(left=.22, right=.98, bottom=.25, top=.98)
        for method_index, method in enumerate(METHODS):
            for seed_offset, seed in zip([-.045, 0, .045], sorted({case['seed'] for case in cases})):
                pairs = [next(case['audit'][method] for case in cases if case['condition'] == condition and case['arm'] == arm and case['seed'] == seed)
                         for arm in ['original', 'permuted']]
                axis.plot([method_index - .16 + seed_offset, method_index + .16 + seed_offset], pairs,
                          color=COLORS[method], alpha=.35, linewidth=.8)
                axis.scatter(method_index - .16 + seed_offset, pairs[0], color=COLORS[method], s=15, alpha=.65)
                axis.scatter(method_index + .16 + seed_offset, pairs[1], facecolors='white', edgecolors=COLORS[method], s=17, alpha=.7)
            for arm_offset, arm in [(-.16, 'original'), (.16, 'permuted')]:
                mean = np.mean([case['audit'][method] for case in cases if case['condition'] == condition and case['arm'] == arm])
                axis.scatter(method_index + arm_offset, mean, marker='D', s=40, zorder=4,
                             facecolors=COLORS[method] if arm == 'original' else 'white', edgecolors=COLORS[method], linewidths=1.3)
        axis.set_xticks(range(len(METHODS)), [LABELS[method] for method in METHODS])
        axis.set_xlim(-.55, 2.65)
        axis.set_ylabel('Fixed-audit MAE')
        axis.set_ylim(.015, .078)
        axis.set_yticks([.02, .04, .06])
        axis.grid(axis='y', color='#dddddd', linewidth=.5)
        export(figure, 'historical_alignment_control_' + condition)
    placeholder()
    entries = [{'figure_id': 'problem_and_evidence_overview', 'figure_type': 'diagram',
                'path_png': 'figures/problem_and_evidence_overview.png', 'generator': 'generate-concept-figure',
                'prompt_log_path': 'figures/problem_and_evidence_overview.prompts.json', 'n_panels': 1,
                'panels_per_row': 1, 'categories_per_panel': [6], 'series_per_panel': [1],
                'source_ids': [], 'placement': 'full_width', 'intended_latex_width_fraction': 1.0,
                'estimated_min_rendered_font_pt': 10,
                'note': 'Orchestrator-owned placeholder. Final overview must retain historical-only fit, query boundary and never-queryable audit targets.'}]
    for figure_id in ['common_target_budget_comparison', 'historical_alignment_control']:
        for condition in CONDITIONS:
            entries.append({'figure_id': figure_id if condition == 'model_group' else figure_id + '_' + condition, 'figure_type': 'line' if figure_id.startswith('common') else 'scatter',
                            'path_pdf': f'figures/{figure_id}_{condition}.pdf', 'path_png': f'figures/{figure_id}_{condition}.png',
                            'generator': 'matplotlib', 'n_panels': 1, 'panels_per_row': 1,
                            'categories_per_panel': [4 if figure_id.startswith('common') else 3],
                            'series_per_panel': [3 if figure_id.startswith('common') else 2],
                            'font_sizes': {'axis': 10, 'ticks': 9.5, 'legend': 9.5, 'title': 10},
                            'source_ids': ['final.evidence.episodes'], 'placement': 'full_width',
                            'intended_latex_width_fraction': .487,
                            'estimated_min_rendered_font_pt': 9.4,
                            'note': 'One panel in a two-panel LaTeX subfigure group, together spanning 5.5-inch text width. Mean plus raw dependent split values; no confidence intervals.'})
    for entry in entries:
        entry['files'] = {'png': entry.pop('path_png')}
        if 'path_pdf' in entry:
            entry['files']['pdf'] = entry.pop('path_pdf')
        entry['panel_count'] = entry.pop('n_panels')
        categories = entry.pop('categories_per_panel')
        series = entry.pop('series_per_panel')
        entry['panels'] = [{'panel_id': 'a', 'category_count': categories[0], 'series_count': series[0]}]
        entry['uses_progression'] = False
        entry['uses_abbrev_labels'] = True
        entry['max_label_chars'] = 31
        entry['min_font_size_pt'] = entry['estimated_min_rendered_font_pt']
    (ROOT / 'figure_manifest.json').write_text(json.dumps({'figures': entries}, indent=2) + '\n')
    print(json.dumps(aggregate, indent=2))
    for condition in CONDITIONS:
        for method in METHODS:
            print(condition, method, [(budget, round(float(np.mean([row['mae'] for row in curves if row['condition'] == condition and row['arm'] == 'original' and row['method'] == method and row['k'] == budget])), 6)) for budget in [1, 2, 4, 8]])


if __name__ == '__main__':
    main()
