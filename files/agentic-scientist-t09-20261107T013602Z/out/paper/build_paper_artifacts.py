import csv
import hashlib
import json
import shutil
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw


FAMILIES = ['SBM', 'BA', 'WS', 'Stanford3']
CONDITIONS = ['No spill', 'Weak linear', 'Strong linear', 'Threshold', 'Two-hop', 'Cluster']
METHODS = ['Endpoint-tuned', 'Difference in means', 'Own-treatment OLS', 'One-hop OLS']
BASELINE_KEYS = ['difference_in_means', 'own_treatment_ols', 'one_hop_ols']
BOOTSTRAP_SEED = 20261107
RESAMPLES = 10000
COLORS = ['#007c83', '#b75824', '#8665ad', '#31599a']


def provenance(path, inputs, kind='derived', notes=None):
    manifest = {'schema_name': 'scientific-evidence.artifact-manifest',
        'artifact': {'path': str(path), 'kind': kind,
                     'sha256': hashlib.sha256(Path(path).read_bytes()).hexdigest()},
        'derived_from': ['@' + 'evidence[[' + source + ']]' for source in inputs],
        'generated_by': {'script_path': 'build_paper_artifacts.py',
                         'command': ['python', 'build_paper_artifacts.py']}}
    if notes:
        manifest['notes'] = notes
    Path(str(path) + '.prov.json').write_text(json.dumps(manifest, indent=2))


def interval(values):
    return np.quantile(values, [.025, .975], axis=0).tolist()


def save_figure(figure, name):
    for extension in ['pdf', 'png']:
        target = Path('figures') / (name + '.' + extension)
        figure.savefig(target, dpi=300, facecolor='white')
        provenance(target, ['paper_data.json#/final_evaluation/evaluation_evidence/episodes',
                            'analysis/summary.json', 'build_paper_artifacts.py'], 'figure')
    plt.close(figure)


def main():
    Path('analysis').mkdir(exist_ok=True)
    Path('source_evidence').mkdir(exist_ok=True)
    source_dir = Path('results/ideas/03_endpoint_contrast_sure_for_exposure_regression/program_1')
    copies = {'estimator.py': source_dir / 'src/program.py',
              'program_spec.toml': source_dir / 'program_spec.toml',
              'evaluate_final.py': Path('task/evaluate_final.py'),
              'benchmark_manifest.json': Path('task/resources/final/manifest.json'),
              'requirements.txt': Path('task/requirements.txt'),
              'final_manifest.json': Path('../final_evaluation/final_manifest.json'),
              'task_contract.json': Path('task/task_contract.json'),
              'missing_comparison_failure.json': Path('results/ideas/02_nonbacktracking_two_hop_regression_with_invariant_gcv/program_1/evaluation_failure.json'),
              'missing_comparison_stderr.log': Path('results/ideas/02_nonbacktracking_two_hop_regression_with_invariant_gcv/program_1/harness_evaluate_stderr.log')}
    for destination, origin in copies.items():
        target = Path('source_evidence') / destination
        shutil.copyfile(origin, target)
        context = 'paper_data.json#/best_correct' if origin.is_relative_to(source_dir) else 'paper_data.json'
        provenance(target, [context], 'source', notes='Raw source snapshot copied byte-for-byte from ' +
                   str(origin) + '. Registry link supplies run context, not substantive proof of source contents or executable identity.')
    # @evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]
    data = json.loads(Path('paper_data.json').read_text())
    episodes = data['final_evaluation']['evaluation_evidence']['episodes']
    seeds = [episode['seed'] for episode in episodes]
    errors = np.full((len(seeds), len(FAMILIES), len(CONDITIONS), len(METHODS)), np.nan)
    fit = np.full(errors.shape[:-1], np.nan)
    support = {}
    records = []
    for seed_index, episode in enumerate(episodes):
        for case in episode['solution']['cases']:
            if case['kind'] != 'scientific':
                continue
            assert case['completed']
            family_index = FAMILIES.index(case['family'])
            condition_index = case['mechanism']
            measured = case['validated']
            assert not measured['clipped']
            error_vector = [measured['uncapped_error']] + [
                measured['baseline_estimates'][name] - measured['true_gate'] for name in BASELINE_KEYS]
            errors[seed_index, family_index, condition_index] = error_vector
            fit[seed_index, family_index, condition_index] = measured['observed_fit_rmse']
            for method, error in zip(METHODS, error_vector):
                records.append({'seed': episode['seed'], 'family': case['family'],
                    'condition': CONDITIONS[condition_index], 'method': method,
                    'true_gate': measured['true_gate'], 'error': error,
                    'observed_fit_rmse': measured['observed_fit_rmse']})
            support.setdefault((case['family'], condition_index), []).append(measured['exposure_support'])
    assert np.isfinite(errors).all()
    with Path('analysis/observations.csv').open('w') as output:
        writer = csv.DictWriter(output, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
    provenance('analysis/observations.csv', ['paper_data.json#/final_evaluation/evaluation_evidence/episodes'])
    # @evidence[[analysis/observations.csv]]
    cell_rmse = np.sqrt(np.mean(errors ** 2, axis=0))
    cell_bias = np.mean(errors, axis=0)
    generator = np.random.default_rng(BOOTSTRAP_SEED)
    indices = generator.integers(0, len(seeds), size=(RESAMPLES, len(seeds)))
    bootstrap_rmse = np.sqrt(np.mean(errors[indices] ** 2, axis=1))
    bootstrap_bias = np.abs(np.mean(errors[indices], axis=1))
    overall_rmse = cell_rmse.mean(axis=(0, 1))
    overall_abias = np.abs(cell_bias).mean(axis=(0, 1))
    bootstrap_overall = bootstrap_rmse.mean(axis=(1, 2))
    ratios = cell_rmse[..., 0, None] / cell_rmse[..., 1:]
    bootstrap_ratios = bootstrap_rmse[..., 0, None] / bootstrap_rmse[..., 1:]
    difference = overall_rmse[0] - overall_rmse[3]
    bootstrap_difference = bootstrap_overall[:, 0] - bootstrap_overall[:, 3]
    summary = {'seeds': seeds, 'seed_count': len(seeds), 'scientific_count': int(fit.size),
        'bootstrap': {'seed': BOOTSTRAP_SEED, 'resamples': RESAMPLES,
                      'unit': 'seed block jointly across all graph-condition-method cells',
                      'interval': '95% percentile, descriptive fixed-benchmark Monte Carlo uncertainty'},
        'methods': METHODS, 'families': FAMILIES, 'conditions': CONDITIONS,
        'rmse': overall_rmse.tolist(), 'rmse_ci': interval(bootstrap_overall),
        'absolute_bias': overall_abias.tolist(),
        'absolute_bias_ci': interval(bootstrap_bias.mean(axis=(1, 2))),
        'endpoint_minus_onehop_rmse': float(difference),
        'endpoint_minus_onehop_rmse_ci': interval(bootstrap_difference),
        'cell_rmse': cell_rmse.tolist(), 'cell_rmse_ci': interval(bootstrap_rmse),
        'cell_signed_bias': cell_bias.tolist(), 'ratios': ratios.tolist(),
        'ratio_ci': interval(bootstrap_ratios),
        'mean_fit_rmse': fit.mean(axis=0).tolist(),
        'fit_rmse_range': [float(fit.min()), float(fit.max())],
        'favorable_cells_vs_onehop': int((ratios[..., 2] < 1).sum()),
        'all_errors_uncapped': True, 'support': {family + ':' + str(condition): {
            field: {'min': min(row[field] for row in rows),
                    'max': max(row[field] for row in rows),
                    'mean': float(np.mean([row[field] for row in rows]))} for field in rows[0]}
            for (family, condition), rows in support.items()}}
    Path('analysis/summary.json').write_text(json.dumps(summary, indent=2))
    provenance('analysis/summary.json', ['paper_data.json#/final_evaluation/evaluation_evidence/episodes',
                                       'build_paper_artifacts.py'])
    plt.rcParams.update({'font.size': 9, 'axes.titlesize': 10, 'axes.labelsize': 9,
                        'xtick.labelsize': 8.5, 'ytick.labelsize': 8.5,
                        'legend.fontsize': 8.5, 'pdf.fonttype': 42,
                        'axes.spines.right': False, 'axes.spines.top': False})
    figure, axes = plt.subplots(2, 2, figsize=(5.5, 4.3), sharex=True, sharey=True)
    bounds = np.quantile(bootstrap_ratios, [.025, .975], axis=0)
    for family_index, axis in enumerate(axes.flat):
        for comparator_index in range(3):
            positions = np.arange(6) + (comparator_index - 1) * .19
            values = ratios[family_index, :, comparator_index]
            axis.errorbar(values, positions, xerr=np.array([
                values - bounds[0, family_index, :, comparator_index],
                bounds[1, family_index, :, comparator_index] - values]),
                fmt=['o', 's', '^'][comparator_index], markersize=3,
                linewidth=.8, capsize=1, color=COLORS[comparator_index + 1],
                label=['Mean difference', 'Own OLS', 'One-hop OLS'][comparator_index])
        axis.axvline(1, color='0.3', linestyle='--', linewidth=.8)
        axis.set_xscale('log')
        axis.set_title(FAMILIES[family_index], loc='left', fontweight='bold')
        axis.set_yticks(np.arange(6), CONDITIONS)
        axis.set_ylim(5.55, -.55)
        axis.grid(axis='x', color='.9', linewidth=.5)
    figure.supxlabel('Endpoint-tuned RMSE / comparator RMSE', fontsize=9, y=.035)
    figure.legend(*axes[0, 0].get_legend_handles_labels(), loc='upper center',
                  bbox_to_anchor=(.55, 1.01), ncol=3, frameon=False, columnspacing=.8)
    figure.subplots_adjust(left=.19, right=.98, bottom=.16, top=.87, hspace=.28, wspace=.18)
    save_figure(figure, 'conditional_accuracy')
    figure, axes = plt.subplots(1, 2, figsize=(5.5, 2.65))
    for group, mask, color in [('Other', np.array([True, True, True, False, False, True]), '.65'),
                              ('Threshold', np.array([False, False, False, True, False, False]), COLORS[1]),
                              ('Two-hop', np.array([False, False, False, False, True, False]), COLORS[3])]:
        axes[0].scatter(fit[:, :, mask].ravel(), np.abs(errors[:, :, mask, 0]).ravel(),
                        s=9, color=color, alpha=.4, label=group, edgecolors='none')
    axes[0].set_xlabel('Observed-fit RMSE')
    axes[0].set_ylabel('Absolute GATE error')
    axes[0].set_title('(a) Fit versus target error', loc='left')
    axes[0].legend(frameon=False, fontsize=8, handletextpad=.25)
    for design_index, condition in enumerate([2, 5]):
        values = cell_rmse[:, condition, 0]
        bounds = np.quantile(bootstrap_rmse[:, :, condition, 0], [.025, .975], axis=0)
        positions = np.arange(4) + (design_index - .5) * .2
        axes[1].errorbar(values, positions, xerr=[values - bounds[0], bounds[1] - values],
                         fmt=['o', 's'][design_index], color=[COLORS[0], COLORS[1]][design_index],
                         capsize=2, markersize=4, linewidth=1,
                         label=['Individual', 'Cluster'][design_index])
    axes[1].set_yticks(np.arange(4), FAMILIES)
    axes[1].invert_yaxis()
    axes[1].set_xlabel('Endpoint-tuned RMSE')
    axes[1].set_title('(b) Strong linear spillover', loc='left')
    axes[1].legend(frameon=False, fontsize=8, loc='lower right')
    figure.subplots_adjust(left=.10, right=.99, bottom=.22, top=.88, wspace=.48)
    save_figure(figure, 'diagnostic_limits')
    concept = Path('figures/endpoint_overview.png')
    prompt_log = Path('figures/endpoint_overview.prompts.json')
    if not Path('.concept_figure_complete').exists() and not concept.exists():
        image = Image.new('RGB', (2400, 780), 'white')
        drawing = ImageDraw.Draw(image)
        drawing.text((80, 340), 'Concept overview pending orchestrator rendering', fill='#888888')
        image.save(concept)
        prompt_log.write_text('{}\n')
    figures = []
    for name, figure_type, panels, categories, series, height in [
            ('endpoint_overview', 'diagram', 1, [6], [1], 1.8),
            ('conditional_accuracy', 'composite', 4, [6] * 4, [3] * 4, 4.3),
            ('diagnostic_limits', 'composite', 2, [3, 4], [3, 2], 2.65)]:
        entry = {'figure_id': name, 'figure_type': figure_type,
            'path_png': 'figures/' + name + '.png', 'n_panels': panels,
            'panels_per_row': 2 if panels > 1 else 1,
            'categories_per_panel': categories, 'series_per_panel': series,
            'max_label_chars': 27, 'uses_abbrev_labels': True, 'uses_progression': False,
            'source_ids': [] if panels == 1 else ['final.evidence.episodes'],
            'generator': 'generate-concept-figure' if panels == 1 else 'matplotlib',
            'placement': 'full_width', 'intended_latex_width_fraction': .98 if panels == 1 else 1,
            'estimated_min_rendered_font_pt': 8.5,
            'font_sizes': {'title': 10, 'axis': 9, 'ticks': 8.5, 'legend': 8.5}}
        if panels == 1:
            entry['prompt_log_path'] = str(prompt_log)
        else:
            entry['path_pdf'] = 'figures/' + name + '.pdf'
        figures.append(entry)
    Path('figure_manifest.json').write_text(json.dumps({'figures': figures}, indent=2))
    print(json.dumps({key: summary[key] for key in ['rmse', 'rmse_ci', 'absolute_bias',
        'endpoint_minus_onehop_rmse', 'endpoint_minus_onehop_rmse_ci',
        'favorable_cells_vs_onehop', 'fit_rmse_range']}, indent=2))


if __name__ == '__main__':
    main()
