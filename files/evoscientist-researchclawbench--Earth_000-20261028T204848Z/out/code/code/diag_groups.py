import sys; sys.path.insert(0,'code')
import recon, pandas as pd, numpy as np, warnings; warnings.filterwarnings('ignore')
cfg = eval(sys.argv[1]) if len(sys.argv)>1 else {}
for rid in recon.REGIONS:
    h,m=recon.run_region(rid,cfg)
    o=pd.read_csv(f"data/glambie/results/hydrological_years/{rid}_{recon.REGIONS[rid]}.csv"); o.index=np.floor(o.start_dates+1e-6).astype(int)
    out=[]
    for g in ['altimetry','gravimetry','demdiff_and_glaciological']:
        if g+'_mwe' not in h or o[g+'_mwe'].isna().all(): 
            if g+'_mwe' in h: out.append(f"{g[:4]}: mine only")
            continue
        k=o.index[o[g+'_mwe'].notna()]
        km=[x for x in k if x in h.index]
        mine=h.loc[km,g+'_mwe']; cov=h.loc[km,g+'_covered']
        out.append(f"{g[:4]}: off {o.loc[km,g+'_mwe'].mean():.3f} mine {mine.mean():.3f} (n={len(km)}, mine-cov {cov.sum()})")
    print(rid, recon.LABELS[rid][:14].ljust(14), ' | '.join(out), '| comb off %.3f mine %.3f'%(o.combined_mwe.mean(), h.loc[o.index.intersection(h.index),'mwe'].mean()))
