"""Figure 6: validation of the growth rate. (a) Gamma_Leaver/Gamma_Detweiler from the continued-fraction calculation
(outputs/rate_table.npz) against x = alpha/alpha_crit for several spins and l = m = 1, 2, 3; (b) benchmark of the
Leaver implementation against Table II of Witek et al. 2012 (paper_003), from outputs/rate_validation.csv."""
import pandas as pd, matplotlib.ticker
from common import *

T = np.load(os.path.join(OUTPUTS, 'rate_table.npz'))
V = pd.read_csv(os.path.join(OUTPUTS, 'rate_validation.csv'))
ag, xg = T['a_grid'], T['x_grid']
cm = plt.get_cmap('viridis')
fig, axs = plt.subplots(1, 4, figsize=(14, 3.9), gridspec_kw=dict(width_ratios=[1, 1, 1, 0.8], wspace=0.28), sharey=False)
for ax, l in zip(axs[:3], (1, 2, 3)):
    R = T[f'ratio_l{l}'].copy()
    if l == 3: R[:, xg < 0.2] = np.nan      # same mask as sr.make_calibrated_rate
    for i in range(0, len(ag), 1):
        ax.plot(xg, R[i], marker='o', ms=2.5, lw=1.1, color=cm(i/(len(ag)-1)), label=rf'$a_*={ag[i]:.2f}$' if l == 1 and i in (0, 3, 5, 7, 9) else None)
    ax.axhline(1, color='k', lw=0.8, ls='--'); ax.axhline(0.5, color='0.6', lw=0.8, ls=':')
    ax.set_yscale('log'); ax.set_ylim(0.15, 8); ax.set_yticks([0.2, 0.5, 1, 2, 5]); ax.set_yticklabels(['0.2', '0.5', '1', '2', '5']); ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_xlabel(r'$x=\alpha/\alpha_{\rm crit}$,  $\alpha_{\rm crit}=m\,\Omega_H r_g$'); ax.set_title(rf'$l=m={l}$', fontsize=10)
    if l == 1: ax.set_ylabel(r'$\Gamma_{\rm Leaver}/\Gamma_{\rm Detweiler}$'); ax.legend(frameon=False, fontsize=7.5, loc='upper left', ncol=1)
    if l == 3: ax.text(0.03, 0.04, r'$x<0.2$ masked (unconverged roots)', transform=ax.transAxes, fontsize=7.5, color='0.4')
ax = axs[3]
b = V[(V.alpha == 0.42) & (V.a_star == 0.99)].iloc[0]
vals = [b['Gamma_Detweiler_rg'], b['Gamma_Leaver_rg'], 1.504e-7]
names = ['Detweiler\n(eq. 18)', 'Leaver\n(this work)', 'Witek+12\nTable II']
ax.bar(range(3), vals, color=['0.65', '#009E73', '0.3'])
for i, v in enumerate(vals): ax.text(i, v*1.25, f'{v:.3e}', ha='center', fontsize=7.5)
ax.set_yscale('log'); ax.set_ylim(1e-9, 1e-6); ax.set_xticks(range(3)); ax.set_xticklabels(names, fontsize=8)
ax.text(0.5, 0.97, r'Detweiler is outside its validity here' '\n' r'($\alpha/\alpha_{\rm crit}=0.97$, near the boundary)', transform=ax.transAxes, ha='center', va='top', fontsize=7.5, color='0.3')
ax.set_ylabel(r'${\rm Im}\,\omega\,r_g$'); ax.set_title(r'benchmark $\alpha=0.42,\ a_*=0.99$', fontsize=10)
fig.subplots_adjust(left=0.07, right=0.99, bottom=0.2, top=0.9)
save(fig, 'fig06_rate_validation.png')
