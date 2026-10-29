import sys; sys.path.insert(0,'/work/code')
from combine import *
def cmp(rid, allow=None):
    o=official(rid); y0=o.start_dates.iloc[0]; T=len(o)
    r=run_region(rid,y0,T,allow)
    return o,r
if __name__=='__main__':
    for rid in REGIONS:
        o,r=cmp(rid,allowed_groups(rid))
        line=[f"{rid:2d} {REGIONS[rid][:14]:14s}"]
        d=r['mu']-o.combined_mwe.values
        line.append(f"comb RMSD {np.sqrt(np.nanmean(d**2)):.3f} bias {np.nanmean(d):+.3f}")
        for g in GROUPS:
            if g in r['groups']:
                dd=r['groups'][g]['y']-o[g+'_mwe'].values
                if np.isfinite(dd).any(): line.append(f"{g[:4]} n={np.isfinite(dd).sum()} rmsd {np.sqrt(np.nanmean(dd**2)):.3f}")
                else: line.append(f"{g[:4]} (mine only)")
        print(' | '.join(line))
