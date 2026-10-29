import sys; sys.path.insert(0,'/work/code')
import pandas as pd, numpy as np
from load_results import load_all
pd.set_option('display.width',250); pd.set_option('display.max_rows',500)
df=load_all('dev')
base=df[(df.method=='rand/mean')].set_index(['bench','protocol','seed','n']).rmse
d0=df[df.n==0]
df=df[df.n>0].copy()
df['rel']=[r.rmse/base[(r.bench,r.protocol,r.seed,r.n)] for r in df.itertuples()]
ms=['rand/mean','strat/mean','anchor/mean','rand/lin','rand/ridge','rand/irt4','rand/plug4','rand/greg4','rand/gregcf4','strat/greg4','pps0.5/greg4','pps1.0/greg4','pps0.5/mean','anchor/plug4','dopt4/plug','dopt4/greg']
t=df[df.method.isin(ms)].pivot_table(index='method',columns=['protocol','n'],values='rel',aggfunc=lambda x: np.exp(np.log(x).mean())).loc[ms]
print(t.round(3).to_string())
t=df[df.method.isin(ms)].pivot_table(index='method',columns=['protocol','n'],values='bias',aggfunc='mean').loc[ms]
print(t.round(4).to_string())
# per benchmark top n=100
t=df[df.method.isin(['strat/mean','rand/ridge','rand/greg4','pps0.5/greg4','anchor/plug4'])&(df.protocol=='top')&(df.n==100)].pivot_table(index='method',columns='bench',values='rel',aggfunc=lambda x: np.exp(np.log(x).mean()))
print(t.round(2).to_string())
