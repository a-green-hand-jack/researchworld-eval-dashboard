import sys; sys.path.insert(0,'./code')
from glambie_recon import *
inp=load_inputs()
for rid in [17,1]:
    r=reconcile_region(rid,inp); a=annualise(r); o=official(rid)
    print(REGNAME[rid]); print(pd.DataFrame({'y':a.year,'mine':a.mwe.round(2),'off':o.combined_mwe.round(2).values,'lev':[np.mean(r['level'][(T>=y)&(T<y+1)]).round(2) for y in a.year],'anom':[np.mean(r['anomaly'][(T>=y)&(T<y+1)]).round(2) for y in a.year]}).to_string())
    for g,ss in r['groups'].items():
        for s in ss: print(g,s['file'][-45:],round(s['dur'],2))
    print(r['off'])
