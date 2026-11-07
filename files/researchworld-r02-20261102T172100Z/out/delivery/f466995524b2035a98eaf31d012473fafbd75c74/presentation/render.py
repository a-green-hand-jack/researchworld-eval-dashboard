"""Render committed replication summaries; never recompute experimental results."""
import argparse
import hashlib
import json
import platform
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import numpy as np
import pandas as pd

ALL_METHODS = ['raw_l2', 'raw_linf', 'tv', 'kl_forward', 'clr_l2', 'clr_scaled', 'clr_mondrian', 'clr_weighted', 'coord_naive', 'coord_bonferroni']
METHODS = ALL_METHODS.copy()
LABELS = ['Raw Euclidean', 'Raw maximum', 'Total variation', 'Forward KL', 'Aitchison', 'Scaled Aitchison', 'Group Aitchison', 'Oracle weighted', 'Coord. naive', 'Coord. Bonferroni']
SHORT = dict(zip(METHODS, LABELS))
COLORS = {'coverage': '#0072B2', 'coverage_g0': '#009E73', 'coverage_g1': '#D55E00', 'shift': '#CC79A7'}
PAIRS = [('clr_scaled','clr_l2'), ('clr_mondrian','clr_l2'), ('raw_l2','clr_l2'), ('raw_linf','clr_l2'), ('tv','clr_l2'), ('kl_forward','clr_l2')]


def load_inputs(root):
    global METHODS, LABELS
    summary = pd.read_csv(root / 'summary.csv')
    paired = pd.read_csv(root / 'paired_contrasts.csv')
    rep = pd.read_csv(root / 'replications.csv')
    unknown=set(summary.method)-set(ALL_METHODS)
    if unknown:
        raise ValueError(f'Unrecognized method labels: {unknown}')
    METHODS=[m for m in ALL_METHODS if m in set(summary.method)]
    LABELS=[SHORT[m] for m in METHODS]
    for frame in (summary, paired, rep):
        if 'alpha' not in frame: frame['alpha']=.1
        # pandas normally infers bool; also handle explicit text without bool('False').
        if frame['shift'].dtype != bool:
            frame['shift'] = frame['shift'].map({'True': True, 'False': False, 'true': True, 'false': False})
        if frame['shift'].isna().any():
            raise ValueError('Unrecognized shift encoding')
    keys = ['k','ncal','scenario','shift','epsilon','alpha','method','metric']
    if summary.duplicated(keys).any():
        raise ValueError('Duplicate summary cells')
    for frame in (summary, paired):
        if frame['n_rep'].max() < 2:
            raise ValueError('Independent-replication intervals required')
    return summary, paired, rep


def select(frame, **keys):
    mask = np.ones(len(frame), dtype=bool)
    for key, value in keys.items():
        mask &= np.isclose(frame[key], value, rtol=1e-10, atol=0) if key == 'epsilon' else (frame[key] == value)
    return frame.loc[mask]


def ordered(cell):
    indexed = cell.set_index('method')
    missing = set(METHODS) - set(indexed.index)
    if missing or indexed.index.duplicated().any():
        raise ValueError(f'Incomplete or ambiguous method cell: {missing}')
    return indexed.loc[METHODS]


def dots(ax, cell, metric, offset=0, color='#0072B2', label=None, marker='o'):
    rows = ordered(select(cell, metric=metric))
    ys = np.arange(len(METHODS)) + offset
    for y, (_, row) in zip(ys, rows.iterrows()):
        if not np.isfinite([row['mean'], row['ci_low'], row['ci_high']]).all():
            raise ValueError('Missing estimate/interval in plotted cell')
        ax.plot([row.ci_low, row.ci_high], [y,y], color=color, lw=1.15, solid_capstyle='round')
        ax.plot(row['mean'], y, marker=marker, color=color, ms=3.4, label=label if y == ys[0] else None)


def coverage_axis(ax, labels=True, bounds=(0,1)):
    lo,hi=bounds
    ax.axvline(.9, color='.3', ls=(0,(3,2)), lw=.9, zorder=0)
    ax.set_xlim(min(0,lo-.01),max(1.015,hi+.01))
    ax.set_xticks([0,.25,.5,.75,1])
    if lo < -.03 or hi > 1.05:
        ax.xaxis.set_major_locator(MaxNLocator(nbins=4))
    ax.set_ylim(len(METHODS)-.45,-.55)
    ax.set_yticks(range(len(METHODS)), LABELS if labels else ['']*len(METHODS))
    ax.grid(axis='x', color='.9', lw=.5)
    ax.set_axisbelow(True)
    ax.set_xlabel('Simultaneous coverage')


def save(fig, name, root):
    fig.savefig(root / 'figures' / f'{name}.pdf', bbox_inches='tight', pad_inches=.035)
    fig.savefig(root / 'figures' / f'{name}.png', dpi=200, bbox_inches='tight', pad_inches=.035)
    plt.close(fig)


def joint_figure(summary, root, ncal, epsilon, alpha):
    summary=select(summary,alpha=alpha)
    fig, axes = plt.subplots(2,2,figsize=(5.5,5.2), constrained_layout=True)
    for i,k in enumerate([3,10]):
        for j,scenario in enumerate(['homogeneous','heterogeneous']):
            ax = axes[i,j]
            cell = select(summary,k=k,ncal=ncal,scenario=scenario,shift=False,epsilon=epsilon)
            dots(ax, cell, 'coverage')
            bounds=select(summary,ncal=ncal,shift=False,epsilon=epsilon,metric='coverage')
            coverage_axis(ax, labels=(j==0),bounds=(bounds.ci_low.min(),bounds.ci_high.max()))
            ax.set_title(f'{chr(97+i*2+j)}) K={k}, {scenario}', loc='left')
    save(fig,'joint_coverage',root)


def subgroup_figure(summary, root, ncal, epsilon, alpha):
    summary=select(summary,alpha=alpha)
    fig, axes = plt.subplots(1,2,figsize=(5.5,3.65), constrained_layout=True)
    for i,k in enumerate([3,10]):
        ax = axes[i]
        iid = select(summary,k=k,ncal=ncal,scenario='heterogeneous',shift=False,epsilon=epsilon)
        shifted = select(summary,k=k,ncal=ncal,scenario='heterogeneous',shift=True,epsilon=epsilon)
        dots(ax,iid,'coverage_g0',-.2,COLORS['coverage_g0'],'Group 0, iid', 'o')
        dots(ax,iid,'coverage_g1',0,COLORS['coverage_g1'],'Group 1, iid', 's')
        dots(ax,shifted,'coverage',.2,COLORS['shift'],'Marginal, shifted', '^')
        bounds=pd.concat([select(iid,metric='coverage_g0'),select(iid,metric='coverage_g1'),select(shifted,metric='coverage')])
        coverage_axis(ax,labels=(i==0),bounds=(bounds.ci_low.min(),bounds.ci_high.max()))
        ax.set_title(f'{chr(97+i)}) K={k}, heterogeneous',loc='left')
    handles,labels=axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='outside lower center',ncol=3,frameon=False,fontsize=7.5)
    save(fig,'group_shift_coverage',root)


def area_figure(summary, paired, root, ncal, epsilon, alpha):
    summary=select(summary,alpha=alpha)
    paired=select(paired,alpha=alpha)
    fig, axes = plt.subplots(2,2,figsize=(5.5,5.2), constrained_layout=True,gridspec_kw={'height_ratios':[1.5,1]})
    max_area=0
    min_area=0
    for j,scenario in enumerate(['homogeneous','heterogeneous']):
        cell=select(summary,k=3,ncal=ncal,scenario=scenario,shift=False,epsilon=epsilon)
        dots(axes[0,j],cell,'volume_fraction')
        areas=ordered(select(cell,metric='volume_fraction'))
        max_area=max(max_area,areas.ci_high.max())
        min_area=min(min_area,areas.ci_low.min())
        axes[0,j].set_title(f'{chr(97+j)}) K=3, {scenario}',loc='left')
        axes[0,j].set_yticks(range(len(METHODS)),LABELS if j==0 else ['']*len(METHODS))
        axes[0,j].set_ylim(len(METHODS)-.45,-.55)
        axes[0,j].set_xlabel('Mean fraction of simplex area')
        diff=select(paired,k=3,ncal=ncal,scenario=scenario,shift=False,epsilon=epsilon,metric='volume_fraction')
        for y,(a,b) in enumerate(PAIRS):
            row=select(diff,method_a=a,method_b=b)
            if len(row)!=1:
                raise ValueError('Missing or ambiguous paired area contrast')
            r=row.iloc[0]
            axes[1,j].plot([r.ci_low,r.ci_high],[y,y],color='#0072B2',lw=1.15)
            axes[1,j].plot(r.mean_difference,y,'o',color='#0072B2',ms=3.4)
        axes[1,j].axvline(0,color='.3',ls=(0,(3,2)),lw=.9)
        axes[1,j].set_yticks(range(len(PAIRS)),['Scaled − Aitch.','Group − Aitch.','Euclidean − Aitch.','Maximum − Aitch.','TV − Aitch.','KL − Aitch.'] if j==0 else ['']*len(PAIRS))
        axes[1,j].set_ylim(len(PAIRS)-.45,-.55)
        axes[1,j].set_xlabel('Paired area difference')
    for ax in axes[0]: ax.set_xlim(min_area*1.08,max_area*1.08)
    limits=[ax.get_xlim() for ax in axes[1]]
    extent=max(abs(x) for lim in limits for x in lim)
    for ax in axes[1]: ax.set_xlim(-extent,extent)
    for ax in axes.flat:
        ax.grid(axis='x',color='.9',lw=.5); ax.set_axisbelow(True)
    save(fig,'simplex_area',root)



def variability_figure(rep, root, epsilon, alpha):
    """ECDF of observed finite-test coverage, not a population-coverage guarantee."""
    fig, axes=plt.subplots(1,2,figsize=(5.5,2.5),constrained_layout=True)
    methods=['clr_l2','clr_scaled','clr_mondrian']
    for ax,ncal in zip(axes,[99,499]):
        for method,color,ls in zip(methods,['#0072B2','#D55E00','#009E73'],['-','--',':']):
            cell=select(rep,k=3,ncal=ncal,scenario='heterogeneous',shift=False,epsilon=epsilon,alpha=alpha,method=method)
            if len(cell)<2: raise ValueError('Missing replication variability cell')
            coverage=np.sort(cell.coverage.to_numpy())
            ecdf=np.arange(1,len(cell)+1)/len(cell)
            ax.step(np.r_[0,coverage,1],np.r_[0,ecdf,1],where='post',color=color,ls=ls,label=SHORT[method],lw=1.3)
        ax.axvline(.9,color='.3',ls=(0,(3,2)),lw=.8)
        ax.set_xlim(min(.5,float(select(rep,k=3,ncal=ncal,scenario='heterogeneous',shift=False,epsilon=epsilon,alpha=alpha).coverage.min())-.01),1); ax.set_ylim(0,1.01)
        ax.set_xticks([.5,.7,.9,1])
        ax.set_title(f'K=3, n={ncal}',loc='left')
        ax.set_xlabel('Per-replication test coverage')
        ax.grid(color='.9',lw=.5)
    axes[0].set_ylabel('Fraction of replications')
    handles,labels=axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='outside lower center',ncol=3,frameon=False,fontsize=7.5)
    save(fig,'replication_variability',root)


def estimate(row, digits=3):
    if row is None or not np.isfinite(row['mean']): return '--'
    return f"{row['mean']:.{digits}f} [{row['ci_low']:.{digits}f}, {row['ci_high']:.{digits}f}]"


def tables(summary, root):
    # Include all completed homogeneous/heterogeneous cells, never geometry-specific radii.
    numeric=summary[summary.scenario.isin(['homogeneous','heterogeneous']) & summary.metric.isin(['coverage','coverage_g0','coverage_g1','volume_fraction'])].copy()
    numeric.to_csv(root/'tables'/'all_estimates.csv',index=False)
    for keys,cell in numeric.groupby(['k','ncal','scenario','shift','epsilon','alpha']):
        k,ncal,scenario,shift,eps,alpha=keys
        lines=[r'\begin{tabular}{lrrr}',r'\toprule',r'Method & Joint coverage & Group 1 coverage & Area fraction \\',r'\midrule']
        for method in METHODS:
            values=[]
            for metric in ['coverage','coverage_g1','volume_fraction']:
                row=select(cell,method=method,metric=metric)
                values.append(estimate(row.iloc[0] if len(row)==1 else None))
            lines.append(SHORT[method]+' & '+' & '.join(values)+r' \\')
        lines += [r'\bottomrule',r'\end{tabular}']
        tag=f'k{k}_n{ncal}_{scenario}_{"shift" if shift else "iid"}_eps{eps:g}_alpha{alpha:g}'
        (root/'tables'/f'{tag}.tex').write_text('\n'.join(lines)+'\n')
        caption=(f'\\textbf{{Full-cell estimates: $K={k}$, calibration size {ncal}, {scenario}.}} ' + ('Controlled mixture-shift test environment. ' if shift else 'IID test environment. ') + f'All methods share {int(cell.n_rep.max())} independent datasets. Brackets are pointwise 95\\% $t$ intervals for replication means, not simultaneous bands. Area is the common Euclidean simplex fraction at $K=3$; -- means unmeasured at $K=10$. TV duplicates raw maximum at $K=3$; forward KL uses $y\Vert\hat\mu$. Group 1 is the prespecified higher-noise group in the heterogeneous mechanism. Full group-0 estimates and denominators are in \\texttt{{tables/all\\_estimates.csv}}.')
        (root/'tables'/f'{tag}_caption.tex').write_text(caption+'\n')



def captions(summary, rep, root, ncal, epsilon, alpha):
    main=select(summary,ncal=ncal,alpha=alpha,epsilon=epsilon,scenario='heterogeneous',metric='coverage')
    counts=sorted(main.n_rep.unique())
    if len(counts)!=1: raise ValueError('Unequal replication denominators need explicit caption treatment')
    count=int(counts[0])
    tests=sorted(rep.n_test.unique())
    test_text=str(int(tests[0])) if len(tests)==1 else '/'.join(map(str,tests))
    common=(f'Dots are means across {count} independent train/calibration/test replications; '
            r'bars are pointwise 95\% $t$ intervals for these means, not simultaneous bands or intervals for a single calibrated run. '
            f'Each replication uses 1000 training and {ncal} calibration observations and {test_text} test observations per environment. ')
    text={
        'joint_coverage':r'\textbf{Joint response coverage under iid sampling.} '+common+
            r'The dashed line marks nominal $1-\alpha=0.90$. The target is the entire observed composition, not a class label. '
            r'``Coord. naive\x27\x27 calibrates each coordinate at $\alpha$ and is a negative control; ``Coord. Bonferroni\x27\x27 uses $\alpha/K$. '
            r'Raw Euclidean and maximum regions are intersected with the simplex; Aitchison denotes the Euclidean norm of clr differences. '
            r'The oracle weighted method uses unit weights under iid sampling. TV is exactly raw maximum at $K=3$ and is distinct at $K=10$; KL is forward $D_{\rm KL}(y\Vert\hat\mu)$.',
        'group_shift_coverage':r'\textbf{Subgroup coverage and controlled mixture shift.} '+common+
            r'Circles and squares are iid coverage in the prespecified lower-noise group 0 and higher-noise group 1. '
            r'Triangles are marginal coverage after the test group-1 probability changes from $0.2$ to $0.8$, with within-group laws preserved. '
            r'Colors and shapes distinguish estimands; shifted marginal coverage is not a third subgroup. '
            r'``Group Aitchison\x27\x27 calibrates within observed groups; ``Oracle weighted\x27\x27 uses the known density ratio, unavailable in general applications. '
            r'The dashed line marks 0.90. TV exactly duplicates raw maximum at $K=3$; KL is forward $y\Vert\hat\mu$. This experiment does not test arbitrary shift.',
        'simplex_area':r'\textbf{A common area measure for $K=3$.} '+common+
            r'Area uses 32 independent feature anchors and 8192 common uniform-simplex candidates per anchor in each replication/environment. Top: mean fraction of Euclidean simplex area under iid sampling. The uniform-simplex reference measure is shared across methods; it is not clr volume or application utility. '
            r'Bottom: paired within-replication differences from unscaled Aitchison, with pointwise 95\% $t$ intervals; negative values indicate smaller area. '
            r'Interpret area jointly with the coverage displays; the naive control has no nominal joint-coverage guarantee. '
            r'TV exactly duplicates raw maximum at $K=3$, so these rows are one geometry. KL is forward $y\Vert\hat\mu$. Intervals crossing zero leave area orderings unresolved. No cross-geometry size comparison is made at $K=10$.',
        'replication_variability':r'\textbf{Mean validity does not guarantee every calibrated run.} '
            f'Empirical cumulative distributions of finite-test joint coverage across {count} independent datasets in the iid heterogeneous $K=3$ setting, '
            r'for calibration sizes 99 and 499. Global, training-only scaled and observed-group Aitchison methods share datasets within each replication. '
            f'Each plotted coverage uses {test_text} independent test responses conditional on its fitted and calibrated predictor; it still contains finite-test noise. '
            r'The dashed line marks 0.90. These distributions and their empirical lower tails are descriptive, not certified probabilities of population conditional validity.'
    }
    for name,caption in text.items():
        # Use conventional TeX closing quotation marks.
        (root/'figures'/f'{name}_caption.tex').write_text(caption.replace(r'\x27\x27',"''")+'\n')


def main_table(summary, root, ncal, epsilon, alpha):
    cell=select(summary,k=3,ncal=ncal,scenario='heterogeneous',epsilon=epsilon,alpha=alpha)
    lines=[r'\begin{tabular}{lrrrr}',r'\toprule',
           r'Method & \shortstack{Joint\\iid} & \shortstack{Group 1\\iid} & \shortstack{Joint\\shifted} & \shortstack{Area fraction\\iid} \\',r'\midrule']
    for method in METHODS:
        values=[]
        for metric,shift in [('coverage',False),('coverage_g1',False),('coverage',True),('volume_fraction',False)]:
            rows=select(cell,method=method,metric=metric,shift=shift)
            if len(rows)!=1: raise ValueError('Ambiguous main numeric table cell')
            row=rows.iloc[0]
            values.append(f"${row['mean']:.3f}\\pm{(row.ci_high-row.ci_low)/2:.3f}$")
        lines.append(SHORT[method]+' & '+' & '.join(values)+r' \\')
    lines += [r'\bottomrule',r'\end{tabular}']
    (root/'tables'/'main_summary.tex').write_text('\n'.join(lines)+'\n')
    caption=(r'\textbf{Reliability and common area in the heterogeneous $K=3$ setting.} '
             f'Calibration size is {ncal}; entries show replication means $\\pm$ pointwise 95\\% interval half-widths, '
             r'not standard deviations across runs. The shifted group-1 probability is 0.8 versus 0.2 for iid evaluation. '
             r'Area is a fraction of Euclidean simplex area, averaged over iid feature anchors. '
             r'Smaller area is useful only with adequate coverage; coordinatewise naive is the negative control. '
             r'TV exactly duplicates raw maximum at $K=3$; forward KL uses $y\Vert\hat\mu$. These intervals are not simultaneous. Full-cell estimates and replication counts are supplied in \texttt{tables/all\_estimates.csv}.')
    (root/'tables'/'main_summary_caption.tex').write_text(caption+'\n')


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--summary-dir',type=Path,required=True)
    ap.add_argument('--output-root',type=Path,required=True)
    ap.add_argument('--ncal',type=int,default=499)
    ap.add_argument('--alpha',type=float,default=.1)
    ap.add_argument('--epsilon',type=float,default=1e-6)
    ap.add_argument('--source-commit',required=True)
    ap.add_argument('--stage',choices=['diagnostic','confirmatory'],required=True)
    args=ap.parse_args()
    if args.alpha != .1:
        raise ValueError('Main displays are designed for alpha=.1; sensitivity needs its separate display')
    root=args.output_root
    for sub in ['figures','tables']: (root/sub).mkdir(parents=True,exist_ok=True)
    summary,paired,rep=load_inputs(args.summary_dir)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.titlesize':8.5,'axes.labelsize':8,'xtick.labelsize':8,'ytick.labelsize':8,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'ps.fonttype':42})
    joint_figure(summary,root,args.ncal,args.epsilon,args.alpha)
    subgroup_figure(summary,root,args.ncal,args.epsilon,args.alpha)
    area_figure(summary,paired,root,args.ncal,args.epsilon,args.alpha)
    tables(summary,root)
    variability_figure(rep,root,args.epsilon,args.alpha)
    main_table(summary,root,args.ncal,args.epsilon,args.alpha)
    captions(summary,rep,root,args.ncal,args.epsilon,args.alpha)
    manifest={'stage':args.stage,'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'source_repository':'world/experiment-repo','source_commit':args.source_commit,'ncal_main_figures':args.ncal,'independent_replications':sorted(summary.n_rep.unique().tolist()),'n_test':sorted(rep.n_test.unique().tolist()),'epsilon':args.epsilon,'alpha':args.alpha,'inputs':{},'rendering':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'matplotlib':matplotlib.__version__},'uncertainty':'Supplied 95% pointwise Student-t intervals across independent dataset replications; area contrasts are paired within seed. Intervals describe replication means, not individual-run coverage spread.','outputs':[]}
    for name in ['summary.csv','paired_contrasts.csv','replications.csv','summary_manifest.json']:
        path=args.summary_dir/name
        manifest['inputs'][name]=hashlib.sha256(path.read_bytes()).hexdigest()
    for path in sorted([*root.glob('figures/*'),*root.glob('tables/*')]):
        if path.is_file() and path.name not in ['provenance.json','supplement_provenance.json']: manifest['outputs'].append({'path':str(path.relative_to(root)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    (root/'figures'/'provenance.json').write_text(json.dumps(manifest,indent=2)+'\n')

if __name__=='__main__': main()
