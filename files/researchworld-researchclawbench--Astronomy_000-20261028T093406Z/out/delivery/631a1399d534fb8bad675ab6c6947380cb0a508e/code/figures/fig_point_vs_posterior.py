"""Figure 4: full-posterior P_ex(mu) against the step function obtained from the median (M, a*) alone (Leaver-calibrated rate).
Reads outputs/pex_vs_mu_leaver.csv, outputs/point_estimate_indicator_*_leaver.csv, summary_leaver.json."""
import pandas as pd
from common import *

d = pd.read_csv(os.path.join(OUTPUTS, 'pex_vs_mu_leaver.csv'))
S = summary()
fig, axs = plt.subplots(1, 2, figsize=(11, 4.0))
rng = {'M33_X-7': (5e-14, 3e-11), 'IRAS_09149-6206': (5e-20, 2e-18)}
for ax, (key, s) in zip(axs, SOURCES.items()):
    pi = pd.read_csv(os.path.join(OUTPUTS, f'point_estimate_indicator_{key}_leaver.csv'))
    ax.step(pi['mu_eV'], pi['excluded_at_median_M_a'], where='mid', color='k', lw=1.2, label=r'point estimate: median $(M,a_*)$ (0/1)')
    p, e = d[f'Pex_{key}'].values, d[f'Pex_err_{key}'].values
    ax.plot(d['mu_eV'], p, color=s['color'], lw=2, label=r'full posterior $P_{\rm ex}(\mu)$')
    ax.fill_between(d['mu_eV'], np.clip(p-3*e, 0, 1), np.clip(p+3*e, 0, 1), color=s['color'], alpha=0.3, lw=0)
    ax.axhline(0.95, color='0.55', ls='--', lw=0.8); ax.text(rng[key][1]/1.05, 0.965, '95%', ha='right', fontsize=8, color='0.35')
    ax.axhline(0.68, color='0.55', ls=':', lw=0.8); ax.text(rng[key][1]/1.05, 0.695, '68%', ha='right', fontsize=8, color='0.35')
    pe = S['point_estimate'][key]['windows_point_estimate']
    txt = 'point-estimate windows [eV]:\n' + '\n'.join(f'{sci(a)} – {sci(b)}' for a, b in pe)
    w95 = S['windows_baseline_eV'][key]['95%']
    txt += '\nposterior 95% window [eV]:\n' + ('\n'.join(f'{sci(a)} – {sci(b)}' for a, b in w95) if w95 else 'none ($P_{\\rm ex}<0.95$ everywhere)')
    ax.text(0.02, 0.985, txt, transform=ax.transAxes, va='top', fontsize=7.5)
    ax.set_xscale('log'); ax.set_xlim(*rng[key]); ax.set_ylim(-0.03, 1.65); ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0]); ax.spines['left'].set_bounds(0, 1.0)
    ax.legend(frameon=False, loc='upper right', fontsize=8, bbox_to_anchor=(1.0, 1.0))
    ax.set_xlabel(r'boson mass $\mu$ [eV]'); ax.set_title(s['label'], fontsize=10)
axs[0].set_ylabel('excluded (0/1) or exclusion probability')
fig.tight_layout(); save(fig, 'fig04_point_vs_posterior.png')
