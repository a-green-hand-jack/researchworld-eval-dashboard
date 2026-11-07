import datetime
import hashlib
import json
import re
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / 'paper_data.json').read_text())
EPISODES = DATA['final_evaluation']['evaluation_evidence']['episodes']
# @evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]
PROTOCOL = json.loads(json.loads((ROOT / 'source_evidence/task_contract.json').read_text())['method']['description'])
NOMINAL = [float(value) for value in re.search(r'Fractions ([.0-9,]+) of', PROTOCOL['scientific_workload']).group(1).split(',')]
# @evidence[[source_evidence/task_contract.json#/method]]
CASES = [case['case'] for case in EPISODES[0]['solution']['cases']]
LABELS = ['Arena', 'NBA 11', 'NBA 12', 'NBA 13', 'NBA 14', 'NBA 15']
METHODS = ['candidate', 'random_flip_score', 'degree_matched_score', 'margin_heuristic_score']
NAMES = ['Guided refit', 'Uniform', 'Degree-stratified', 'Small margin']
COLORS = ['#0072B2', '#777777', '#009E73', '#D55E00']
MARKERS = ['o', 's', '^', 'D']
FIGURES = ROOT / 'figures'
FIGURES.mkdir(exist_ok=True)
plt.rcParams.update({'font.size': 9, 'axes.labelsize': 9, 'axes.titlesize': 9,
                     'xtick.labelsize': 8, 'ytick.labelsize': 8,
                     'legend.fontsize': 8, 'font.family': 'DejaVu Sans',
                     'pdf.fonttype': 42, 'ps.fonttype': 42,
                     'axes.spines.top': False, 'axes.spines.right': False})


def sidecar(path, inputs=None):
    payload = {
        'schema_name': 'scientific-evidence.artifact-manifest',
        'artifact': {'path': str(path.relative_to(ROOT)), 'kind': 'figure' if path.suffix in ['.png', '.pdf'] else 'derived-data',
                     'sha256': hashlib.sha256(path.read_bytes()).hexdigest()},
        'derived_from': inputs or ['@evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]'],
        'generated_by': {'script_path': 'build_figures.py', 'command': ['python', 'build_figures.py']}}
    Path(str(path) + '.prov.json').write_text(json.dumps(payload, indent=2))


def save(figure, figure_id):
    for extension in ['pdf', 'png']:
        path = FIGURES / f'{figure_id}.{extension}'
        options = {'dpi': 300, 'facecolor': 'white'}
        if extension == 'png':
            options['dpi'] = max(300, 2400 / figure.get_figwidth())
            options['pil_kwargs'] = {'dpi': (300, 300)}
        figure.savefig(path, **options)
        sidecar(path)
    plt.close(figure)


def curves(case_name, method):
    values = []
    for episode in EPISODES:
        case = next(case for case in episode['solution']['cases'] if case['case'] == case_name)
        values.append(case['candidate_curves'] if method == 'candidate' else case['baseline_curves'][method])
    return np.asarray(values)


def overview_placeholder():
    image_path = FIGURES / 'sensitivity_overview.png'
    log_path = FIGURES / 'sensitivity_overview.prompts.json'
    if (ROOT / '.concept_figure_complete').exists():
        return
    if log_path.exists() and json.loads(log_path.read_text()):
        return
    if not image_path.exists():
        image = Image.new('RGB', (2400, 740), 'white')
        draw = ImageDraw.Draw(image)
        draw.text((100, 330), 'Concept overview reserved for orchestrator rendering', fill='#777777')
        image.save(image_path)
    if not log_path.exists():
        log_path.write_text('{}\n')


overview_placeholder()
figure, axes = plt.subplots(3, 1, figsize=(5.5, 3.95), sharex=True, sharey=True)
figure.subplots_adjust(left=.12, right=.98, bottom=.12, top=.83, hspace=.29)
for budget, axis in enumerate(axes):
    for method_index, method in enumerate(METHODS):
        values = [curves(case, method).mean(axis=0)[budget] * 100 for case in CASES]
        axis.plot(np.arange(len(CASES)) + (method_index - 1.5) * .12, values,
                  marker=MARKERS[method_index], linestyle='none', markersize=4.5,
                  color=COLORS[method_index], label=NAMES[method_index])
    axis.set_title(f'({chr(97 + budget)}) Nominal edits: {100 * NOMINAL[budget]:.1f}%', loc='left', pad=2)
    axis.set_ylim(-.3, 12.2)
    axis.set_yticks([0, 5, 10])
    axis.grid(axis='y', alpha=.18)
    axis.set_ylabel('Disruption (%)')
axes[-1].set_xticks(np.arange(len(CASES)), LABELS)
figure.legend(*axes[0].get_legend_handles_labels(), ncol=2, loc='upper center', frameon=False,
              bbox_to_anchor=(.53, 1), columnspacing=1.4)
save(figure, 'final_disruption_comparison')

figure, axes = plt.subplots(3, 1, figsize=(5.5, 4.95), sharex=True)
figure.subplots_adjust(left=.15, right=.98, bottom=.105, top=.91, hspace=.39)
styles = ['solid', 'dashed', 'dotted']
for baseline_index, axis in enumerate(axes):
    method = METHODS[baseline_index + 1]
    for seed_index, episode in enumerate(EPISODES):
        for case_index, case in enumerate(episode['solution']['cases']):
            low, high = np.asarray(case['paired_intervals'][method]) * 100
            axis.plot([low, high], [case_index + (seed_index - 1) * .19] * 2,
                      color=COLORS[baseline_index + 1], linewidth=1.35, linestyle=styles[seed_index])
    axis.axvline(0, color='black', linewidth=.7)
    axis.set_yticks(np.arange(len(CASES)), LABELS)
    axis.invert_yaxis()
    axis.set_title(f'({chr(97 + baseline_index)}) Guided refit minus {NAMES[baseline_index + 1].lower()}', loc='left', pad=3)
    axis.set_xlim(-2.5, 8.4)
    axis.grid(axis='x', alpha=.16)
axes[-1].set_xlabel('Paired disruption difference (percentage points)')
legend_lines = [plt.Line2D([], [], color='#333333', linestyle=style, label=f'Seed {episode["seed"]}')
                for episode, style in zip(EPISODES, styles)]
figure.legend(handles=legend_lines, ncol=3, loc='upper center', frameon=False,
              bbox_to_anchor=(.56, 1))
save(figure, 'paired_effect_uncertainty')

summary = {'seeds': [episode['seed'] for episode in EPISODES], 'cases': {}}
for case_index, case_name in enumerate(CASES):
    summary['cases'][case_name] = {method: curves(case_name, method).mean(axis=0).tolist() for method in METHODS}
    summary['cases'][case_name]['counts'] = EPISODES[0]['solution']['cases'][case_index]['counts']
    summary['cases'][case_name]['seed_budget_means'] = {
        method: curves(case_name, method).mean(axis=1).tolist() for method in METHODS}
summary_path = ROOT / 'derived_summary.json'
summary_path.write_text(json.dumps(summary, indent=2))
sidecar(summary_path)

table = ['\\begin{tabular}{lrrrrrr}', '\\toprule',
         'Panel & $p$ & Edges & Min. degree & $k_{.001}$ & $k_{.005}$ & $k_{.01}$\\\\', '\\midrule']
for case, label in zip(EPISODES[0]['solution']['cases'], LABELS):
    graph = case['graph']
    entries = [graph['participants'], graph['edges'], graph['minimum_degree'], *case['counts']]
    table.append(label + ' & ' + ' & '.join(map(str, entries)) + '\\\\')
table += ['\\bottomrule', '\\end{tabular}']
table_path = ROOT / 'panel_table.tex'
table_path.write_text('\n'.join(table) + '\n')
sidecar(table_path)

table = ['\\begin{tabular}{llrrrr}', '\\toprule',
         'Panel & Seed & Guided & Uniform & Degree & Margin\\\\', '\\midrule']
for case_name, label in zip(CASES, LABELS):
    for seed_index, episode in enumerate(EPISODES):
        means = [curves(case_name, method)[seed_index].mean() * 100 for method in METHODS]
        table.append(f'{label} & {episode["seed"]} & ' + ' & '.join(f'{value:.3f}' for value in means) + '\\\\')
table += ['\\bottomrule', '\\end{tabular}']
table_path = ROOT / 'seed_table.tex'
table_path.write_text('\n'.join(table) + '\n')
sidecar(table_path)

specs = json.loads((ROOT / 'paper_strategy.json').read_text())['figure_specs']
manifest_path = ROOT / 'figure_manifest.json'
existing_figures = {
    entry['figure_id']: entry
    for entry in json.loads(manifest_path.read_text()).get('figures', [])
} if manifest_path.exists() else {}
manifest = {'figures': []}
for spec in specs:
    concept = spec['figure_type'] == 'diagram'
    figure_id = spec['figure_id']
    if concept and figure_id in existing_figures:
        manifest['figures'].append(existing_figures[figure_id])
        continue
    panels = 2 if concept else 3
    entry = {
        'figure_id': figure_id, 'figure_type': spec['figure_type'],
        'files': {'png': f'figures/{figure_id}.png', **({} if concept else {'pdf': f'figures/{figure_id}.pdf'})},
        'panel_count': panels,
        'panels': [{'label': chr(97 + index), 'category_count': 6,
                    'series_count': 1 if concept else (4 if figure_id == 'final_disruption_comparison' else 3)}
                   for index in range(panels)],
        'uses_progression': False, 'generator': 'generate-concept-figure' if concept else 'matplotlib',
        'source_ids': ['final.evidence.episodes'], 'placement': 'full_width',
        'intended_latex_width_fraction': 1., 'estimated_min_rendered_font_pt': 9 if concept else 8,
        'min_font_size_pt': 9 if concept else 8, 'panels_per_row': 2 if concept else 1,
        'uses_abbrev_labels': True, 'required': True}
    if concept:
        entry['prompt_log_path'] = f'figures/{figure_id}.prompts.json'
    manifest['figures'].append(entry)
(ROOT / 'figure_manifest.json').write_text(json.dumps(manifest, indent=2))
print('Generated descriptive plots and tables from sealed final evidence; no fits or evaluations rerun.')
