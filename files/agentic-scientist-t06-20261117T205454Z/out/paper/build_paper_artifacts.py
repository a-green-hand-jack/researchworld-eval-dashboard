import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / 'paper_data.json').read_text())
# @evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]
EPISODES = DATA['final_evaluation']['evaluation_evidence']['episodes']
FRACTIONS = [0.001, 0.005, 0.01]
FAMILIES = ['arena', 'nba']
COLORS = {'candidate': '#16697A', 'disagreement': '#B45F06', 'random': '#6D597A'}
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9.5,
                     'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.labelsize': 9.5, 'xtick.labelsize': 9.5,
                     'ytick.labelsize': 9.5, 'legend.fontsize': 9.5,
                     'pdf.fonttype': 42})


def provenance(path, refs):
    sidecar = {'schema_name': 'scientific-evidence.artifact-manifest',
               'artifact': {'path': str(path), 'kind': 'figure' if path.suffix in ('.pdf', '.png') else 'derived',
                            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()},
               'derived_from': ['@' + 'evidence[[' + ref + ']]' for ref in refs],
               'generated_by': {'script_path': 'build_paper_artifacts.py',
                                'command': ['python', 'build_paper_artifacts.py']}}
    Path(str(path) + '.prov.json').write_text(json.dumps(sidecar, indent=2))


def save(figure, stem):
    for extension in ['pdf', 'png']:
        path = Path('figures') / (stem + '.' + extension)
        figure.savefig(path, dpi=450 if extension == 'png' else 300)
        provenance(path, ['paper_data.json#/final_evaluation/evaluation_evidence/episodes', 'build_paper_artifacts.py'])
    plt.close(figure)


def cases(family):
    return [next(case for case in episode['solution']['cases']
                 if case['family'] == family and not case['permuted']) for episode in EPISODES]


def main():
    Path('figures').mkdir(exist_ok=True)
    summary = {'datasets': {}, 'metrics': DATA['final_evaluation']['metrics']}
    figure, axes = plt.subplots(1, 2, figsize=(5.5, 2.85), sharey=True)
    for axis, family in zip(axes, FAMILIES):
        records = cases(family)
        curves = {method: np.array([record['curves'][method] for record in records])
                  for method in COLORS}
        for method in ('candidate', 'disagreement'):
            assert np.all(curves[method] == curves[method][0])
        assert all(all(value == 0 for value in record['curves']['copy']) for record in records)
        offsets = {'candidate': -0.17, 'disagreement': 0, 'random': 0.17}
        for method, label in [('candidate', 'Exact-refit'), ('disagreement', 'High-loss'), ('random', 'Random')]:
            positions = np.arange(3) + offsets[method]
            if method == 'random':
                for seed_index, values in enumerate(curves[method]):
                    axis.scatter(positions + (seed_index - 2) * 0.014, 100 * values,
                                 color=COLORS[method], s=12, alpha=0.35, edgecolors='none')
            axis.scatter(positions, 100 * curves[method].mean(axis=0),
                         marker={'candidate': 'o', 'disagreement': 's', 'random': 'D'}[method],
                         color=COLORS[method], s=34, label=label, zorder=4)
        axis.set_title(('(a) Arena' if family == 'arena' else '(b) NBA'), fontsize=10)
        axis.set_xticks(range(3), ['0.1', '0.5', '1'])
        axis.set_xlabel('Removed rows (%)')
        axis.grid(axis='y', color='#E5E7EB', linewidth=0.6)
        summary['datasets'][family] = {'curves': {key: value.tolist() for key, value in curves.items()},
                                       'means': {key: value.mean(axis=0).tolist() for key, value in curves.items()},
                                       'budgets': [len(mask) for mask in records[0]['candidate_masks']],
                                       'participants': len(records[0]['clean_scores'])}
    axes[0].set_ylabel('Inverted pairs (%)')
    axes[0].set_ylim(-0.08, 2.65)
    handles, labels = axes[0].get_legend_handles_labels()
    figure.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, 1.01), ncol=3,
                  frameon=False, columnspacing=1.1, handletextpad=0.3)
    figure.subplots_adjust(left=0.12, right=0.99, top=0.78, bottom=0.21, wspace=0.17)
    save(figure, 'dataset_budget_comparison')

    bootstrap = EPISODES[0]['solution']['conditional_group_bootstrap']
    assert all(episode['solution']['conditional_group_bootstrap'] == bootstrap for episode in EPISODES)
    figure, axes = plt.subplots(1, 2, figsize=(5.5, 2.75), sharey=True)
    jitter = np.random.default_rng(41)
    for axis, comparator, title in zip(axes, ['disagreement', 'random'], ['(a) Minus high-loss', '(b) Minus random']):
        axis.axhline(0, color='#4B5563', lw=0.8)
        for family_index, family in enumerate(FAMILIES):
            records = bootstrap[family]
            assert len(records) == 32 and all(record['complete'] for record in records)
            gains = np.array([record['gain_' + comparator] for record in records])
            axis.scatter(family_index + jitter.uniform(-0.15, 0.15, len(gains)), 100 * gains,
                         color=['#16697A', '#9C3D54'][family_index], alpha=0.7, s=12, linewidths=0)
            summary['datasets'][family]['bootstrap_' + comparator] = {
                'values': gains.tolist(), 'mean': float(gains.mean()),
                'min': float(gains.min()), 'max': float(gains.max())}
        axis.set_title(title, fontsize=10)
        axis.set_xticks([0, 1], ['Arena', 'NBA'])
        axis.set_xlim(-0.45, 1.45)
        axis.grid(axis='y', color='#E5E7EB', lw=0.6)
    axes[0].set_ylabel('Inversion difference (pp)')
    axes[0].set_ylim(-1, 2.6)
    axes[0].set_yticks([-1, 0, 1, 2])
    figure.supxlabel('Fixed-mask group-weight resampling; no reselection', fontsize=9.5, y=0.02)
    figure.subplots_adjust(left=0.14, right=0.99, top=0.84, bottom=0.24, wspace=0.18)
    save(figure, 'conditional_resampling_contrasts')

    for family in FAMILIES:
        for episode in EPISODES:
            same = [case for case in episode['solution']['cases'] if case['family'] == family]
            assert same[0]['curves'] == same[1]['curves']
    summary['seeds'] = [episode['seed'] for episode in EPISODES]
    Path('analysis_summary.json').write_text(json.dumps(summary, indent=2))
    provenance(Path('analysis_summary.json'), ['paper_data.json#/final_evaluation/evaluation_evidence/episodes'])
    lines = ['\\begin{tabular}{llrrr}', '\\toprule', 'Setting & Removed rows & Exact-refit & High-loss & Random \\\\', '\\midrule']
    for family in FAMILIES:
        values = summary['datasets'][family]
        for budget_index, budget in enumerate(values['budgets']):
            numbers = [100 * values['means'][method][budget_index] for method in COLORS]
            setting = 'Arena' if family == 'arena' else 'NBA'
            lines.append(f"{setting} & {budget} & " + ' & '.join(f'{value:.3f}' for value in numbers) + r' \\')
    lines.extend(['\\bottomrule', '\\end{tabular}'])
    Path('results_table.tex').write_text('% @evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]\n' + '\n'.join(lines))
    provenance(Path('results_table.tex'), ['paper_data.json#/final_evaluation/evaluation_evidence/episodes'])
    lines = [r'\begin{tabular}{rrrrr}', r'\toprule', r' & \multicolumn{2}{c}{Arena} & \multicolumn{2}{c}{NBA} \\', r'Draw & vs. high-loss & vs. random & vs. high-loss & vs. random \\', r'\midrule']
    for index in range(32):
        values = [100 * bootstrap[family][index]['gain_' + comparator] for family in FAMILIES for comparator in ['disagreement', 'random']]
        lines.append(str(index + 1) + ' & ' + ' & '.join(f'{value:+.3f}' for value in values) + r' \\')
    lines.extend([r'\bottomrule', r'\end{tabular}'])
    Path('bootstrap_table.tex').write_text('% @evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes/0/solution/conditional_group_bootstrap]]\n' + '\n'.join(lines))
    provenance(Path('bootstrap_table.tex'), ['paper_data.json#/final_evaluation/evaluation_evidence/episodes/0/solution/conditional_group_bootstrap'])

    strategy = json.loads(Path('paper_strategy.json').read_text())
    manifest = {'figures': []}
    for spec in strategy['figure_specs']:
        identifier = spec['figure_id']
        conceptual = spec['figure_type'] == 'diagram'
        if conceptual and not Path('.concept_figure_complete').exists():
            log = Path('figures', identifier + '.prompts.json')
            if not log.exists() or not json.loads(log.read_text()):
                if not Path('figures', identifier + '.png').exists():
                    image = Image.new('RGB', (2400, 1158), '#FAFAFA')
                    ImageDraw.Draw(image).text((850, 560), 'Overview reserved for synchronous rendering', fill='#555555')
                    image.save(Path('figures', identifier + '.png'))
                if not log.exists():
                    log.write_text('{}\n')
        entry = {'figure_id': identifier, 'figure_type': spec['figure_type'],
                 'files': {'png': 'figures/' + identifier + '.png'},
                 'panel_count': spec['max_panels'], 'panels_per_row': spec['max_panels_per_row'],
                 'panels': [{'panel_id': str(index), 'category_count': spec['max_categories_per_panel'],
                             'series_count': spec['max_series_per_panel'], 'content': spec['purpose']}
                            for index in range(spec['max_panels'])],
                 'uses_progression': False, 'generator': spec['preferred_generator'],
                 'placement': 'full_width', 'intended_latex_width_fraction': spec['target_width_fraction'],
                 'estimated_min_rendered_font_pt': 9.3, 'min_font_size_pt': 9.5,
                 'required': True, 'source_ids': spec['source_ids']}
        if conceptual:
            entry['prompt_log_path'] = 'figures/' + identifier + '.prompts.json'
            entry['note'] = 'Guarded placeholder; synchronous renderer owns the final overview.'
        else:
            entry['files']['pdf'] = 'figures/' + identifier + '.pdf'
            entry['note'] = 'Canonical scatter type; layout follows the strategy content specification.'
        manifest['figures'].append(entry)
    Path('figure_manifest.json').write_text(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
