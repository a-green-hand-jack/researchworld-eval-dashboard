"""Figure 3: exclusion probability P_ex(mu) per black hole and combined (Leaver-calibrated rate), with the
posterior density of mu and the literature windows of Stott (2018). Reads outputs/pex_vs_mu*.csv, summary_leaver.json."""
from common import *

import pandas as pd
d = pd.read_csv(os.path.join(OUTPUTS, 'pex_vs_mu_leaver.csv'))
dd = pd.read_csv(os.path.join(OUTPUTS, 'pex_vs_mu.csv'))
lit = json.load(open(os.path.join(OUTPUTS, 'literature_windows.json')))['Stott2018_excluded_mu_eV']
S = summary()
mu = d['mu_eV'].values
fig, (ax, axp, axl) = plt.subplots(3, 1, figsize=(8.4, 7.4), sharex=True, gridspec_kw=dict(height_ratios=[4, 1.6, 0.9], hspace=0.1))
for lv, ls in ((0.5, (0, (1, 3))), (0.68, ':'), (0.95, '--')):
    ax.axhline(lv, color='0.55', lw=0.8, ls=ls)
    ax.text(mu[-1]/1.05, lv+0.012, f'{100*lv:g}%', color='0.35', fontsize=8, ha='right')
for key, s in SOURCES.items():
    p, e = d[f'Pex_{key}'], d[f'Pex_err_{key}']
    ax.plot(mu, p, color=s['color'], lw=1.8, label=f"{s['label']} (Leaver-calibrated rate)")
    ax.fill_between(mu, np.clip(p-3*e, 0, 1), np.clip(p+3*e, 0, 1), color=s['color'], alpha=0.3, lw=0)
    ax.plot(mu, dd[f'Pex_{key}'], color=s['color'], lw=0.9, ls='--', label=f"{s['label']} (Detweiler rate)")
ax.plot(mu, d['Pex_combined'], color=COMB, lw=4, alpha=0.2, zorder=0, label=r'combined, $1-\prod_i(1-P_{\rm ex,i})$')
for w in S['windows_baseline_eV']['M33_X-7']['95%']:
    ax.axvspan(*w, color=SOURCES['M33_X-7']['color'], alpha=0.08, lw=0)
    ax.text(np.sqrt(w[0]*w[1]), 0.5, rf'95% window: {sci(w[0])} – {sci(w[1])} eV', rotation=90, ha='center', va='center', fontsize=8,
            color=SOURCES['M33_X-7']['color'])
iras = d['Pex_IRAS_09149-6206'].values; k = iras.argmax()
ax.text(mu[k]*3, 0.62, rf'IRAS 09149-6206: max $P_{{\rm ex}}={iras[k]:.2f}$' '\n' rf'at $\mu=$ {sci(mu[k])} eV, never reaches 95%', fontsize=8, color=SOURCES['IRAS_09149-6206']['color'])
ax.set_ylim(-0.02, 1.04); ax.set_ylabel(r'exclusion probability $P_{\rm ex}(\mu)$')
ax.legend(frameon=False, loc='upper center', fontsize=8, bbox_to_anchor=(0.36, 1.0))
axp.fill_between(mu, d['posterior_density_per_dex'], color=COMB, alpha=0.5, lw=0)
axp.set_ylabel(r'$p(\mu\,|\,{\rm data})$' '\n[per dex]'); axp.set_ylim(0, None)
axl.set_ylim(0, 2); axl.set_yticks([])
axl.spines['left'].set_visible(False)
axl.barh(0.5, lit['SMBHs'][1]-lit['SMBHs'][0], left=lit['SMBHs'][0], height=0.8, color='0.6')
axl.barh(1.5, lit['stellar_BHs'][1]-lit['stellar_BHs'][0], left=lit['stellar_BHs'][0], height=0.8, color='0.6')
axl.text(lit['SMBHs'][1]*2, 0.5, 'Stott (2018), SMBHs', va='center', fontsize=8)
axl.text(lit['stellar_BHs'][0]/2, 1.5, 'Stott (2018), stellar BHs', va='center', ha='right', fontsize=8)
axl.set_xscale('log'); axl.set_xlim(mu[0], mu[-1]); axl.set_xlabel(r'boson mass $\mu$ [eV]')
fig.subplots_adjust(left=0.12, right=0.97, top=0.98, bottom=0.08)
save(fig, 'fig03_pex_vs_mu.png')
