"""Generate every paper figure, table, and data-dependent numerical macro."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import norm
ROOT=Path(__file__).resolve().parents[1];RES=ROOT/'results';FIG=ROOT/'figures';GEN=ROOT/'paper/generated'
FIG.mkdir(exist_ok=True);GEN.mkdir(exist_ok=True)
PRIMARY=['arena','mt_human','mt_gpt4','nba2013','nba2014','nba2015']
LABEL={'arena':'Arena','mt_human':'MT human','mt_gpt4':'MT GPT-4','nba2013':'NBA 2013','nba2014':'NBA 2014','nba2015':'NBA 2015','matched_human':'Matched human','matched_gpt4':'Matched GPT-4','mt_gpt4_consistent':'MT consistent GPT-4'}
COLORS=['#0072B2','#D55E00','#009E73','#8C6BB1','#B39DCC','#5E3C99']
plt.rcParams.update({'font.size':9,'axes.labelsize':9,'legend.fontsize':7,'pdf.fonttype':42,'ps.fonttype':42,'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False})
A=pd.read_csv(RES/'attacks.csv');R=pd.read_csv(RES/'random.csv');S=pd.read_csv(RES/'data_summary.csv');SIM=pd.read_csv(RES/'simultaneous.csv')
D=A[(A.scope=='all')&(A.kind=='delete')]
def fmt(v,digits=2):return 'NF' if pd.isna(v) else f'{v:.{digits}f}'
def write_table(name,header,lines):
 (GEN/f'{name}.tex').write_text(header+'\n'+'\n'.join(lines)+'\n\\bottomrule\n\\end{tabular}\n')
def wilson(x,n):
 z=norm.ppf(.975);p=x/n;c=(p+z*z/(2*n))/(1+z*z/n);h=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n);return c-h,c+h

# Figure 1: found-witness profiles, not certified robustness CDFs.
fig,axes=plt.subplots(1,2,figsize=(6.7,2.45))
for name,c in zip(PRIMARY,COLORS):
 d=D[D.dataset==name]
 for ax,col in zip(axes,['alpha','local']):
  xx=np.geomspace(1e-5,.15,350);yy=np.array([(d[col]<=x).sum()/len(d) for x in xx])
  ax.plot(100*xx,100*yy,label=LABEL[name],color=c,lw=1.6)
for ax,lab in zip(axes,['Edits / all records (%)','Edits / target-pair exposure (%)']):
 ax.set_xscale('log');ax.set_xlabel(lab);ax.set_ylim(-2,103);ax.grid(alpha=.2)
axes[0].set_ylabel('Adjacent boundaries with witness (%)');axes[0].set_xlim(.001,5);axes[1].set_xlim(.01,15)
axes[1].legend(loc='lower right',ncol=2,frameon=False)
fig.tight_layout();fig.savefig(FIG/'profiles.pdf',bbox_inches='tight');fig.savefig(FIG/'profiles.png',dpi=400,bbox_inches='tight');plt.close(fig)

# Figure 2: random edits at 1%, uncertainty is Monte Carlo Wilson or mean intervals.
fig,axes=plt.subplots(1,2,figsize=(6.7,2.45));x=np.arange(len(PRIMARY));summary=[]
for offset,kind,c in [(-.18,'delete','#0072B2'),(.18,'flip','#D55E00')]:
 for metric,ax in zip(['leader_loss','boundary_reversal'],axes):
  means=[];los=[];his=[]
  for name in PRIMARY:
   vals=R[(R.dataset==name)&(R.kind==kind)&(R.alpha==.01)][metric];mean=vals.mean()
   if metric=='leader_loss':lo,hi=wilson(vals.sum(),len(vals))
   else:lo,hi=mean-1.96*vals.std(ddof=1)/np.sqrt(len(vals)),mean+1.96*vals.std(ddof=1)/np.sqrt(len(vals))
   means.append(mean*100);los.append(max(0,mean-lo)*100);his.append(max(0,hi-mean)*100)
   summary.append(dict(dataset=name,kind=kind,metric=metric,mean=mean,lo=lo,hi=hi))
  ax.bar(x+offset,means,width=.33,color=c,label=kind.capitalize(),yerr=np.array([los,his]),capsize=2,error_kw={'lw':.7})
for ax in axes:
 ax.set_xticks(x,[LABEL[n].replace(' ','\n') for n in PRIMARY],fontsize=7);ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
axes[0].set_ylabel('Trials losing original leader (%)');axes[1].set_ylabel('Adjacent boundaries reversed (%)');axes[0].legend(frameon=False)
fig.tight_layout();fig.savefig(FIG/'random.pdf',bbox_inches='tight');fig.savefig(FIG/'random.png',dpi=400,bbox_inches='tight');plt.close(fig)
pd.DataFrame(summary).to_csv(RES/'random_summary_1pct.csv',index=False)

# Figure 3: paired bootstrap difference in found edit fractions, same evaluation units.
P=pd.read_csv(RES/'paired_bootstrap.csv');E=pd.read_csv(RES/'matched_extended.csv')
fig,axes=plt.subplots(1,2,figsize=(6.7,2.2));paired=[]
for ax,kind,c in zip(axes,['delete','flip'],['#0072B2','#D55E00']):
 p=P[P.kind==kind].pivot(index='rep',columns='judge',values='alpha');delta=100*(p.gpt4-p.human)
 ax.hist(delta,bins=22,color=c,alpha=.8);ax.axvline(0,color='black',ls='--',lw=1)
 lo,hi=np.quantile(delta,[.025,.975]);ax.axvspan(lo,hi,color=c,alpha=.08)
 ax.set_xlabel(f'GPT-4 minus human, {kind} (percentage points)');ax.set_ylabel('Bootstrap replicates')
 for val in ['gap','alpha','local']:
  p0=P[P.kind==kind].pivot(index='rep',columns='judge',values=val);dd=p0.gpt4-p0.human;low,high=np.quantile(dd,[.025,.975])
  paired.append(dict(kind=kind,quantity=val,lo=low,median=dd.median(),hi=high,positive=float((dd>0).mean())))
fig.tight_layout();fig.savefig(FIG/'matched.pdf',bbox_inches='tight');fig.savefig(FIG/'matched.png',dpi=400,bbox_inches='tight');plt.close(fig)
pd.DataFrame(paired).to_csv(RES/'paired_summary.csv',index=False)

# Figure 4: approximation validation, repeated random choices of fixed boundaries.
V=pd.read_csv(RES/'approximation.csv');agg=[]
fig,axes=plt.subplots(1,2,figsize=(6.7,2.5))
for ax,kind in zip(axes,['delete','flip']):
 for name,c in zip(PRIMARY,COLORS):
  d=V[(V.dataset==name)&(V.kind==kind)].copy();d['rel']=np.abs(d.error)/np.maximum(np.abs(d.actual_change),1e-12)
  q=d.groupby('alpha').rel.quantile([.5,.9]).unstack()
  ax.plot(100*q.index,100*q[.5],'-o',ms=3,color=c,label=LABEL[name])
  for alpha,rr in q.iterrows():agg.append(dict(dataset=name,kind=kind,alpha=alpha,median_relative_error=rr[.5],p90_relative_error=rr[.9]))
 ax.set_xscale('log');ax.set_xlabel(f'{kind.capitalize()} budget / all records (%)');ax.set_ylabel('Median relative change error (%)');ax.grid(alpha=.2)
axes[0].legend(frameon=False,ncol=2,loc='upper left');fig.tight_layout();fig.savefig(FIG/'approximation.pdf',bbox_inches='tight');fig.savefig(FIG/'approximation.png',dpi=400,bbox_inches='tight');plt.close(fig)
pd.DataFrame(agg).to_csv(RES/'approximation_summary.csv',index=False)

# Data table.
lines=[]
for name in PRIMARY:
 s=S[S.dataset==name].iloc[0];lines.append(f"{LABEL[name]} & {s.N:,} & {s.M} & {100*s.ties/s.N:.1f} & {s.exposure_min}--{s.exposure_max} & {s.clusters:,} \\\\")
write_table('data',r'\begin{tabular}{lrrrrr}\toprule Dataset & $N$ & $M$ & Ties (\%) & Exposure range & Clusters \\ \midrule',lines)

# Leader table.
lines=[]
for name in PRIMARY:
 g=A[(A.dataset==name)&(A.boundary==1)&(A.scope=='all')];d=g[g.kind=='delete'].iloc[0];f=g[g.kind=='flip'].iloc[0]
 ci=f'[{d.ci_lo:.3f}, {d.ci_hi:.3f}]'
 lines.append(f"{LABEL[name]} & {d.gap:.3f} & {ci} & {fmt(d.k,0)} & {fmt(100*d.alpha,4)} & {fmt(100*d.local,2)} & {fmt(f.k,0)} & {fmt(100*f.alpha,4)} \\\\")
write_table('leaders',r'\begin{tabular}{lrr rrr rr}\toprule & & & \multicolumn{3}{c}{Deletion witness} & \multicolumn{2}{c}{Flip witness} \\ \cmidrule(lr){4-6}\cmidrule(lr){7-8} Dataset & Gap & Pointwise 95\% interval & $k$ & $100k/N$ & $100k/E_{ab}$ & $k$ & $100k/N$ \\ \midrule',lines)

# Profile table with full denominator, no conditioning on successes for medians.
lines=[]
for name in PRIMARY:
 d=D[D.dataset==name];sim=SIM[SIM.dataset==name];m=len(d)
 direct=A[(A.dataset==name)&(A.scope=='direct')&(A.kind=='delete')]
 lines.append(f"{LABEL[name]} & {m} & {d.k.notna().sum()}/{m} & {direct.k.notna().sum()}/{m} & {(d.ci_lo>0).sum()} & {(sim.sim_lo>0).sum()} & {(d.alpha<=.01).sum()}/{m} \\\\")
write_table('boundaries',r'\begin{tabular}{lrrrrrr}\toprule & & \multicolumn{2}{c}{Witness by 5\%} & \multicolumn{2}{c}{Positive gap lower bound} & Witness \\ Dataset & Boundaries & All records & Direct only & Pointwise & Simultaneous & by 1\% \\ \midrule',lines)

# Matched budget table.
lines=[]
for kind in ['delete','flip']:
 h=E[(E.judge=='human')&(E.kind==kind)].iloc[0];g=E[(E.judge=='gpt4')&(E.kind==kind)].iloc[0]
 p=pd.DataFrame(paired);q=p[(p.kind==kind)&(p.quantity=='alpha')].iloc[0]
 lines.append(f"{kind.capitalize()} & {int(h.k)} & {100*h.alpha:.2f} & {int(g.k)} & {100*g.alpha:.2f} & {100*(g.alpha-h.alpha):.2f} & [{100*q.lo:.2f}, {100*q.hi:.2f}] \\\\")
write_table('matched',r'\begin{tabular}{lrrrrrr}\toprule & \multicolumn{2}{c}{Human} & \multicolumn{2}{c}{GPT-4} & \multicolumn{2}{c}{GPT-4 minus human (pp)} \\ Edit & $k$ & $100k/N$ & $k$ & $100k/N$ & Point & Paired 95\% interval \\ \midrule',lines)

# Ablation leader table; labels readable and deterministic.
B=pd.read_csv(RES/'ablations.csv');lines=[]
for name in PRIMARY:
 base=D[(D.dataset==name)&(D.boundary==1)].iloc[0]
 for setting in ['ridge_0.0001','ridge_0.01','ridge_1.0','decisive_only','home_covariate']:
  ss=B[(B.dataset==name)&(B.setting==setting)&(B.boundary==1)&(B.kind=='delete')]
  if ss.empty:continue
  r=ss.iloc[0];lab={'ridge_0.0001':r'$\lambda=10^{-4}$','ridge_0.01':r'$\lambda=10^{-2}$','ridge_1.0':r'$\lambda=1$','decisive_only':'Decisive only','home_covariate':'Home covariate'}[setting]
  lines.append(f"{LABEL[name]} & {lab} & {fmt(r.k,0)} & {fmt(100*r.alpha,4)} & {fmt(100*r.local,2)} \\\\")
write_table('ablations',r'\begin{tabular}{llrrr}\toprule Dataset & Setting & $k$ & $100k/N$ & $100k/E_{ab}$ \\ \midrule',lines)

# Appendix random summary complete across budgets.
lines=[]
for name in PRIMARY:
 for kind in ['delete','flip']:
  for alpha in [.001,.005,.01,.02,.05]:
   d=R[(R.dataset==name)&(R.kind==kind)&(R.alpha==alpha)];lo,hi=wilson(d.leader_loss.sum(),len(d))
   lines.append(f"{LABEL[name]} & {kind} & {100*alpha:g} & {100*d.leader_loss.mean():.1f} [{100*lo:.1f}, {100*hi:.1f}] & {100*d.boundary_reversal.mean():.2f} & {100*d.discordance.mean():.3f} \\\\")
# longtable repeats header, works in one-column appendix.
(GEN/'random_full.tex').write_text(r'\begin{longtable}{llrrrr}\caption{Random edit results (200 repetitions per edit, dataset, and budget). Leader intervals are Wilson 95\% Monte Carlo intervals; boundary and discordance columns are means. Actual integer budgets are in the CSV files.}\label{tab:randomfull}\\ \toprule Dataset & Edit & Nominal \% & Leader loss \% [95\%] & Boundary \% & Discordance \% \\ \midrule\endfirsthead \toprule Dataset & Edit & Nominal \% & Leader loss \% [95\%] & Boundary \% & Discordance \% \\ \midrule\endhead'+'\n'+'\n'.join(lines)+'\n\\bottomrule\\end{longtable}\n')

# Useful numerical macros from results, never manual transcription.
macros={}
def macro(key,value):macros[key]=str(value)
macro('WitnessCount',len(pd.read_csv(RES/'witness_validation.csv')))
macro('PrimarySeconds',f"{json.loads((RES/'run_metadata.json').read_text())['seconds']:.1f}")
macro('ControlSeconds',f"{json.loads((RES/'controls_metadata.json').read_text())['seconds']:.1f}")
macro('MatchedN',int(S[S.dataset=='matched_human'].iloc[0].N))
macro('ArenaLeaderGap',f"{D[(D.dataset=='arena')&(D.boundary==1)].iloc[0].gap:.4f}")
macro('ArenaRandomDeleteLeader',f"{100*R[(R.dataset=='arena')&(R.kind=='delete')&(R.alpha==.01)].leader_loss.mean():.1f}")
macro('ArenaRandomFlipLeader',f"{100*R[(R.dataset=='arena')&(R.kind=='flip')&(R.alpha==.01)].leader_loss.mean():.1f}")
macro('ArenaMedianGlobal',f"{100*D[D.dataset=='arena'].alpha.median():.4f}")
macro('ArenaMedianLocal',f"{100*D[D.dataset=='arena'].local.median():.3f}")
macro('ArenaSeparatedK',int(D[(D.dataset=='arena')&(D.boundary==2)].iloc[0].k))
macro('ArenaSeparatedAlpha',f"{100*D[(D.dataset=='arena')&(D.boundary==2)].iloc[0].alpha:.3f}")
macro('ArenaSeparatedLocal',f"{100*D[(D.dataset=='arena')&(D.boundary==2)].iloc[0].local:.2f}")
macro('ArenaSeparatedLo',f"{SIM[(SIM.dataset=='arena')&(SIM.boundary==2)].iloc[0].sim_lo:.3f}")
macro('ArenaSeparatedHi',f"{SIM[(SIM.dataset=='arena')&(SIM.boundary==2)].iloc[0].sim_hi:.3f}")
q=pd.DataFrame(paired);q=q[(q.kind=='delete')&(q.quantity=='gap')].iloc[0]
macro('MatchedGapDiffLo',f'{q.lo:.3f}');macro('MatchedGapDiffHi',f'{q.hi:.3f}')
for kind,key in [('delete','Delete'),('flip','Flip')]:
 v=V[(V.dataset=='arena')&(V.kind==kind)&(V.alpha==.001)]
 macro('ArenaApprox'+key,f'{100*np.median(np.abs(v.error)/np.abs(v.actual_change)):.1f}')
(GEN/'numbers.tex').write_text('\n'.join('\\newcommand{\\'+k+'}{'+v+'}' for k,v in macros.items())+'\n')
print('Generated 4 figures, 6 tables, and',len(macros),'numeric macros.')
