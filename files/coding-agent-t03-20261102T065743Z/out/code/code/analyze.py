"""All paper numbers, tables and plots are derived from saved experimental arrays."""
from common import *
import json,itertools
import pandas as pd
from scipy.stats import beta,spearmanr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
OUT=ROOT/'results/analysis';OUT.mkdir(parents=True,exist_ok=True)
FIG=ROOT/'paper/figures';FIG.mkdir(parents=True,exist_ok=True)
TAB=ROOT/'paper/tables';TAB.mkdir(parents=True,exist_ok=True)
LABEL={'german':'German','pima':'Pima','acs':'ACS','logistic':'LR','forest':'RF','boosting':'HGB','kernel':'Kernel','permutation':'Permutation'}
NBOOT=2000
BOOT=np.random.default_rng(seed_for(809)).integers(0,N_CASES,(NBOOT,N_CASES))

def interval(x):
 x=np.asarray(x,float);m=x.mean();lo,hi=np.quantile(x[BOOT].mean(axis=1),[.025,.975]);return float(m),float(lo),float(hi)
def fmt(x,percent=True):
 m,l,h=x;k=100 if percent else 1
 return f'{m*k:.1f} [{l*k:.1f}, {h*k:.1f}]'
def metrics(p,ref):
 err=np.max(abs(p-ref),axis=-1)
 idx=np.sort(np.argsort(-abs(p),axis=-1,kind='stable')[...,:3],axis=-1)
 rt=np.sort(np.argsort(-abs(ref),kind='stable')[:3])
 top=(idx==rt).all(axis=-1);num=err<=.01;joint=top&num
 material=abs(ref)>=.01
 signs=np.all((p[...,material]*ref[material])>0,axis=-1)
 eq=(idx[...,::2,:]==idx[...,1::2,:]).all(axis=-1)
 pairnum=np.max(abs(p[...,::2,:]-p[...,1::2,:]),axis=-1)<=.01
 samejoint=eq&pairnum;wrong=(~joint[...,::2])|(~joint[...,1::2])
 return dict(numeric=num.mean(axis=-1),top3=top.mean(axis=-1),joint=joint.mean(axis=-1),sign=signs.mean(axis=-1),maxerror=err.mean(axis=-1),relative_l1=(np.sum(abs(p-ref),axis=-1)/max(np.sum(abs(ref)),1e-12)).mean(axis=-1),repeat_top3=eq.mean(axis=-1),repeat_joint=samejoint.mean(axis=-1),agreed_wrong_top3=(eq&~top[...,::2]).mean(axis=-1),agreed_wrong_joint=(samejoint&wrong).mean(axis=-1),certified=(beta.ppf(.05,joint.sum(axis=-1),p.shape[-2]-joint.sum(axis=-1)+1)>=.95).astype(float),numeric005=(err<=.005).mean(axis=-1),numeric020=(err<=.02).mean(axis=-1)),err,top,joint

def load_main():
 rows=[];raw={};warnings=[];averages=[]
 for ds,md in itertools.product(DATASETS,MODELS):
  for case in range(N_CASES):
   f=ROOT/f'results/runs/{ds}_{md}_{case:02d}.npz';a=np.load(f);p=a['phi'];ref=a['ref'];raw[ds,md,case]=a
   met,err,top,joint=metrics(p,ref);rank=np.sort(abs(ref))[::-1];gap=rank[2]-rank[3]
   for ai,method in enumerate(['kernel','permutation']):
    for bi,c in enumerate(MULTIPLIERS):
     row=dict(dataset=ds,model=md,case=case,method=method,c=c,gap=gap,active=len(a['active']),cost=a['cost'][ai,bi].mean(),**{k:float(v[ai,bi]) for k,v in met.items()})
     # Empirical theorem check; the sufficient margin implication must never fail.
     row['margin_bound_fraction']=float((2*err[ai,bi]<gap).mean())
     row['margin_violations']=int(np.sum((2*err[ai,bi]<gap)&~top[ai,bi]))
     rows.append(row)
    avg=p[ai,0].reshape(16,4,len(ref)).mean(axis=1);am,_,_,_=metrics(avg,ref)
    averages.append(dict(dataset=ds,model=md,case=case,method=method,numeric=float(am['numeric']),top3=float(am['top3']),joint=float(am['joint']),cost=4*a['cost'][ai,0].mean()+8))
   if len(a['warnings']):warnings.extend([{'dataset':ds,'model':md,'case':case,'warning':str(x)} for x in a['warnings']])
 df=pd.DataFrame(rows);df.to_csv(OUT/'per_case.csv',index=False);pd.DataFrame(averages).to_csv(OUT/'averaging_per_case.csv',index=False)
 (OUT/'warnings.json').write_text(json.dumps(warnings,indent=2))
 return df,raw,pd.DataFrame(averages)

def aggregate(df):
 rows=[]
 keys=['numeric','top3','joint','sign','maxerror','relative_l1','repeat_top3','repeat_joint','agreed_wrong_top3','agreed_wrong_joint','certified','numeric005','numeric020','cost','margin_bound_fraction']
 for (ds,md,method,c),g in df.groupby(['dataset','model','method','c'],sort=False):
  r=dict(dataset=ds,model=md,method=method,c=c)
  for k in keys:
   m,l,h=interval(g.sort_values('case')[k]);r[k]=m;r[k+'_lo']=l;r[k+'_hi']=h
  rows.append(r)
 out=pd.DataFrame(rows);out.to_csv(OUT/'summary.csv',index=False)
 # Main table: joint rate and its case-bootstrap CI at each budget for all models.
 lines=[r'\begin{tabular}{llrrrr}',r'\toprule',r'Data & Model & $2d$ & $8d$ & $32d$ & $128d$ \\',r'\midrule']
 for ds,md in itertools.product(DATASETS,MODELS):
  vals=[]
  for c in MULTIPLIERS:
   g=out[(out.dataset==ds)&(out.model==md)&(out.method=='kernel')&(out.c==c)].iloc[0]
   vals.append(fmt((g.joint,g.joint_lo,g.joint_hi)))
  lines.append(f'{LABEL[ds]} & {LABEL[md]} & '+' & '.join(vals)+r' \\')
 lines.extend([r'\bottomrule',r'\end{tabular}']);(TAB/'main.tex').write_text('\n'.join(lines))
 # Full metric table in appendix.
 lines=[r'\begin{tabular}{llrrrrrr}',r'\toprule',r'Data/model & Budget & Num. & Top-3 & Joint & Signs & Repeat top-3 & Cert. cases \\',r'\midrule']
 for _,g in out[out.method=='kernel'].iterrows():
  lines.append(f'{LABEL[g.dataset]}/{LABEL[g.model]} & {int(g.c)}d & '+ ' & '.join(f'{100*g[k]:.1f}' for k in ['numeric','top3','joint','sign','repeat_top3'])+f' & {int(round(g.certified*N_CASES))}/32'+r' \\')
 lines.extend([r'\bottomrule',r'\end{tabular}']);(TAB/'full_metrics.tex').write_text('\n'.join(lines))
 return out

def overall(df,key,method='kernel',c=8):
 # Equal dataset weighting; resample matched cases within each dataset, preserve all models.
 arr=[]
 for ds in DATASETS:
  g=df[(df.dataset==ds)&(df.method==method)&(df.c==c)].pivot(index='case',columns='model',values=key).sort_index().mean(axis=1).to_numpy();arr.append(g)
 arr=np.array(arr);rng=np.random.default_rng(seed_for(819));res=[]
 for _ in range(NBOOT):res.append(np.mean([a[rng.integers(N_CASES,size=N_CASES)].mean() for a in arr]))
 return [float(arr.mean()),*map(float,np.quantile(res,[.025,.975]))]

def plots(df,out):
 # Accuracy dimensions differ, especially near ranking ties.
 fig,axs=plt.subplots(1,3,figsize=(6.8,2.25),sharey=True)
 for ax,ds in zip(axs,DATASETS):
  for md,color in zip(MODELS,['#0072B2','#D55E00','#009E73']):
   for metric,ls in [('numeric','-'),('top3','--')]:
    g=out[(out.dataset==ds)&(out.model==md)&(out.method=='kernel')].sort_values('c');x=np.arange(4)
    ax.plot(x,g[metric],ls,color=color,marker='o',ms=3,label=LABEL[md]+(' numeric' if metric=='numeric' else ' top-3'))
  ax.set_xticks(range(4),['2d','8d','32d','128d']);ax.set_title(LABEL[ds]);ax.set_ylim(-.03,1.04);ax.set_xlabel('Interior coalition cap');ax.grid(alpha=.2)
 axs[0].set_ylabel('Fraction of runs correct');axs[-1].legend(fontsize=7,ncol=2,loc='lower right');fig.tight_layout();fig.savefig(FIG/'accuracy.pdf');plt.close(fig)
 # Kernel vs permutation, joint success with bootstrap CIs aggregated fixed-model average per dataset.
 fig,axs=plt.subplots(1,3,figsize=(6.8,2.15),sharey=True)
 for ax,ds in zip(axs,DATASETS):
  for method,col,off in [('kernel','#0072B2',-.04),('permutation','#D55E00',.04)]:
   vals=[]
   for c in MULTIPLIERS:
    g=df[(df.dataset==ds)&(df.method==method)&(df.c==c)].pivot(index='case',columns='model',values='joint').mean(axis=1);vals.append(interval(g))
   vals=np.array(vals);ax.errorbar(np.arange(4)+off,vals[:,0],yerr=[vals[:,0]-vals[:,1],vals[:,2]-vals[:,0]],color=col,marker='o',capsize=2,label=LABEL[method])
  ax.set_title(LABEL[ds]);ax.set_xticks(range(4),['2d','8d','32d','128d']);ax.set_ylim(-.04,1.04);ax.grid(alpha=.2)
 axs[0].set_ylabel('Joint success (mean over models)');axs[-1].legend(fontsize=8);fig.tight_layout();fig.savefig(FIG/'baseline.pdf');plt.close(fig)
 # Margin stratification, no selected examples.
 g=df[(df.method=='kernel')&(df.c==8)].copy();g['stratum']=pd.cut(g.gap,[-1e-12,.005,.02,1.],labels=['<=0.005','(0.005,0.02]','>0.02'])
 sr=g.groupby('stratum',observed=False).agg(top3=('top3','mean'),numeric=('numeric','mean'),count=('case','count'));sr.to_csv(OUT/'margin.csv')
 fig,ax=plt.subplots(figsize=(4.7,2.55));x=np.arange(len(sr));ax.bar(x-.18,sr.numeric,.35,label='Numeric',color='#0072B2');ax.bar(x+.18,sr.top3,.35,label='Top-3',color='#D55E00');ax.set_xticks(x,[f'{i}\n(n={int(n)})' for i,n in zip(sr.index,sr['count'])]);ax.set_ylim(0,1.05);ax.set_ylabel('Correct-run fraction');ax.set_xlabel('Exact top-3 cutoff gap, at budget 8d');ax.legend(fontsize=8);fig.tight_layout();fig.savefig(FIG/'margin.pdf');plt.close(fig)

def bg_analysis():
 rows=[]
 for ds,md,case in itertools.product(['pima','acs'],MODELS,range(8)):
  a=np.load(ROOT/f'results/background/{ds}_{md}_{case:02d}.npz')['phi']
  for bi,b in enumerate([4,16,64]):
   x=a[bi];tops=np.sort(np.argsort(-abs(x),axis=1,kind='stable')[:,:3],axis=1)
   err=[];eq=[]
   for i,j in itertools.combinations(range(8),2):err.append(max(abs(x[i]-x[j])));eq.append((tops[i]==tops[j]).all())
   rows.append(dict(dataset=ds,model=md,case=case,bgsize=b,top3=float(np.mean(eq)),within001=float(np.mean(np.array(err)<=.01)),maxerror=float(np.mean(err))))
 df=pd.DataFrame(rows);df.to_csv(OUT/'background_per_case.csv',index=False)
 lines=[r'\begin{tabular}{llrrr}',r'\toprule',r'Dataset & $B$ & Top-3 agreement & $\|\Delta\phi\|_\infty\leq .01$ & Mean $\|\Delta\phi\|_\infty$ \\',r'\midrule']
 summ=[]
 for ds,b in itertools.product(['pima','acs'],[4,16,64]):
  g=df[(df.dataset==ds)&(df.bgsize==b)].groupby('case')[['top3','within001','maxerror']].mean();rng=np.random.default_rng(seed_for(998));ix=rng.integers(0,8,(NBOOT,8));vals=[];row={'dataset':ds,'bgsize':b}
  for k in g:
   x=g[k].to_numpy();ci=[float(x.mean()),*map(float,np.quantile(x[ix].mean(axis=1),[.025,.975]))];row[k]=ci;vals.append(fmt(ci,percent=k!='maxerror') if k!='maxerror' else f'{ci[0]:.3f} [{ci[1]:.3f}, {ci[2]:.3f}]')
  summ.append(row);lines.append(f'{LABEL[ds]} & {b} & '+' & '.join(vals)+r' \\')
 lines.extend([r'\bottomrule',r'\end{tabular}']);(TAB/'background.tex').write_text('\n'.join(lines));return summ

def defaults(raw):
 rows=[]
 for md,case in itertools.product(MODELS,range(N_CASES)):
  a=np.load(ROOT/f'results/runs/german_{md}_{case:02d}_default.npz');met,_,_,_=metrics(a['phi'],a['ref'])
  for k in met:pass
  rows.append(dict(model=md,case=case,**{k:float(v[0,0]) for k,v in met.items()}))
 df=pd.DataFrame(rows);df.to_csv(OUT/'default_per_case.csv',index=False)
 lines=[r'\begin{tabular}{llrrr}',r'\toprule',r'Model & Regularization & Numeric & Top-3 & Repeat top-3 \\',r'\midrule']
 for md in MODELS:
  for reg in ['None','Top 10']:
   if reg=='Top 10':g=df[df.model==md]
   else:g=GLOBAL_DF[(GLOBAL_DF.dataset=='german')&(GLOBAL_DF.model==md)&(GLOBAL_DF.method=='kernel')&(GLOBAL_DF.c==128)]
   lines.append(f'{LABEL[md]} & {reg} & '+' & '.join(fmt(interval(g[k])) for k in ['numeric','top3','repeat_top3'])+r' \\')
 lines.extend([r'\bottomrule',r'\end{tabular}']);(TAB/'regularization.tex').write_text('\n'.join(lines))
 return {md:{k:list(interval(df[df.model==md][k])) for k in ['numeric','top3','repeat_top3','joint']} for md in MODELS}

def auxiliary(df,avg):
 out={}
 # Paired case CIs comparing 4 averaged low runs against one 8d run.
 lines=[r'\begin{tabular}{llrrr}',r'\toprule',r'Data & Method & Four $2d$ runs & One $8d$ run & Difference (pp) \\',r'\midrule']
 for ds,method in itertools.product(DATASETS,['kernel','permutation']):
  g=avg[(avg.dataset==ds)&(avg.method==method)].pivot(index='case',columns='model',values='joint').mean(axis=1)
  h=df[(df.dataset==ds)&(df.method==method)&(df.c==8)].pivot(index='case',columns='model',values='joint').mean(axis=1)
  lines.append(f'{LABEL[ds]} & {LABEL[method]} & {fmt(interval(g))} & {fmt(interval(h))} & {fmt(interval(g-h))}'+r' \\')
 lines.extend([r'\bottomrule',r'\end{tabular}']);(TAB/'averaging.tex').write_text('\n'.join(lines))
 # How often top3 agreement is wrong, conditional on agreement; bootstrap stratified clusters.
 for c in MULTIPLIERS:
  num=[];den=[]
  for ds in DATASETS:
   g=df[(df.dataset==ds)&(df.method=='kernel')&(df.c==c)]
   num.append(g.pivot(index='case',columns='model',values='agreed_wrong_top3').mean(axis=1).to_numpy());den.append(g.pivot(index='case',columns='model',values='repeat_top3').mean(axis=1).to_numpy())
  num=np.array(num);den=np.array(den);rng=np.random.default_rng(seed_for(123));rs=[]
  for _ in range(NBOOT):
   ni=[];de=[]
   for i in range(3):
    ix=rng.integers(0,32,32);ni.append(num[i,ix].mean());de.append(den[i,ix].mean())
   rs.append(np.mean(ni)/np.mean(de))
  out[str(c)]={'wrong_given_top3_agreement':[float(num.mean()/den.mean()),*map(float,np.quantile(rs,[.025,.975]))]}
 return out

def models_table():
 df=pd.read_json(ROOT/'results/models.json');lines=[r'\begin{tabular}{lrrrrrr}',r'\toprule',r'Dataset & $n$ & Train & Test & $d$ & LR/RF/HGB AUC & LR/RF/HGB acc. \\',r'\midrule']
 for ds in DATASETS:
  g=df[df.dataset==ds].set_index('model').loc[MODELS];r=g.iloc[0]
  lines.append(f'{LABEL[ds]} & {int(r.n_total):,} & {int(r.n_train):,} & {int(r.n_test):,} & {int(r.d)} & '+ '/'.join(f'{x:.3f}' for x in g.auc)+' & '+ '/'.join(f'{x:.3f}' for x in g.accuracy)+r' \\')
 lines.extend([r'\bottomrule',r'\end{tabular}']);(TAB/'models.tex').write_text('\n'.join(lines))

def timing_table():
 df=pd.read_json(ROOT/'results/timing.json');lines=[r'\begin{tabular}{llrrrr}',r'\toprule',r'Dataset & Model & $2d$ & $8d$ & $32d$ & $128d$ \\',r'\midrule']
 for ds,md in itertools.product(DATASETS,MODELS):
  vals=[df[(df.dataset==ds)&(df.model==md)&(df.c==c)].seconds.median()*1000 for c in MULTIPLIERS]
  lines.append(f'{LABEL[ds]} & {LABEL[md]} & '+' & '.join(f'{v:.1f}' for v in vals)+r' \\')
 lines.extend([r'\bottomrule',r'\end{tabular}']);(TAB/'timing.tex').write_text('\n'.join(lines))
 return {'online_seconds_min':float(df.groupby(['dataset','model','c']).seconds.median().min()),'online_seconds_max':float(df.groupby(['dataset','model','c']).seconds.median().max()),'timing_rows':len(df)}

def runtime():
 out={};maximum=0
 for typ,pattern in [('games','games/*.npz'),('runs','runs/*.npz'),('background','background/*.npz'),('solver','solver/*.npz')]:
  files=list((ROOT/'results').glob(pattern));cpu=0;wall=0
  for f in files:
   a=np.load(f);cpu+=float(a['cpu_seconds']);wall+=float(a['seconds'])
   if 'v' in a:maximum=max(maximum,float(abs(a['phi'].sum()-(a['v'][-1]-a['v'][0]))))
  out[typ]={'files':len(files),'cpu_seconds':cpu,'sum_wall_seconds':wall}
 if out['games']['files']==0:
  refs=json.loads((ROOT/'results/reference_summary.json').read_text())
  out['games']={'files':len(refs),'cpu_seconds':sum(r['cpu_seconds'] for r in refs),'sum_wall_seconds':sum(r['seconds'] for r in refs),'source':'saved audited reference metadata; full tables omitted from lightweight archive'}
  maximum=max(r['efficiency_error'] for r in refs)
 out['max_reference_efficiency_error']=maximum
 return out

if __name__=='__main__':
 GLOBAL_DF,raw,avg=load_main();s=aggregate(GLOBAL_DF);plots(GLOBAL_DF,s);models_table()
 summary={'overall':{f'{method}_{c}':{k:overall(GLOBAL_DF,k,method,c) for k in ['numeric','top3','joint','repeat_top3','sign','numeric005','numeric020','certified','agreed_wrong_joint','repeat_joint']} for method,c in itertools.product(['kernel','permutation'],MULTIPLIERS)},'background':bg_analysis(),'defaults':defaults(raw),'pair_diagnostics':auxiliary(GLOBAL_DF,avg),'runtime':runtime(),'timing':timing_table(),'margin_violations':int(GLOBAL_DF.margin_violations.sum())}
 (OUT/'report.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
