import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parent
METHODS = ['Column mean', 'Query mean', 'Random low-rank', 'Variance low-rank', 'Linear ridge', 'Residual transfer']
COLORS = ['#888888', '#bb9944', '#8064a2', '#d48232', '#408c87', '#2464a6']


def provenance(path, kind='figure'):
    payload = dict(schema_name='scientific-evidence.artifact-manifest',
                   artifact=dict(path=str(path), kind=kind, sha256=hashlib.sha256(path.read_bytes()).hexdigest()),
                   derived_from=['@evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]', '@evidence[[build_paper_artifacts.py]]'],
                   generated_by=dict(script_path='build_paper_artifacts.py', command=['python', 'build_paper_artifacts.py']))
    Path(str(path) + '.prov.json').write_text(json.dumps(payload, indent=2))


def save_plot(figure, stem):
    for extension in ['pdf', 'png']:
        path = ROOT / 'figures' / (stem + '.' + extension)
        figure.savefig(path, dpi=600, facecolor='white')
        provenance(path.relative_to(ROOT))
    plt.close(figure)


def main():
    """@evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]
    @evidence[[source_evidence/evaluate_final.py#L970-L1045]]
    """
    payload = json.loads((ROOT / 'paper_data.json').read_text())
    final = payload['final_evaluation']
    episodes = final['evaluation_evidence']['episodes']
    seeds = [episode['seed'] for episode in episodes]
    arrays = {}
    for case in ['A', 'B', 'C', 'D']:
        arrays[case] = []
        for episode in episodes:
            condition = episode['solution']['cases'][case]
            baselines = np.asarray(condition['baseline_mae_by_method_row_checkpoint'])
            studied = np.asarray(condition['mae_by_row_checkpoint'])[None, :, :]
            arrays[case].append(np.concatenate([baselines, studied], axis=0).mean(axis=1))
        arrays[case] = np.asarray(arrays[case])
    primary_seed = (arrays['A'].mean(axis=2) + arrays['B'].mean(axis=2)) / 2
    primary = primary_seed.mean(axis=0)
    assert np.isclose(primary[-1], final['metrics']['mae'], atol=1e-14)
    assert np.isclose(primary[:-1].min(), final['metrics']['baseline_mae'], atol=1e-14)
    budget = (arrays['A'][:, -1].mean(axis=0) + arrays['B'][:, -1].mean(axis=0)) / 2
    for index, count in enumerate([1, 2, 4, 8]):
        assert np.isclose(budget[index], final['metrics']['mae_k' + str(count)], atol=1e-14)
    summary = dict(seeds=seeds, methods=METHODS, primary_mean=primary.tolist(),
                   primary_seed=primary_seed.tolist(), primary_seed_sd=primary_seed.std(axis=0, ddof=1).tolist(),
                   cases={case:dict(seed_budget=values.tolist(), mean_budget=values.mean(axis=0).tolist(), mean=values.mean(axis=(0, 2)).tolist(), seed_sd=values.mean(axis=2).std(axis=0, ddof=1).tolist()) for case, values in arrays.items()},
                   relative_reduction=float((primary[:-1].min() - primary[-1]) / primary[:-1].min()),
                   changing_target_mae={case:float(np.mean([np.asarray(episode['solution']['cases'][case]['all_unqueried_mae_by_row_checkpoint']).mean() for episode in episodes])) for case in arrays})
    gain_intervals = resample_bounds(episodes)
    summary['baseline_gain_bounds'] = gain_intervals.tolist()
    assert np.isclose(gain_intervals[0].min(), final['metrics']['gain_ci_low'])
    assert np.isclose(gain_intervals[1].min(), final['metrics']['gain_ci_high'])
    (ROOT / 'derived_results.json').write_text(json.dumps(summary, indent=2))
    provenance(Path('derived_results.json'), 'derived')
    create_tables(summary)
    plt.rcParams.update({'font.size': 9, 'axes.labelsize': 9, 'axes.titlesize': 10, 'legend.fontsize': 9, 'xtick.labelsize': 9, 'ytick.labelsize': 9, 'pdf.fonttype': 42, 'axes.spines.top': False, 'axes.spines.right': False})
    figure, axes = plt.subplots(1, 2, figsize=(5.5, 2.65), sharey=True)
    series = [5, 2, 3, 4]
    for axis, case, title in zip(axes, ['A', 'B'], ['(a) Model holdout', '(b) Family holdout']):
        for method in series:
            mean = arrays[case][:, method].mean(axis=0)
            deviation = arrays[case][:, method].std(axis=0, ddof=1)
            axis.errorbar(range(4), mean, yerr=deviation, color=COLORS[method], marker='o', markersize=3.5, capsize=2, linewidth=1.4, label=METHODS[method])
        axis.set(xticks=range(4), xticklabels=['1', '2', '4', '8'], xlabel='Queried columns, k', title=title, ylim=(0.025, 0.067))
        axis.grid(axis='y', alpha=.16)
    axes[0].set_ylabel('Sealed-target MAE')
    handles, labels = axes[0].get_legend_handles_labels()
    figure.legend(handles, labels, loc='lower center', ncol=2, frameon=False, columnspacing=1.1)
    figure.subplots_adjust(left=.12, right=.98, bottom=.37, top=.87, wspace=.12)
    save_plot(figure, 'budget_comparison')
    figure, axis = plt.subplots(figsize=(4.95, 1.95))
    for offset, method in zip([-.12, 0, .12], [5, 0, 3]):
        means = [arrays[case][:, method].mean() for case in ['A', 'C', 'D']]
        deviation = [arrays[case][:, method].mean(axis=1).std(ddof=1) for case in ['A', 'C', 'D']]
        axis.errorbar(np.arange(3) + offset, means, yerr=deviation, color=COLORS[method], marker='o', capsize=3, linestyle='none', markersize=5, label=METHODS[method])
    axis.set(xticks=range(3), xticklabels=['Intact', 'Constant', 'Column-shifted'], ylabel='Sealed-target MAE', ylim=(.025, .082))
    axis.grid(axis='y', alpha=.16)
    figure.legend(loc='lower center', ncol=3, frameon=False, columnspacing=.7, handletextpad=.3)
    figure.subplots_adjust(left=.14, right=.98, bottom=.30, top=.95)
    save_plot(figure, 'history_structure_controls')
    create_overview_placeholder()
    create_manifest()


def resample_bounds(episodes):
    """@evidence[[source_evidence/evaluate_final.py#L999-L1017]]"""
    groups = sorted({group for episode in episodes for case in ['A', 'B'] for group in episode['solution']['cases'][case]['resampling_components']})
    group_index = {group: index for index, group in enumerate(groups)}
    rng = np.random.default_rng(424242)
    samples = np.zeros((400, 5))
    for resample in range(len(samples)):
        multiplicity = np.bincount(rng.integers(len(groups), size=len(groups)), minlength=len(groups))
        for episode in episodes:
            for case in ['A', 'B']:
                condition = episode['solution']['cases'][case]
                weights = np.asarray([multiplicity[group_index[group]] for group in condition['resampling_components']], dtype=float)
                if weights.sum() == 0:
                    samples[resample] -= np.ones(5) / (2 * len(episodes))
                else:
                    gains = np.asarray(condition['baseline_mae_by_method_row_checkpoint']).mean(axis=2) - np.asarray(condition['mae_by_row_checkpoint']).mean(axis=1)
                    samples[resample] += gains @ weights / weights.sum() / (2 * len(episodes))
    return np.quantile(samples, [.005, .995], axis=0)


def create_tables(summary):
    evidence = '% @evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]\n'
    lines = [evidence, r'\begin{tabular}{lrrr}', r'\toprule', r'Estimator & Model holdout & Family holdout & Overall \\', r'\midrule']
    for index, method in enumerate(METHODS):
        means = [summary['cases'][case]['mean'][index] for case in ['A', 'B']] + [summary['primary_mean'][index]]
        lines.append(method + ' & ' + ' & '.join(f'{value:.5f}' for value in means) + r' \\')
    lines.extend([r'\bottomrule', r'\end{tabular}'])
    Path('tables/main_comparison.tex').write_text('\n'.join(lines) + '\n')
    lines = [evidence, r'\begin{tabular}{llrrrr}', r'\toprule', r'Holdout & Estimator & $k=1$ & $k=2$ & $k=4$ & $k=8$ \\', r'\midrule']
    for case, label in [('A', 'Model'), ('B', 'Family')]:
        for index, method in enumerate(METHODS):
            values = summary['cases'][case]['mean_budget'][index]
            lines.append(label + ' & ' + method + ' & ' + ' & '.join(f'{value:.5f}' for value in values) + r' \\')
        if case == 'A':
            lines.append(r'\midrule')
    lines.extend([r'\bottomrule', r'\end{tabular}'])
    Path('tables/budget_details.tex').write_text('\n'.join(lines) + '\n')
    lines = [evidence, r'\begin{tabular}{lrrrrrr}', r'\toprule', r'Seed & Col. mean & Query mean & Random LR & Var. LR & Ridge & Studied \\', r'\midrule']
    for seed, values in zip(summary['seeds'], summary['primary_seed']):
        lines.append(str(seed) + ' & ' + ' & '.join(f'{value:.5f}' for value in values) + r' \\')
    lines.append(r'\midrule')
    lines.append('Seed SD & ' + ' & '.join(f'{value:.5f}' for value in summary['primary_seed_sd']) + r' \\')
    lines.extend([r'\bottomrule', r'\end{tabular}'])
    Path('tables/seed_details.tex').write_text('\n'.join(lines) + '\n')
    for path in Path('tables').glob('*.tex'):
        provenance(path, 'table')


def create_overview_placeholder():
    if Path('.concept_figure_complete').exists():
        return
    prompt_path = Path('figures/method_overview.prompts.json')
    if prompt_path.exists() and json.loads(prompt_path.read_text()):
        return
    image_path = Path('figures/method_overview.png')
    if not image_path.exists():
        from PIL import Image, ImageDraw
        image = Image.new('RGB', (2400, 950), 'white')
        draw = ImageDraw.Draw(image)
        draw.text((70, 70), 'Overview reserved for synchronous concept-figure rendering', fill='#555555', font_size=42)
        image.save(image_path)
    if not prompt_path.exists():
        prompt_path.write_text('{}\n')


def create_manifest():
    common = dict(placement='full_width', intended_latex_width_fraction=1.0, estimated_min_rendered_font_pt=8.8, font_sizes=dict(title=10, axis=9, ticks=9, legend=9), source_ids=['final.evidence.episodes'], max_label_chars=36, uses_abbrev_labels=True, uses_progression=False)
    figures = [dict(common, figure_id='method_overview', figure_type='diagram', path_png='figures/method_overview.png', generator='generate-concept-figure', prompt_log_path='figures/method_overview.prompts.json', n_panels=2, panels_per_row=1, categories_per_panel=[5, 5], series_per_panel=[2, 2], source_ids=[]),
               dict(common, figure_id='budget_comparison', figure_type='line', path_pdf='figures/budget_comparison.pdf', path_png='figures/budget_comparison.png', generator='matplotlib', n_panels=2, panels_per_row=2, categories_per_panel=[4, 4], series_per_panel=[4, 4]),
               dict(common, figure_id='history_structure_controls', figure_type='scatter', path_pdf='figures/history_structure_controls.pdf', path_png='figures/history_structure_controls.png', generator='matplotlib', n_panels=1, panels_per_row=1, categories_per_panel=[3], series_per_panel=[3], intended_latex_width_fraction=.9)]
    Path('figure_manifest.json').write_text(json.dumps(dict(figures=figures), indent=2))


if __name__ == '__main__':
    main()
