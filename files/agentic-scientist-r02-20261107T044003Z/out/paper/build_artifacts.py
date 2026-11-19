import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
FIGURES = ROOT / 'figures'
DERIVED = ROOT / 'derived'
TABLES = ROOT / 'tables'
for directory in (FIGURES, DERIVED, TABLES):
    directory.mkdir(exist_ok=True)

REGISTRY = json.loads((ROOT / 'paper_data.json').read_text())
EPISODES = REGISTRY['final_evaluation']['evaluation_evidence']['episodes']
METHODS = ('euclidean', 'ilr', 'adaptive')
NAMES = {'euclidean': 'Euclidean', 'ilr': 'ILR ball', 'adaptive': 'Adaptive ILR'}
COLORS = {'euclidean': '#527a9d', 'ilr': '#c98b31', 'adaptive': '#258779'}
CASES = ('C1', 'C2', 'C3', 'C4', 'C5', 'C6')
LABELS = ['Homosk.', 'Heterosk.', 'Boundary', 'Shifted', 'Constant', 'Unpaired']
SOURCE = '@evidence[[paper_data.json#final_evaluation.evaluation_evidence.episodes]]'
SEARCH_SOURCE = '@evidence[[paper_data.json#all_programs]]'

def provenance(path, source=SOURCE):
    relative = str(path.relative_to(ROOT))
    sidecar = {
        'schema_name': 'scientific-evidence.artifact-manifest',
        'artifact': {'path': relative, 'kind': 'figure' if path.suffix in ('.png', '.pdf') else 'derived',
                     'sha256': hashlib.sha256(path.read_bytes()).hexdigest()},
        'derived_from': [source, '@evidence[[build_artifacts.py]]'],
        'generated_by': {'script_path': 'build_artifacts.py', 'command': ['python', 'build_artifacts.py'], 'cwd': '.'},
    }
    Path(str(path) + '.prov.json').write_text(json.dumps(sidecar, indent=2) + '\n')

def write_json(path, payload, source=SOURCE):
    path.write_text(json.dumps(payload, indent=2) + '\n')
    provenance(path, source)

def values(case, method):
    return case['details']['candidate'] if method == 'adaptive' else case['details']['baselines'][method]

def array(field, method):
    return np.array([[values(case, method)[field] for case in episode['solution']['cases']] for episode in EPISODES])

plt.rcParams.update({'font.size': 9, 'axes.labelsize': 9, 'axes.titlesize': 9,
                     'xtick.labelsize': 8.5, 'ytick.labelsize': 8.5, 'legend.fontsize': 8.5,
                     'font.family': 'DejaVu Sans', 'pdf.fonttype': 42, 'axes.spines.top': False,
                     'axes.spines.right': False, 'axes.grid': True, 'grid.alpha': 0.16,
                     'savefig.dpi': 300})

def export(figure, identifier):
    for suffix in ('pdf', 'png'):
        path = FIGURES / f'{identifier}.{suffix}'
        figure.savefig(path, dpi=300, facecolor='white')
        provenance(path, SEARCH_SOURCE if identifier.startswith('search_') else SOURCE)
    plt.close(figure)

figure, axes = plt.subplots(2, 1, figsize=(5.5, 3.8), sharex=True)
for metric, axis, ylabel in zip(('coverage', 'volume'), axes, ('Joint coverage', 'Simplex-volume fraction')):
    for method_index, method in enumerate(METHODS):
        matrix = array(metric, method)
        centers = np.arange(len(CASES)) + (method_index - 1) * .20
        for seed_index in range(len(EPISODES)):
            jitter = (seed_index - (len(EPISODES) - 1) / 2) * .021
            axis.scatter(centers + jitter, matrix[seed_index], s=10, color=COLORS[method], alpha=.55, linewidths=0)
        axis.scatter(centers, matrix.mean(axis=0), s=38, marker='_', linewidth=2,
                     color=COLORS[method], label=NAMES[method], zorder=4)
    axis.set_ylabel(ylabel)
    axis.axvline(3.5, color='#888888', lw=.6, ls=':')
    axis.set_ylim((.55, 1.025) if metric == 'coverage' else (-.04, 1.04))
axes[0].axhline(.9, color='#555555', lw=.9, ls='--')
handles, labels = axes[0].get_legend_handles_labels()
figure.legend(handles, labels, ncol=3, loc='upper center', frameon=False, handletextpad=.4, columnspacing=1)
axes[1].set_xticks(np.arange(len(CASES)), LABELS)
figure.subplots_adjust(left=.14, right=.98, top=.90, bottom=.08, hspace=.11)
export(figure, 'coverage_volume_by_regime')

figure, axes = plt.subplots(1, 2, figsize=(5.5, 2.25), sharey=True)
stratum_labels = [r'$x_1<0$', r'$x_1\geq0$', r'$x_2<0$', r'$x_2\geq0$']
for case_index, axis, title in zip((1, 3), axes, ('Heteroskedastic', 'Shifted')):
    for method_index, method in enumerate(METHODS):
        matrix = np.array([values(episode['solution']['cases'][case_index], method)['strata'] for episode in EPISODES])
        centers = np.arange(4) + (method_index - 1) * .18
        for seed_index in range(len(EPISODES)):
            axis.scatter(centers + (seed_index - 2) * .018, matrix[seed_index], s=9,
                         color=COLORS[method], alpha=.55, linewidths=0)
        axis.scatter(centers, matrix.mean(axis=0), marker='_', s=40, color=COLORS[method], linewidth=2,
                     label=NAMES[method], zorder=4)
    axis.axhline(.9, color='#555555', ls='--', lw=.8)
    axis.set_xticks(np.arange(4), stratum_labels)
    axis.set_title(title)
    axis.set_ylim(.5, 1.035)
axes[0].set_ylabel('Stratum coverage')
handles, labels = axes[0].get_legend_handles_labels()
figure.legend(handles, labels, loc='lower center', ncol=3, frameon=False, bbox_to_anchor=(.53, 0))
figure.subplots_adjust(left=.12, right=.98, top=.87, bottom=.28, wspace=.12)
export(figure, 'descriptive_sign_strata')

search_models = [REGISTRY['all_programs'][index] for index in (0, 1, 2)]
search_names = ['Single split', 'Four-fold', 'Interpolated']
search_colors = ['#777777', COLORS['adaptive'], '#8865a9']
figure, axes = plt.subplots(2, 1, figsize=(5.5, 3.5), sharex=True)
search_summary = []
for model_index, model in enumerate(search_models):
    seed_cases = [episode['solution']['cases'] for episode in model['evaluation_evidence']['episodes']]
    item = {'configuration': search_names[model_index], 'seeds': [episode['seed'] for episode in model['evaluation_evidence']['episodes']]}
    for field, axis in zip(('coverage', 'volume'), axes):
        matrix = np.array([[case[field] for case in cases] for cases in seed_cases])
        item[field + '_means'] = matrix.mean(axis=0).tolist()
        centers = np.arange(6) + (model_index - 1) * .2
        for seed_index in range(matrix.shape[0]):
            axis.scatter(centers + (seed_index - 1) * .025, matrix[seed_index], s=12,
                         color=search_colors[model_index], alpha=.6, linewidths=0)
        axis.scatter(centers, matrix.mean(axis=0), s=40, marker='_', linewidth=2,
                     color=search_colors[model_index], label=search_names[model_index])
        axis.axvline(3.5, ls=':', lw=.6, color='#888888')
    search_summary.append(item)
axes[0].axhline(.9, ls='--', color='#555555', lw=.8)
axes[0].set_ylabel('Joint coverage')
axes[0].set_ylim(.78, 1.01)
axes[1].set_ylabel('Simplex-volume fraction')
axes[1].set_ylim(-.04, 1.04)
axes[1].set_xticks(np.arange(6), LABELS)
handles, labels = axes[0].get_legend_handles_labels()
figure.legend(handles, labels, ncol=3, loc='upper center', frameon=False, columnspacing=.7)
figure.subplots_adjust(left=.14, right=.98, top=.90, bottom=.09, hspace=.12)
export(figure, 'search_configuration_comparison')
write_json(DERIVED / 'search_comparison.json', search_summary, SEARCH_SOURCE)

overview = FIGURES / 'geometry_calibration_overview.png'
prompt_log = FIGURES / 'geometry_calibration_overview.prompts.json'
rendered = (ROOT / '.concept_figure_complete').exists()
if prompt_log.exists():
    rendered = rendered or bool(json.loads(prompt_log.read_text()))
if not rendered and not overview.exists():
    image = Image.new('RGB', (2400, 676), 'white')
    ImageDraw.Draw(image).text((35, 35), 'Overview figure pending orchestrator rendering', fill='#777777')
    image.save(overview, dpi=(300, 300))
if not prompt_log.exists():
    prompt_log.write_text('{}\n')

summary = {method: {field: {'mean_by_condition': array(field, method).mean(axis=0).tolist(),
                           'seed_sd_by_condition': array(field, method).std(axis=0, ddof=1).tolist()}
                   for field in ('coverage', 'volume')} for method in METHODS}
summary['labels'] = dict(zip(CASES, LABELS))
summary['paired_bootstrap_95'] = EPISODES[0]['solution']['paired_seed_bootstrap_comparisons95']
summary['qualification'] = {key: REGISTRY['grounding_sources']['final.qualification.' + key]['value']
                            for key in ('status', 'outcome', 'correct')}
summary['duration_seconds'] = [episode['duration_seconds'] for episode in EPISODES]
write_json(DERIVED / 'summary.json', summary)
rows = []
for episode in EPISODES:
    for case in episode['solution']['cases']:
        for method in METHODS:
            result = values(case, method)
            row = {'seed': episode['seed'], 'condition': case['case'], 'method': NAMES[method]}
            row.update({key: value for key, value in result.items() if key != 'coverage_indicators'})
            row['paired_volume_mc_se_vs_adaptive'] = None if method == 'adaptive' else case['details']['paired_volume_mc_se'][method]
            row['empty_strata_indices'] = [0, 2] if case['case'] == 'C5' else []
            rows.append(row)
write_json(DERIVED / 'complete_results.json', rows)

lines = [r'% @evidence[[paper_data.json#final_evaluation.evaluation_evidence.episodes]]',
         r'\begin{tabular}{lrrrrrr}', r'\toprule',
         r'& \multicolumn{3}{c}{Joint coverage} & \multicolumn{3}{c}{Simplex-volume fraction} \\',
         r'Condition & Euclid. & ILR ball & Adaptive & Euclid. & ILR ball & Adaptive \\', r'\midrule']
for case_index, label in enumerate(LABELS):
    numbers = [summary[method][field]['mean_by_condition'][case_index]
               for field in ('coverage', 'volume') for method in METHODS]
    lines.append(label + ' & ' + ' & '.join(f'{value:.4f}' for value in numbers) + r' \\')
lines.extend([r'\bottomrule', r'\end{tabular}'])
path = TABLES / 'condition_means.tex'
path.write_text('\n'.join(lines) + '\n')
provenance(path)

lines = [r'% @evidence[[paper_data.json#final_evaluation.evaluation_evidence.episodes]]',
         r'\begin{longtable}{rrlrrrr}', r'\caption{Complete held-out seed-level measurements. Coverage intervals are Wilson intervals; volume SE is conditional Monte Carlo integration error, not between-seed variability.}\\',
         r'\toprule', r'Seed & Case & Method & Coverage & Wilson 95\% & Volume & MC SE \\', r'\midrule\endfirsthead',
         r'\toprule Seed & Case & Method & Coverage & Wilson 95\% & Volume & MC SE \\ \midrule\endhead']
for row in rows:
    low, high = row['coverage_wilson95']
    lines.append(f"{row['seed']} & {row['condition']} & {row['method']} & {row['coverage']:.4f} & [{low:.4f},{high:.4f}] & {row['volume']:.4f} & {row['volume_mc_se']:.5f}" + r' \\')
lines.extend([r'\bottomrule', r'\end{longtable}'])
path = TABLES / 'seed_results.tex'
path.write_text('\n'.join(lines) + '\n')
provenance(path)

manuscript_path = ROOT / 'paper.tex'
if manuscript_path.exists():
    manuscript = manuscript_path.read_text()
    start = '% BEGIN GENERATED SEED RESULTS'
    end = '% END GENERATED SEED RESULTS'
    generated = start + '\n' + '\n'.join(lines) + '\n' + end
    if start in manuscript:
        before, remainder = manuscript.split(start, 1)
        _, after = remainder.split(end, 1)
        manuscript = before + generated + after
    else:
        manuscript = manuscript.replace(r'\input{tables/seed_results.tex}', generated)
    manuscript_path.write_text(manuscript)

figures = []
for identifier, panels, categories in [('geometry_calibration_overview', 1, [6]),
                                     ('coverage_volume_by_regime', 2, [6, 6]),
                                     ('descriptive_sign_strata', 2, [4, 4]),
                                     ('search_configuration_comparison', 2, [6, 6])]:
    conceptual = identifier == 'geometry_calibration_overview'
    figures.append({'figure_id': identifier, 'figure_type': 'diagram' if conceptual else 'scatter',
                    'path_png': 'figures/' + identifier + '.png',
                    **({} if conceptual else {'path_pdf': 'figures/' + identifier + '.pdf'}),
                    'n_panels': panels, 'categories_per_panel': categories,
                    'series_per_panel': [3] * panels, 'generator': 'generate-concept-figure' if conceptual else 'matplotlib',
                    **({'prompt_log_path': 'figures/' + identifier + '.prompts.json'} if conceptual else {}),
                    'source_ids': ['result.top_program_01', 'result.top_program_02', 'result.top_program_03'] if identifier.startswith('search_') else ['final.evidence.episodes'],
                    'placement': 'full_width', 'intended_latex_width_fraction': 1.0,
                    'panels_per_row': 2 if identifier == 'descriptive_sign_strata' else 1,
                    'max_label_chars': 30, 'uses_abbrev_labels': True,
                    'uses_progression': False,
                    'estimated_min_rendered_font_pt': 8.5,
                    'font_sizes': {'title': 9, 'axis': 9, 'ticks': 8.5, 'legend': 8.5}})
(ROOT / 'figure_manifest.json').write_text(json.dumps({'figures': figures}, indent=2) + '\n')
print(json.dumps(summary, indent=2))
