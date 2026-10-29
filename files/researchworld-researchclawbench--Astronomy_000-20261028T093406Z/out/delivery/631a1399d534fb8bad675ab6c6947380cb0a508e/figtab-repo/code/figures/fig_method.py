"""Figure 2: how a posterior sample is classified as excluded/allowed at fixed boson mass mu (Leaver-calibrated rate, t_BH = 4.5e7 yr)."""
import sys, numpy as np, matplotlib.ticker
from common import *
sys.path.insert(0, os.path.join(HERE, '..'))   # code/ holds sr.py
import sr

T = 4.5e7
RATE = sr.make_calibrated_rate(os.path.join(OUTPUTS, 'rate_table.npz'))   # headline (Leaver-calibrated) rate
MUS = {'M33_X-7': [3e-13, 2e-12, 1e-11], 'IRAS_09149-6206': [1e-19, 3e-19, 1e-18]}
fig, axs = plt.subplots(2, 3, figsize=(11, 6.4))
for r, (key, s) in enumerate(SOURCES.items()):
    M, a = load(key).T
    for c, mu in enumerate(MUS[key]):
        ax = axs[r, c]
        ex = sr.excluded(mu, M, a, T, rate=RATE)
        ax.scatter(M[~ex], a[~ex], s=2, color='0.55', alpha=0.4, rasterized=True, label='allowed')
        ax.scatter(M[ex], a[ex], s=2, color=s['color'], alpha=0.5, rasterized=True, label='excluded')
        Mg = np.linspace(M.min(), M.max(), 300)
        for m_, ls in ((1, '-'), (2, '--')):
            af = sr.a_final(sr.alpha_of(mu, Mg), m_)
            ax.plot(Mg, af, 'k', ls=ls, lw=1, label=rf'$a_{{\rm sat}}$ ($m={m_}$)')
        ax.set_ylim(a.min()-0.03, 1.0); ax.set_xlim(M.min(), M.max())
        if key.startswith('IRAS'):
            ax.set_xscale('log'); ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
            ax.set_xticks([3e7, 1e8, 3e8]); ax.set_xticklabels([r'$3\times10^7$', r'$10^8$', r'$3\times10^8$'])
        ax.set_title(rf'{s["label"]},  $\mu={mu/10**np.floor(np.log10(mu)):g}\times10^{{{int(np.floor(np.log10(mu)))}}}$ eV:  $P_{{\rm ex}}={ex.mean():.2f}$', fontsize=9)
        ax.set_xlabel(r'$M\ [M_\odot]$')
        if c == 0: ax.set_ylabel(r'spin $a_*$')
        if c == 0 and r == 0: ax.legend(frameon=False, fontsize=7.5, markerscale=4, loc='lower right')
fig.tight_layout(); save(fig, 'fig02_method.png')
