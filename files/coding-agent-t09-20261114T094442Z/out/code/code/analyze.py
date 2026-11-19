import sys; sys.path.insert(0,'/work/code')
from look import *
import numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
OUT='/work/paper/'; import os; os.makedirs(OUT,exist_ok=True)
plt.rcParams.update({'font.size':8,'figure.dpi':150})
EC={'dm':'#888888','ols_frac':'#1b9e77','ols_count':'#d95f02','ols_rich':'#7570b3','poly':'#e7298a','hgb':'#66a61e','hajek':'#a6761d'}
NM={'dm':'DM','ols_frac':'OLS-frac','ols_count':'OLS-count','ols_rich':'OLS-rich','poly':'Poly','hgb':'GBM','hajek':'Hajek-exposure'}
def f(x): return f'{x:.2f}'
# ---- Table 1: E1 RMSE with CI (main), written as latex
d=load('E1'); gs={'sbm':'SBM','ba':'BA','ws':'WS','stanford':'Stanford3','egofb':'ego-FB'}
d['gk']=d.g.str.extract(r'^(\w+?)(?:\{|$)')[0]
ests=['dm','ols_frac','ols_count','ols_rich','poly','hgb','hajek']
lines=[]
for gk in gs:
  for m in ['linfrac','lincount','quad','sigmoid','inter']:
    for des in ['bern','cluster']:
      s=d[(d.gk==gk)&(d.model==m)&(d.design==des)].set_index('est')
      vals=[]
      for e in ests:
        if e in s.index and s.loc[e,'nreps']>=3:
          v=s.loc[e,'rmse']; vals.append(f"{v:.2f}"+(f"$^\\dagger$" if s.loc[e,'nan_frac']>0.05 else ''))
        else: vals.append('--')
      best=np.nanargmin([float(v.replace('$^\\dagger$','')) if v!='--' else 9 for v in vals])
      vals[best]='\\textbf{'+vals[best]+'}'
      lines.append(f"{gs[gk]} & {m} & {'Bern' if des=='bern' else 'Clust'} & "+' & '.join(vals)+' \\\\')
open(OUT+'tab_main.tex','w').write('\n'.join(lines))
# summary for text: bias/sd decomposition for ols_frac
r=d[d.est.isin(['ols_frac','ols_rich','poly','hgb'])].copy()
r['abs_bias']=r.bias.abs()
print(r[['gk','model','design','est','bias','bias_se','sd','rmse','cover']].round(3).to_string())
# coverage table
cv=d[d.est.isin(['ols_frac','ols_rich','poly'])].pivot_table(index=['gk','model','design'],columns='est',values='cover')
cv.round(2).to_csv('/work/results/coverage_E1.csv')
# ---- Fig: sweeps
def sweep(ax,e,xcol,model,design=None,graphfilter=None,ests=('dm','ols_frac','ols_rich','poly','hgb'),logx=False,xl=''):
    dd=load(e)
    if xcol in('gam','p','sigma'): dd['x']=dd[xcol]
    elif xcol=='n': dd['x']=dd['n']
    elif xcol=='deg': dd['x']=dd['graph'].apply(lambda s:json.loads(s)['deg'])
    elif xcol=='rho': dd['x']=dd['graph'].apply(lambda s:json.loads(s)['rho'])
    dd=dd[dd.model==model]
    if design: dd=dd[dd.design==design]
    for es in ests:
        q=dd[dd.est==es].sort_values('x')
        if len(q)==0: continue
        ax.errorbar(q.x,q.rmse,yerr=[q.rmse-q.rmse_lo,q.rmse_hi-q.rmse],color=EC[es],label=NM[es],marker='o',ms=3,lw=1,capsize=1.5)
    ax.set_yscale('log'); 
    if logx: ax.set_xscale('log')
    ax.set_xlabel(xl); ax.set_title(f'{model}'+(f', {design}' if design else ''),fontsize=8)
fig,ax=plt.subplots(2,4,figsize=(11,4.6))
sweep(ax[0,0],'E3','deg','linfrac',logx=True,xl='mean degree (WS, Bernoulli)')
sweep(ax[0,1],'E3','deg','sigmoid',logx=True,xl='mean degree (WS, Bernoulli)')
sweep(ax[0,2],'E4','p','sigmoid','bern',xl='treatment prob p (SBM)')
sweep(ax[0,3],'E4','p','sigmoid','cluster',xl='treatment prob p (SBM)')
sweep(ax[1,0],'E5','rho','sigmoid',xl='out-cluster edge share (SBM, cluster design)')
sweep(ax[1,1],'E5','rho','quad',xl='out-cluster edge share (SBM, cluster design)')
sweep(ax[1,2],'E2','gam','sigmoid','bern',xl='interference strength $\\gamma$ (SBM)')
sweep(ax[1,3],'E2','gam','sigmoid','cluster',xl='interference strength $\\gamma$ (SBM)')
for a in ax.ravel(): a.set_ylabel('RMSE of GATE est.')
ax[0,0].legend(fontsize=6); plt.tight_layout(); plt.savefig(OUT+'fig_sweeps.pdf')
# ---- scaling fit n and degree for correctly specified linfrac
dd=load('E6'); dd=dd[(dd.model=='linfrac')]
fig,ax=plt.subplots(1,2,figsize=(6.5,2.4))
for es in ['dm','ols_frac','ols_rich']:
    q=dd[dd.est==es].sort_values('n'); ax[0].errorbar(q.n,q.sd,color=EC[es],marker='o',ms=3,label=NM[es])
    if es!='dm': print('slope sd vs n',es,np.polyfit(np.log(q.n),np.log(q.sd),1)[0])
q=dd[dd.est=='ols_frac'].sort_values('n'); ax[0].plot(q.n,q.sd.iloc[0]*(q.n.iloc[0]/q.n)**.5,'k--',lw=.7,label='$n^{-1/2}$')
ax[0].set_xscale('log');ax[0].set_yscale('log');ax[0].set_xlabel('n (WS, deg 20, Bernoulli)');ax[0].set_ylabel('SD of estimate');ax[0].legend(fontsize=6)
d3=load('E3'); d3['deg']=d3['graph'].apply(lambda s:json.loads(s)['deg']); d3=d3[d3.model=='linfrac']
for es in ['ols_frac','ols_rich']:
    q=d3[d3.est==es].sort_values('deg'); ax[1].plot(q.deg,q.sd,color=EC[es],marker='o',ms=3,label=NM[es])
    print('slope sd vs deg',es,np.polyfit(np.log(q.deg),np.log(q.sd),1)[0])
q=d3[d3.est=='ols_frac'].sort_values('deg'); ax[1].plot(q.deg,q.sd.iloc[0]*(q.deg/q.deg.iloc[0])**.5,'k--',lw=.7,label='$\\sqrt{d}$')
ax[1].set_xscale('log');ax[1].set_yscale('log');ax[1].set_xlabel('degree (WS, n=5000)');ax[1].set_ylabel('SD of estimate');ax[1].legend(fontsize=6)
plt.tight_layout(); plt.savefig(OUT+'fig_scaling.pdf')
# print compact sweep tables for text
for e,cols in [('E2',['gam']),('E3',['graph']),('E4',['p']),('E5',['graph']),('E6',['n']),('E7',['sigma'])]:
    dd=load(e); dd['k']=dd['graph'].apply(lambda s:json.dumps({k:v for k,v in json.loads(s).items() if k in('deg','rho')}))
    print(e); print(dd.pivot_table(index=['model']+(['design'] if 'design' in dd and dd.design.nunique()>1 else [])+cols+(['k'] if e in('E3','E5') else []),columns='est',values='rmse').round(3).to_string())
    if e in('E2','E4','E5','E6'):print(dd[dd.est.isin(['ols_frac'])].pivot_table(index=['model']+(['design'] if dd.design.nunique()>1 else [])+cols+(['k'] if e=='E5' else []),values=['bias','sd']).round(3).to_string())
