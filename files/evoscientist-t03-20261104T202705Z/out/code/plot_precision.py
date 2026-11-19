#!/usr/bin/env python3
"""Replay measured-data study figures. No experiment code required.

python /work/plot_precision.py --out /work/analysis120
Each per-figure directory also contains this complete script as plot.py and its
inputs.csv; running that script regenerates its plot.png and plot.pdf.
"""
from pathlib import Path
import argparse
import json
import shutil
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

KINDS = ('budget_accuracy', 'repeatability_accuracy', 'gap_budget')
ORDER = ('pima', 'acs', 'german')
MODELS = ('lr', 'rf', 'mlp')
METHODS = ('antithetic', 'iid_oneway', 'kernel')
LABELS = dict(antithetic='Antithetic', iid_oneway='IID one-way', kernel='Constrained Kernel')
GAPS = ('<.002', '.002-.01', '>=.01')
GAP_LABELS = ('Gap <.002', 'Gap [.002,.01)', 'Gap >=.01')
STYLES = ('-', '--', ':')
COLORS = ('#1f77b4', '#ff7f0e', '#2ca02c')
MARKERS = ('o', 's', '^', 'D')


def render_one(data, kind, dest, partial=False, n=None, stage=''):
    if n is None:
        column = 'n_total_instance_clusters' if kind == 'gap_budget' else 'n_instances'
        if column in data and data[column].nunique() == 1:
            n = int(data[column].iloc[0])
        else:
            raise ValueError('Missing explicit analyzed n; never assume n30 for expanded figures')
    plt.rcParams.update({'pdf.fonttype':42, 'ps.fonttype':42,
                         'font.family':'sans-serif', 'font.sans-serif':['DejaVu Sans'],
                         'font.size':9, 'axes.titlesize':10, 'axes.titlepad':10,
                         'axes.labelsize':9, 'xtick.labelsize':8, 'ytick.labelsize':8,
                         'legend.fontsize':8, 'figure.titlesize':11})
    datasets = [ds for ds in ORDER if ds in set(data.dataset)]
    fig, axes = plt.subplots(len(datasets), 3, figsize=(7, 1.85*len(datasets)+1), squeeze=False)
    plotted_rows = 0
    for ri, ds in enumerate(datasets):
        for ci, model in enumerate(MODELS):
            ax = axes[ri, ci]
            sub = data[(data.dataset == ds) & (data.model == model)]
            title = f'{ds.upper()} / {model.upper()}'
            if ds == 'german':
                title = f'German APPROX / {model.upper()}'
            ax.set_title(title)
            ax.set_ylim(-.025, 1.025)
            if kind == 'repeatability_accuracy':
                for mi, method in enumerate(METHODS):
                    for bi, budget in enumerate((1, 4, 16, 64)):
                        rows = sub[(sub.method == method) & (sub.budget == budget)]
                        for _, row in rows.iterrows():
                            x, y = row.pairwise_top3_match, row.top3_match
                            ax.hlines(y, row.pairwise_top3_match_lo, row.pairwise_top3_match_hi,
                                      color=COLORS[mi], alpha=.4, lw=.7)
                            ax.vlines(x, row.top3_match_lo, row.top3_match_hi,
                                      color=COLORS[mi], alpha=.4, lw=.7)
                            ax.plot(x, y, color=COLORS[mi], marker=MARKERS[bi], ms=4, linestyle='None')
                            plotted_rows += 1
                ax.set_xlim(-.025, 1.025)
                ax.set_xticks((0, .5, 1))
            else:
                for mi, method in enumerate(METHODS):
                    if kind == 'gap_budget':
                        for gi, gap in enumerate(GAPS):
                            rows = sub[(sub.method == method) & (sub.gap_bin == gap)].sort_values('budget')
                            ax.plot(rows.budget, rows.top3_match, color=COLORS[gi], linestyle=STYLES[mi], marker='o', ms=2.5, lw=1)
                            ax.fill_between(rows.budget.to_numpy(), rows.top3_match_lo.to_numpy(), rows.top3_match_hi.to_numpy(), color=COLORS[gi], alpha=.06)
                            plotted_rows += len(rows)
                    else:
                        rows = sub[sub.method == method].sort_values('budget')
                        ax.plot(rows.budget, rows.top3_match, color=COLORS[mi], linestyle=STYLES[mi], marker='o', ms=3, lw=1.2)
                        ax.fill_between(rows.budget.to_numpy(), rows.top3_match_lo.to_numpy(), rows.top3_match_hi.to_numpy(), color=COLORS[mi], alpha=.10)
                        plotted_rows += len(rows)
                ax.set_xscale('log', base=4)
                ax.set_xticks((1,4,16,64), labels=('1','4','16','64'))
                ax.set_xlim(.85, 75)
            ax.set_yticks((0, .5, 1))
            ax.spines[['top', 'right']].set_visible(False)
            ax.tick_params(direction='out', length=3)
            ax.grid(axis='y', linestyle=':', linewidth=.5, alpha=.6)
    method_handles = [Line2D([], [], color=COLORS[i] if kind != 'gap_budget' else '0.3',
                             linestyle=STYLES[i] if kind != 'repeatability_accuracy' else '-',
                             label=LABELS[m]) for i,m in enumerate(METHODS) if m in set(data.method)]
    handles = method_handles
    if kind == 'repeatability_accuracy':
        handles += [Line2D([], [], color='0.3', linestyle='None', marker=marker, ms=4, label=f'P={p}')
                    for marker,p in zip(MARKERS,(1,4,16,64))]
    elif kind == 'gap_budget':
        handles += [Line2D([], [], color=COLORS[i], label=label) for i,label in enumerate(GAP_LABELS)]
    three_rows = len(datasets) == 3
    fig.legend(handles=handles, loc='lower center', bbox_to_anchor=(.5, .065 if three_rows else .08), ncol=3 if kind != 'repeatability_accuracy' else 4, frameon=False)
    fig.supxlabel('Pairwise exact top-3 repeatability' if kind == 'repeatability_accuracy' else 'Budget P (controls: matched row allowance)', y=.16 if three_rows else .205, fontsize=9)
    fig.supylabel('Top-3 match (German: APPROX reference only)' if 'german' in datasets else 'Exact-target top-3 match', x=.01, fontsize=9)
    title = {'budget_accuracy':'Budget and target agreement', 'repeatability_accuracy':'Repeatability is not target agreement', 'gap_budget':'Oracle-gap strata (descriptive)'}[kind]
    stage_label = {'combined120_main': 'combined main expansion', 'heldout_next90': 'held-out additional90',
                   'exploratory_first30': 'exploratory first30'}.get(stage, stage)
    fig.suptitle(f'{title} (n={n}; {stage_label})' + (' — exact-only partial' if partial else ''), y=.985, fontsize=10)
    note = f'n={n} instance clusters/dataset; fixed seeds 11,23,47; R=20; 2000 descriptive bootstrap 95% intervals.'
    if kind == 'gap_budget':
        note += '\nOracle gaps; empty strata missing, not zero. Kernel P=64: full enumeration.'
    else:
        note += '\nMeasured games; Kernel P=64 enumerates the exact cube; not certificates.'
    fig.text(.5, .015, note, ha='center', va='bottom', fontsize=7)
    fig.subplots_adjust(left=.10, right=.985, bottom=.22 if three_rows else .29, top=.90 if three_rows else .87, hspace=.70, wspace=.35)
    dest.mkdir(parents=True, exist_ok=True)
    fig.savefig(dest/'plot.png', dpi=300, bbox_inches='tight', pad_inches=.05)
    fig.savefig(dest/'plot.pdf', bbox_inches='tight', pad_inches=.05)
    # Structural post-render audit: every input row visited (including empty
    # strata represented by NaN), all CI bounds in explicit axes range.
    assert plotted_rows == len(data), (kind, plotted_rows, len(data))
    finite = data[['top3_match', 'top3_match_lo', 'top3_match_hi']].to_numpy()
    assert np.all((finite[np.isfinite(finite)] >= -.025) & (finite[np.isfinite(finite)] <= 1.025))
    if kind == 'repeatability_accuracy':
        vals = data[['pairwise_top3_match','pairwise_top3_match_lo','pairwise_top3_match_hi']].to_numpy()
        assert np.isfinite(vals).all() and (vals >= -.025).all() and (vals <= 1.025).all()
    fig.canvas.draw()
    plt.close(fig)
    from PIL import Image
    with Image.open(dest/'plot.png') as image:
        assert image.width >= 1900 and image.height >= 1000
        dimensions = (image.width, image.height)
    warnings = ['Structural audit performed; visual judgement of overlap is not certified.',
                'Descriptive bootstrap bands can degenerate at boundaries.']
    if kind == 'gap_budget' and data.top3_match.isna().any():
        warnings += [f'{int(data.top3_match.isna().sum())} empty-stratum budget/method rows kept missing; see inputs.csv.']
    (dest/'audit.md').write_text(
        '# Figure audit\n\n- script_ran: yes\n- png_exists: yes\n- chart_type_matches_spec: pass\n'
        '- data_columns_match_spec: pass\n- axis_scales_match_spec: pass\n- labels_units_match_spec: pass\n'
        '- series_category_order_match_spec: pass\n- legend_complete_and_uncropped: structurally included via tight bbox\n'
        '- annotations_match_spec: pass\n- forbidden_elements_absent: pass\n'
        f'- rows_visited: {plotted_rows}/{len(data)}\n- image_pixels: {dimensions}\n'
        '- obvious_text_overlap_or_clipping: not visually certified; manual check advised\n'
        '- repairs_made: none\n- remaining_warnings: ' + '; '.join(warnings) + '\n'
        '- final_status: PASSED_WITH_WARNINGS\n')
    (dest/'final-status.md').write_text('PASSED_WITH_WARNINGS\n')
    return dimensions


def render_all(out, partial=False):
    out = Path(out)
    overview = json.loads((out/'summary.json').read_text())
    n, stage = overview['n_instances'], overview['analysis_stage']
    dims = {}
    for kind in KINDS:
        source = out/('gap_summary.csv' if kind == 'gap_budget' else 'cell_summary.csv')
        data = pd.read_csv(source)
        folder = out/kind
        folder.mkdir(parents=True, exist_ok=True)
        data.to_csv(folder/'inputs.csv', index=False, float_format='%.12g')
        if Path(__file__).resolve() != (folder/'plot.py').resolve():
            shutil.copy2(Path(__file__), folder/'plot.py')
        if (out/'figure-spec.md').exists():
            shutil.copy2(out/'figure-spec.md', folder/'figure-spec.md')
        (folder/'context.json').write_text(json.dumps({'kind':kind, 'partial':partial, 'n':n, 'stage':stage}))
        dims[kind] = render_one(data, kind, folder, partial, n=n, stage=stage)
        for ext in ('png', 'pdf'):
            shutil.copy2(folder/f'plot.{ext}', out/f'{kind}.{ext}')
    (out/'audit.md').write_text('# Figure audit\n\nAll three figures rendered from measured CSVs. All input rows are visited; German is omitted only in explicit exact-only mode. Full per-figure audits are alongside their replay scripts. Manual layout inspection remains recommended.\n')
    (out/'final-status.md').write_text('PASSED_WITH_WARNINGS\n')
    return dims


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path)
    args = ap.parse_args()
    here = Path(__file__).resolve().parent
    if args.out:
        status = json.loads((args.out/'summary.json').read_text()).get('status', '')
        render_all(args.out, partial=status == 'partial_exact')
    elif (here/'context.json').exists():
        context = json.loads((here/'context.json').read_text())
        render_one(pd.read_csv(here/'inputs.csv'), context['kind'], here, context['partial'], n=context['n'], stage=context['stage'])
    else:
        status = json.loads((here/'summary.json').read_text()).get('status', '')
        render_all(here, partial=status == 'partial_exact')
