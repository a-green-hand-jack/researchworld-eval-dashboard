import datetime
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent
CONDITIONS = ['gene_expression', 'linear', 'nonlinear', 'rare_outcome',
              'uninformative', 'constant_nonlinear', 'permuted_nonlinear']
LABELS = ['Gene expression', 'Linear', 'Nonlinear', 'Rare outcome',
          'Uninformative', 'Constant score', 'Permuted score']
METHODS = ['candidate', 'label_only', 'ppi', 'ppi_plus_plus']
NAMES = ['Frozen-score control', 'Label only', 'PPI', 'PPI++']
COLORS = ['#096b67', '#777777', '#a85f0a', '#6254a5']


def sidecar(path, kind, inputs):
    record = {'schema_name': 'scientific-evidence.artifact-manifest',
              'artifact': {'path': str(path), 'kind': kind,
                           'sha256': hashlib.sha256(Path(path).read_bytes()).hexdigest()},
              'derived_from': inputs, 'generated_by': {'script_path': 'build_artifacts.py',
              'command': ['python', 'build_artifacts.py']}}
    Path(str(path)+'.prov.json').write_text(json.dumps(record, indent=2))


def main():
    # @evidence[[paper_data.json#final_evaluation/evaluation_evidence/episodes]]
    data = json.loads((ROOT/'paper_data.json').read_text())
    final = data['final_evaluation']
    assert final['status'] == 'completed'
    episodes = final['evaluation_evidence']['episodes']
    summary = episodes[0]['solution']['summary']
    output = {'qualification': {key: final[key] for key in ['status', 'outcome', 'correct']},
              'n_repeats': len(episodes), 'seeds': [episode['seed'] for episode in episodes], 'conditions': {}}
    for case in CONDITIONS:
        records = [episode['solution']['cases'][case]['observations'] for episode in episodes]
        estimates = {}
        for method in METHODS:
            widths = np.array([record[method][1]-record[method][0] for record in records])
            covered = np.array([record[method][0] <= record['target'] <= record[method][1] for record in records])
            estimates[method] = {'mean_width': float(widths.mean()), 'coverage': float(covered.mean()),
                                 'covered': int(covered.sum()), 'zero_width_count': int((widths == 0).sum()),
                                 'coverage_interval': summary[case]['coverage_intervals'][method]}
        for comparator in METHODS[1:]:
            np.testing.assert_allclose(estimates[comparator]['mean_width'], summary[case]['paired_widths'][comparator]['mean_baseline_width'], rtol=1e-12)
            np.testing.assert_allclose(estimates['candidate']['mean_width'], summary[case]['paired_widths'][comparator]['mean_candidate_width'], rtol=1e-12)
        output['conditions'][case] = {'methods': estimates, 'comparisons': summary[case]['paired_widths']}
    (ROOT/'analysis_summary.json').write_text(json.dumps(output, indent=2))
    sidecar('analysis_summary.json', 'derived', ['@evidence[[paper_data.json#final_evaluation/evaluation_evidence/episodes]]'])
    plt.rcParams.update({'font.size': 9, 'axes.labelsize': 9, 'xtick.labelsize': 8.5, 'ytick.labelsize': 9,
                         'legend.fontsize': 8.4, 'axes.spines.top': False, 'axes.spines.right': False,
                         'axes.spines.left': False, 'pdf.fonttype': 42, 'font.family': 'DejaVu Sans'})
    (ROOT/'figures').mkdir(exist_ok=True)
    manifest = []
    for figure_id, metric in [('paired_width_comparison', 'width'), ('coverage_with_uncertainty', 'coverage')]:
        figure, axes = plt.subplots(2, 1, figsize=(5.5, 3.7), gridspec_kw={'height_ratios': [4, 3]})
        figure.subplots_adjust(left=.255, right=.98, bottom=.13, top=.80 if metric == 'coverage' else .87, hspace=.50)
        for panel_index, indices in enumerate([list(range(4)), list(range(4, 7))]):
            axis = axes[panel_index]
            for method_index, method in enumerate(METHODS[1:] if metric == 'width' else METHODS):
                offsets = [-.22, 0, .22] if metric == 'width' else [-.27, -.09, .09, .27]
                for position, case_index in enumerate(indices):
                    case = CONDITIONS[case_index]
                    if metric == 'width':
                        comparison = summary[case]['paired_widths'][method]
                        value = comparison['mean_candidate_width'] / comparison['mean_baseline_width']
                        lower, upper = comparison['ratio_interval']
                    else:
                        point = output['conditions'][case]['methods'][method]
                        value = point['coverage']
                        lower, upper = point['coverage_interval']
                    color = COLORS[METHODS.index(method)]
                    axis.errorbar(value, position+offsets[method_index], xerr=[[value-lower], [upper-value]],
                                  fmt='o', color=color, markersize=3.3, elinewidth=1.05, capsize=1.7,
                                  label=NAMES[METHODS.index(method)] if position == 0 and panel_index == 0 else None)
            axis.set_yticks(range(len(indices)), [LABELS[index] for index in indices])
            axis.tick_params(axis='y', length=0)
            axis.invert_yaxis()
            axis.set_ylim(len(indices)-.5, -.5)
            axis.grid(axis='x', alpha=.15)
            axis.set_title(('(a) Predictive conditions' if panel_index == 0 else '(b) Information controls'), fontsize=9, loc='left', pad=5)
            if metric == 'width':
                axis.set_xscale('log')
                axis.set_xlim(.26, 1.25)
                axis.set_xticks([.3, .5, .75, 1, 1.2], ['0.30', '0.50', '0.75', '1.00', '1.20'])
                axis.minorticks_off()
                axis.axvline(1, color='#333333', lw=.9, linestyle='--')
            else:
                axis.set_xlim(.86, 1.002)
                axis.set_xticks([.86, .90, .95, 1.0])
                axis.axvline(.95, color='#333333', lw=.9, linestyle='--')
            if panel_index == 0:
                axis.tick_params(labelbottom=False)
        axes[-1].set_xlabel('Mean width / comparator mean width (log scale)' if metric == 'width' else 'Empirical coverage with simultaneous interval')
        handles, labels = axes[0].get_legend_handles_labels()
        figure.legend(handles, labels, loc='upper center', bbox_to_anchor=(.54, .995), frameon=False,
                      ncol=2 if metric == 'coverage' else 3, handlelength=1.0, columnspacing=.8)
        for extension in ['pdf', 'png']:
            path = 'figures/'+figure_id+'.'+extension
            figure.savefig(ROOT/path, dpi=300)
            sidecar(path, 'figure', ['@evidence[[paper_data.json#final_evaluation/evaluation_evidence/episodes]]', '@evidence[[analysis_summary.json]]', '@evidence[[build_artifacts.py]]'])
        plt.close(figure)
        manifest.append(dict(figure_id=figure_id, figure_type='composite', files={'pdf': 'figures/'+figure_id+'.pdf', 'png': 'figures/'+figure_id+'.png'},
                             panel_count=2, panels=[dict(panel_id='a', category_count=4, series_count=3 if metric == 'width' else 4),
                                                   dict(panel_id='b', category_count=3, series_count=3 if metric == 'width' else 4)],
                             uses_progression=False, generator='matplotlib', source_ids=['final.evidence.episodes'],
                             placement='full_width', intended_latex_width_fraction=1., estimated_min_rendered_font_pt=8.4,
                             min_font_size_pt=8.4, max_label_chars=32, panels_per_row=1, uses_abbrev_labels=True))
    image_path = ROOT/'figures/fixed_resource_overview.png'
    log_path = ROOT/'figures/fixed_resource_overview.prompts.json'
    completed = (ROOT/'.concept_figure_complete').exists()
    rendered_log = log_path.exists() and log_path.read_text().strip() not in ('', '{}')
    if not completed and not rendered_log and not image_path.exists():
        image = Image.new('RGB', (2400, 873), 'white')
        ImageDraw.Draw(image).text((70, 390), 'Concept figure pending orchestrator rendering', fill='#444444')
        image.save(image_path)
        log_path.write_text('{}\n')
    manifest.insert(0, dict(figure_id='fixed_resource_overview', figure_type='diagram', files={'png': 'figures/fixed_resource_overview.png'},
                           panel_count=2, panels=[dict(panel_id='a', content='Fixed inputs and training-only risk selection'),
                                                 dict(panel_id='b', content='Held-out correction and empirical assessment')],
                           uses_progression=False, generator='generate-concept-figure', source_ids=[], prompt_log_path='figures/fixed_resource_overview.prompts.json',
                           placement='full_width', intended_latex_width_fraction=1., estimated_min_rendered_font_pt=9.,
                           note='Orchestrator-owned deterministic render; no paid image enhancement. Placeholder is guarded and is not a scientific result.'))
    (ROOT/'figure_manifest.json').write_text(json.dumps({'figures': manifest}, indent=2))
    print('Verified stored means against all endpoint records; exported plots and evidence trails.')
    for case in CONDITIONS:
        point = output['conditions'][case]
        print(case, [round(point['methods'][method]['mean_width'], 6) for method in METHODS],
              [point['methods'][method]['coverage'] for method in METHODS])


if __name__ == '__main__':
    main()
