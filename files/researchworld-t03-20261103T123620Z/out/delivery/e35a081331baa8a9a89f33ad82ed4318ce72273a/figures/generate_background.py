"""Present changed-game accuracy separately from exact-reference target shifts."""
import argparse
import json
from pathlib import Path
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'figures'))
from rendering import WIDTH_IN, METHOD_STYLE, paper_style, export_figure, file_record
from generate_main import truth, DATASET_NAMES, MODEL_NAMES
sys.path.insert(0,str(ROOT/'tables'))
from generate_main_tables import emit_table
DATASETS=['acs','diabetes']
MODELS=['logistic','forest','histboost']
ESTIMATORS=['permutation','kernel']


def frame(path):
    f=pd.read_csv(path);f['input_csv_line']=f.index+2;return f


def validated(f, metric, runs=False):
    q=f[f.metric==metric].copy()
    keys=['dataset','model','background_size']+(['estimator'] if runs else [])
    expected={(d,m,b,e) for d in DATASETS for m in MODELS for b in [8,128] for e in ESTIMATORS} if runs else {(d,m,b) for d in DATASETS for m in MODELS for b in [8,128]}
    actual=list(q[keys].itertuples(index=False,name=None))
    if len(actual)!=len(expected) or set(actual)!=expected:raise ValueError('Background grid missing/duplicated')
    if not (q.n_instances.eq(12).all() and q.n_metric_instances.eq(12).all() and q.n_repeats.eq(20 if runs else 1).all()):
        raise ValueError('Changed-background denominators require revision')
    if not np.isfinite(q[['estimate','ci_low','ci_high']].to_numpy()).all():raise ValueError('Missing intervals')
    if ((q.ci_low>q.estimate)|(q.ci_high<q.estimate)).any():raise ValueError('Invalid intervals')
    if runs and not all(q.budget==q.dataset.map({'acs':256,'diabetes':64})):raise ValueError('Middle budget changed')
    return q


def draw(ax,q,offset,style):
    q=q.sort_values('background_size');x=np.array([0.,1.])+offset;y=q.estimate.to_numpy()
    ax.errorbar(x,y,yerr=np.vstack([y-q.ci_low.to_numpy(),q.ci_high.to_numpy()-y]),
                capsize=2,elinewidth=.8,linestyle='none',**style)
    flags=np.array([truth(v) for v in q.boundary_adjusted])
    if flags.any():ax.plot(x[flags],y[flags],'+',color='black',linestyle='none',markersize=6,zorder=6)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--results',type=Path,default=ROOT/'results/background_sensitivity');p.add_argument('--analysis-revision',required=True);a=p.parse_args()
    root=a.results.resolve();paths={n:root/n for n in ['aggregate_metrics.csv','aggregate_reference_shift.csv','aggregation_manifest.json','reference_diagnostics.csv','job_costs.csv','warning_disposition.json']}
    manifest=json.loads(paths['aggregation_manifest.json'].read_text())
    if (manifest['status']!='complete' or manifest['n_runs']!=5760 or manifest['n_reference_inputs']!=144 or manifest['n_model_cells']!=6 or manifest['n_failed_attempts']!=0):raise ValueError('Incomplete sensitivity evidence')
    refs=frame(paths['reference_diagnostics.csv'])
    if len(refs)!=144 or not all(truth(v) for v in refs.exhaustive):raise ValueError('Nonexact changed targets')
    metrics=validated(frame(paths['aggregate_metrics.csv']),'joint_success_0p2',True)
    shift=frame(paths['aggregate_reference_shift.csv'])
    nl1=validated(shift,'nl1_error');top1=validated(shift,'top1_match')
    command='python3 figures/generate_background.py --results '+str(root.relative_to(ROOT))+' --analysis-revision '+a.analysis_revision
    with paper_style():
        for d in DATASETS:
            fig,axes=plt.subplots(3,3,figsize=(WIDTH_IN,5.5),sharex=True)
            fig.get_layout_engine().set(rect=(0,.13,1,.75))
            fig.suptitle(DATASET_NAMES[d]+' · changed-background check',fontsize=10,y=.97)
            mappings=[]
            for ci,m in enumerate(MODELS):
                axes[0,ci].set_title(MODEL_NAMES[m],fontsize=9)
                for ri,(f,metric) in enumerate([(nl1,'nl1_error'),(top1,'top1_match'),(metrics,'joint_success_0p2')]):
                    ax=axes[ri,ci];q=f[(f.dataset==d)&(f.model==m)]
                    subsets=[(e,q[q.estimator==e]) for e in ESTIMATORS] if ri==2 else [('exact targets',q)]
                    for ei,(label,qq) in enumerate(subsets):
                        style={'color':'.2','marker':'D' if ri==0 else 's'} if ri<2 else {'color':METHOD_STYLE[label]['color'],'marker':METHOD_STYLE[label]['marker']}
                        draw(ax,qq,(ei-.5)*.12 if ri==2 else 0,style)
                        mappings.append(dict(panel=f'{d}/{m}/{metric}/{label}',
                            file=str(paths['aggregate_metrics.csv' if ri==2 else 'aggregate_reference_shift.csv'].relative_to(ROOT)),
                            metric=metric,input_csv_lines=qq.input_csv_line.astype(int).tolist(),
                            x_column='background_size (categorical; one draw per size)',y_columns=['estimate','ci_low','ci_high'],
                            interval=qq.interval.tolist(),n_instances=12,n_repeats=20 if ri==2 else 1))
                    ax.grid(axis='y',color='.88',linewidth=.5);ax.set_xlim(-.3,1.3)
                    ax.set_ylim((-.025,1.025) if ri else (0,.8));ax.set_xticks([0,1],['8','128'])
                    if ci:ax.tick_params(labelleft=False)
                    if ri==0:ax.set_yticks([0,.4,.8])
                    else:ax.set_yticks([0,.5,1])
            for ri,label in enumerate(['Mean normalized\ntarget shift','Top-1 exact\ntarget match','Observed one-run\nadequacy rate']):axes[ri,0].set_ylabel(label,fontsize=8.5)
            handles=[Line2D([],[],color='.2',marker='D',linestyle='none',label='Exact targets vs B32')]
            handles += [Line2D([],[],color=METHOD_STYLE[e]['color'],marker=METHOD_STYLE[e]['marker'],linestyle='none',label=e.title()) for e in ESTIMATORS]
            fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.5,.045),ncol=3,frameon=False,fontsize=8)
            fig.supxlabel('Background rows (one training-row draw per size)',fontsize=9,y=.01)
            caption=(f'Changed-background sensitivity for {DATASET_NAMES[d]}. Top: exact changed-game attribution versus the '
                'main B32 exact attribution, using L1 difference/max(B32 attribution L1,0.01). Middle: fraction of inputs '
                'with the same most salient absolute-attribution feature under those two exact targets (stable raw-index '
                'tie order). These measure a target shift, not estimator error; B32 is a comparison target, not population '
                'truth. Bottom: stochastic accuracy against each changed game\'s own exact target, requiring normalized '
                'L1 <=0.20 and signed top-3 overlap >=2/3 with floor 0.01. Both estimators use the middle requested budget '
                f"({256 if d=='acs' else 64}); actual work is not equated. The same 12 main inputs and fitted models are retained, "
                'with 20 independent runs per input/estimator/background; exact target comparisons use one value per input. '
                'Bars are supplied pointwise 95% instance-cluster percentile intervals, conditional on each fitted model '
                'and each single background draw; black plus marks identify supplied two-sided Hoeffding boundary '
                'intervals for all-success panels. No >=0.95 population or individual certificate follows. Whole-row '
                'empirical interventional integration uses positive-class probability and grouped raw features. '
                'Size and selected training rows change together; one draw per size cannot identify a pure-size effect '
                'or background-population variance. These calls are separate from fixed-B32 main repetitions.')
            cp=ROOT/f'figures/background_sensitivity_{d}.caption.txt';cp.write_text(caption+'\n')
            export_figure(fig,ROOT/f'figures/background_sensitivity_{d}',root=ROOT,inputs=[*paths.values(),ROOT/'figures/generate_main.py',ROOT/'tables/generate_main_tables.py'],analysis_revision=a.analysis_revision,
                generator=Path(__file__),command=command,panels=mappings,caption_path=cp);plt.close(fig)
    jobs=frame(paths['job_costs.csv']);rows=[];rowmap=[]
    for d in DATASETS:
        for m in MODELS:
            q=jobs[(jobs.dataset==d)&(jobs.model==m)]
            if len(q)!=1 or q.status.iloc[0]!='complete':raise ValueError('Missing/duplicate sensitivity cost cell')
            r=q.iloc[0]
            if r.n_instances!=12 or r.n_repeats!=20 or r.n_backgrounds!=2 or truth(r.pilot):raise ValueError('Changed cost denominator')
            rows.append([DATASET_NAMES[d],MODEL_NAMES[m],f'{r.process_cpu_seconds:.2f}',f'{r.wall_seconds:.2f}',f'{r.peak_rss_kib/1024:.0f}'])
            rowmap.append(dict(dataset=d,model=m,file=str(paths['job_costs.csv'].relative_to(ROOT)),input_csv_line=int(r.input_csv_line),columns=['process_cpu_seconds','wall_seconds','peak_rss_kib'],conversion='KiB/1024 to MiB; seconds retained'))
    emit_table('background_compute','Completed changed-background phase costs: each row has 24 exact targets and 960 stochastic calls '
        '(12 inputs, two background draws, two estimators and 20 repeats). Phase CPU/wall starts after imports, bundle and data loading, '
        'so it is not comparable to the full-process main total without the scope difference. Peak RSS is whole process. '
        'Reference and call timing scopes overlap these phase totals and must not be added. The complete arm has 144 references, '
        '5760 calls and no failed attempts. Its 18 captured first-import colormap-deprecation messages are retained in '
        'warning\_disposition.json; no numerical warning was recorded. One background draw per size does not estimate a pure-size effect.',
        ['Dataset','Model','Phase CPU s','Phase wall s','Peak MiB'],rows,rowmap,
        dict(schema_version=1,analysis_revision=a.analysis_revision,inputs=[file_record(x,ROOT) for x in paths.values()],
            generator=file_record(Path(__file__),ROOT),supporting_code=[file_record(ROOT/'tables/generate_main_tables.py',ROOT),file_record(ROOT/'figures/generate_main.py',ROOT),file_record(ROOT/'figures/rendering.py',ROOT)]),command)
    print('Rendered separate exact-target/changed-game displays and phase cost table; inspect all outputs.')

if __name__=='__main__':main()
