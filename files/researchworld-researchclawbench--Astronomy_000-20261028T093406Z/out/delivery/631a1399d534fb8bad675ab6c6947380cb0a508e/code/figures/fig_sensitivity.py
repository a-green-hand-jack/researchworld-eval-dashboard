"""Figure 7: sensitivity of the 95% exclusion windows to the BH age, the set of levels, the e-fold floor and the rate model.
Reads outputs/summary_leaver.json (Leaver-calibrated rate) and outputs/summary.json (Detweiler rate): `sensitivity_95`."""
from common import *

SL, SD = summary('leaver')['sensitivity_95'], summary('detweiler')['sensitivity_95']
labels = {k: k for k in SL}
labels = {'baseline (t=4.5e7 yr, l=1-5, no self-int.)': r'baseline: $t_{\rm BH}=4.5\times10^7$ yr, $l=1$–5',
          't=1e6 yr': r'$t_{\rm BH}=10^6$ yr', 't=1e7 yr': r'$t_{\rm BH}=10^7$ yr', 't=1.38e10 yr (Hubble)': r'$t_{\rm BH}=1.38\times10^{10}$ yr (Hubble)',
          'levels l=m=1 only': r'$l=m=1$ only', 'levels l=m=1,2': r'$l=m\leq2$', 'min 100 e-folds (A&D)': r'$\geq100$ e-folds (Arvanitaki–Dubovsky)'}
fig, axs = plt.subplots(1, 2, figsize=(12, 4.2), gridspec_kw=dict(width_ratios=[1.4, 1]))
rng = {'M33_X-7': (5e-14, 3e-11), 'IRAS_09149-6206': (1e-19, 1e-18)}
for ax, (key, s) in zip(axs, SOURCES.items()):
    ys = np.arange(len(SL))[::-1]
    for y, k in zip(ys, SL):
        for off, SS, hatch, alpha, nm in ((0.17, SL, None, 0.9, 'Leaver-calibrated'), (-0.17, SD, '////', 0.45, 'Detweiler')):
            ws = SS[k][key]
            for j, (a, b) in enumerate(ws):
                ax.barh(y+off, b-a, left=a, height=0.3, color=s['color'], alpha=alpha, hatch=hatch, edgecolor='w' if hatch else None, lw=0,
                        label=nm if (y == ys[0] and j == 0) else None)
        if not SL[k][key] and not SD[k][key]: ax.text(rng[key][0]*1.08, y, 'no 95% window (either rate)', va='center', fontsize=7.5, color='0.4')
    ax.set_yticks(ys); ax.set_yticklabels([labels[k] for k in SL] if key == 'M33_X-7' else [], fontsize=8.5); ax.set_ylim(-0.6, len(SL)-0.4)
    ax.set_xscale('log'); ax.set_xlim(*rng[key]); ax.set_title(s['label'] + ': 95% exclusion windows', fontsize=10)
    ax.set_xlabel(r'boson mass $\mu$ [eV]')
h, l_ = [], []
from matplotlib.patches import Patch
axs[0].legend([Patch(color=SOURCES['M33_X-7']['color'], alpha=0.9), Patch(facecolor=SOURCES['M33_X-7']['color'], alpha=0.45, hatch='////', edgecolor='w')],
              ['Leaver-calibrated rate (headline)', 'Detweiler rate'], frameon=False, fontsize=8, loc='upper center', bbox_to_anchor=(0.5, -0.17), ncol=2)
fig.tight_layout(); save(fig, 'fig07_sensitivity.png')
