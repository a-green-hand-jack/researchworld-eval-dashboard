"""Recompute tables/plots from recorded predictions, without model execution.

@evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]
@evidence[[source_evidence/evaluator/evaluate_final.py#L545]]
"""

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import kendalltau, spearmanr


ROOT = Path(__file__).resolve().parents[1]
METHODS = ['selected', 'irt_mae', 'uniform_mae', 'prior_mae', 'anchor_mae']
LABELS = {'selected': 'Score-targeted package', 'irt_mae': 'Local IRT',
          'uniform_mae': 'Uniform', 'prior_mae': 'Source prior', 'anchor_mae': 'Local anchors'}
COLORS = {'selected': '#244b87', 'irt_mae': '#168077', 'uniform_mae': '#707782',
          'prior_mae': '#875b9e', 'anchor_mae': '#c87728'}
DISPLAY = {'bbh': 'BBH', 'gpqa': 'GPQA', 'mmlu_pro': 'MMLU-Pro', 'musr': 'MuSR',
           'openllm_math': 'Leaderboard MATH', 'legalbench': 'LegalBench',
           'math': 'HELM MATH', 'med_qa': 'MedQA', 'mmlu': 'MMLU'}


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def provenance(path, sources):
    write_json(Path(str(path) + '.prov.json'), {
        'schema_name': 'scientific-evidence.artifact-manifest',
        'artifact': {'path': str(path.relative_to(ROOT)), 'kind': 'derived',
                     'sha256': hashlib.sha256(path.read_bytes()).hexdigest()},
        'derived_from': sources,
        'generated_by': {'script_path': 'scripts/build_paper_artifacts.py',
                         'command': ['python', 'scripts/build_paper_artifacts.py'], 'cwd': '.'}})


def summarize(values):
    return {metric: float(np.mean([value[metric] for value in values]))
            for metric in ['mae', 'rmse', 'spearman', 'kendall']}


def metrics(prediction, truth, groups):
    unique, inverse, counts = np.unique(groups, return_inverse=True, return_counts=True)
    weights = 1.0 / (len(unique) * counts[inverse])
    difference = prediction - truth
    group_predictions = [prediction[groups == group].mean() for group in unique]
    group_truth = [truth[groups == group].mean() for group in unique]
    if len(set(group_predictions)) < 2 or len(set(group_truth)) < 2:
        spearman, kendall = -1.0, -1.0
    else:
        spearman = spearmanr(group_predictions, group_truth).statistic
        kendall = kendalltau(group_predictions, group_truth).statistic
    return dict(mae=float(weights @ np.abs(difference)),
                rmse=float(np.sqrt(weights @ difference ** 2)),
                spearman=float(spearman), kendall=float(kendall))


def save_figure(figure, identifier):
    sources = ['@evidence[[analysis/paper_statistics.json]]', '@evidence[[scripts/build_paper_artifacts.py]]']
    for suffix in ['pdf', 'png']:
        path = ROOT / 'figures' / (identifier + '.' + suffix)
        figure.savefig(path, dpi=450 if suffix == 'png' else 300, facecolor='white')
        provenance(path, sources)
    plt.close(figure)


def figure_entry(identifier, figure_type, panels, categories, series):
    return dict(figure_id=identifier, figure_type=figure_type,
                path_png='figures/' + identifier + '.png', path_pdf='figures/' + identifier + '.pdf',
                generator='matplotlib', n_panels=panels, panels_per_row=1,
                categories_per_panel=categories, series_per_panel=series,
                max_label_chars=24, font_sizes=dict(title=10, axis=9, ticks=9, legend=9),
                uses_abbrev_labels=True, uses_progression=False,
                placement='full_width', intended_latex_width_fraction=1.0,
                estimated_min_rendered_font_pt=9.0, source_ids=['final.evidence.episodes'])


def main():
    paper = json.loads((ROOT / 'paper_data.json').read_text())
    final = paper['final_evaluation']
    outer_records = final['evaluation_evidence']['episodes']
    uncertainty = outer_records[0]['solution']['paired_mae_uncertainty']
    assert all(record['solution']['paired_mae_uncertainty'] == uncertainty for record in outer_records)
    rows = []
    keys = set()
    for outer in outer_records:
        for episode in outer['solution']['episodes']:
            if episode['condition'] != 'normal' or episode.get('replay', False):
                continue
            for checkpoint in episode['checkpoints']:
                key = (outer['seed'], episode['case'], checkpoint['budget'])
                assert key not in keys
                keys.add(key)
                truth = np.array(checkpoint['references'])
                groups = np.array(checkpoint['lineage_groups'])
                for method in METHODS:
                    prediction = np.array(checkpoint['predictions'] if method == 'selected'
                                          else checkpoint['baseline_predictions'][method])
                    rows.append(dict(seed=outer['seed'], case=episode['case'], budget=checkpoint['budget'],
                                     method=method, target_rows=len(truth), target_groups=len(np.unique(groups)),
                                     **metrics(prediction, truth, groups)))
    aggregate = {method: summarize([row for row in rows if row['method'] == method]) for method in METHODS}
    for method in METHODS:
        metric_name = 'mae' if method == 'selected' else method
        assert np.isclose(aggregate[method]['mae'], final['metrics'][metric_name], rtol=0, atol=1e-12)
    for metric in ['rmse', 'spearman', 'kendall']:
        assert np.isclose(aggregate['selected'][metric], final['metrics'][metric], rtol=0, atol=1e-12)
    cases = list(dict.fromkeys(row['case'] for row in rows))
    budgets = sorted(set(row['budget'] for row in rows))
    seeds = sorted(set(row['seed'] for row in rows))
    by_budget = {str(budget): {method: summarize([row for row in rows if row['budget'] == budget and row['method'] == method]) for method in METHODS} for budget in budgets}
    by_case_budget = {case: {str(budget): {method: summarize([row for row in rows if row['case'] == case and row['budget'] == budget and row['method'] == method]) for method in METHODS} for budget in budgets} for case in cases}
    by_seed = {str(seed): {method: summarize([row for row in rows if row['seed'] == seed and row['method'] == method]) for method in METHODS} for seed in seeds}
    reversals = [(case, budget) for case in cases for budget in budgets
                 if by_case_budget[case][str(budget)]['selected']['mae'] > by_case_budget[case][str(budget)]['irt_mae']['mae']]
    summary = dict(aggregate=aggregate, by_budget=by_budget, by_case_budget=by_case_budget,
                   by_seed=by_seed, cases=cases, seeds=seeds, budgets=budgets,
                   cell_count=len(keys), uncertainty=uncertainty, local_irt_reversals=reversals,
                   qualification={name: final[name] for name in ['status', 'outcome']},
                   relative_mae_reduction_vs_irt=1-aggregate['selected']['mae']/aggregate['irt_mae']['mae'])
    write_json(ROOT / 'analysis/paper_statistics.json', summary)
    provenance(ROOT / 'analysis/paper_statistics.json', ['@evidence[[paper_data.json#/final_evaluation]]'])
    with (ROOT / 'analysis/recorded_cell_metrics.csv').open('w') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    provenance(ROOT / 'analysis/recorded_cell_metrics.csv', ['@evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]'])
    main_rows = []
    for method in METHODS:
        values = aggregate[method]
        cost = '0' if method == 'prior_mae' else '$k$'
        ranking = '-- & --' if method == 'prior_mae' else f"{values['spearman']:.3f} & {values['kendall']:.3f}"
        main_rows.append(f"{LABELS[method]} & {cost} & {values['mae']*100:.2f} & {values['rmse']*100:.2f} & {ranking} \\")
    (ROOT / 'tables/aggregate.tex').write_text('% @evidence[[analysis/paper_statistics.json#/aggregate]]\n' +
        '\\begin{tabular}{lrrrrr}\n\\toprule\nEstimator & Answers & MAE (pp) & RMSE (pp) & Spearman & Kendall\\\\\n\\midrule\n' +
        '\n'.join(row + '\\' for row in main_rows) + '\n\\bottomrule\n\\end{tabular}\n')
    case_rows = []
    for case in cases:
        for budget in budgets:
            values = by_case_budget[case][str(budget)]
            numeric = ' & '.join(f"{values[method]['mae']*100:.2f}" for method in METHODS)
            case_rows.append(f"{DISPLAY[case]} & {budget} & {numeric} \\\\")
    (ROOT / 'tables/case_budget.tex').write_text('% @evidence[[analysis/paper_statistics.json#/by_case_budget]]\n' +
        '\\begin{tabular}{lrrrrrr}\n\\toprule\nBenchmark & Items & Package & IRT & Uniform & Prior & Anchors\\\\\n\\midrule\n' +
        '\n'.join(case_rows) + '\n\\bottomrule\n\\end{tabular}\n')
    seed_rows = []
    for seed in seeds:
        values = by_seed[str(seed)]['selected']
        seed_rows.append(f"{seed} & {values['mae']*100:.3f} & {values['rmse']*100:.3f} & {values['spearman']:.4f} & {values['kendall']:.4f} \\\\")
    (ROOT / 'tables/seeds.tex').write_text('% @evidence[[analysis/paper_statistics.json#/by_seed]]\n' +
        '\\begin{tabular}{rrrrr}\n\\toprule\nSeed & MAE & RMSE & Spearman & Kendall\\\\\n\\midrule\n' +
        '\n'.join(seed_rows) + '\n\\bottomrule\n\\end{tabular}\n')
    for path in (ROOT / 'tables').glob('*.tex'):
        provenance(path, ['@evidence[[analysis/paper_statistics.json]]'])
    plt.rcParams.update({'font.size': 9, 'axes.labelsize': 9, 'xtick.labelsize': 9,
                         'ytick.labelsize': 9, 'legend.fontsize': 9, 'axes.spines.top': False,
                         'axes.spines.right': False, 'pdf.fonttype': 42})
    figure, axis = plt.subplots(figsize=(5.5, 2.2), layout='constrained')
    comparators = ['irt_mae', 'prior_mae', 'uniform_mae', 'anchor_mae']
    for position, method in enumerate(comparators):
        comparison = uncertainty['comparisons'][method]
        point, lower, upper = [comparison[field]*100 for field in ['candidate_minus_baseline_mae', 'lower_95', 'upper_95']]
        axis.errorbar(point, position, xerr=[[point-lower], [upper-point]], fmt='o',
                      capsize=4, color=COLORS[method], linewidth=1.8, markersize=5)
    axis.axvline(0, color='#303030', linewidth=0.8)
    axis.set(yticks=range(len(comparators)), yticklabels=[LABELS[method] for method in comparators],
             xlabel='Package − comparator MAE (percentage points)', ylim=(-0.6, 3.6))
    axis.invert_yaxis()
    axis.grid(axis='x', alpha=0.15)
    save_figure(figure, 'paired_error_comparison')
    figure, axes = plt.subplots(2, 1, figsize=(5.5, 3.65), sharex=True, layout='constrained',
                                gridspec_kw={'height_ratios': [5, 4]})
    ecosystem_cases = [cases[:5], cases[5:]]
    markers = ['o', 's', '^']
    for axis, subset, title in zip(axes, ecosystem_cases, ['(a) Leaderboard matrices', '(b) HELM matrices']):
        for budget_index, budget in enumerate(budgets):
            differences = [(by_case_budget[case][str(budget)]['selected']['mae'] - by_case_budget[case][str(budget)]['irt_mae']['mae'])*100 for case in subset]
            axis.scatter(differences, np.arange(len(subset)) + (budget_index-1)*0.20,
                         marker=markers[budget_index], color=COLORS['selected'], s=27, label=str(budget) + ' items')
        axis.axvline(0, color='#333333', linewidth=0.8)
        axis.set(yticks=range(len(subset)), yticklabels=[DISPLAY[case] for case in subset],
                 ylim=(-0.55, len(subset)-0.45))
        axis.invert_yaxis()
        axis.set_title(title, loc='left', fontsize=10)
        axis.grid(axis='x', alpha=0.15)
    axes[0].legend(loc='lower left', ncol=3, frameon=False, bbox_to_anchor=(-0.02, 1.13), borderaxespad=0, handletextpad=0.3, columnspacing=0.9)
    axes[1].set_xlabel('Package − local IRT MAE (percentage points)')
    save_figure(figure, 'case_budget_reversals')
    figure, axes = plt.subplots(2, 1, figsize=(5.5, 3.8), sharex=True, layout='constrained')
    for method in ['selected', 'irt_mae', 'uniform_mae', 'anchor_mae']:
        axes[0].plot(budgets, [by_budget[str(budget)][method]['mae']*100 for budget in budgets],
                     color=COLORS[method], marker='o', label=LABELS[method])
        axes[1].plot(budgets, [by_budget[str(budget)][method]['spearman'] for budget in budgets],
                     color=COLORS[method], marker='o')
    axes[0].set_ylabel('MAE (percentage points)')
    axes[1].set_ylabel('Spearman correlation')
    axes[1].set_xlabel('Queried items per target')
    axes[1].set_xticks(budgets)
    axes[0].legend(ncol=2, fontsize=9, frameon=False)
    for axis in axes:
        axis.grid(alpha=0.15)
    save_figure(figure, 'budget_sensitivity')
    concept_png = ROOT / 'figures/score_prediction_overview.png'
    concept_log = ROOT / 'figures/score_prediction_overview.prompts.json'
    completed = (ROOT / '.concept_figure_complete').exists()
    populated_log = concept_log.exists() and concept_log.read_text().strip() not in ['', '{}']
    if not completed and not populated_log and not concept_png.exists():
        figure = plt.figure(figsize=(8, 2.9))
        figure.text(0.5, 0.5, 'Conceptual overview reserved for orchestrator rendering', ha='center', va='center', fontsize=15, color='#555555')
        figure.savefig(concept_png, dpi=300, facecolor='#fafafa')
        plt.close(figure)
        concept_log.write_text('{}\n')
    entries = [dict(figure_id='score_prediction_overview', path_png='figures/score_prediction_overview.png',
                    generator='generate-concept-figure', prompt_log_path='figures/score_prediction_overview.prompts.json',
                    figure_type='diagram', n_panels=1, panels_per_row=1, categories_per_panel=[6], series_per_panel=[1],
                    max_label_chars=30, font_sizes=dict(title=10, axis=9, ticks=9, legend=9),
                    uses_abbrev_labels=True, uses_progression=False, placement='full_width',
                    intended_latex_width_fraction=1.0, estimated_min_rendered_font_pt=9.0, source_ids=[])]
    entries += [figure_entry('paired_error_comparison', 'scatter', 1, [4], [1]),
                figure_entry('case_budget_reversals', 'composite', 2, [5, 4], [3, 3]),
                figure_entry('budget_sensitivity', 'line', 2, [3, 3], [4, 4])]
    write_json(ROOT / 'figure_manifest.json', {'figures': entries})
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
