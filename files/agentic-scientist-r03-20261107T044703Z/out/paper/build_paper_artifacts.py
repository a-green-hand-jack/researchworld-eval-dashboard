import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent
FIGURES = ROOT / 'figures'
TABLES = ROOT / 'tables'
FIGURES.mkdir(exist_ok=True)
TABLES.mkdir(exist_ok=True)
PAYLOAD = json.loads((ROOT / 'paper_data.json').read_text())
EPISODES = PAYLOAD['final_evaluation']['evaluation_evidence']['episodes']
METRICS = PAYLOAD['final_evaluation']['metrics']
METHODS = ['studied', 'random_lowrank', 'selected_ridge', 'medoid_ridge', 'copy', 'constant']
LABELS = ['Variance LF', 'Random LF', 'Info ridge', 'Medoid ridge', 'Mean offset', 'Means']
COLORS = ['#007A87', '#777777', '#B96328', '#6571A5', '#9A7C42', '#A3A3A3']
SEEDS = [episode['seed'] for episode in EPISODES]
CONDITIONS = [('mteb', 'model'), ('mteb', 'family'), ('open_llm', 'model'), ('open_llm', 'family')]
SOURCE_LABELS = {'mteb': 'MTEB', 'open_llm': 'Open LLM'}
SPLIT_LABELS = {'model': 'Model split', 'family': 'Name-family split'}
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9,
    'axes.titlesize': 9, 'axes.labelsize': 9, 'xtick.labelsize': 8.5,
    'ytick.labelsize': 8.5, 'axes.spines.top': False, 'axes.spines.right': False,
    'pdf.fonttype': 42, 'ps.fonttype': 42})


def sidecar(path, kind, sources=None):
    record = {'schema_name': 'scientific-evidence.artifact-manifest',
        'artifact': {'path': str(path.relative_to(ROOT)), 'kind': kind},
        'derived_from': sources or ['@evidence[[paper_data.json#final_evaluation.evaluation_evidence.episodes]]'],
        'generated_by': {'script_path': 'build_paper_artifacts.py', 'command': ['python', 'build_paper_artifacts.py']}}
    Path(str(path) + '.prov.json').write_text(json.dumps(record, indent=2))


def save_figure(figure, name):
    for extension in ['pdf', 'png']:
        path = FIGURES / (name + '.' + extension)
        figure.savefig(path, dpi=300)
        sidecar(path, 'figure')
    plt.close(figure)


def case(seed, source, split, control=False):
    episode = next(item for item in EPISODES if item['seed'] == seed)
    return next(item for item in episode['solution']['cases'] if item['source'] == source
        and item['split'] == split and item['control'] == control and not item['replay'])


def method_score(item, method):
    return item['score'] if method == 'studied' else item['baselines'][method]


def write_table(name, content):
    path = TABLES / (name + '.tex')
    path.write_text('% @evidence[[paper_data.json#final_evaluation.evaluation_evidence.episodes]]\n' + content)
    sidecar(path, 'table')


def placeholder():
    if (ROOT / '.concept_figure_complete').exists():
        return
    prompt = FIGURES / 'concept_overview.prompts.json'
    if prompt.exists() and json.loads(prompt.read_text()):
        return
    image_path = FIGURES / 'concept_overview.png'
    if not image_path.exists():
        image = Image.new('RGB', (2400, 742), 'white')
        drawing = ImageDraw.Draw(image)
        drawing.text((90, 320), 'Conceptual overview reserved for orchestrator rendering', fill='#777777', font_size=44)
        image.save(image_path)
    if not prompt.exists():
        prompt.write_text('{}\n')


def main():
    # @evidence[[paper_data.json#final_evaluation.evaluation_evidence.episodes]]
    # @evidence[[paper_data.json#final_evaluation.metrics]]
    summary = {'seeds': SEEDS, 'conditions': {}}
    for source, split in CONDITIONS:
        summary['conditions'][source + '/' + split] = {
            method: {'scores': [method_score(case(seed, source, split), method) for seed in SEEDS],
                'mean': float(np.mean([method_score(case(seed, source, split), method) for seed in SEEDS])),
                'sd': float(np.std([method_score(case(seed, source, split), method) for seed in SEEDS], ddof=1))}
            for method in METHODS}
    summary['checkpoints'] = {'mteb': [1, 2, 4, 8], 'open_llm': [1, 2, 3]}
    (ROOT / 'derived_results.json').write_text(json.dumps(summary, indent=2))
    sidecar(ROOT / 'derived_results.json', 'derived')
    figure, axes = plt.subplots(2, 2, figsize=(5.5, 3.85), sharex=True, sharey=True)
    for panel_index, ((source, split), axis) in enumerate(zip(CONDITIONS, axes.flat)):
        for method_index, method in enumerate(METHODS):
            values = np.array(summary['conditions'][source + '/' + split][method]['scores'])
            axis.scatter(values, method_index + np.linspace(-.13, .13, len(SEEDS)),
                s=17, color=COLORS[method_index], alpha=.55, edgecolors='none')
            axis.scatter(values.mean(), method_index, s=38, color=COLORS[method_index], marker='D',
                edgecolors='white', linewidths=.5, zorder=4)
        axis.set_title('(' + 'abcd'[panel_index] + ') ' + SOURCE_LABELS[source] + ' · ' + SPLIT_LABELS[split])
        axis.set_yticks(range(len(METHODS)), LABELS)
        axis.set_xlim(.885, .973)
        axis.set_xticks([.90, .93, .96])
        axis.grid(axis='x', color='#dddddd', linewidth=.5)
    axes[0, 0].invert_yaxis()
    figure.supxlabel('Normalized prediction score (1 − MAE)', fontsize=9, y=.015)
    figure.subplots_adjust(left=.19, right=.985, top=.92, bottom=.13, hspace=.40, wspace=.17)
    save_figure(figure, 'main_comparison')

    figure, axes = plt.subplots(1, 2, figsize=(5.5, 2.22), sharey=True)
    for source, axis in zip(['mteb', 'open_llm'], axes):
        for split_index, split in enumerate(['model', 'family']):
            for seed_index, seed in enumerate(SEEDS):
                horizontal = np.array([0, 1]) + (seed_index - 1) * .055
                values = [case(seed, source, split, control)['score'] for control in [False, True]]
                axis.plot(horizontal, values, color=['#007A87', '#6571A5'][split_index],
                    marker=['o', 's'][split_index], markersize=4, linewidth=.8, alpha=.8,
                    label=SPLIT_LABELS[split] if seed_index == 0 else None)
        axis.set_title(SOURCE_LABELS[source])
        axis.set_xticks([0, 1], ['Aligned', 'Deranged'])
        axis.set_xlim(-.2, 1.2)
        axis.set_ylim(.895, .975)
        axis.set_yticks([.90, .93, .96])
        axis.grid(axis='y', color='#dddddd', linewidth=.5)
    axes[0].set_ylabel('Prediction score')
    axes[1].legend(loc='lower left', frameon=False, fontsize=8.5)
    figure.subplots_adjust(left=.12, right=.98, top=.86, bottom=.23, wspace=.15)
    save_figure(figure, 'historical_dependence_control')

    figure, axes = plt.subplots(1, 2, figsize=(5.5, 2.35), sharey=True)
    for source, axis in zip(['mteb', 'open_llm'], axes):
        for split_index, split in enumerate(['model', 'family']):
            for seed_index, seed in enumerate(SEEDS):
                axis.plot(summary['checkpoints'][source], case(seed, source, split)['curve'],
                    color=['#007A87', '#6571A5'][split_index], marker=['o', 's'][split_index],
                    linewidth=.8, markersize=3, alpha=.7,
                    label=SPLIT_LABELS[split] if seed_index == 0 else None)
        axis.set_xticks(summary['checkpoints'][source])
        axis.set_xlabel('Purchased benchmarks')
        axis.set_title(SOURCE_LABELS[source])
        axis.grid(axis='y', color='#dddddd', linewidth=.5)
    axes[0].set_ylabel('Prediction score')
    axes[1].legend(frameon=False, fontsize=8.5, loc='lower right')
    figure.subplots_adjust(left=.12, right=.98, top=.86, bottom=.23, wspace=.15)
    save_figure(figure, 'budget_sensitivity')

    metric_keys = ['combined_score', 'random_lowrank_score', 'selected_ridge_score', 'medoid_ridge_score', 'copy_score', 'constant_score']
    rows = ['\\begin{tabular}{lrr}\\toprule Method & Score $\\uparrow$ & MAE $\\downarrow$ \\\\ \\midrule']
    for label, metric in zip(LABELS, metric_keys):
        rows.append(f'{label} & {METRICS[metric]:.4f} & {1 - METRICS[metric]:.4f} \\\\')
    rows.append('\\bottomrule\\end{tabular}')
    write_table('pooled', '\n'.join(rows))

    rows = ['\\begin{tabular}{llrrrrrr}\\toprule Source & Split/seed & Var LF & Rand LF & Info R & Med R & Offset & Means \\\\ \\midrule']
    for source, split in CONDITIONS:
        for seed in SEEDS:
            item = case(seed, source, split)
            values = ' & '.join(f'{method_score(item, method):.4f}' for method in METHODS)
            rows.append(SOURCE_LABELS[source] + ' & ' + ('M' if split == 'model' else 'F') + '/' + str(seed) + ' & ' + values + ' \\\\')
        rows.append('\\addlinespace')
    rows.append('\\bottomrule\\end{tabular}')
    write_table('seed_scores', '\n'.join(rows))

    rows = ['\\begin{tabular}{llrr}\\toprule Source & Split/seed & Aligned & Deranged \\\\ \\midrule']
    for source, split in CONDITIONS:
        for seed in SEEDS:
            rows.append(SOURCE_LABELS[source] + ' & ' + ('M' if split == 'model' else 'F') + '/' + str(seed)
                + f" & {case(seed, source, split)['score']:.4f} & {case(seed, source, split, True)['score']:.4f} \\\\")
    rows.append('\\bottomrule\\end{tabular}')
    write_table('controls', '\n'.join(rows))
    placeholder()
    entries = []
    for name, figure_type, count, categories, series in [
        ('concept_overview', 'diagram', 1, 6, 3),
        ('main_comparison', 'scatter', 4, 6, 4),
        ('historical_dependence_control', 'scatter', 2, 2, 2),
        ('budget_sensitivity', 'line', 2, 4, 2)]:
        entry = {'figure_id': name, 'figure_type': figure_type,
            'files': {'png': 'figures/' + name + '.png'}, 'panel_count': count,
            'panels': [{'panel_id': str(index), 'category_count': categories, 'series_count': series} for index in range(count)],
            'uses_progression': False, 'generator': 'matplotlib', 'placement': 'full_width',
            'intended_latex_width_fraction': 1.0, 'estimated_min_rendered_font_pt': 8.5,
            'min_font_size_pt': 8.5, 'panels_per_row': 2 if count > 1 else 1,
            'font_sizes': {'title': 9, 'axis': 9, 'ticks': 8.5, 'legend': 8.5},
            'source_ids': ['final.evidence.episodes']}
        if name == 'concept_overview':
            entry.update(generator='generate-concept-figure', prompt_log_path='figures/concept_overview.prompts.json',
                estimated_min_rendered_font_pt=9.0, min_font_size_pt=9.0,
                font_sizes={'title': 9, 'axis': 9, 'ticks': 9, 'legend': 9},
                source_ids=['final.evidence.episodes', 'study.selection_kind'])
        else:
            entry['files']['pdf'] = 'figures/' + name + '.pdf'
        entries.append(entry)
    (ROOT / 'figure_manifest.json').write_text(json.dumps({'figures': entries}, indent=2))


if __name__ == '__main__':
    main()
