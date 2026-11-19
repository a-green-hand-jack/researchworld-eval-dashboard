"""Generate all paper figures/tables/macros from actual result CSVs. No hand-entered results."""
import json,math
from pathlib import Path
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import spearmanr
ROOT=Path(__file__).resolve().parents[1];A=ROOT/'artifacts';P=ROOT/'paper';F=P/'figures';T=P/'tables';F.mkdir(exist_ok=True);T.mkdir(exist_ok=True)
LABEL={'arena':'Arena crowd','mt_human':'MT expert','mt_gpt4':'MT GPT-4','nba2013':'NBA 2013','nba2014':'NBA 2014','nba2015':'NBA 2015','arena_top6_n2400':'Arena top-six (N=2400)','mt_human_cell':'MT expert matched','mt_gpt4_cell':'MT GPT-4 matched'}
ORDER=list(LABEL)[:6]
COLOR={'uniform':'#0072B2','incident_random':'#56B4E9','incident_adverse':'#009E73','influence':'#D55E00'}
METHOD={'uniform':'Uniform','incident_random':'Incident uniform','incident_adverse':'Incident adverse','influence':'Frozen influence'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'ps.fonttype':42,'savefig.bbox':'tight'})
def save(fig,name):
 fig.savefig(F/f'{name}.pdf');fig.savefig(F/f'{name}.png',dpi=240);plt.close(fig)
def tab(name,headers,rows,align=None):
 if align is None:align='l'+'r'*(len(headers)-1)
 text='\\begin{tabular}{'+align+'}\n\\toprule\n'+' & '.join(headers)+' \\\\\n\\midrule\n'
 text+='\n'.join(' & '.join(map(str,row))+' \\\\' for row in rows)
 text+='\n\\bottomrule\n\\end{tabular}\n';(T/f'{name}.tex').write_text(text)
def wilson(x,n):
 z=1.959963984540054;p=x/n;d=1+z*z/n;mid=(p+z*z/(2*n))/d;rad=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
 return max(0,mid-rad),min(1,mid+rad)
def main():
 base=pd.read_csv(A/'baseline.csv').set_index('dataset').loc[ORDER];U=pd.read_csv(A/'uncertainty.csv');C=pd.read_csv(A/'controls.csv');D=pd.read_csv(A/'random_curves.csv');M=pd.read_csv(A/'matched.csv');AD=pd.read_csv(A/'adjacent.csv');AB=pd.read_csv(A/'fixed_target_ablations.csv')
 rows=[]
 for name,r in base.iterrows():rows.append([LABEL[name],f'{r.n:,}',int(r.m),f'{r.E:,}',f'{r.gap:.3f}',int(r.k),f'{r.global_pct:.4f}' if name=='arena' else f'{r.global_pct:.3f}',f'{r.exposure_pct:.3f}'])
 tab('main',['Dataset','$N$','$M$','$E_{ab}$','$\\hat\\Delta$','$k$','$100k/N$','$100k/E_{ab}$'],rows)
 stats=[];controls=[]
 for name in ORDER:
  row=[LABEL[name]]
  for method in ['uniform','incident_random','incident_adverse','edge_matched']:
   s=C[(C.dataset==name)&(C.method==method)].success;x=int(s.sum());n=len(s);lo,hi=wilson(x,n)
   stats.append(dict(dataset=name,method=method,successes=x,repeats=n,rate=x/n,low=lo,high=hi));row.append(f'{x}/{n}')
  controls.append(row)
 pd.DataFrame(stats).to_csv(A/'control_summary.csv',index=False)
 tab('controls',['Dataset','Uniform','Incident','Adverse','Edge-matched'],controls)
 boots=[];bootstats=[]
 for name in ORDER:
  sub=U[U.dataset==name];lo,hi=sub.gap.quantile([.025,.975]);pos=int(sub.positive.sum());attempt=sub.iloc[:30];valid=attempt[attempt.witness_status=='found_on_resampled_slots']
  boots.append([LABEL[name],f'[{lo:.3f}, {hi:.3f}]',f'{pos}/{len(sub)}',f'{len(valid)}/30'])
  bootstats.append(dict(dataset=name,low=lo,high=hi,positive=pos,repeats=len(sub),witness_positive_draws=len(valid),slot_budget_median=float(valid.witness_k.median()),slot_budget_low=float(valid.witness_k.quantile(.025)),slot_budget_high=float(valid.witness_k.quantile(.975))))
 pd.DataFrame(bootstats).to_csv(A/'bootstrap_summary.csv',index=False)
 tab('bootstrap',['Dataset','Gap percentile band','Positive margin','Slot witnesses'],boots)
 fig,axes=plt.subplots(1,2,figsize=(7.1,2.9),gridspec_kw={'width_ratios':[1.2,1]})
 y=np.arange(6)
 for i,name in enumerate(ORDER):
  r=base.loc[name];axes[0].plot([r.global_pct,r.exposure_pct],[i,i],color='0.7',lw=1)
 axes[0].scatter(base.global_pct,y,label='$100k/N$',marker='o',color='#0072B2',s=29,zorder=4);axes[0].scatter(base.exposure_pct,y,label='$100k/E_{ab}$',marker='D',color='#D55E00',s=25,zorder=4)
 axes[0].set_xscale('log');axes[0].set_yticks(y,[LABEL[n] for n in ORDER]);axes[0].invert_yaxis();axes[0].set_xlabel('Witness budget (%) — log scale');axes[0].legend(frameon=False,fontsize=8,loc='lower left');axes[0].set_title('(a) Same edits, different denominators',fontsize=10)
 bs=pd.DataFrame(bootstats).set_index('dataset').loc[ORDER]
 axes[1].errorbar(base.gap,y,xerr=np.stack([base.gap-bs.low,bs.high-base.gap]),fmt='o',color='#009E73',capsize=3,ms=4,lw=1.2)
 axes[1].axvline(0,color='0.6',ls='--',lw=.8);axes[1].set_yticks(y,[]);axes[1].invert_yaxis();axes[1].set_xlabel('Leader − runner-up log-strength');axes[1].set_title('(b) Empirical resampling bands',fontsize=10)
 fig.tight_layout();save(fig,'budget_and_margin')
 fig,axs=plt.subplots(2,3,figsize=(7.1,4.1),sharex=True,sharey=True)
 for ax,name in zip(axs.flat,ORDER):
  for method in COLOR:
   sub=D[(D.dataset==name)&(D.method==method)];g=sub.groupby('local_budget').success.agg(['sum','count']).reset_index();rates=g['sum']/g['count'];x=g.local_budget*100
   ax.plot(x,rates,color=COLOR[method],label=METHOD[method],lw=1.3,marker='o' if method!='influence' else 's',ms=3,ls='-' if method!='influence' else '--')
   if method!='influence':
    intervals=np.array([wilson(int(s),int(n)) for s,n in zip(g['sum'],g['count'])]);ax.fill_between(x,intervals[:,0],intervals[:,1],color=COLOR[method],alpha=.12,lw=0)
  ax.set_xscale('log');ax.set_title(LABEL[name],fontsize=9);ax.set_xticks([.5,2,10,20],['0.5','2','10','20']);ax.set_ylim(-.03,1.03);ax.grid(axis='y',color='.9',lw=.5)
 for ax in axs[1]:ax.set_xlabel('$100\\lceil fE_{ab}\\rceil/E_{ab}$ (nominal % grid)')
 for ax in axs[:,0]:ax.set_ylabel('Pair reversal rate')
 handles,labels=axs[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='upper center',ncol=4,frameon=False,fontsize=8,bbox_to_anchor=(.5,1.03));fig.tight_layout(rect=(0,0,1,.96));save(fig,'dose_response')
 # Secondary adjacent-pair relation, descriptive only.
 fig,ax=plt.subplots(figsize=(5.2,3.1));corr=[]
 for name in ORDER:
  sub=AD[AD.dataset==name].dropna(subset=['k']);ax.scatter(sub.gap,sub.exposure_pct,label=LABEL[name],s=15,alpha=.7)
  rho=spearmanr(sub.gap,sub.exposure_pct).statistic;corr.append(dict(dataset=name,adjacent_pairs=len(sub),rho=rho,k_min=int(sub.k.min()),k_median=float(sub.k.median()),k_max=int(sub.k.max())))
 ax.set_xscale('log');ax.set_yscale('log');ax.set_xlabel('Baseline adjacent-pair gap');ax.set_ylabel('Exposure-scaled witness budget (%)');ax.legend(frameon=False,fontsize=7,ncol=2);fig.tight_layout();save(fig,'adjacent_pairs');pd.DataFrame(corr).to_csv(A/'adjacent_summary.csv',index=False)
 # Matched support summaries are min/median/max, not confidence intervals.
 matched=[];ms=[]
 for name,sub in M.groupby('dataset',sort=False):
  values=dict(dataset=name,runs=len(sub),n=int(sub.n.iloc[0]),k_min=int(sub.k.min()),k_median=float(sub.k.median()),k_max=int(sub.k.max()),exposure_min=float(sub.exposure_pct.min()),exposure_median=float(sub.exposure_pct.median()),exposure_max=float(sub.exposure_pct.max()),gap_median=float(sub.gap.median()))
  ms.append(values);matched.append([LABEL[name],len(sub),int(sub.n.iloc[0]),f'{values["k_min"]}/{values["k_median"]:g}/{values["k_max"]}',f'{values["exposure_min"]:.2f}/{values["exposure_median"]:.2f}/{values["exposure_max"]:.2f}'])
 tab('matched',['Cohort','Runs','$N$','$k$: min/med/max','$100k/E$: min/med/max'],matched)
 pd.DataFrame(ms).to_csv(A/'matched_summary.csv',index=False)
 # Supplementary tables.
 names={'ridge_0.1':'$\\lambda=0.1$','ridge_10':'$\\lambda=10$','drop_ties':'Remove ties','home_covariate':'Home covariate','exclude_inconsistent':'Remove inconsistent'}
 tab('fixed_ablations',['Dataset','Change','Original-pair gap','$k$','Status'],[[LABEL[r.dataset],names[r.ablation],f'{r.gap:.3f}',int(r.k) if pd.notna(r.k) else '--','Already reversed' if r.status=='already_reversed' else 'Witness'] for r in AB.itertuples()],align='llrrl')
 meth=pd.read_csv(A/'method_comparison.csv');methrows=[]
 for name,r in base.iterrows():
  sub=meth[meth.dataset==name].set_index('method');methrows.append([LABEL[name],int(r.k),int(sub.loc['adaptive_flip','k']),int(sub.loc['deletion_static','k']),int(r.predicted_k)])
 tab('methods',['Dataset','Frozen flips','Adaptive flips','Deletion','Linear prediction'],methrows)
 E=pd.read_csv(A/'eda.csv').set_index('dataset').loc[ORDER]
 tab('eda',['Dataset','Raw rows','Used rows','Ties','Clusters'],[[LABEL[name],f'{r.raw_rows:,}',f'{r.n:,}',f'{r.ties:,}',f'{r.unique_clusters:,}'] for name,r in E.iterrows()])
 rt=pd.read_csv(A/'runtime.csv')
 tab('runtime',['Dataset','Fits','Seconds','Max $\\|g\\|_\\infty$'],[[LABEL[r.dataset],int(r.fit_count),f'{r.seconds:.2f}',f'{r.max_gradient:.2g}'] for r in rt.itertuples()])
 meta=json.loads((A/'run_metadata.json').read_text());summary={'base':base.reset_index().to_dict('records'),'bootstrap':bootstats,'matched':ms,'controls':stats,'run':meta,'adjacent':corr};(A/'summary.json').write_text(json.dumps(summary,indent=2))
 macros={'MainSeconds':f'{meta["total_seconds"]:.1f}','ZeroUpper':f'{100*wilson(0,100)[1]:.1f}','MainFitCount':str(int(rt.fit_count.sum())),'AdjacentCount':str(len(AD)),'MinGradient':f'{rt.max_gradient.max():.1e}'}
 (P/'numbers.tex').write_text('\n'.join('\\newcommand{\\'+k+'}{'+v+'}' for k,v in macros.items())+'\n')
 print('all tables/figures generated; main seconds',meta['total_seconds'])
if __name__=='__main__':main()
