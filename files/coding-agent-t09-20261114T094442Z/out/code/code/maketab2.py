import sys; sys.path.insert(0,'/work/code')
from look import *
d=load('E1'); d['gk']=d.g.str.extract(r'^(\w+?)(?:\{|$)')[0]
gs={'sbm':'SBM','ba':'BA','ws':'WS','stanford':'Stanford3','egofb':'ego-FB'}
L=[]
for gk in gs:
  for des in ['bern','cluster']:
    row=[gs[gk],'Bern' if des=='bern' else 'Clust']
    for m in ['linfrac','sigmoid']:
      for e in ['dm','ols_frac','ols_rich','hgb']:
        s=d[(d.gk==gk)&(d.model==m)&(d.design==des)&(d.est==e)].iloc[0]
        row.append(f"{s.rmse:.2f}")
    L.append(' & '.join(row)+' \\\\')
open('/work/paper/tab_small.tex','w').write('\n'.join(L))
