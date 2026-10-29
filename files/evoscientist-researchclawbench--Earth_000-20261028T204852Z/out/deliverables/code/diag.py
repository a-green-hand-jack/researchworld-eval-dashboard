import sys; sys.path.insert(0,'./code')
import warnings; warnings.filterwarnings('ignore')
from glambie_recon import *
inp=load_inputs()
for rid in [8,16]:
    r=reconcile_region(rid,inp)
    m=(T>=2000)&(T<2024)
    for g,ss in r['groups'].items():
        for s in ss:
            print(rid,g,s['file'][-40:],'dur %.2f'%s['dur'],'mean %.3f'%np.nanmean(s['R'][m]),'min %.2f max %.2f'%(np.nanmin(s['R'][m]),np.nanmax(s['R'][m])), 'n',np.sum(~np.isnan(s['R'][m])))
    for g in r['glev']: print(g,np.nanmean(r['glev'][g][m]),np.nanmax(np.abs(r['gan'][g][m])) if g in r['gan'] else None, r['off'][g])
