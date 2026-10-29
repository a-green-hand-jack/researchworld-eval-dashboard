import sys, time, numpy as np, pandas as pd
sys.path.insert(0,'/work/code')
from data import load; import bp
Y,_=load(sys.argv[1]); rng=np.random.default_rng(1)
perm=rng.permutation(len(Y)); nt=int(.3*len(Y)); T=perm[:nt]; S=perm[nt:]
t0=time.time(); rows=bp.evaluate_split(Y,S,T,[25,100],0); print(time.time()-t0)
df=pd.DataFrame(rows); pd.set_option('display.width',200); pd.set_option('display.max_rows',500)
print(df[df.n==25][['design','est','rmse','mae','bias','spearman']].round(4).to_string())
