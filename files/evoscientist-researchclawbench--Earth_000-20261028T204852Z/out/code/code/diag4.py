import sys; sys.path.insert(0,'./code')
from glambie_recon import *
inp=load_inputs()
def ann_series(R):
    return np.array([np.mean(R[(T>=y)&(T<y+1)]) for y in range(2003,2021)])
for rid in [17,1]:
    r=reconcile_region(rid,inp); o=official(rid)
    ser={}
    for g,ss in r['groups'].items():
        for s in ss:
            if s['dur']<2: ser[g[:3]+':'+s['file'].split('_')[-3][:10]+s['file'].split('_')[-2][:6]]=ann_series(s['R'])
    ser['OFF']=o.combined_mwe.values[3:21]; ser['mine']=ann_series(r['rate'])
    df=pd.DataFrame(ser); print(rid); print(df.corr().round(2).to_string())
d=inp[(inp.region_id==17)&(inp.file.str.contains('WGMS'))]; print(d.head(4))
