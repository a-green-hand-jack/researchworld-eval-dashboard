import sys; sys.path.insert(0,'code')
import recon, pandas as pd, numpy as np
pd.set_option('display.width',250); pd.set_option('display.max_columns',30)
rid=int(sys.argv[1])
h,m=recon.run_region(rid)
print(m['meta']); 
for u in m['used']: print(u)
off=pd.read_csv(f"data/glambie/results/hydrological_years/{rid}_{recon.REGIONS[rid]}.csv")
off['k']=np.floor(off.start_dates+1e-6).astype(int); off=off.set_index('k')
cols=[c for c in h.columns if c.endswith('_mwe')]
print(pd.concat([h[['mwe','mwe_err']+cols], off[['combined_mwe','combined_mwe_errors']+[c for c in off.columns if c.endswith('_mwe')]]],axis=1).round(3))
