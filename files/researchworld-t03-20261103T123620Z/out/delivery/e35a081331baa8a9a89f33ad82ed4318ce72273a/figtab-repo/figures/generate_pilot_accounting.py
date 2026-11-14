"""Render measured pilot work and raw call costs; no reliability inference."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rendering import WIDTH_IN, METHOD_STYLE, paper_style, export_figure, file_record

ROOT = Path(__file__).resolve().parents[1]
DATASETS = [('german', 'German', 20), ('acs', 'ACSIncome', 10), ('diabetes', 'Diabetes', 8)]
MODELS = [('logistic', 'LR'), ('forest', 'RF'), ('histboost', 'HGB')]
BUDGETS = [128, 2048]
CAPTION = (
    'Pilot budget accounting, not main-study reliability evidence. Each line '
    'joins two measured calls for one of two pilot inputs per fitted model, '
    'with a fixed 32-row empirical background and grouped raw-feature players. '
    'The horizontal axis is the requested coalition-work setting; the vertical '
    'axis counts actual input rows evaluated by the prediction pipeline. '
    'Colors, markers and line styles identify the estimators. Hollow Kernel '
    'SHAP markers denote exhaustive evaluation over the effective varying '
    'players; complete permutation-cache coverage does not imply an exact '
    'path-sampling estimate. Overlapping calls may obscure one another. '
    'Traces for the three fitted models coincide in prediction-row count; '
    'the accompanying table shows their distinct CPU costs. These pilot calls '
    'have no population uncertainty interval. They motivate measuring actual '
    'work and using dimension-specific stochastic budgets in the subsequent study.'
)
TABLE_CAPTION = (
    'Measured pilot CPU time per explanation call (milliseconds, three '
    'significant figures). C1 and C2 are the two pilot inputs per fitted '
    'model; each number is one timed call, not an average or confidence '
    'interval. Column labels are requested coalition-work settings, not actual '
    'prediction-row counts. The background contains 32 rows. Library import '
    'was warmed before timing; training and references are excluded. '
    'The initial 2048 Kernel setting is exhaustive for ACSIncome and Diabetes '
    'and is retained as a labeled control, not stochastic main-study evidence. '
    'LR, RF and HGB denote logistic regression, random forest and histogram '
    'gradient boosting. This table describes the pilot, not final-study costs.'
)


def load_records(path, source):
    if hashlib.sha256(path.read_bytes()).hexdigest() != source['sha256']:
        raise ValueError('Pilot input differs from the committed source hash')
    raw = [json.loads(line) for line in path.read_text().splitlines()]
    if any(r.get('stage') != 'pilot' for r in raw):
        raise ValueError('Only explicitly marked pilot records are accepted')
    if any(r.get('kind') == 'failure' for r in raw):
        raise ValueError('Failure records require explicit presentation before rendering')
    models = {(r['dataset'], r['model']): r['info'] for r in raw if r['kind'] == 'model'}
    rows = {}
    line_numbers = {}
    for lineno, r in enumerate(raw, 1):
        if r['kind'] != 'estimator':
            continue
        key = (r['dataset'], r['model'], r['instance_index'], r['estimator'], r['budget'])
        if key in rows:
            raise ValueError(f'Duplicate call {key}')
        if r['cpu_seconds'] <= 0 or r['prediction_rows'] <= 0:
            raise ValueError(f'Nonpositive work/cost {key}')
        rows[key] = r
        line_numbers[key] = lineno
    expected = {(d, m, i, e, b) for d, _, _ in DATASETS for m, _ in MODELS
                for i in [0, 1] for e in METHOD_STYLE for b in BUDGETS}
    if set(rows) != expected:
        raise ValueError('Pilot grid is incomplete or includes unexpected calls')
    for d, _, features in DATASETS:
        for m, _ in MODELS:
            info = models[d, m]
            if info['background_size'] != 32 or info['n_features'] != features:
                raise ValueError('Caption no longer matches the pilot configuration')
    for d, _, _ in DATASETS:
        for i in [0, 1]:
            for e in METHOD_STYLE:
                for b in BUDGETS:
                    if len({rows[d, m, i, e, b]['prediction_rows'] for m, _ in MODELS}) != 1:
                        raise ValueError('Caption requires identical observed work across fitted models')
    return rows, line_numbers


def render_table(rows, line_numbers):
    lines = [r'\begin{table}[tb]', r'\centering', r'\caption{' + TABLE_CAPTION + '}',
             r'\label{tab:pilot-call-costs}', r'\small', r'\begin{tabular}{llcrrrr}',
             r'\toprule',
             r' & & & \multicolumn{2}{c}{Permutation (ms)} & \multicolumn{2}{c}{Kernel (ms)} \\',
             r'\cmidrule(lr){4-5}\cmidrule(lr){6-7}',
             r'Dataset & Model & Input & 128 & 2048 & 128 & 2048 \\', r'\midrule']
    cell_map = []
    for di, (d, label, _) in enumerate(DATASETS):
        if di:
            lines.append(r'\midrule')
        for mi, (m, short) in enumerate(MODELS):
            for i in [0, 1]:
                keys = [(d, m, i, e, b) for e in METHOD_STYLE for b in BUDGETS]
                numbers = [format(1000 * rows[key]['cpu_seconds'], '#.3g').rstrip('.') for key in keys]
                lines.append(' & '.join([label if mi == 0 and i == 0 else '',
                                          short if i == 0 else '', f'C{i+1}', *numbers]) + r' \\')
                cell_map.append({'dataset': d, 'model': m, 'input': f'C{i+1}',
                                 'source_id': rows[keys[0]]['source_id'],
                                 'input_jsonl_lines': [line_numbers[k] for k in keys],
                                 'column': 'cpu_seconds', 'conversion': 'multiply by 1000; format #.3g; strip final decimal point'})
    lines += [r'\bottomrule', r'\end{tabular}', r'\end{table}', '']
    path = ROOT / 'tables/pilot_call_costs.tex'
    path.parent.mkdir(exist_ok=True)
    path.write_text('\n'.join(lines))
    return path, cell_map


def preview_table(table):
    with tempfile.TemporaryDirectory(prefix='pilot-table-') as tmp:
        work = Path(tmp)
        doc = (r'\documentclass[10pt]{article}' '\n'
               r'\usepackage{times,booktabs}' '\n'
               r'\usepackage[letterpaper,left=1.5in,right=1.5in,top=1in,bottom=1in]{geometry}' '\n'
               r'\pagestyle{empty}\begin{document}' '\n' + table.read_text() +
               '\n' r'\end{document}' '\n')
        (work / 'preview.tex').write_text(doc)
        done = subprocess.run(['pdflatex', '-interaction=nonstopmode', '-halt-on-error',
                               'preview.tex'], cwd=work, capture_output=True, text=True)
        if done.returncode:
            raise RuntimeError(done.stdout[-5000:])
        log = (work / 'preview.log').read_text()
        if 'Overfull \\hbox' in log or 'Overfull \\vbox' in log:
            raise ValueError('Table preview overflows the 5.5-inch geometry')
        target = ROOT / 'tables/pilot_call_costs.preview.pdf'
        target.write_bytes((work / 'preview.pdf').read_bytes())
        subprocess.run(['pdftoppm', '-singlefile', '-scale-to', '1600', '-png',
                        str(target), str(ROOT / 'tables/pilot_call_costs.preview')], check=True)
        return [target, ROOT / 'tables/pilot_call_costs.preview.png']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview', action='store_true', help='Compile and rasterize the actual table')
    args = parser.parse_args()
    input_path = ROOT / 'figures/inputs/pilot.jsonl'
    source_path = ROOT / 'figures/inputs/pilot-source.json'
    source = json.loads(source_path.read_text())
    rows, line_numbers = load_records(input_path, source)
    caption_path = ROOT / 'figures/pilot_budget_accounting.caption.tex'
    caption_path.write_text(CAPTION + '\n')
    panel_map = []
    with paper_style():
        fig, axes = plt.subplots(1, 3, figsize=(WIDTH_IN, 2.7), sharex=True, sharey=True)
        for ax, (d, name, features) in zip(axes, DATASETS):
            for m, short in MODELS:
                for e, style in METHOD_STYLE.items():
                    for i in [0, 1]:
                        keys = [(d, m, i, e, b) for b in BUDGETS]
                        calls = [rows[k] for k in keys]
                        ax.plot(BUDGETS, [r['prediction_rows'] for r in calls],
                                color=style['color'], linestyle=style['linestyle'], alpha=.45)
                        for b, call in zip(BUDGETS, calls):
                            exact = e == 'kernel' and call['exhaustive']
                            ax.plot(b, call['prediction_rows'], marker=style['marker'],
                                    color=style['color'], linestyle='none',
                                    markerfacecolor='white' if exact else style['color'])
                        panel_map.append({'panel': name, 'model': short, 'estimator': e,
                                          'instance_index': i,
                                          'input_jsonl_lines': [line_numbers[k] for k in keys],
                                          'x': 'budget (requested)', 'y': 'prediction_rows (actual)',
                                          'aggregation': 'none: raw pilot calls; no CI',
                                          'exhaustive_flag': 'use only for kernel; permutation legacy flag is cache coverage'})
            ax.set_title(f'{name} ({features} features)', fontsize=9)
            ax.set_xscale('log', base=2)
            ax.set_yscale('log', base=2)
            ax.set_xticks(BUDGETS, labels=['128', '2048'])
            ax.set_yticks([4096, 16384, 65536], labels=['4,096', '16,384', '65,536'])
            ax.minorticks_off()
            ax.grid(axis='y', color='.88', linewidth=.5)
        fig.supxlabel('Requested coalition-work budget', fontsize=9)
        fig.supylabel('Actual prediction rows', fontsize=9)
        handles = [Line2D([], [], label='Permutation', **METHOD_STYLE['permutation']),
                   Line2D([], [], label='Kernel', **METHOD_STYLE['kernel']),
                   Line2D([], [], color='.2', marker='s', markerfacecolor='white',
                          linestyle='none', label='Exhaustive Kernel')]
        fig.legend(handles=handles, loc='outside upper center', ncol=3, frameon=False,
                   columnspacing=1.1, handlelength=1.5)
        command = 'python3 figures/generate_pilot_accounting.py' + (' --preview' if args.preview else '')
        export_figure(fig, ROOT / 'figures/pilot_budget_accounting', root=ROOT,
                      inputs=[input_path, source_path], analysis_revision=source['revision'],
                      generator=Path(__file__), command=command, panels=panel_map,
                      caption_path=caption_path)
        plt.close(fig)
    table, cell_map = render_table(rows, line_numbers)
    previews = preview_table(table) if args.preview else []
    manifest = {'schema_version': 1, 'evidence_role': 'pilot cost accounting only',
                'source': source, 'inputs': [file_record(p, ROOT) for p in [input_path, source_path]],
                'generator': file_record(Path(__file__), ROOT), 'command': command,
                'cells': cell_map, 'outputs': [file_record(p, ROOT) for p in [table, *previews]],
                'inspection': 'Pending visual inspection record'}
    (ROOT / 'tables/pilot_call_costs.manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'Rendered 72 raw pilot calls, {len(cell_map)} table rows. No reliability estimates computed.')


if __name__ == '__main__':
    main()
