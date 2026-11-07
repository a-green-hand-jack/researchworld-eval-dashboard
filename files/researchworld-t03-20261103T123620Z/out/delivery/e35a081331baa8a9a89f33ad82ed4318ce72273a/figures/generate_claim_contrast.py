"""Compact main-text criterion and individual-input contrast from saved metrics."""
import argparse
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
from generate_main import load_evidence,verify_metric,DATASET_NAMES,MODEL_NAMES,truth
from generate_diagnostics import verify_instances
from rendering import WIDTH_IN,METHOD_STYLE,paper_style,export_figure


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--results',type=Path,default=ROOT/'results');p.add_argument('--config',type=Path,required=True);p.add_argument('--analysis-revision',required=True);a=p.parse_args()
 config,manifest,paths,metrics=load_evidence(a.results.resolve(),a.config.resolve())
 strict=verify_metric(pd.read_csv(paths['aggregate_metrics.csv']),'strict_joint_success_0p2',config,repeats=30)
 paths['instance_success.csv']=a.results.resolve()/'instance_success.csv';instances=pd.read_csv(paths['instance_success.csv']);instances['input_csv_line']=instances.index+2;verify_instances(instances,config)
 if config['n_instances']!=60 or config['n_repeats']!=30 or config['background_size']!=32:raise ValueError('Caption denominators require revision')
 cells=[(d,m) for d in config['datasets'] for m in config['models']];maps=[]
 broad=metrics['joint_success_0p2'];broad=broad[broad.apply(lambda row: row.budget==max(config['budgets'][row.dataset]),axis=1)]
 if len(broad)!=18 or not broad.estimate.eq(1).all() or not np.allclose(broad.ci_low,.8246698482359177):raise ValueError('Broad-event caption needs revision')
 maps.append(dict(panel='caption/highest-budget-primary',file='results/aggregate_metrics.csv',input_csv_lines=broad.input_csv_line.astype(int).tolist(),metric='joint_success_0p2',n_instances=60,n_repeats=30))
 with paper_style():
  fig,(left,right)=plt.subplots(1,2,figsize=(WIDTH_IN,3.4),gridspec_kw={'width_ratios':[1.05,1]})
  fig.get_layout_engine().set(rect=(0,0,1,.9))
  left.set_title('Highest budget: strict signed recovery',fontsize=8.5)
  for ei,e in enumerate(config['estimators']):
   for i,(d,m) in enumerate(cells):
    q=strict[(strict.dataset==d)&(strict.model==m)&(strict.estimator==e)&(strict.budget==max(config['budgets'][d]))].iloc[0]
    style=METHOD_STYLE[e];y=i+(ei-.5)*.22
    left.errorbar(q.estimate,y,xerr=[[q.estimate-q.ci_low],[q.ci_high-q.estimate]],color=style['color'],marker=style['marker'],linestyle='none',capsize=2,elinewidth=.8,markersize=3)
    if truth(q.boundary_adjusted):left.plot(q.estimate,y,'+',color='black',markersize=5,zorder=6)
    maps.append(dict(panel=f'strict/{d}/{m}/{e}',file='results/aggregate_metrics.csv',input_csv_line=int(q.input_csv_line),metric='strict_joint_success_0p2',budget=int(q.budget),interval=q.interval,n_instances=60,n_repeats=30))
  left.axvline(1,color='.5',linestyle=':',linewidth=.8)
  left.set_yticks(range(len(cells)),[f'{DATASET_NAMES[d]} {MODEL_NAMES[m]}' for d,m in cells],fontsize=7.5)
  left.invert_yaxis();left.set_xlim(.8,1.015);left.set_xticks([.8,.9,1]);left.set_xlabel('Observed strict-event rate',fontsize=8.5);left.grid(axis='x',color='.9',linewidth=.5)
  right.set_title('ACS RF: lowest-budget input rates',fontsize=8.5)
  for e in config['estimators']:
   q=instances[(instances.dataset=='acs')&(instances.model=='forest')&(instances.estimator==e)&(instances.budget==64)]
   values=np.sort(q.success_rate.to_numpy());xs=np.unique(np.r_[0,values,1]);ys=np.searchsorted(values,xs,side='right')/len(values);style=METHOD_STYLE[e]
   right.step(xs,ys,where='post',color=style['color'],linewidth=1.2)
   right.plot(xs,ys,color=style['color'],marker=style['marker'],markersize=3,linestyle='none',markevery=max(1,len(xs)//5))
   right.plot([0,0],[0,ys[0]],color=style['color'],linewidth=1.2)
   maps.append(dict(panel=f'instance/acs/forest/{e}/64',file='results/instance_success.csv',input_csv_lines=q.input_csv_line.astype(int).tolist(),x_column='successes/n_repeats',y_transform='empirical fraction of input rates <= x',n_instances=60,n_repeats=30))
  zero=instances[(instances.dataset=='acs')&(instances.model=='forest')&(instances.estimator=='kernel')&(instances.budget==64)&(instances.instance==30)].iloc[0]
  if zero.successes!=0:raise ValueError('The highlighted observed-input claim changed')
  right.annotate('One input: 0/30',xy=(0,1/60),xytext=(.10,.48),fontsize=8,arrowprops=dict(arrowstyle='->',color='.4',linewidth=.7))
  right.set_xlim(-.03,1.03);right.set_ylim(-.03,1.03);right.set_xticks([0,.5,1]);right.set_yticks([0,.5,1]);right.grid(axis='y',color='.9',linewidth=.5)
  right.set_xlabel('Observed successes / 30 runs',fontsize=8.5);right.set_ylabel('Fraction of inputs at or below x',fontsize=8.5)
  fig.legend(handles=[Line2D([],[],color=METHOD_STYLE[e]['color'],marker=METHOD_STYLE[e]['marker'],linestyle='none',label=e.title()) for e in config['estimators']],loc='upper center',ncol=2,frameon=False)
  caption=('Criterion and input dependence. Left: the strict event at the highest requested budgets '
    '(German 2048, ACS 512, Diabetes 128) requires normalized L1 <=0.20 and all three signed top-3 '
    'features matching the exact reference. Broad two-of-three primary-event rates are observed 1 '
    'for all these conditions, with supplied boundary interval [0.824670,1]; they do not imply exact '
    'feature recovery or population >=0.95 certification. Strict-event bars are supplied pointwise '
    '95% instance-cluster percentile intervals; black plus marks denote the supplied two-sided '
    'Hoeffding replacement at an observed all-success boundary. Each condition has 60 inputs and '
    '30 independent runs/input. Right: ECDF of observed primary-event input success fractions '
    'for ACS RF at requested budget 64; means can hide poor individual observations. Kernel input '
    f"30 (original source row {int(zero.source_id)}) has 0/30 successes, with supplied Wilson interval "
    f'[{zero.wilson_low:.3f},{zero.wilson_high:.3f}]. The ECDF has no confidence band and is not the '
    'distribution of known latent input probabilities. All panels condition on fixed fitted models, '
    'split and B32 empirical interventional probability game over raw-feature groups, with L1 '
    'normalization max(exact-reference L1,0.01). No individual certificate or equal-cost superiority follows.')
  cp=ROOT/'figures/criterion_instance_contrast.caption.txt';cp.write_text(caption+'\n')
  command='python3 figures/generate_claim_contrast.py --results results --config '+str(a.config.resolve().relative_to(ROOT))+' --analysis-revision '+a.analysis_revision
  export_figure(fig,ROOT/'figures/criterion_instance_contrast',root=ROOT,inputs=[*paths.values(),a.config.resolve(),ROOT/'figures/generate_main.py',ROOT/'figures/generate_diagnostics.py'],analysis_revision=a.analysis_revision,generator=Path(__file__),command=command,panels=maps,caption_path=cp)
 print('Rendered compact criterion/input contrast; open PDF before accepting.')

if __name__=='__main__':main()
