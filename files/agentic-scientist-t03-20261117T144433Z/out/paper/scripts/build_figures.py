import hashlib
import itertools
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.titlesize': 9, 'axes.labelsize': 9, 'xtick.labelsize': 8.5, 'ytick.labelsize': 8.5, 'legend.fontsize': 8.5, 'pdf.fonttype': 42})
COLORS = ['#167d9a', '#c86535', '#759eaf', '#d9aa86']
FAMILIES = ['logistic', 'forest', 'boosting']
LABELS = ['Logistic', 'Forest', 'Boosting']


def quality(attribution, reference):
    return float(1 / (1 + np.abs(attribution - reference).sum() / max(1e-8, np.abs(reference).sum())))


def fidelity(attribution, cell):
    if cell['exact'] is not None:
        return quality(attribution, np.asarray(cell['exact']))
    return float(np.mean([quality(attribution, np.asarray(reference)) for reference in cell['references']]))


def sidecar(path, kind):
    payload = {'schema_name': 'scientific-evidence.artifact-manifest', 'artifact': {'path': str(path.relative_to(ROOT)), 'kind': kind, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}, 'derived_from': ['@evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]'], 'generated_by': {'script_path': 'scripts/build_figures.py', 'command': ['python', 'scripts/build_figures.py']}, 'notes': 'Deterministic reduction of retained observations; no new model calls, bootstrap intervals, or tests.'}
    Path(str(path) + '.prov.json').write_text(json.dumps(payload, indent=2) + '\n')


def save_figure(figure, identifier):
    for extension in ['pdf', 'png']:
        path = ROOT / 'figures' / (identifier + '.' + extension)
        figure.savefig(path, dpi=300)
        sidecar(path, 'figure')
    plt.close(figure)


def main():
    registry = json.loads((ROOT / 'paper_data.json').read_text())
    # @evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]
    cases, costs = [], []
    errors = []
    for episode in registry['final_evaluation']['evaluation_evidence']['episodes']:
        for case_id, case in episode['solution'].items():
            if case.get('replay') or 'cells' not in case:
                continue
            dataset, family = case['case']
            means = {key: float(np.mean([cell['metrics'][key] for cell in case['cells']])) for key in case['cells'][0]['metrics']}
            budget_quality = {str(budget): {'studied': [], 'library': []} for budget in [64, 256]}
            rank, sign = [], []
            for cell in case['cells']:
                recomputed_fidelity, recomputed_overlap = [], []
                for rung_index, rung in enumerate(cell['rungs']):
                    vectors = np.asarray(rung['phi'])
                    values = [fidelity(vector, cell) for vector in vectors]
                    budget_quality[str(rung['budget'])]['studied'].append(float(np.mean(values)))
                    budget_quality[str(rung['budget'])]['library'].append(fidelity(np.asarray(cell['baseline'][rung_index]), cell))
                    recomputed_fidelity.extend(values)
                    for first, second in itertools.combinations(vectors, 2):
                        first_order = np.argsort(-np.abs(first), kind='stable')
                        second_order = np.argsort(-np.abs(second), kind='stable')
                        recomputed_overlap.append(len(set(first_order[:3]) & set(second_order[:3])) / 3)
                    rank.extend(pair['rank'] for pair in rung['pair_agreement'])
                    sign.extend(pair['sign'] for pair in rung['pair_agreement'])
                    counts = cell['baseline_counts'][rung_index]
                    costs.append(dict(dataset=dataset, family=family, seed=episode['seed'], background=cell['background_size'], budget=rung['budget'], studied_rows=rung['budget'] * cell['background_size'], studied_wall=float(np.mean(rung['duration_seconds'])), library_rows=counts['prediction_rows'], library_coalitions=counts['coalitions'], library_cpu=counts['cpu_seconds']))
                reference = np.asarray(cell['exact']) if cell['exact'] is not None else np.mean(cell['references'], axis=0)
                gain = quality(np.asarray(cell['matched_average']), reference) - quality(np.asarray(cell['rungs'][1]['phi'][0]), reference)
                for key, value in [('reference_fidelity', np.mean(recomputed_fidelity)), ('repeat_agreement', np.mean(recomputed_overlap)), ('matched_budget_gain', gain)]:
                    errors.append(abs(float(value) - cell['metrics'][key]))
            cases.append(dict(dataset=dataset, family=family, seed=episode['seed'], source_case=case_id, metrics=means, intervals=case['input_cluster_intervals'], budget_quality={budget: {method: float(np.mean(values)) for method, values in methods.items()} for budget, methods in budget_quality.items()}, rank=float(np.mean(rank)), sign=float(np.mean(sign)), validation_accuracy=case['validation_accuracy'], fit_cpu_seconds=case['fit_cpu_seconds'], training_rows=case['training_rows'], validation_rows=case['validation_rows'], selection_rows=case['selection_rows']))
    assert max(errors) < 1e-12
    aggregate = {key: float(np.mean([case['metrics'][key] for case in cases])) for key in cases[0]['metrics']}
    for key, value in aggregate.items():
        assert abs(value - registry['final_evaluation']['metrics'][key]) < 1e-12
    summary = dict(cases=cases, aggregate=aggregate, costs=costs, maximum_reconstruction_error=max(errors), nonreplay_scientific_cases=len(cases), cells=sum(1 for episode in registry['final_evaluation']['evaluation_evidence']['episodes'] for case in episode['solution'].values() if not case.get('replay') for cell in case.get('cells', [])))
    summary_path = ROOT / 'derived_summary.json'
    summary_path.write_text(json.dumps(summary, indent=2) + '\n')
    sidecar(summary_path, 'derived')
    supplementary = ROOT / 'supplementary_rows.tex'
    supplementary.write_text('\n'.join(f"{'German' if case['dataset'] == 'german' else 'ACSIncome'} & {case['family'].capitalize()} & {case['seed']} & {case['rank']:.4f} & {case['sign']:.4f} & {case['validation_accuracy']:.4f} " + r'\\' for case in cases) + '\n')
    sidecar(supplementary, 'table')
    seeds = sorted(set(case['seed'] for case in cases))
    def get_case(dataset, family, seed):
        return next(case for case in cases if (case['dataset'], case['family'], case['seed']) == (dataset, family, seed))
    figure, axes = plt.subplots(2, 2, figsize=(5.5, 2.9), sharex=True, layout='constrained')
    for row_index, dataset in enumerate(['german', 'acs']):
        for column_index, metric in enumerate(['repeat_agreement', 'reference_fidelity']):
            axis = axes[row_index, column_index]
            for seed_index, seed in enumerate(seeds):
                entries = [get_case(dataset, family, seed) for family in FAMILIES]
                values = np.array([entry['metrics'][metric] for entry in entries])
                bounds = np.array([entry['intervals'][metric] for entry in entries])
                axis.errorbar(values, np.arange(3) + (seed_index - .5) * .18, xerr=np.stack([values - bounds[:, 0], bounds[:, 1] - values]), fmt=['o', 's'][seed_index], color=COLORS[seed_index], markersize=3.5, linewidth=1, capsize=2, label=str(seed))
            axis.set_yticks(range(3), LABELS)
            axis.invert_yaxis()
            axis.set_xlim(.8, 1.005)
            axis.set_xticks([.8, .9, 1.])
            axis.grid(axis='x', alpha=.2)
            axis.set_title(('German' if dataset == 'german' else 'ACSIncome') + ' · ' + ('Overlap' if metric == 'repeat_agreement' else 'Fidelity'))
    axes[1, 0].set_xlabel('Top-three overlap')
    axes[1, 1].set_xlabel('Reference quality')
    figure.legend(*axes[0, 0].get_legend_handles_labels(), loc='outside upper center', ncol=2, frameon=False, title='Fitted seed')
    save_figure(figure, 'agreement_and_reference_fidelity')
    figure, axes = plt.subplots(1, 2, figsize=(5.5, 1.9), sharex=True, layout='constrained')
    for axis, dataset in zip(axes, ['german', 'acs']):
        for seed_index, seed in enumerate(seeds):
            entries = [get_case(dataset, family, seed) for family in FAMILIES]
            values = np.array([entry['metrics']['matched_budget_gain'] for entry in entries])
            bounds = np.array([entry['intervals']['matched_budget_gain'] for entry in entries])
            axis.errorbar(values, np.arange(3) + (seed_index - .5) * .18, xerr=np.stack([values - bounds[:, 0], bounds[:, 1] - values]), fmt=['o', 's'][seed_index], color=COLORS[seed_index], markersize=3.5, linewidth=1, capsize=2, label=str(seed))
        axis.axvline(0, color='.4', linewidth=.8)
        axis.set_yticks(range(3), LABELS)
        axis.invert_yaxis()
        axis.set_title('German Credit' if dataset == 'german' else 'ACSIncome')
        axis.set_xlim(-.12, .025)
        axis.set_xticks([-.1, -.05, 0])
        axis.set_xlabel('Four-short minus one-long quality')
        axis.grid(axis='x', alpha=.2)
    save_figure(figure, 'budget_allocation_contrast')
    figure, axes = plt.subplots(2, 2, figsize=(5.5, 2.95), sharex=True, sharey=True, layout='constrained')
    for row_index, dataset in enumerate(['german', 'acs']):
        for column_index, seed in enumerate(seeds):
            axis = axes[row_index, column_index]
            for series_index, (method, budget) in enumerate([('studied', '64'), ('studied', '256'), ('library', '64'), ('library', '256')]):
                values = [get_case(dataset, family, seed)['budget_quality'][budget][method] for family in FAMILIES]
                axis.plot(range(3), values, marker=['o', 'o', 's', 's'][series_index], linestyle=['--', '-', '--', '-'][series_index], linewidth=1, markersize=3.5, color=COLORS[series_index], label=('Studied ' if method == 'studied' else 'Library ') + budget)
            axis.set_title(('German' if dataset == 'german' else 'ACSIncome') + ' · ' + str(seed))
            axis.set_xticks(range(3), ['Log.', 'Forest', 'Boost'])
            axis.set_ylim(.72, 1.005)
            axis.grid(axis='y', alpha=.2)
    axes[0, 0].set_ylabel('Reference quality')
    axes[1, 0].set_ylabel('Reference quality')
    figure.legend(*axes[0, 0].get_legend_handles_labels(), loc='outside upper center', ncol=2, frameon=False)
    save_figure(figure, 'deployment_estimator_comparison')
    overview = ROOT / 'figures/fixed_game_overview.png'
    prompt_log = ROOT / 'figures/fixed_game_overview.prompts.json'
    if not (ROOT / '.concept_figure_complete').exists() and not (prompt_log.exists() and prompt_log.read_text().strip() not in ['', '{}']):
        image = Image.new('RGB', (2400, 840), '#f4f7f8')
        draw = ImageDraw.Draw(image)
        draw.text((80, 380), 'Conceptual overview reserved for orchestrator rendering', fill='#42545d', font_size=42)
        image.save(overview)
        prompt_log.write_text('{}\n')
    strategy = json.loads((ROOT / 'paper_strategy.json').read_text())
    manifest = []
    for specification in strategy['figure_specs']:
        identifier = specification['figure_id']
        diagram = identifier == 'fixed_game_overview'
        entry = dict(figure_id=identifier, figure_type='diagram' if diagram else 'composite', path_png='figures/' + identifier + '.png', generator='generate-concept-figure' if diagram else 'matplotlib', source_ids=specification['source_ids'], n_panels=1 if diagram else (2 if identifier == 'budget_allocation_contrast' else 4), placement='full_width', intended_latex_width_fraction=1.0, estimated_min_rendered_font_pt=9 if diagram else 8.5)
        entry.update(panels_per_row=1 if diagram else 2, categories_per_panel=[6] if diagram else [3] * entry['n_panels'], series_per_panel=[0] if diagram else [4 if identifier == 'deployment_estimator_comparison' else 2] * entry['n_panels'], max_label_chars=58 if diagram else 22, font_sizes=dict(title=9, axis=9, ticks=9 if diagram else 8.5, legend=9 if diagram else 8.5), uses_abbrev_labels=not diagram, uses_progression=False)
        if identifier == 'budget_allocation_contrast':
            entry['max_label_chars'] = 33
        if diagram:
            entry['prompt_log_path'] = 'figures/fixed_game_overview.prompts.json'
        else:
            entry['path_pdf'] = 'figures/' + identifier + '.pdf'
            entry['font_sizes'] = dict(title=9, axis=9, ticks=8.5, legend=8.5)
            entry['categories_per_panel'] = [3] * entry['n_panels']
            entry['series_per_panel'] = [4 if identifier == 'deployment_estimator_comparison' else 2] * entry['n_panels']
        manifest.append(entry)
    (ROOT / 'figure_manifest.json').write_text(json.dumps(dict(figures=manifest), indent=2) + '\n')
    print('Reconstructed', len(cases), 'cases;', summary['cells'], 'cells; maximum error', max(errors))
    for case in cases:
        print(case['dataset'], case['family'], case['seed'], {key: round(value, 5) for key, value in case['metrics'].items()})


if __name__ == '__main__':
    main()
