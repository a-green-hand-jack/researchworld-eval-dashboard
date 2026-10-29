"""Generate every paper table, figure, and scalar macro from saved results."""
from pathlib import Path
import json
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];P=R/'paper/generated';P.mkdir(exist_ok=True)
LABEL={'arena':'Arena','mt_human':'MT human','mt_gpt4':'MT GPT-4','nba2014':'NBA 2014','nba2015':'NBA 2015'}
COLORS=dict(zip(LABEL,['#0072B2','#D55E00','#009E73','#CC79A7','#E69F00']))
plt.rcParams.update({'text.usetex':True,'font.family':'serif','font.serif':['Times'],'font.size':8,'axes.labelsize':9,'legend.fontsize':7,'pdf.fonttype':42,'ps.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
def wilson(x,n):
 p=x/n;z=1.959963984540054;den=1+z*z/n;mid=(p+z*z/(2*n))/den;half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
 return mid-half,mid+half

def table(name,cols,head,rows):
 s='\\begin{tabular}{'+cols+'}\n\\toprule\n'+head+' \\\\\n\\midrule\n'
 s+='\n'.join(' & '.join(map(str,r))+' \\\\' for r in rows)+'\n\\bottomrule\n\\end{tabular}\n'
 (P/(name+'.tex')).write_text(s)

def main():
 s=pd.read_csv(R/'results/summary.csv').set_index('dataset');boot=pd.read_csv(R/'results/bootstrap.csv');noise=pd.read_csv(R/'results/noise.csv');a=pd.DataFrame(json.load(open(R/'results/attacks.json')));a=a[a['mode']=='influence'].set_index('dataset');pairs=pd.read_csv(R/'results/allpairs.csv');matched=pd.read_csv(R/'results/matched.csv');rows=[];details=[]
 for name in LABEL:
  v=s.loc[name];bb=boot[boot.dataset==name];lo,hi=bb.gap.quantile([.025,.975]);ties=100*(v.n-v.decisive)/v.n
  rows.append([LABEL[name],f'{int(v.n):,}',int(v.m),f'{ties:.1f}',int(v.clusters),f'{v.gap:.3f}',f'[{lo:.3f}, {hi:.3f}]',f'{100*bb.top_retained.mean():.1f}'])
 table('data_table','lrrrrrrr','Data & $N$ & $M$ & Tie \\% & Clusters & Gap & 95\\% interval & Top kept \\%',rows)
 rows=[]
 for name in LABEL:
  v=s.loc[name];at=a.loc[name];k=int(at.k);r=noise[(noise.dataset==name)&(noise.k==k)];lo,hi=wilson(r.top_changed.sum(),len(r));top=pairs[(pairs.dataset==name)&(pairs.rank_i==1)].k.min()
  rows.append([LABEL[name],int(at.predicted_k),k,f'{100*k/v.n:.4f}',f'{100*k/at.exposure:.2f}',int(top),f'{100*r.top_changed.mean():.1f} [{100*lo:.1f}, {100*hi:.1f}]'])
  details.append({'dataset':name,'k':k,'global_percent':100*k/v.n,'decisive_percent':100*k/v.decisive,'exposure_percent':100*k/at.exposure,'random_top_probability':r.top_changed.mean(),'random_wilson_low':lo,'random_wilson_high':hi,'top_witness':int(top)})
 table('radii_table','lrrrrrr','Data & $K_{\\rm lin}$ & $K_{12}$ & $100K_{12}/N$ & $100K_{12}/E_{12}$ & $K_{\\rm lead}$ & Random top loss \\%',rows)
 pd.DataFrame(details).to_csv(R/'results/report_radii.csv',index=False)
 rows=[]
 for name in LABEL:
  aa=a.loc[name];sub=pd.DataFrame(json.load(open(R/'results/attacks.json')));sub=sub[sub.dataset==name].set_index('mode')
  fmt=lambda x:'--' if pd.isna(x) else str(int(x))
  rows.append([LABEL[name]]+[fmt(sub.loc[mode,'k']) for mode in ['influence','endpoint','direct','wins']])
 table('baselines','lrrrr','Data & Full & Endpoint & Direct & Win gain',rows)
 rows=[];vv=pairs.dropna(subset=['k','predicted_k']).copy();vv['error']=abs(vv.k-vv.predicted_k);vv['relative']=vv.error/vv.k
 for name in LABEL:
  z=vv[vv.dataset==name];total=len(pairs[pairs.dataset==name]);rows.append([LABEL[name],f'{len(z)}/{total}',f'{z.error.median():.1f}',f'{z.error.max():.0f}',f'{100*z.relative.median():.1f}'])
 table('approximation','lrrrr','Data & Crossed/tested & Median $|\\Delta K|$ & Max & Median rel. \\%',rows)
 rows=[]
 ab=pd.read_csv(R/'results/ablations.csv')
 for name in LABEL:
  z=ab[ab.dataset==name];ks=[int(z[(z.variant=='ridge')&(z.value==l)].k.iloc[0]) for l in [.00001,.1,1.]];drop=z[z.variant=='decisive_only'].iloc[0]
  rows.append([LABEL[name],int(a.loc[name].k),*ks,int(drop.k),f'{drop.gap:.3f}'])
 table('ablations','lrrrrrr','Data & Base & $10^{-5}$ & $0.1$ & $1$ & No ties & No-tie gap',rows)
 ex=pd.read_csv(R/'results/supplement.csv');table('supplement','llrrrr','Data & Variant & $N$ & $K_{12}$ & Gap & $100K_{12}/N$',[[LABEL[r.dataset],{'experts_only':'Experts only','dedup_judgment_key':'Deduplicated key','exclude_inconsistent':'Omit inconsistent'}[r.variant],r.n,r.k,f'{r.gap:.3f}',f'{100*r.k/r.n:.2f}'] for r in ex.itertuples()])
 rows=[]
 for name in ['human','gpt4']:
  v=matched[matched.design==name];q=v.pair_radius.quantile([.025,.975]);rows.append(['Human' if name=='human' else 'GPT-4',f'{v.pair_radius.mean():.2f}',f'[{q.iloc[0]:.1f}, {q.iloc[1]:.1f}]',f'{v.top_radius.mean():.2f}',f'{v.win_margin.mean():.2f}',f'{v.theta_gap.mean():.3f}'])
 table('matched_table','lrrrrr','Judge & Mean $K_{4,C}$ & Panel interval & Mean $K_{\\rm lead}$ & Mean $W_4-W_C$ & Mean gap',rows)
 # Sampling noise across budgets.
 fig,axes=plt.subplots(1,2,figsize=(7,2.55),layout='constrained')
 for name in LABEL:
  n=noise[noise.dataset==name];g=n.groupby('k');ks=np.array(sorted(n.k.unique()));x=100*ks/s.loc[name,'n'];ys=[];los=[];his=[];dis=[];err=[]
  for k in ks:
   r=g.get_group(k);ys.append(r.top_changed.mean());lo,hi=wilson(r.top_changed.sum(),len(r));los.append(lo);his.append(hi);dis.append(1-r.tau.mean());err.append(1.96*r.tau.std()/np.sqrt(len(r)))
  axes[0].plot(x,ys,'o-',ms=3,color=COLORS[name],label=LABEL[name]);axes[0].fill_between(x,los,his,color=COLORS[name],alpha=.12)
  axes[1].errorbar(x,dis,yerr=err,fmt='o-',ms=3,lw=1,color=COLORS[name],label=LABEL[name])
 for ax in axes:ax.set_xscale('log');ax.set_xlabel('Reversed records (\% of all records)');ax.grid(alpha=.2)
 axes[0].set_ylabel('Probability original leader is lost');axes[0].set_ylim(-.02,.6);axes[1].set_ylabel(r'Mean rank disorder $1-\tau$');axes[0].legend(loc='upper left');fig.savefig(R/'figures/noise.pdf');plt.close(fig)
 # Matched balanced designs and differences, not population CIs.
 fig,axes=plt.subplots(1,2,figsize=(7,2.4),layout='constrained')
 for name,c,label in [('human',COLORS['mt_human'],'Human'),('gpt4',COLORS['mt_gpt4'],'GPT-4')]:
  vals=matched[matched.design==name].pair_radius;axes[0].hist(vals,bins=np.arange(8.5,43.5,1),histtype='step',lw=1.7,color=c,label=label)
 w=matched.pivot(index='rep',columns='design',values='pair_radius');diff=w.gpt4-w.human
 axes[1].hist(diff,bins=np.arange(diff.min()-.5,diff.max()+1.5),color='#666666',alpha=.75)
 axes[0].set_xlabel('Exact reversals to put Claude above GPT-4');axes[0].set_ylabel('Matched panels');axes[0].legend();axes[1].set_xlabel('GPT-4 judge radius minus human radius');axes[1].set_ylabel('Matched panels');fig.savefig(R/'figures/matched.pdf');plt.close(fig)
 # Broad validation: censored cases excluded transparently.
 fig,ax=plt.subplots(figsize=(3.35,2.65),layout='constrained')
 for name in LABEL:
  z=vv[vv.dataset==name];ax.scatter(z.predicted_k,z.k,label=LABEL[name],color=COLORS[name],s=13,alpha=.7)
 maxv=max(vv.k.max(),vv.predicted_k.max());ax.plot([1,maxv],[1,maxv],color='black',ls='--',lw=.8);ax.set(xscale='log',yscale='log',xlabel='Linear predicted budget',ylabel='First refitted crossing');ax.legend(fontsize=6,loc='upper left');fig.savefig(R/'figures/approximation.pdf');plt.close(fig)
 # Scalar macros: one source of truth for prose.
 rb=pd.read_csv(R/'results/gpt_radius_bootstrap.csv').k;glo,ghi=rb.quantile([.025,.975]);human=matched[matched.design=='human'];gpt=matched[matched.design=='gpt4'];dl,dh=diff.quantile([.025,.975]);metadata=json.load(open(R/'results/run_metadata.json'))
 macros={'HumanMatchMean':f'{human.pair_radius.mean():.2f}','GPTMatchMean':f'{gpt.pair_radius.mean():.2f}','MatchDiffMean':f'{diff.mean():.2f}','MatchDiffLow':f'{dl:.0f}','MatchDiffHigh':f'{dh:.0f}','GPTBootLow':f'{glo:.1f}','GPTBootHigh':f'{ghi:.1f}','MainRuntime':f'{metadata["seconds"]:.1f}','CrossedPairs':str(len(vv)),'TestedPairs':str(len(pairs)),'CensoredPairs':str(len(pairs)-len(vv)),'MaxBudgetError':str(int(vv.error.max()))}
 (P/'numbers.tex').write_text('\n'.join('\\newcommand{\\'+k+'}{'+v+'}' for k,v in macros.items())+'\n')
 # Machine-readable source of every summary used above.
 (R/'results/report_summary.json').write_text(json.dumps({'macros':macros,'matched_difference_mean':diff.mean(),'matched_difference_positive':int((diff>0).sum()),'matched_repetitions':len(diff),'complete_gpt_exact_radius':int(pd.read_csv(R/'results/balanced_exact.csv').query("i == 'gpt-4' and j == 'claude-v1'").exact_k.iloc[0])},indent=2)+'\n')
if __name__=='__main__':main()
