"""Figure 5: self-interaction (bosenova-limited) exclusion in the (mu, f_a) plane and the implied upper limit on the
quartic coupling lambda = mu^2/f_a^2 (Leaver-calibrated rate). Reads outputs/pex_grid_mu_fa_leaver.npz and
outputs/fa_min_95_vs_mu_leaver.csv. The excluded region is f_a >= f_a,min(mu): weak self-interaction."""
import pandas as pd
from matplotlib.colors import LogNorm
from common import *

Z = np.load(os.path.join(OUTPUTS, 'pex_grid_mu_fa_leaver.npz'))
F = pd.read_csv(os.path.join(OUTPUTS, 'fa_min_95_vs_mu_leaver.csv'))
mu, fa = Z['mu_eV'], Z['fa_GeV']
KC = {'kappa0.1': ('0.1', '--'), 'kappa1': ('1', '-'), 'kappa10': ('10', ':')}
fig = plt.figure(figsize=(14.5, 4.6))
gs = fig.add_gridspec(1, 5, width_ratios=[1, 1, 0.04, 0.42, 1.2], wspace=0.22, left=0.06, right=0.985, bottom=0.2, top=0.92)
axs = [fig.add_subplot(gs[0]), fig.add_subplot(gs[1], sharey=None), fig.add_subplot(gs[4])]
cax = fig.add_subplot(gs[2])
for ax, (key, s) in zip(axs[:2], SOURCES.items()):
    P = Z[f'kappa1_{key}']
    im = ax.pcolormesh(mu, fa, P, cmap='viridis', vmin=0, vmax=1, shading='auto', rasterized=True)
    for kk, (kl, ls) in KC.items():
        ax.contour(mu, fa, Z[f'{kk}_{key}'], levels=[0.95], colors='w', linestyles=ls, linewidths=1.6)
    ax.contour(mu, fa, P, levels=[0.68], colors='0.75', linewidths=1.0, linestyles='-.')
    ax.set_xscale('log'); ax.set_yscale('log'); ax.set_xlabel(r'boson mass $\mu$ [eV]')
    ax.set_title(s['label'], fontsize=10)
    ax.set_xlim(*{'M33_X-7': (1e-14, 1e-10), 'IRAS_09149-6206': (1e-20, 1e-17)}[key])
    if key == 'M33_X-7': ax.set_ylabel(r'decay constant $f_a$ [GeV]')
    else: ax.text(0.03, 0.05, 'no 95% contour', color='w', transform=ax.transAxes, fontsize=8)
cb = fig.colorbar(im, cax=cax); cb.set_label(r'$P_{\rm ex}(\mu, f_a)$, $\kappa=1$')
from matplotlib.lines import Line2D
axs[0].legend([Line2D([], [], color='w', ls=ls, lw=1.6) for _, (_, ls) in KC.items()] + [Line2D([], [], color='0.75', ls='-.')],
              [rf'95%, $\kappa={kl}$' for _, (kl, _) in KC.items()] + [r'68%, $\kappa=1$'], fontsize=7.5, loc='lower left',
              facecolor='0.3', labelcolor='w', framealpha=0.7)
ax = axs[2]
muf = F['mu_eV'].values
for kk, (kl, ls) in KC.items():
    f = F[f'fa_min95_GeV_{kk}_M33_X-7'].values
    lam = (muf / (f * 1e9))**2
    ax.plot(muf, lam, color=SOURCES['M33_X-7']['color'], ls=ls, lw=1.8, label=rf'M33 X-7, $\kappa={kl}$')
ax.set_xscale('log'); ax.set_yscale('log'); ax.set_xlim(1e-13, 3e-11)
ax.set_xlabel(r'boson mass $\mu$ [eV]' '\n' r'kinks at $\mu\approx2\times10^{-12}$ and $4\times10^{-12}$ eV: $l=1\to2\to3$ transitions' '\n' r'steps: 0.125 dex $f_a$ grid', fontsize=8.5); ax.set_ylabel(r'$\lambda_{\max}(\mu)=\mu^2/f_{a,\min}^2$   [dimensionless]')
ax.set_title(r'upper limit on the quartic coupling (95%)', fontsize=10)
ax.text(0.03, 0.97, 'above the curves: allowed\n(strong coupling escapes via\nbosenova-limited spin-down);\nbelow the curves: excluded', transform=ax.transAxes, fontsize=7.5, va='top', color='0.3')
ax.legend(frameon=False, fontsize=8, loc='lower right')
save(fig, 'fig05_mu_fa_map.png')
