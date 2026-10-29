import pandas as pd, numpy as np
pd.set_option('display.width',250); pd.set_option('display.max_columns',40)
c=pd.read_csv('results/pairs_core.csv'); j=pd.read_csv('results/pairs_judges.csv')
df=pd.concat([c,j]); 
def design(b):
    if b.startswith('nba_alltime'): return 'sport_all'
    if b.startswith('nba'): return 'sport_season'
    if b=='arena55k_human': return 'crowd'
    if b=='mtbench_human': return 'expert'
    if b=='mtbench_gpt4': return 'gpt4'
    if b=='arenaST_human': return 'crowd_ST'
    return 'judge_'+b.split('judge_')[1][:10]
df['design']=df.board.map(design)
df['kap']=df.k_drop/df.N; df['kapf']=df.k_flip/df.N
df['sig']=df.z>2
print(df.groupby('design').agg(n=('z','size'),boards=('board','nunique'),N=('N','median'),inf_drop=('k_drop',lambda x: np.isinf(x).mean()),
   med_z=('z','median')))
s=df[(df.z>2)&np.isfinite(df.k_drop)]
print(s.groupby('design').agg(n=('z','size'),z_med=('z','median'),kd_med=('k_drop','median'),kap_med=('kap','median'),kf_med=('k_flip','median'),kapf_med=('kapf','median'),ka_med=('k_add','median')))
# c = k/(z sqrt(Ninv))
df['cc']=df.k_drop/(df.z*np.sqrt(df.n_inv)); 
print(df[(df.z>1)&np.isfinite(df.cc)].groupby('design').cc.describe())
print(df[(df.rank_i==0)&(df.rank_j==1)][['board','gap','se','z','boot_flip','k_drop','k_flip','k_add','N']].head(60).to_string())
print('-----')
from scipy.stats import norm
def kpred(z,n):
    eps=z/np.sqrt(n)
    out=np.where(eps>=0.3989, 0.5*n, np.nan)
    ok=eps<0.3989
    t=np.sqrt(-2*np.log(eps[ok]*np.sqrt(2*np.pi)))
    out[ok]=n[ok]*norm.sf(t); return out
m=df[(df.z>1)&np.isfinite(df.k_drop)&(df.k_drop>0)].copy()
m['kp_inv']=kpred(m.z.values,m.n_inv.values.astype(float)); m['kp_N']=kpred(m.z.values,m.N.values.astype(float))
m['r_inv']=np.log(m.k_drop/m.kp_inv); m['r_N']=np.log(m.k_drop/m.kp_N)
print(m.groupby('design')[['r_inv','r_N']].agg(['mean','std']))
print('rand baselines')
r=df[df.rand_drop_flip.notna()]
print(r.groupby('design')[['rand_drop_flip','rand_flip_flip']].agg(['mean','max']))
print(r[['z','rand_drop_flip','k_drop','boot_flip']].sort_values('z').iloc[::40].to_string())
# bootstrap flip vs z
print(df.groupby('design').apply(lambda g: pd.Series(dict(frac_sig=(g.z>2).mean(), bf_sig=g[g.z>2].boot_flip.max()))))
