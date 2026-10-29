import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glambie_lib as L, numpy as np
for mode in ['rms', 'epoch']:
    for rid in [1, 3, 4, 6, 7, 9, 17]:
        r = L.process_region(rid, dict(hr_err=mode))
        G = r['groups']; d = G['demdiff_glac']
        for g in ['gravimetry', 'altimetry']:
            if g in G:
                diff = G[g]['mwe'] - d['mwe']; s = np.sqrt(G[g]['err'] ** 2 + d['err'] ** 2)
                z = diff / s; z = z[np.isfinite(z)]
                print(mode, rid, g, len(z), np.round(np.std(z), 2), np.round(np.nanmean(G[g]['err']), 2))
