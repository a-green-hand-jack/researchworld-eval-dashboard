import sys; sys.path.insert(0,'./code')
from glambie_recon import *
inp=load_inputs(); r=reconcile_region(1,inp); m=(T>=2005)&(T<2006)
a=r['area'][m].mean()
for g,e in r['gerr'].items(): print(g,np.nanmean(e[m]),'mwe/yr ->Gt',np.nanmean(e[m])*a/1e3)
for g,ss in r['groups'].items():
    for s in ss: print(g,s['file'][-40:],np.nanmean(s['E'][m]) *a/1e3)
