import sys; sys.path.insert(0,'/work/code')
import pandas as pd, numpy as np
from load_results import load_all
pd.set_option('display.width',250); pd.set_option('display.max_rows',500)
df=load_all(sys.argv[1])
base=df[(df.method=='rand/mean')].set_index(['bench','protocol','seed','n']).rmse
df=df[df.n>0].copy()
df['method']=np.where(df.design=='AUTO','AUTO/'+df.est,df.method)
df['rel']=[r.rmse/base[(r.bench,r.protocol,r.seed,r.n)] for r in df.itertuples()]
ms=['rand/mean','strat/mean','anchor/mean','rand/lin','rand/ridge','rand/plug4','rand/cal4','rand/greg4','strat/cal4','strat/greg4','pps0.5/cal4','pps0.5/greg4','pps0.5/calgreg4','pps1.0/cal4','pps0.5/cal2','pps0.5/cal8','anchor/cal4','anchor/ridge','dopt4/cal','AUTO/minimax','AUTO/mean']
f=lambda x: np.exp(np.log(x).mean())
print(df[df.method.isin(ms)].pivot_table(index='method',columns=['protocol','n'],values='rel',aggfunc=f).loc[ms].round(3).to_string())
print(df[df.method.isin(ms)].pivot_table(index='method',columns=['protocol','n'],values='spearman',aggfunc='mean').loc[ms].round(3).to_string())
print(df[df.design=='AUTO'].groupby(['protocol','n','est']).chosen.agg(lambda x: x.value_counts().head(4).to_dict()).to_string())
