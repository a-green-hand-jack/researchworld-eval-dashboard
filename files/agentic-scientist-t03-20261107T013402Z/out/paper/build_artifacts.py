import argparse
import ast
import hashlib
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent
COLORS = {'standard': '#c17b14', 'multistart': '#956ba5', 'structure': '#176b8c'}
CASE_NAMES = {'german_logistic': 'German / logistic', 'german_forest': 'German / forest', 'acs_logistic': 'ACS / logistic', 'acs_forest': 'ACS / forest'}
PLOT_SCALE = 8 / 5.5
PLOT_FONT_SIZES = {key: size * PLOT_SCALE for key, size in {'title': 10, 'axis': 10, 'ticks': 9, 'legend': 9}.items()}
plt.rcParams.update({'font.size': 10, 'axes.labelsize': 10, 'axes.titlesize': 10, 'xtick.labelsize': 9, 'ytick.labelsize': 9, 'legend.fontsize': 9, 'pdf.fonttype': 42, 'ps.fonttype': 42, 'axes.spines.top': False, 'axes.spines.right': False})
for setting in ('font.size', 'axes.labelsize', 'axes.titlesize', 'xtick.labelsize', 'ytick.labelsize', 'legend.fontsize', 'axes.linewidth', 'axes.labelpad', 'axes.titlepad', 'lines.linewidth', 'lines.markeredgewidth', 'grid.linewidth', 'patch.linewidth', 'xtick.major.size', 'xtick.major.width', 'xtick.major.pad', 'xtick.minor.size', 'xtick.minor.width', 'ytick.major.size', 'ytick.major.width', 'ytick.major.pad', 'ytick.minor.size', 'ytick.minor.width'):
    plt.rcParams[setting] *= PLOT_SCALE


def provenance(path, inputs):
    manifest = {'schema_name': 'scientific-evidence.artifact-manifest', 'artifact': {'path': str(path), 'kind': 'figure' if str(path).endswith(('.png', '.pdf')) else 'derived', 'sha256': hashlib.sha256(Path(path).read_bytes()).hexdigest()}, 'derived_from': inputs, 'generated_by': {'script_path': 'build_artifacts.py', 'command': ['python', 'build_artifacts.py', *sys.argv[1:]]}}
    Path(str(path) + '.prov.json').write_text(json.dumps(manifest, indent=2))


def save_plot(figure, figure_id, inputs):
    for extension in ('pdf', 'png'):
        output = Path('figures') / (figure_id + '.' + extension)
        figure.savefig(output, dpi=300)
        provenance(output, inputs)
    plt.close(figure)


def get_caps():
    tree = ast.parse(Path('source_evidence/evaluation/evaluate_final.py').read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if isinstance(key, ast.Constant) and key.value == 'budgets' and isinstance(value, ast.IfExp):
                    return ast.literal_eval(value.orelse.orelse), ast.literal_eval(value.orelse.body)
    raise RuntimeError('No grounded budget configuration')


def selected_cases(episodes):
    return [(episode['seed'], case) for episode in episodes for case in episode['solution']['cases'] if case['case'] != 'controls' and not case['replay']]


def main(figures_only=False):
    Path('figures').mkdir(exist_ok=True)
    Path('tables').mkdir(exist_ok=True)
    data = json.loads(Path('paper_data.json').read_text())
    final_caps, development_caps = get_caps()
    final_episodes = data['final_evaluation']['evaluation_evidence']['episodes']
    final = selected_cases(final_episodes)
    source = ['@evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]']
    rows = []
    for seed, case in final:
        observations = case['observations']
        cells = np.asarray(case['cells'])
        repeat_pairs = np.asarray(case['repeat_pairs'])
        for cap_index, cap in enumerate(final_caps):
            rows.append({'seed': seed, 'case': case['case'], 'cap': cap, 'structure': cells[cap_index].mean(axis=(0, 1)).tolist(), 'standard': observations['baseline_metrics']['standard'][cap_index], 'multistart': observations['baseline_metrics']['multistart'][cap_index], 'repeat': repeat_pairs[cap_index].mean(axis=(0, 1)).tolist(), 'bootstrap_ci95': observations['fidelity_instance_bootstrap_ci95']})
    summary = {'final': rows, 'final_caps': final_caps, 'development_caps': development_caps}
    # @evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]
    summary['reference_sign_mean'] = float(np.mean([row['structure'][2] for row in rows]))
    summary['min_reference_sign'] = float(min(row['structure'][2] for row in rows))
    summary['max_repeat_vector_difference'] = float(max(np.ptp(np.asarray(case['observations']['attributions']), axis=1).max() for seed, case in final))
    summary['reference_uncertainty'] = {name: float(np.mean([np.mean(case['observations']['reference_uncertainty']) for seed, case in final if case['case'] == name])) for name in CASE_NAMES}
    figure, axes = plt.subplots(2, 2, figsize=(8, 3.85 * PLOT_SCALE), sharex=True, sharey=True)
    markers = {'standard': 'o', 'multistart': 's', 'structure': 'D'}
    labels = {'standard': 'Library one-shot', 'multistart': 'Two-start, split cap', 'structure': 'Structure-aware'}
    for axis, name in zip(axes.flat, CASE_NAMES):
        for offset, method in enumerate(labels):
            means = []
            for cap_index, cap in enumerate(final_caps):
                values = [row[method][0] for row in rows if row['case'] == name and row['cap'] == cap]
                positions = np.full(len(values), cap_index + (offset - 1) * .1)
                axis.scatter(positions, values, color=COLORS[method], marker=markers[method], alpha=.5, s=13 * PLOT_SCALE ** 2, zorder=4)
                means.append(np.mean(values))
            axis.plot(np.arange(len(final_caps)) + (offset - 1) * .1, means, color=COLORS[method], marker=markers[method], markersize=4 * PLOT_SCALE, label=labels[method], linewidth=1.1 * PLOT_SCALE)
        axis.set_title(CASE_NAMES[name] + '\n' + ('approximate reference' if name.startswith('german') else 'exhaustive reference'), pad=5 * PLOT_SCALE)
        axis.set_xticks(range(len(final_caps)), final_caps)
        axis.set_ylim(0, 1.05)
        axis.set_yticks([0, .5, 1])
        axis.grid(axis='y', alpha=.18)
    for axis in axes[1]:
        axis.set_xlabel('Coalition cap')
    for axis in axes[:, 0]:
        axis.set_ylabel('Reference agreement')
    handles, legend_labels = axes[0, 0].get_legend_handles_labels()
    figure.legend(handles, legend_labels, loc='lower center', ncol=3, frameon=False, handlelength=1.1, columnspacing=.7)
    figure.subplots_adjust(left=.12, right=.985, top=.88, bottom=.20, hspace=.72, wspace=.22)
    save_plot(figure, 'final_reference_comparison', source)
    # @evidence[[paper_data.json#/all_programs]]
    development = []
    for config_index, config in enumerate(data['all_programs']):
        for seed, case in selected_cases(config['evaluation_evidence']['episodes']):
            for cap_index, cap in enumerate(development_caps):
                development.append({'configuration': config_index, 'seed': seed, 'case': case['case'], 'cap': cap, 'agreement': float(np.asarray(case['cells'])[cap_index, :, :, 0].mean())})
    summary['development'] = development
    figure, axes = plt.subplots(1, 2, figsize=(8, 2.65 * PLOT_SCALE), sharey=True)
    for axis, kind, before, after in zip(axes, ('forest', 'logistic'), (0, 1), (1, 2)):
        categories = [(dataset + '_' + kind, cap) for dataset in ('german', 'acs') for cap in development_caps]
        for config_index, offset, color, label in ((before, -.09, '#9b9b9b', 'Without component'), (after, .09, '#176b8c', 'With component')):
            for category_index, (name, cap) in enumerate(categories):
                values = [row['agreement'] for row in development if row['configuration'] == config_index and row['case'] == name and row['cap'] == cap]
                axis.scatter(np.full(len(values), category_index + offset), values, color=color, s=19 * PLOT_SCALE ** 2, label=label if category_index == 0 else None, zorder=3)
                axis.plot([category_index + offset - .055, category_index + offset + .055], [np.mean(values)] * 2, color=color, linewidth=2 * PLOT_SCALE)
        axis.set_xticks(range(len(categories)), [name.split('_')[0].replace('german', 'Ger').replace('acs', 'ACS') + '\n' + str(cap) for name, cap in categories])
        axis.set_title('Exact forest component' if kind == 'forest' else 'Logistic integration component')
        axis.set_ylim(.80, 1.01)
        axis.set_yticks([.8, .9, 1.])
        axis.grid(axis='y', alpha=.18)
    axes[0].set_ylabel('Reference agreement')
    figure.legend(*axes[0].get_legend_handles_labels(), loc='lower center', ncol=2, frameon=False)
    figure.subplots_adjust(left=.12, right=.985, top=.85, bottom=.28, wspace=.25)
    save_plot(figure, 'component_comparison', ['@evidence[[paper_data.json#/all_programs]]'])
    figure, axes = plt.subplots(1, 2, figsize=(8, 2.65 * PLOT_SCALE))
    for axis, name in zip(axes, ('german_logistic', 'german_forest')):
        for seed, case in final:
            if case['case'] != name:
                continue
            reference = np.asarray(case['observations']['reference'])
            estimate = np.asarray(case['observations']['attributions'])[0, 0]
            half_difference = np.abs(np.asarray(case['observations']['reference_uncertainty'])).sum(axis=-1)
            observed_distance = np.abs(estimate - reference).sum(axis=-1)
            axis.scatter(half_difference, observed_distance, alpha=.6, s=12 * PLOT_SCALE ** 2)
        maximum = max(axis.get_xlim()[1], axis.get_ylim()[1])
        axis.plot([0, maximum], [0, maximum], color='#777777', linestyle='--', linewidth=.8 * PLOT_SCALE)
        axis.set_title(CASE_NAMES[name])
        axis.set_xlabel('Reference half-difference, L1')
        axis.set_xlim(left=0)
        axis.set_ylim(bottom=0)
        axis.grid(alpha=.15)
    axes[0].set_ylabel('Estimate-to-reference L1')
    figure.subplots_adjust(left=.13, right=.98, bottom=.25, top=.86, wspace=.40)
    save_plot(figure, 'reference_diagnostics', source)
    if figures_only:
        manifest_path = Path('figure_manifest.json')
        manifest = json.loads(manifest_path.read_text())
        for entry in manifest['figures']:
            if entry['figure_id'] in ('final_reference_comparison', 'component_comparison', 'reference_diagnostics'):
                entry['font_sizes'] = PLOT_FONT_SIZES.copy()
        manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
        return
    concept = Path('figures/fixed_game_overview.png')
    log = Path('figures/fixed_game_overview.prompts.json')
    if not Path('.concept_figure_complete').exists() and not (log.exists() and json.loads(log.read_text())) and not concept.exists():
        image = Image.new('RGB', (2400, 680), 'white')
        drawing = ImageDraw.Draw(image)
        drawing.text((80, 300), 'Conceptual overview reserved for synchronous rendering', fill='#555555')
        image.save(concept)
        log.write_text('{}\n')
    Path('analysis_summary.json').write_text(json.dumps(summary, indent=2))
    provenance(Path('analysis_summary.json'), source + ['@evidence[[paper_data.json#/all_programs]]'])
    table_lines = []
    for name in CASE_NAMES:
        chosen = [row for row in rows if row['case'] == name and row['cap'] == final_caps[0]]
        means = {method: np.mean([row[method][0] for row in chosen]) for method in labels}
        signs = np.mean([row['structure'][2] for row in chosen])
        table_lines.append(f"{CASE_NAMES[name]} & {means['standard']:.4f} & {means['multistart']:.4f} & {means['structure']:.4f} & {signs:.4f} \\\\")
    Path('tables/main_rows.tex').write_text('% @evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]\n' + '\n'.join(table_lines) + '\n')
    provenance(Path('tables/main_rows.tex'), source)
    extended = []
    for row in rows:
        extended.append(f"{row['seed']} & {CASE_NAMES[row['case']]} & {row['cap']} & {row['standard'][0]:.4f} & {row['multistart'][0]:.4f} & {row['structure'][0]:.4f} \\\\")
    Path('tables/extended_rows.tex').write_text('% @evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]\n' + '\n'.join(extended) + '\n')
    provenance(Path('tables/extended_rows.tex'), source)
    intervals = []
    for seed, case in final:
        interval = case['observations']['fidelity_instance_bootstrap_ci95']
        intervals.append(f"{seed} & {CASE_NAMES[case['case']]} & [{interval[0]:.10f}, {interval[1]:.10f}] \\\\")
    Path('tables/interval_rows.tex').write_text('% @evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]\n' + '\n'.join(intervals) + '\n')
    provenance(Path('tables/interval_rows.tex'), source)
    specs = json.loads(Path('paper_strategy.json').read_text())['figure_specs']
    figures = []
    for spec in specs:
        figure_id = spec['figure_id']
        concept_figure = spec['preferred_generator'] == 'generate-concept-figure'
        entry = {'figure_id': figure_id, 'figure_type': spec['figure_type'], 'generator': spec['preferred_generator'], 'path_png': 'figures/' + figure_id + '.png', 'n_panels': spec['max_panels'], 'n_rows': 2 if figure_id == 'final_reference_comparison' else 1, 'n_cols': 2 if spec['max_panels'] > 1 else 1, 'source_ids': spec['source_ids'], 'categories_per_panel': [spec['max_categories_per_panel']] * spec['max_panels'], 'series_per_panel': [spec['max_series_per_panel']] * spec['max_panels'], 'font_sizes': {'title': 10, 'axis': 10, 'ticks': 9, 'legend': 9}, 'placement': 'full_width', 'intended_latex_width_fraction': 1.0, 'estimated_min_rendered_font_pt': 9.0}
        if concept_figure:
            entry['prompt_log_path'] = 'figures/' + figure_id + '.prompts.json'
        else:
            entry['path_pdf'] = 'figures/' + figure_id + '.pdf'
        figures.append(entry)
    figures.append({'figure_id': 'reference_diagnostics', 'figure_type': 'scatter', 'generator': 'matplotlib', 'path_pdf': 'figures/reference_diagnostics.pdf', 'path_png': 'figures/reference_diagnostics.png', 'n_panels': 2, 'n_rows': 1, 'n_cols': 2, 'categories_per_panel': [0, 0], 'series_per_panel': [3, 3], 'source_ids': ['final.evidence.episodes'], 'font_sizes': {'title': 10, 'axis': 10, 'ticks': 9, 'legend': 9}, 'placement': 'full_width', 'intended_latex_width_fraction': 1.0, 'estimated_min_rendered_font_pt': 9.0})
    for entry in figures:
        entry['panels_per_row'] = entry.pop('n_cols')
        entry.pop('n_rows')
        entry['max_label_chars'] = 29
        entry['uses_abbrev_labels'] = True
        entry['uses_progression'] = False
        if entry['figure_type'] in ('grouped_dot', 'paired_dot'):
            entry['figure_type'] = 'scatter'
        if entry['generator'] == 'matplotlib':
            entry['font_sizes'] = PLOT_FONT_SIZES.copy()
    Path('figure_manifest.json').write_text(json.dumps({'figures': figures}, indent=2))
    print('Final reference sign mean:', summary['reference_sign_mean'])
    print('Reference uncertainty:', summary['reference_uncertainty'])
    print('Repeat vector max difference:', summary['max_repeat_vector_difference'])
    for name in CASE_NAMES:
        print(name, [[round(np.mean([row[method][0] for row in rows if row['case'] == name and row['cap'] == cap]), 6) for cap in final_caps] for method in labels])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--figures-only', action='store_true', help='Regenerate quantitative figures and update their manifest metadata without rewriting tables or summaries.')
    main(figures_only=parser.parse_args().figures_only)
