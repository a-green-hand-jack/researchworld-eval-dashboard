"""Figure: posterior samples of (M, a*) for the two black holes, with 68/95% highest-density regions."""
import numpy as np
from scipy.ndimage import gaussian_filter
from common import *

fig = plt.figure(figsize=(11, 5.2))
gs = fig.add_gridspec(2, 4, width_ratios=[4, 1, 4, 1], height_ratios=[1, 4], wspace=0.05, hspace=0.05,
                      left=0.07, right=0.98, bottom=0.12, top=0.93)
for i, (key, s) in enumerate(SOURCES.items()):
    M, a = load(key).T
    logM = key.startswith('IRAS')
    x = np.log10(M) if logM else M
    ax = fig.add_subplot(gs[1, 2*i]); axt = fig.add_subplot(gs[0, 2*i], sharex=ax); axr = fig.add_subplot(gs[1, 2*i+1], sharey=ax)
    ax.scatter(x, a, s=2, alpha=0.25, color=s['color'], rasterized=True, label=f'{len(x)} samples')
    px, pa = 0.08*np.ptp(x), 0.08*np.ptp(a)
    xe = np.linspace(x.min()-px, x.max()+px, 61); ae = np.linspace(a.min()-pa, a.max()+pa, 61)
    H, _, _ = np.histogram2d(x, a, bins=[xe, ae]); H = gaussian_filter(H, 1.5)
    srt = np.sort(H.ravel())[::-1]; c = np.cumsum(srt)/srt.sum()
    lv = [srt[np.searchsorted(c, f)] for f in (0.95, 0.68)]
    cs = ax.contour(0.5*(xe[1:]+xe[:-1]), 0.5*(ae[1:]+ae[:-1]), H.T, levels=lv, colors='k', linewidths=[0.8, 1.4])
    ax.plot([], [], 'k-', lw=1.4, label='68% / 95% HPD')
    med = np.median(x), np.median(a)
    ax.plot(*med, 'w*', mec='k', ms=11, label='median')
    ax.set_xlim(xe[0], xe[-1]); ax.set_ylim(ae[0], ae[-1])
    ax.legend(frameon=False, loc='lower right' if key.startswith('M33') else 'lower left', fontsize=8)
    ax.set_xlabel(r'$\log_{10}(M/M_\odot)$' if logM else r'$M\ [M_\odot]$'); 
    if i == 0: ax.set_ylabel(r'dimensionless spin $a_*$')
    axt.hist(x, bins=50, color=s['color'], alpha=0.7); axr.hist(a, bins=50, orientation='horizontal', color=s['color'], alpha=0.7)
    for q in np.percentile(x, [16, 84]): axt.axvline(q, color='k', lw=0.8, ls=':')
    for q in np.percentile(a, [16, 84]): axr.axhline(q, color='k', lw=0.8, ls=':')
    axt.set_yticks([]); axr.set_xticks([]); axt.spines['left'].set_visible(False); axr.spines['bottom'].set_visible(False)
    plt.setp(axt.get_xticklabels(), visible=False); plt.setp(axr.get_yticklabels(), visible=False)
    axt.set_title(f"{s['label']}" + (f"  (Pearson $r$ = {(lambda r: 0.0 if abs(r) < 0.005 else r)(np.corrcoef(x,a)[0,1]):+.2f})"), fontsize=10)
save(fig, 'fig01_data_overview.png')
