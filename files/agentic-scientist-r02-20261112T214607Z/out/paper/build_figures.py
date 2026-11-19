import hashlib
import json
import shutil
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent
FIGURES = ROOT / 'figures'
FIGURES.mkdir(exist_ok=True)
DATA = json.loads((ROOT / 'paper_data.json').read_text())
EPISODES = DATA['final_evaluation']['evaluation_evidence']['episodes']
# @evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]
METHODS = [('Local scale', 'variants', 'actual', '#176b87'),
           ('Global ILR', 'baselines', 'global_ilr', '#db7b24'),
           ('Raw L-infinity', 'baselines', 'raw_linf', '#747a87'),
           ('Bonferroni', 'baselines', 'bonferroni', '#8e63a9')]
CASES = ['H3', 'H10', 'B3', 'B10', 'S3', 'S10']
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9,
                     'axes.labelsize': 9, 'axes.titlesize': 10,
                     'xtick.labelsize': 8, 'ytick.labelsize': 8,
                     'legend.fontsize': 8, 'pdf.fonttype': 42,
                     'axes.spines.top': False, 'axes.spines.right': False})


def provenance(path, sources, kind='figure'):
    sidecar = dict(schema_name='scientific-evidence.artifact-manifest',
                   artifact=dict(path=str(path.relative_to(ROOT)), kind=kind,
                                 sha256=hashlib.sha256(path.read_bytes()).hexdigest()),
                   derived_from=sources,
                   generated_by=dict(script_path='build_figures.py',
                                     command=['python', 'build_figures.py']))
    Path(str(path) + '.prov.json').write_text(json.dumps(sidecar, indent=2) + '\n')


def values(case, group, method, field, level=None):
    records = [next(item for item in episode['solution']['cases'] if item['case'] == case)
               [group][method] for episode in EPISODES]
    if level is not None:
        return np.array([record['details'][level][field] for record in records])
    return np.array([record[field] for record in records])


def export(figure, name):
    for extension in ['pdf', 'png']:
        path = FIGURES / (name + '.' + extension)
        figure.savefig(path, dpi=300)
        provenance(path, ['@evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]'])
    plt.close(figure)


def main():
    summary = {'seeds': [episode['seed'] for episode in EPISODES], 'cases': {}, 'aggregate': {}}
    for case in CASES:
        summary['cases'][case] = {}
        for label, group, method, color in METHODS:
            record = {}
            for field in ['utility', 'mass', 'marginal', 'group']:
                samples = values(case, group, method, field)
                record[field] = dict(mean=float(samples.mean()), sd=float(samples.std(ddof=1)),
                                     seeds=samples.tolist())
            record['coverage'] = [values(case, group, method, 'coverage', level).tolist() for level in [0, 1]]
            summary['cases'][case][method] = record
        for method in ['constant', 'permuted']:
            summary['cases'][case][method] = {
                field: values(case, 'variants', method, field).tolist()
                for field in ['utility', 'mass', 'marginal', 'group']}
    for label, group, method, color in METHODS:
        summary['aggregate'][method] = {
            field: float(np.mean([values(case, group, method, field) for case in CASES]))
            for field in ['utility', 'mass', 'marginal', 'group']}
    summary['paired_intervals'] = EPISODES[0]['solution']['paired_seed_intervals']
    path = ROOT / 'analysis_summary.json'
    path.write_text(json.dumps(summary, indent=2) + '\n')
    provenance(path, ['@evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]'], 'derived')

    table_directory = ROOT / 'tables'
    table_directory.mkdir(exist_ok=True)
    lines = [r'\begin{tabular}{lrrrr}', r'\toprule',
             r'Condition & Local & Global ILR & Raw $L_\infty$ & Bonferroni\\', r'\midrule']
    group_lines = [r'\begin{tabular}{lrrrr}', r'\toprule',
                   r'Condition & $E_g$ local & $E_g$ global & $M$ local & $M$ global\\', r'\midrule']
    for case in CASES:
        cells = [f"${summary['cases'][case][method]['utility']['mean']:.4f}"
                 f"\\pm{summary['cases'][case][method]['utility']['sd']:.4f}$"
                 for label, group, method, color in METHODS]
        lines.append(case + ' & ' + ' & '.join(cells) + r'\\')
        cells = [f"{summary['cases'][case][method][field]['mean']:.5f}"
                 for field, method in [('group', 'actual'), ('group', 'global_ilr'),
                                       ('mass', 'actual'), ('mass', 'global_ilr')]]
        group_lines.append(case + ' & ' + ' & '.join(cells) + r'\\')
    for name, contents in [('condition_utility', lines), ('group_mass', group_lines)]:
        contents.extend([r'\bottomrule', r'\end{tabular}'])
        table_path = table_directory / (name + '.tex')
        table_path.write_text('\n'.join(contents) + '\n')
        provenance(table_path, ['@evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]'], 'table')

    figure, axes = plt.subplots(2, 2, figsize=(5.5, 4.2), sharex=True, sharey=True)
    for panel, (dimension, level) in enumerate([(3, 0), (10, 0), (3, 1), (10, 1)]):
        axis = axes.flat[panel]
        nominal = 1 - EPISODES[0]['solution']['cases'][0]['variants']['actual']['details'][level]['alpha']
        axis.axhline(nominal, color='black', linestyle='--', linewidth=.8)
        for method_index, (label, group, method, color) in enumerate(METHODS):
            for condition_index, condition in enumerate(['H', 'B', 'S']):
                samples = values(condition + str(dimension), group, method, 'coverage', level)
                position = condition_index + (method_index - 1.5) * .16
                axis.scatter(position + np.linspace(-.026, .026, len(samples)), samples,
                             s=10, alpha=.65, color=color, edgecolors='none')
                axis.plot(position, samples.mean(), marker='_', markersize=9, color=color,
                          markeredgewidth=1.6, linestyle='none', label=label if condition_index == 0 else None)
        axis.set_title(f'({chr(97 + panel)}) D={dimension}, nominal {nominal:.2f}')
        axis.set_xticks(range(3), ['H', 'B', 'S'])
        axis.set_xlim(-.5, 2.5)
        axis.set_ylim(.60, 1.005)
        axis.grid(axis='y', alpha=.18)
        if panel % 2 == 0:
            axis.set_ylabel('Joint coverage')
    figure.legend(*axes[0, 0].get_legend_handles_labels(), loc='lower center', ncol=2,
                  frameon=False, bbox_to_anchor=(.5, -.005))
    figure.subplots_adjust(left=.12, right=.98, top=.92, bottom=.19, hspace=.4, wspace=.18)
    export(figure, 'coverage_by_condition')

    figure, axes = plt.subplots(1, 2, figsize=(5.5, 2.5), sharey=True)
    for panel, dimension in enumerate([3, 10]):
        axis = axes[panel]
        for method_index, (label, group, method, color) in enumerate(METHODS):
            for condition_index, condition in enumerate(['H', 'B', 'S']):
                samples = values(condition + str(dimension), group, method, 'mass')
                position = condition_index + (method_index - 1.5) * .16
                axis.scatter(position + np.linspace(-.026, .026, len(samples)), samples,
                             s=10, alpha=.65, color=color, edgecolors='none')
                axis.plot(position, samples.mean(), marker='_', markersize=9, color=color,
                          markeredgewidth=1.6, linestyle='none', label=label if condition_index == 0 else None)
        axis.set_xticks(range(3), ['H', 'B', 'S'])
        axis.set_title(f'({chr(97 + panel)}) D={dimension}')
        axis.set_ylim(0, .8)
        axis.set_xlim(-.5, 2.5)
        axis.grid(axis='y', alpha=.18)
    axes[0].set_ylabel('Reference mass')
    figure.legend(*axes[0].get_legend_handles_labels(), loc='lower center', ncol=2,
                  frameon=False, bbox_to_anchor=(.5, -.02))
    figure.subplots_adjust(left=.12, right=.98, top=.85, bottom=.32, wspace=.18)
    export(figure, 'reference_mass_by_condition')

    complete = ROOT / '.concept_figure_complete'
    prompt = FIGURES / 'conceptual_overview.prompts.json'
    if not complete.exists() and (not prompt.exists() or prompt.read_text().strip() in ['', '{}']):
        image = Image.new('RGB', (2400, 830), 'white')
        draw = ImageDraw.Draw(image)
        draw.rectangle((20, 20, 2380, 810), outline='#cccccc', width=3)
        draw.text((80, 350), 'Conceptual overview reserved for orchestrator rendering', fill='#555555')
        image.save(FIGURES / 'conceptual_overview.png')
        prompt.write_text('{}\n')

    manifest = []
    for name, panel_count, rows in [('conceptual_overview', 1, 1),
                                    ('coverage_by_condition', 4, 2),
                                    ('reference_mass_by_condition', 2, 2)]:
        concept = name == 'conceptual_overview'
        item = dict(figure_id=name, figure_type='diagram' if concept else 'composite',
                    path_png=f'figures/{name}.png', n_panels=panel_count, panels_per_row=rows,
                    categories_per_panel=[6 if concept else 3] * panel_count,
                    series_per_panel=[1 if concept else 4] * panel_count,
                    max_label_chars=24, uses_abbrev_labels=True, uses_progression=False,
                    generator='generate-concept-figure' if concept else 'matplotlib',
                    source_ids=[] if concept else ['final.evidence.episodes'],
                    placement='full_width', intended_latex_width_fraction=1.0,
                    estimated_min_rendered_font_pt=8,
                    font_sizes=dict(title=10, axis=9, ticks=8, legend=8))
        if concept:
            item['prompt_log_path'] = 'figures/conceptual_overview.prompts.json'
        else:
            item['path_pdf'] = f'figures/{name}.pdf'
        manifest.append(item)
    (ROOT / 'figure_manifest.json').write_text(json.dumps(dict(figures=manifest), indent=2) + '\n')


if __name__ == '__main__':
    main()
