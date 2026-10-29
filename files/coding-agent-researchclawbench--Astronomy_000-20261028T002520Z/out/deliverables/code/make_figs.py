import numpy as np, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, sr
plt.rcParams.update({'font.size': 11, 'figure.dpi': 130, 'axes.grid': True, 'grid.alpha': .25})
IM = '../report/images/'
names = ['M33_X-7', 'IRAS_09149-6206']; tt = {'M33_X-7': 3e6, 'IRAS_09149-6206': 4.5e7}
D = {n: np.loadtxt(f'../data/{n}_samples.dat') for n in names}
PAL = ['#d95f02','#1b9e77','#7570b3','#e7298a']
C = ['#1f77b4', '#d95f02', '#1b9e77', '#7570b3', '#666666']

# Fig1: data overview
fig, ax = plt.subplots(1, 2, figsize=(11, 4.3))
for k, n in enumerate(names):
    M, a = D[n].T
    x = M if n == 'M33_X-7' else np.log10(M)
    ax[k].scatter(x, a, s=3, alpha=.3, color=C[0])
    ax[k].set_xlabel(r'$M\,[M_\odot]$' if k == 0 else r'$\log_{10}(M/M_\odot)$'); ax[k].set_ylabel(r'$a_*$')
    ax[k].set_title(f'{n}  (N={len(M)})'); 
    ax[k].text(.03, .05, f'M: {np.percentile(M,16):.3g}–{np.percentile(M,84):.3g}\na*: {np.percentile(a,16):.3f}–{np.percentile(a,84):.3f} (68%)', transform=ax[k].transAxes, bbox=dict(fc='w', alpha=.8))
plt.tight_layout(); plt.savefig(IM + 'fig1_data.png'); plt.close()

# Fig2: exclusion region in (M,a) for chosen mu, with posterior
fig, ax = plt.subplots(1, 2, figsize=(11, 4.5))
for k, (n, mus) in enumerate([('M33_X-7', [1e-13*2, 5e-13, 2e-12, 5e-12]), ('IRAS_09149-6206', [1.5e-19, 3.2e-19, 6e-19])]):
    M, a = D[n].T
    Mg = np.linspace(M.min()*.7, np.percentile(M, 99.5), 220) if k == 0 else np.logspace(np.log10(M.min()*.7), np.log10(np.percentile(M, 99.9)), 220)
    ag = np.linspace(0.3, 0.999, 180); MM, AA = np.meshgrid(Mg, ag)
    ax[k].scatter(M, a, s=2, alpha=.25, color='k', zorder=3)
    for j, mu in enumerate(mus):
        ex = sr.excluded(MM.ravel(), AA.ravel(), mu, t_yr=tt[n]).reshape(MM.shape)
        ax[k].contourf(MM, AA, ex.astype(float), levels=[.5, 1.5], colors=[PAL[j]], alpha=.35)
        ax[k].contour(MM, AA, ex.astype(float), levels=[.5], colors=[PAL[j]], linewidths=1.5)
        ax[k].plot([], [], color=PAL[j], label=rf'$\mu={mu:.2g}$ eV  ($L$={1-sr.excluded(M,a,mu,t_yr=tt[n]).mean():.2f})')
    if k == 1: ax[k].set_xscale('log')
    ax[k].set_xlabel(r'$M\,[M_\odot]$'); ax[k].set_ylabel(r'$a_*$'); ax[k].set_title(n + f'  (t={tt[n]:.2g} yr)'); ax[k].legend(fontsize=8, loc='lower left')
plt.tight_layout(); plt.savefig(IM + 'fig2_regions.png'); plt.close()

# Fig3: L(mu)
fig, ax = plt.subplots(1, 2, figsize=(11, 4.3))
for k, n in enumerate(names):
    z = np.load(f'../outputs/L1d_{n}.npz'); mu = z['mu']
    ax[k].semilogx(mu, z['L_base'], 'k', lw=2, label='baseline')
    ax[k].semilogx(mu, z['L_marg'], color=C[1], label=r'marginalised $\sigma_t$=0.5 dex')
    ax[k].semilogx(mu, z['L_t/10'], color=C[2], ls='--', label='t/10'); ax[k].semilogx(mu, z['L_t*10'], color=C[2], ls=':', label='t×10')
    ax[k].semilogx(mu, z['L_211only'], color=C[3], ls='-.', label='(211) only')
    ax[k].semilogx(mu, z['L_t_hubble'], color=C[4], ls='--', label=r't=$10^9$ yr')
    ax[k].axhline(.05, color='r', lw=.8); ax[k].axhline(.32, color='r', lw=.8, ls='--')
    ax[k].set_xlabel(r'$\mu$ [eV]'); ax[k].set_ylabel(r'$\mathcal{L}(\mu)=P(\mathrm{data}\mid\mu)/P(\mathrm{data}\mid\mathrm{no\ boson})$')
    ax[k].set_title(n); ax[k].legend(fontsize=8); ax[k].set_ylim(-.02, 1.05)
plt.tight_layout(); plt.savefig(IM + 'fig3_likelihood_1d.png'); plt.close()

# Fig4: 2D (mu, f)
def f2d(ax, z, key, title):
    mu = z['mu']; lf = z['logf']; L = z[key]
    im = ax.pcolormesh(mu, lf - 9, L, shading='auto', cmap='viridis', vmin=0, vmax=1)
    ax.contour(mu, lf - 9, L, levels=[.05], colors='r', linewidths=2)
    ax.contour(mu, lf - 9, L, levels=[.32], colors='w', linewidths=1.5, linestyles='--')
    ax.set_xscale('log'); ax.set_xlabel(r'$\mu$ [eV]'); ax.set_ylabel(r'$\log_{10}(f/\mathrm{GeV})$'); ax.set_title(title)
    return im
fig, ax = plt.subplots(1, 2, figsize=(11.5, 4.5))
z = np.load('../outputs/L2d_M33_X-7.npz'); im = f2d(ax[0], z, 'L_base', 'M33 X-7 (red: L=0.05, white dashed: L=0.32)')
z2 = np.load('../outputs/L2d_IRAS_09149-6206.npz'); f2d(ax[1], z2, 'L_base', 'IRAS 09149-6206, t=4.5e7 yr')
plt.colorbar(im, ax=ax, label=r'$\mathcal{L}(\mu,f)$'); plt.savefig(IM + 'fig4_mu_f.png', bbox_inches='tight'); plt.close()

# IRAS with t=1e9 yr 2D
d = D['IRAS_09149-6206']; rng = np.random.default_rng(5); d = d[rng.choice(len(d), 3000, replace=False)]
mu = z2['mu']; lf = z2['logf'][::2]
Lh = np.array([sr.likelihood(d[:, 0], d[:, 1], mu, f=10**x, t_yr=1e9) for x in lf])
np.savez('../outputs/L2d_IRAS_1Gyr.npz', mu=mu, logf=lf, L=Lh)

# Fig5: M33 sensitivity to cbn, and boundary f_crit(mu)
fig, ax = plt.subplots(1, 2, figsize=(11, 4.3))
zz = np.load('../outputs/L2d_M33_X-7.npz'); mu = zz['mu']; lf = zz['logf']
for key, c, lab in [('L_base', 'k', r'$c_{bn}=1$'), ('L_cbn0.1', C[1], r'$c_{bn}=0.1$'), ('L_cbn10', C[2], r'$c_{bn}=10$')]:
    ax[0].contour(mu, lf - 9, zz[key], levels=[.05], colors=[c]); ax[0].plot([], [], color=c, label=lab)
ax[0].set_xscale('log'); ax[0].set_xlabel(r'$\mu$ [eV]'); ax[0].set_ylabel(r'$\log_{10}(f/\mathrm{GeV})$'); ax[0].legend(); ax[0].set_title('M33 X-7: 95% exclusion boundary')
# marginal L(mu) over log-uniform f in [1e5,1e19] GeV
Lm = zz['L_base'].mean(0); ax[1].semilogx(mu, Lm, 'k', label='marginalised over $\\log f$ (flat)')
ax[1].semilogx(mu, zz['L_base'][-1], color=C[1], ls='--', label=r'$f\to$ large ($10^{19}$ GeV)')
ax[1].axhline(.05, color='r', lw=.8); ax[1].set_xlabel(r'$\mu$ [eV]'); ax[1].set_ylabel(r'$\mathcal{L}$'); ax[1].legend(); ax[1].set_title('M33 X-7: marginal over self-interaction')
plt.tight_layout(); plt.savefig(IM + 'fig5_selfint.png'); plt.close()

# Fig6: IRAS 1 Gyr
fig, ax = plt.subplots(figsize=(5.8, 4.5)); zi = np.load('../outputs/L2d_IRAS_1Gyr.npz')
im = ax.pcolormesh(zi['mu'], zi['logf'] - 9, zi['L'], shading='auto', vmin=0, vmax=1)
ax.contour(zi['mu'], zi['logf'] - 9, zi['L'], levels=[.05], colors='r'); ax.contour(zi['mu'], zi['logf'] - 9, zi['L'], levels=[.32], colors='w', linestyles='--')
ax.set_xscale('log'); ax.set_xlabel(r'$\mu$ [eV]'); ax.set_ylabel(r'$\log_{10}(f/\mathrm{GeV})$'); ax.set_title('IRAS 09149-6206, $t=10^9$ yr'); plt.colorbar(im, label='L')
plt.tight_layout(); plt.savefig(IM + 'fig6_iras_1gyr.png'); plt.close()

# Fig7: calibration + rates
r = np.load('../outputs/mock_calibration.npy')
fig, ax = plt.subplots(1, 3, figsize=(15, 4.2))
ax[0].hist(r[:, 1], bins=20, range=(0, 1), color=C[0]); ax[0].axvline(.05, color='r'); ax[0].set_xlabel(r'$\mathcal{L}(\mu_0)$ at true boson mass'); ax[0].set_ylabel('mocks')
ax[0].set_title(f'Calibration: {100*(r[:,1]<.05).mean():.1f}% false 95% exclusions')
ax[1].hist(r[:, 2], bins=20, range=(0, 1), color=C[1]); ax[1].axvline(.05, color='r'); ax[1].set_xlabel(r'$\mathcal{L}(0.5\mu_0)$'); ax[1].set_title(f'Wrong mass: {100*(r[:,2]<.05).mean():.0f}% excluded')
al = np.logspace(-2, 0, 200)
for (n, l, m) in sr.LEVELS:
    ax[2].loglog(al, sr.gamma_tM(0.9, al, n, l, m).clip(1e-30), label=f'({n}{l}{m})')
ax[2].loglog(al, (0.9 - 2 * (1 + np.sqrt(1 - .81)) * al).clip(1e-30) * al**9 / 24, 'k:', label='Detweiler (211)')
ax[2].set_ylim(1e-20, 1e-3); ax[2].set_xlabel(r'$\alpha$'); ax[2].set_ylabel(r'$\Gamma\,GM/c^3$  ($a_*=0.9$)'); ax[2].legend(fontsize=7); ax[2].set_title('Growth rates')
plt.tight_layout(); plt.savefig(IM + 'fig7_validation.png'); plt.close()

# numbers
for n in names:
    z = np.load(f'../outputs/L1d_{n}.npz'); mu = z['mu']
    for k in z.files:
        if k == 'mu': continue
        print(n, k, [(f'{a:.3g}', f'{b:.3g}') for a, b in sr.limits(mu, z[k], .05)], 'minL=%.3f' % z[k].min())
a_, b_ = np.load('../outputs/L2d_M33_X-7.npz')['mu'], None
for key in ['L_base', 'L_cbn0.1', 'L_cbn10']:
    L = zz[key]
    for fgev in [1e8, 1e10, 1e12, 1e14, 1e16]:
        i = np.argmin(abs(lf - 9 - np.log10(fgev)))
        print(key, 'f=%.0e GeV' % fgev, [(f'{a:.3g}', f'{b:.3g}') for a, b in sr.limits(mu, L[i], .05)])
# minimum f excluded at any mu
for key in ['L_base', 'L_cbn0.1', 'L_cbn10']:
    ex = (zz[key] < .05).any(1); print(key, 'min log10 f/GeV excluded', (lf - 9)[ex].min())
    # f_crit at mu giving max reach
print('IRAS 1Gyr min L', zi['L'].min(), 'excluded f min', (zi['logf'] - 9)[(zi['L'] < .05).any(1)].min() if (zi['L'] < .05).any() else None)
print('IRAS 4.5e7 min L 2D', z2['L_base'].min(), ' 68% region any:', (z2['L_base'] < .32).sum())
