import json
import csv
import re
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.stats import spearmanr, kendalltau

ROOT = Path(__file__).resolve().parent
FIGURES = ROOT / 'figures'
TABLES = ROOT / 'tables'
CASES = ['bbh', 'gpqa', 'musr', 'openllm_math', 'commonsense', 'gsm', 'legalbench', 'math', 'med_qa', 'mmlu']
LABELS = ['BBH', 'GPQA', 'MuSR', 'OL-Math', 'Commonsense', 'GSM', 'LegalBench', 'MATH', 'MedQA', 'MMLU']
COLORS = ['#2166ac', '#d95f02', '#7570b3', '#419a75']


def provenance(path, inputs=None):
    record = dict(schema_name='scientific-evidence.artifact-manifest',
                  artifact=dict(path=str(path.relative_to(ROOT)), kind='figure' if path.suffix in ['.pdf', '.png'] else 'derived'),
                  derived_from=inputs or ['@evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]'],
                  generated_by=dict(script_path='build_paper_artifacts.py', command=['python', 'build_paper_artifacts.py']))
    Path(str(path) + '.prov.json').write_text(json.dumps(record, indent=2))


def export(figure, stem):
    scale = max(1.0, 8.25 / figure.get_figwidth())
    figure.set_size_inches(figure.get_size_inches() * scale)
    for artist in figure.findobj():
        if isinstance(artist, matplotlib.text.Text):
            artist.set_fontsize(artist.get_fontsize() * scale)
        elif isinstance(artist, matplotlib.lines.Line2D):
            artist.set_markersize(artist.get_markersize() * scale)
            artist.set_linewidth(artist.get_linewidth() * scale)
        elif isinstance(artist, matplotlib.collections.PathCollection):
            artist.set_sizes(artist.get_sizes() * scale ** 2)
            artist.set_linewidths(artist.get_linewidths() * scale)
    for extension in ['pdf', 'png']:
        path = FIGURES / f'{stem}.{extension}'
        figure.savefig(path, dpi=300)
        provenance(path)
    plt.close(figure)


def predictions(case, method):
    if method in case['conditions']:
        condition = case['conditions'][method]
        if not condition['completed']:
            return None
        values = condition['predictions']
    else:
        values = (case['baseline_predictions'] or {}).get(method)
    return None if values is None else np.asarray(values, dtype=float)


def main():
    FIGURES.mkdir(exist_ok=True)
    TABLES.mkdir(exist_ok=True)
    # @evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]
    data = json.loads((ROOT / 'paper_data.json').read_text())
    episodes = data['final_evaluation']['evaluation_evidence']['episodes']
    seeds = [episode['seed'] for episode in episodes]
    methods = ['primary', 'no_diversity', 'anchor', 'irt']
    budget_methods = ['primary', 'no_diversity', 'no_calibration', 'uniform']
    method_values = np.full((len(CASES), len(seeds), len(methods)), np.nan)
    errors = np.full((len(CASES), len(seeds), len(budget_methods), 3), np.nan)
    ranks = errors.copy()
    support = {}
    audit = []
    complete_rows = []
    primary_rows = []
    for case_index, name in enumerate(CASES):
        support[name] = []
        for seed_index, episode in enumerate(episodes):
            case = episode['solution']['cases'][name]
            truth = np.asarray(case['target_full_means'])
            for method in list(case['conditions']) + ['anchor', 'irt', 'uniform', 'source_mean']:
                values = predictions(case, method)
                condition = case['conditions'].get(method)
                for budget_index, budget in enumerate(episode['solution']['budgets']):
                    row = dict(case=name, seed=episode['seed'], budget=budget, method=method,
                               target_count=len(truth), target_group_count=len(set(case['target_lineages'])),
                               available=values is not None,
                               structural_failure=condition['structural_failure'] if condition else None,
                               mae=None, rmse=None, spearman=None, kendall_tau_b=None)
                    if values is not None:
                        predicted = values[budget_index]
                        row['mae'] = float(np.abs(predicted - truth).mean())
                        row['rmse'] = float(np.sqrt(np.mean((predicted - truth) ** 2)))
                        row['spearman'] = float(spearmanr(truth, predicted).statistic) if np.ptp(predicted) > 0 and np.ptp(truth) > 0 else 0.0
                        row['kendall_tau_b'] = float(kendalltau(truth, predicted).statistic) if np.ptp(predicted) > 0 and np.ptp(truth) > 0 else 0.0
                    complete_rows.append(row)
            primary = case['conditions']['primary']
            metrics_text = ' & '.join(f'{primary[metric]:.4f}' for metric in ['mae', 'rmse', 'spearman', 'kendall_tau_b']) if primary['completed'] else r'\multicolumn{4}{c}{Missing; not a measured loss}'
            primary_rows.append(f'{LABELS[case_index]} & {episode["seed"]} & {len(truth)} & {len(set(case["target_lineages"]))} & {metrics_text}' + r' \\')
            arrays = [predictions(case, method) for method in methods]
            if all(array is not None for array in arrays):
                support[name].append(episode['seed'])
                for method_index, array in enumerate(arrays):
                    method_values[case_index, seed_index, method_index] = np.abs(array - truth).mean()
            arrays = [predictions(case, method) for method in budget_methods]
            if all(array is not None for array in arrays):
                for method_index, array in enumerate(arrays):
                    errors[case_index, seed_index, method_index] = np.abs(array - truth).mean(axis=1)
                    ranks[case_index, seed_index, method_index] = [float(spearmanr(truth, row).statistic) if np.ptp(row) > 0 and np.ptp(truth) > 0 else 0.0 for row in array]
            for condition, value in case['conditions'].items():
                if not value['completed'] or value['structural_failure']:
                    audit.append(dict(case=name, seed=episode['seed'], condition=condition,
                                      completed=value['completed'], structural_failure=value['structural_failure']))
    # Conditional weights: equal source-domain, equal case in domain, equal AVAILABLE seed per case.
    # @evidence[[source_evidence/evaluate_final.py#L1005-L1018]]
    case_weights = np.array([0.5 / 4] * 4 + [0.5 / 6] * 6)
    budget_error = np.einsum('c,cmb->mb', case_weights, np.nanmean(errors, axis=1))
    budget_rank = np.einsum('c,cmb->mb', case_weights, np.nanmean(ranks, axis=1))
    seed_error = np.array([np.einsum('c,cmb->mb', case_weights / np.isfinite(errors[:, seed_index, 0, 0]).dot(case_weights), np.nan_to_num(errors[:, seed_index])) for seed_index in range(len(seeds))])
    seed_rank = np.array([np.einsum('c,cmb->mb', case_weights / np.isfinite(ranks[:, seed_index, 0, 0]).dot(case_weights), np.nan_to_num(ranks[:, seed_index])) for seed_index in range(len(seeds))])
    summary = dict(seeds=seeds, budgets=episodes[0]['solution']['budgets'], cases=CASES,
                   methods=methods, budget_methods=budget_methods, common_support=support,
                   case_mae=np.nanmean(method_values, axis=1).tolist(),
                   case_seed_mae=method_values.tolist(), budget_mae=budget_error.tolist(),
                   budget_spearman=budget_rank.tolist(), audit=audit,
                   aggregation='Equal data-source mass, equal case mass within data source, equal available-seed mass within case. Seed dots separately normalize over cases available for that seed; they are descriptive, not replicates of the pooled statistic.')
    summary_path = ROOT / 'derived_results.json'
    summary_path.write_text(json.dumps(summary, indent=2).replace('NaN', 'null'))
    provenance(summary_path)
    complete_path = ROOT / 'complete_metrics.csv'
    with complete_path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(complete_rows[0]))
        writer.writeheader()
        writer.writerows(complete_rows)
    provenance(complete_path)
    plt.rcParams.update({'font.size': 9, 'axes.labelsize': 9, 'xtick.labelsize': 8.5,
                         'ytick.labelsize': 8.5, 'legend.fontsize': 8.5, 'axes.spines.top': False,
                         'axes.spines.right': False, 'pdf.fonttype': 42})
    figure, axes = plt.subplots(2, 1, figsize=(5.5, 3.8), sharex=True, gridspec_kw={'height_ratios': [4, 6]})
    labels = ['Score design', 'Uniform + fit', 'Anchor ref.', 'IRT ref.']
    for panel_index, (axis, indices) in enumerate(zip(axes, [range(4), range(4, 10)])):
        for method_index, (label, color) in enumerate(zip(labels, COLORS)):
            for local_index, case_index in enumerate(indices):
                values = method_values[case_index, :, method_index]
                values = values[np.isfinite(values)]
                ordinate = local_index + (method_index - 1.5) * .14
                axis.scatter(values, np.full(len(values), ordinate), s=10, alpha=.45, color=color, linewidths=0)
                axis.scatter(values.mean(), ordinate, marker='|', s=65, color=color, linewidths=1.6,
                             label=label if local_index == 0 and panel_index == 0 else None)
        axis.set_yticks(range(len(indices)), [f'{LABELS[case_index]} ({len(support[CASES[case_index]])})' + (' *' if len(support[CASES[case_index]]) < len(seeds) else '') for case_index in indices])
        axis.invert_yaxis()
        axis.grid(axis='x', alpha=.2)
        axis.set_title(['(a) Open LLM Leaderboard-derived', '(b) HELM-derived'][panel_index], fontsize=9, loc='left', pad=3)
    axes[-1].set_xlabel('Available-pair MAE (score fraction; lower is better)')
    axes[-1].set_xlim(left=0)
    figure.legend(*axes[0].get_legend_handles_labels(), loc='upper center', ncol=4, frameon=False,
                  columnspacing=.8, handletextpad=.35)
    figure.subplots_adjust(left=.27, right=.98, top=.86, bottom=.13, hspace=.25)
    export(figure, 'available_pair_method_comparison')
    figure, axes = plt.subplots(1, 2, figsize=(5.5, 2.5))
    budget_labels = ['Score design', 'Uniform + fit', 'Selected mean', 'Uniform mean']
    for axis_index, (axis, values, seed_values) in enumerate(zip(axes, [budget_error, budget_rank], [seed_error, seed_rank])):
        for method_index, (label, color) in enumerate(zip(budget_labels, COLORS)):
            positions = np.arange(3) + (method_index - 1.5) * .15
            axis.scatter(positions, values[method_index], s=25, color=color, label=label)
            for seed_index in range(len(seeds)):
                axis.scatter(positions + (seed_index - 1) * .025, seed_values[seed_index, method_index],
                             s=10, color=color, alpha=.35, linewidths=0)
        axis.set_xticks(range(3), summary['budgets'])
        axis.set_xlabel('Queried items')
        axis.set_title(['(a) MAE (lower is better)', '(b) Spearman (higher is better)'][axis_index], fontsize=9)
        axis.grid(axis='y', alpha=.2)
    figure.legend(*axes[0].get_legend_handles_labels(), loc='upper center', ncol=2, frameon=False,
                  bbox_to_anchor=(.5, 1.02), columnspacing=1.2)
    figure.subplots_adjust(left=.10, right=.99, top=.72, bottom=.18, wspace=.35)
    export(figure, 'budget_accuracy_and_ranking')
    overview = FIGURES / 'method_and_evidence_overview.png'
    prompt_log = FIGURES / 'method_and_evidence_overview.prompts.json'
    if not (ROOT / '.concept_figure_complete').exists() and not overview.exists():
        canvas = Image.new('RGB', (2400, 830), 'white')
        font = ImageFont.truetype('DejaVuSans.ttf', 65)
        ImageDraw.Draw(canvas).text((160, 350), 'Overview pending synchronous rendering', font=font, fill='#333333')
        canvas.save(overview)
    if not prompt_log.exists():
        prompt_log.write_text('{}\n')
    case_rows = []
    for case_index, label in enumerate(LABELS):
        means = np.nanmean(method_values[case_index], axis=0)
        case_rows.append(label + ' & ' + str(len(support[CASES[case_index]])) + ' & ' + ' & '.join(f'{value:.4f}' for value in means) + r' \\')
    (TABLES / 'case_mae.tex').write_text('% @evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]\n' + '\n'.join(case_rows) + '\n')
    budget_rows = []
    for budget_index, budget in enumerate(summary['budgets']):
        for method_index, label in enumerate(budget_labels):
            budget_rows.append(f'{budget} & {label} & {budget_error[method_index, budget_index]:.4f} & {budget_rank[method_index, budget_index]:.4f}' + r' \\')
    (TABLES / 'budget_metrics.tex').write_text('% @evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]\n' + '\n'.join(budget_rows) + '\n')
    (TABLES / 'primary_seed_metrics.tex').write_text('% @evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]\n' + '\n'.join(primary_rows) + '\n')
    for table in TABLES.glob('*.tex'):
        provenance(table)
    manuscript = ROOT / 'paper.tex'
    if manuscript.exists():
        text = manuscript.read_text()
        for stem in ['case_mae', 'budget_metrics', 'primary_seed_metrics']:
            content = (TABLES / f'{stem}.tex').read_text().rstrip()
            replacement = f'% BEGIN GENERATED {stem}\n{content}\n% END GENERATED {stem}'
            text = re.sub(f'% BEGIN GENERATED {stem}.*?% END GENERATED {stem}', lambda match: replacement, text, flags=re.S)
        manuscript.write_text(text)
    figures = []
    specs = json.loads((ROOT / 'paper_strategy.json').read_text())['figure_specs']
    manifest_path = ROOT / 'figure_manifest.json'
    previous_figures = {record['figure_id']: record for record in json.loads(manifest_path.read_text())['figures']} if manifest_path.exists() else {}
    for spec in specs:
        stem = spec['figure_id']
        diagram = spec['figure_type'] == 'diagram'
        if diagram and stem in previous_figures:
            figures.append(previous_figures[stem])
            continue
        files = {'png': f'figures/{stem}.png'}
        if not diagram:
            files['pdf'] = f'figures/{stem}.pdf'
        panels = [dict(panel_id='overview', category_count=6, series_count=3)] if diagram else (
            [dict(panel_id='openllm', category_count=4, series_count=4), dict(panel_id='helm', category_count=6, series_count=4)] if stem.startswith('available') else
            [dict(panel_id='mae', category_count=3, series_count=4), dict(panel_id='spearman', category_count=3, series_count=4)])
        record = dict(figure_id=stem, figure_type=spec['figure_type'], files=files, panel_count=len(panels),
                      panels=panels, uses_progression=False, generator=spec['preferred_generator'],
                      placement='full_width', intended_latex_width_fraction=1.0,
                      estimated_min_rendered_font_pt=9 if diagram else 8.5, min_font_size_pt=9 if diagram else 8.5,
                      source_ids=['final.evidence.episodes'], required=True,
                      note='Single-column 5.5-inch text width. Quantitative means use common available support; no confidence bars.')
        if diagram:
            record['prompt_log_path'] = f'figures/{stem}.prompts.json'
            record['note'] = 'Orchestrator-owned rendering; draft placeholder only. No numerical claims.'
        figures.append(record)
    (ROOT / 'figure_manifest.json').write_text(json.dumps({'figures': figures}, indent=2))
    print(json.dumps({key: summary[key] for key in ['common_support', 'case_mae', 'budget_mae', 'budget_spearman']}, indent=2))


if __name__ == '__main__':
    main()
