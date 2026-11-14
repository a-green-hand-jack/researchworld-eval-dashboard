import sys; sys.path.insert(0,'code')
import pandas as pd, numpy as np
from analyze_common import *
pd.set_option('display.width',250); pd.set_option('display.max_rows',500)
df=pd.read_csv('results/synth_main.csv')
a=agg(df,['dgp','K','n_cal','method'],['cov','size_pool','size_unif'])
sub=a[(a.n_cal==200)&(a.K==5)]
for d in ['ln','ln_het','dir','mult']:
    s=sub[sub.dgp==d].set_index('method').loc[ORDER]
    print(d); print(s[['cov','cov_hw','size_pool','size_pool_hw','size_unif']].round(4))
