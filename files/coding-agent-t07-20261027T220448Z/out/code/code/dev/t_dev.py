import sys; sys.path.insert(0,'/work/code')
import pandas as pd, numpy as np
from load_results import load_all
pd.set_option('display.width',250); pd.set_option('display.max_rows',500)
df=load_all(sys.argv[1])
base=df[(df.method=='rand/mean')].set_index(['bench','protocol','seed','n']).rmse
df=df[df.n>0].copy()
df['rel']=df.apply(lambda r: r.rmse/base[(r.bench,r.protocol,r.seed,r.n)],axis=1)
for prot in df.protocol.unique():
    for n in sorted(df.n.unique()):
        s=df[(df.protocol==prot)&(df.n==n)]
        # geometric mean of rmse ratios, and mean spearman
        g=s.groupby('method').agg(rel=('rel',lambda x: np.exp(np.log(x).mean())), sp=('spearman','mean'), bias=('bias','mean')).sort_values('rel')
        print('\n===',prot,'n=',n); print(g.head(12).round(3).to_string()); print(g.loc[[m for m in ['rand/mean','strat/mean','anchor/mean'] if m in g.index]].round(3).to_string())
