"""Main analysis: Bayesian black-hole-superradiance constraints on ultralight bosons."""
import json, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import sr

IMG = '/work/report/images/'; OUT = '/work/outputs/'
plt.rcParams.update({'figure.dpi': 130, 'font.size': 10, 'axes.grid': True, 'grid.alpha': 0.25})
rng = np.random.default_rng(42)
BH = {'M33 X-7': sr.load('M33_X-7'), 'IRAS 09149-6206': sr.load('IRAS_09149-6206')}
MU_RANGE = {'M33 X-7': (-14.0, -10.0), 'IRAS 09149-6206': (-20.0, -16.0)}
COL = {'M33 X-7': '#1f77b4', 'IRAS 09149-6206': '#d95f02', 'combined': 'k'}
T_FID, NE_FID = 4.5e7, 100.0
res = {}

def grid(name, n=1200):
    lo, hi = MU_RANGE[name]; return np.logspace(lo, hi, n)

def intervals(mu, p_allow, thr):
    """log10(mu) intervals where p_allow < thr."""
    ex = p_allow < thr
    out = []; i = 0
    while i < len(ex):
        if ex[i]:
            j = i
            while j + 1 < len(ex) and ex[j+1]: j += 1
            out.append((float(np.log10(mu[i])), float(np.log10(mu[j])))); i = j + 1
        else: i += 1
    return out

# ----------------------------------------------------------------------------- 1. data overview
fig, ax = plt.subplots(2, 2, figsize=(10, 8))
for k, (name, (M, a)) in enumerate(BH.items()):
    x = M if k == 0 else np.log10(M)
    ax[0, k].scatter(x, a, s=2, alpha=0.3, color=COL[name])
    ax[0, k].set_xlabel('$M_{BH}$ [$M_\\odot$]' if k == 0 else '$\\log_{10} M_{BH}/M_\\odot$'); ax[0, k].set_ylabel('$a_*$'); ax[0, k].set_title(f'{name}: {len(M)} posterior samples')
    ax[1, k].hist(x, bins=50, color=COL[name], alpha=0.7, density=True); ax[1, k].set_xlabel(ax[0, k].get_xlabel()); ax[1, k].set_ylabel('posterior density')
    for q in np.percentile(x, [16, 50, 84]): ax[1, k].axvline(q, color='k', ls=':')
plt.tight_layout(); plt.savefig(IMG + 'fig1_data_overview.png'); plt.close()
res['data'] = {}
for name, (M, a) in BH.items():
    res['data'][name] = {'N': len(M), 'M_pct[2.5,16,50,84,97.5]': np.percentile(M, [2.5, 16, 50, 84, 97.5]).tolist(),
                         'a_pct[2.5,16,50,84,97.5]': np.percentile(a, [2.5, 16, 50, 84, 97.5]).tolist(), 'corr(M,a)': float(np.corrcoef(M, a)[0, 1])}

# ----------------------------------------------------------------------------- 2. rate validation
T = np.load(OUT + 'leaver_table.npz')
fig, ax = plt.subplots(1, 3, figsize=(15, 4.2))
als = np.linspace(0.05, 0.6, 200)
for a0, c in [(0.99, 'C0'), (0.9, 'C1'), (0.7, 'C2')]:
    ax[0].plot(als, np.maximum(sr.gamma(als, a0, 1), 1e-20), c + '--', label=f'analytic, $a_*$={a0}')
    ax[0].plot(als, np.maximum(sr.exact_gamma(als, np.full_like(als, a0), 1), 1e-20), c + '-', label=f'calibrated, $a_*$={a0}')
    ia = np.argmin(abs(T['l1_a'] - a0)); w = T['l1_w'][ia]
    ax[0].plot(T['l1_al'], np.where(w[:, 1] > 0, w[:, 1], np.nan), c + '.', ms=3)
ax[0].set_yscale('log'); ax[0].set_ylim(1e-13, 1e-6); ax[0].set_xlabel('$\\alpha=GM\\mu/\\hbar c$'); ax[0].set_ylabel('$\\Gamma_{211}\\,GM/c^3$'); ax[0].legend(fontsize=7); ax[0].set_title('l=m=1: analytic vs. Leaver (dots)')
ax[1].set_title('Superradiance threshold $a_{crit}(\\alpha)$')
for l in (1, 2, 3, 4):
    x = np.linspace(0.02, l * 0.5 + 0.1, 300)
    ax[1].plot(x, sr.a_crit(x, l), '--', color=f'C{l-1}'); ax[1].plot(x, sr.acrit_fast(x, l), '-', color=f'C{l-1}', label=f'l=m={l}')
ax[1].set_xlabel('$\\alpha$'); ax[1].set_ylabel('$a_{crit}$'); ax[1].legend(); ax[1].set_ylim(0, 1.02)
for l in (1, 2, 3, 4, 5, 6):
    x = np.linspace(0.1, 0.5 * l, 300); a0 = 0.95
    g = sr.exact_gamma(x, np.full_like(x, a0), l); ax[2].plot(x, np.where(g > 0, g, np.nan), label=f'l=m={l}')
ax[2].set_yscale('log'); ax[2].set_ylim(1e-14, 1e-6); ax[2].set_xlabel('$\\alpha$'); ax[2].set_ylabel('$\\Gamma\\,GM/c^3$ ($a_*=0.95$)'); ax[2].legend(fontsize=7); ax[2].set_title('Calibrated rates, l=m=1..6')
plt.tight_layout(); plt.savefig(IMG + 'fig2_rates_validation.png'); plt.close()
g_pk = sr.exact_gamma(np.linspace(0.2, 0.6, 400), np.full(400, 0.99), 1)
res['validation'] = {'peak_Gamma_211_a0.99_exact': float(g_pk.max()), 'alpha_at_peak': float(np.linspace(0.2, 0.6, 400)[g_pk.argmax()]),
                     'peak_Gamma_211_a0.99_analytic': float(sr.gamma(np.linspace(0.2, 0.6, 400), 0.99, 1).max())}

# ----------------------------------------------------------------------------- 3. exclusion probability
MU = {n: grid(n) for n in BH}
pal = {n: sr.allowed_fraction(*BH[n][::1], MU[n], T_FID, Ne=NE_FID) if False else sr.allowed_fraction(BH[n][0], BH[n][1], MU[n], T_FID, Ne=NE_FID) for n in BH}
res['fiducial'] = {'t_yr': T_FID, 'N_efold': NE_FID}
for n in BH:
    res['fiducial'][n] = {'excl95_log10mu_eV': intervals(MU[n], pal[n], 0.05), 'excl68_log10mu_eV': intervals(MU[n], pal[n], 0.32),
                          'max_exclusion_prob': float(1 - pal[n].min()), 'mu_at_max_exclusion_eV': float(MU[n][pal[n].argmin()])}
    print(n, res['fiducial'][n])

# point-estimate comparison
pe = {}
for n, (M, a) in BH.items():
    Mm, am = np.median(M), np.median(a); a16 = np.percentile(a, 16); M84 = np.percentile(M, 84); M16 = np.percentile(M, 16)
    ex_med = ~sr.allowed(np.array([Mm]), np.array([am]), MU[n], T_FID, Ne=NE_FID)[:, 0]
    ex_lo = ~sr.allowed(np.array([Mm]), np.array([a16]), MU[n], T_FID, Ne=NE_FID)[:, 0]
    pe[n] = (ex_med, ex_lo)
    res['fiducial'][n]['point_estimate_excl_log10mu'] = intervals(MU[n], 1.0 - ex_med, 0.5)
    res['fiducial'][n]['point_estimate_(a-1sigma)_excl_log10mu'] = intervals(MU[n], 1.0 - ex_lo, 0.5)

fig, ax = plt.subplots(1, 2, figsize=(13, 4.5))
for k, n in enumerate(BH):
    mu = MU[n]
    ax[k].fill_between(mu, 0, 1, where=pe[n][0], color='0.85', step='mid', label='point estimate (median $M,a_*$) excluded')
    ax[k].plot(mu, 1 - pal[n], color=COL[n], lw=2, label='$P_{ex}(\\mu)$, full posterior')
    ax[k].axhline(0.95, color='r', ls='--', lw=1, label='95%'); ax[k].axhline(0.68, color='r', ls=':', lw=1, label='68%')
    ax[k].set_xscale('log'); ax[k].set_xlabel('boson mass $\\mu$ [eV]'); ax[k].set_ylabel('exclusion probability'); ax[k].set_title(n); ax[k].legend(fontsize=7, loc='center right')
plt.tight_layout(); plt.savefig(IMG + 'fig3_exclusion_probability.png'); plt.close()

# bootstrap on the posterior samples
BOOT = 30
bo = {n: [] for n in BH}
for n, (M, a) in BH.items():
    for b in range(BOOT):
        ii = rng.integers(0, len(M), len(M))
        p = sr.allowed_fraction(M[ii], a[ii], MU[n][::6], T_FID, Ne=NE_FID); bo[n].append(p)
    bo[n] = np.array(bo[n])
    ed = []
    for p in bo[n]:
        iv = intervals(MU[n][::6], p, 0.05)
        ed.append((iv[0][0], iv[-1][1]) if iv else (np.nan, np.nan))
    ed = np.array(ed)
    res['fiducial'][n]['bootstrap_95_edges_log10mu_mean_std'] = {'lower': [float(np.nanmean(ed[:, 0])), float(np.nanstd(ed[:, 0]))], 'upper': [float(np.nanmean(ed[:, 1])), float(np.nanstd(ed[:, 1]))],
                                                              'frac_with_95_exclusion': float(np.mean(~np.isnan(ed[:, 0])))}
np.savez(OUT + 'fiducial_pallow.npz', **{('mu_' + n.replace(' ', '_')): MU[n] for n in BH}, **{('pallow_' + n.replace(' ', '_')): pal[n] for n in BH})

# ----------------------------------------------------------------------------- 4. Regge-plane illustration
fig, ax = plt.subplots(1, 2, figsize=(13, 5))
cfg = {'M33 X-7': (np.linspace(8, 25, 120), [1e-12, 3e-12, 1e-11], False, 'M33 X-7', 1e-11),
       'IRAS 09149-6206': (np.logspace(7, 9.3, 120), [1e-18, 3e-18, 1e-17], True, 'IRAS', 1e-17)}
for k, n in enumerate(BH):
    Mg, mus, logx, _, _ = cfg[n]; ag = np.linspace(0.3, 0.995, 140)
    M, a = BH[n]
    xs = np.log10(M) if logx else M
    xg = np.log10(Mg) if logx else Mg
    H, xe, ye = np.histogram2d(xs, a, bins=40, range=[[xg[0], xg[-1]], [0.3, 1]])
    ax[k].contourf(0.5*(xe[1:]+xe[:-1]), 0.5*(ye[1:]+ye[:-1]), H.T, levels=6, cmap='Greys', alpha=0.8)
    for mu0, c in zip(mus, ['C0', 'C2', 'C3']):
        MM, AA = np.meshgrid(Mg, ag)
        ok = sr.allowed(MM.ravel(), AA.ravel(), np.array([mu0]), T_FID, Ne=NE_FID)[0].reshape(MM.shape)
        ax[k].contourf(xg, ag, (~ok).astype(float), levels=[0.5, 1.5], colors=[c], alpha=0.25)
        ax[k].contour(xg, ag, (~ok).astype(float), levels=[0.5], colors=c, linewidths=1.5)
        ax[k].plot([], [], color=c, label=f'$\\mu$={mu0:.0e} eV (shaded: excluded)')
    ax[k].set_xlabel('$\\log_{10}M/M_\\odot$' if logx else '$M$ [$M_\\odot$]'); ax[k].set_ylabel('$a_*$'); ax[k].set_title(n + ': Regge plane'); ax[k].legend(fontsize=8, loc='lower left'); ax[k].set_ylim(0.3, 1)
plt.tight_layout(); plt.savefig(IMG + 'fig4_regge_plane.png'); plt.close()

# ----------------------------------------------------------------------------- 5. posterior samples coloured by exclusion
fig, ax = plt.subplots(2, 4, figsize=(18, 7))
show = {'M33 X-7': [1.5e-13, 5e-13, 1.5e-12, 5e-12], 'IRAS 09149-6206': [3e-19, 1e-18, 3e-18, 1e-17]}
for r, n in enumerate(BH):
    M, a = BH[n]
    for c, mu0 in enumerate(show[n]):
        ok = sr.allowed(M, a, np.array([mu0]), T_FID, Ne=NE_FID)[0]
        x = M if r == 0 else np.log10(M)
        ax[r, c].scatter(x[ok], a[ok], s=2, color='C0', label='allowed'); ax[r, c].scatter(x[~ok], a[~ok], s=2, color='C3', label='excluded')
        ax[r, c].set_title(f'{n}, $\\mu$={mu0:.1e} eV\nP(allowed)={ok.mean():.3f}', fontsize=9); ax[r, c].set_xlabel('$M$' if r == 0 else '$\\log_{10}M$'); ax[r, c].set_ylabel('$a_*$')
    ax[r, 0].legend(markerscale=4, fontsize=7)
plt.tight_layout(); plt.savefig(IMG + 'fig5_sample_classification.png'); plt.close()

# ----------------------------------------------------------------------------- 6. sensitivity
sens = {}
fig, ax = plt.subplots(2, 3, figsize=(16, 8))
for r, n in enumerate(BH):
    mu = MU[n]; M, a = BH[n]
    for c, (title, runs) in enumerate([
        ('BH age $t_{BH}$', [(f'{t:.1e} yr', dict(t_yr=t, Ne=NE_FID)) for t in (4.6e6, 4.5e7, 4.5e8, 1.4e10)]),
        ('e-folds $N_e$', [(f'N_e={ne}', dict(t_yr=T_FID, Ne=float(ne))) for ne in (30, 100, 180, 300)]),
        ('rate model', [('calibrated (Leaver)', dict(t_yr=T_FID, Ne=NE_FID, model='exact')), ('analytic small-$\\alpha$', dict(t_yr=T_FID, Ne=NE_FID, model='analytic'))])]):
        for lab, kw in runs:
            p = sr.allowed_fraction(M, a, mu[::2], **kw); ax[r, c].plot(mu[::2], 1 - p, label=lab)
            iv = intervals(mu[::2], p, 0.05); sens[f'{n}|{title}|{lab}'] = {'excl95': iv, 'max_Pex': float(1 - p.min())}
        ax[r, c].set_xscale('log'); ax[r, c].axhline(0.95, color='r', ls='--', lw=0.8); ax[r, c].set_title(f'{n}: {title}', fontsize=9); ax[r, c].legend(fontsize=7); ax[r, c].set_xlabel('$\\mu$ [eV]'); ax[r, c].set_ylabel('$P_{ex}$')
plt.tight_layout(); plt.savefig(IMG + 'fig6_sensitivity.png'); plt.close()
res['sensitivity'] = sens

# ----------------------------------------------------------------------------- 7. self-interaction: (mu, f_a) plane
FA = np.logspace(13, 19, 49)
Z = {}
for n in BH:
    M, a = BH[n]
    lo, hi = MU_RANGE[n]; mu = np.logspace(lo, hi, 320)
    P = np.empty((len(FA), len(mu)))
    for i in range(0, len(mu), 40):
        pre = sr.prepare(M, a, mu[i:i+40])
        for j, fa in enumerate(FA):
            P[j, i:i+40] = sr.allowed_from(pre, M, T_FID, fa, NE_FID).mean(1)
    Z[n] = (mu, P)
    np.savez(OUT + f'pallow_mu_fa_{n.replace(" ", "_")}.npz', mu=mu, fa=FA, pallow=P)
fig, ax = plt.subplots(1, 3, figsize=(18, 5.2))
qcd_f = np.logspace(13, 19, 50); qcd_mu = 5.7e-6 * (1e12 / qcd_f)
for k, n in enumerate(list(BH) + ['combined']):
    if n == 'combined':
        # BH data sets constrain different mass windows: combine the likelihoods on a common grid
        mu = np.logspace(-20, -10, 800)
        P = np.ones((len(FA), len(mu)))
        for m_ in BH:
            mm, pp = Z[m_]
            for j in range(len(FA)): P[j] *= np.interp(np.log10(mu), np.log10(mm), pp[j], left=1.0, right=1.0)
    else:
        mu, P = Z[n]
    cs = ax[k].contourf(mu, FA, 1 - P, levels=[0, 0.32, 0.68, 0.95, 0.999, 1.0001], colors=['white', '#c6dbef', '#6baed6', '#2171b5', '#08306b'], alpha=0.9)
    ax[k].contour(mu, FA, 1 - P, levels=[0.95], colors='r', linewidths=1.5)
    ax[k].plot(qcd_mu, qcd_f, 'k--', lw=1, label='QCD axion $\\mu f_a=m_\\pi f_\\pi$')
    ax[k].set_xscale('log'); ax[k].set_yscale('log'); ax[k].set_xlabel('$\\mu$ [eV]'); ax[k].set_ylabel('$f_a$ [GeV]'); ax[k].set_title(n + ' ($P_{ex}$ shading: 0.32/0.68/0.95/0.999)')
    ax[k].set_xlim(mu[0] if n != 'combined' else 1e-19, mu[-1] if n != 'combined' else 1e-11); ax[k].set_ylim(1e13, 1e19); ax[k].legend(fontsize=8, loc='lower left')
    if n == 'combined': Zc = (mu, P)
    sec = ax[k].secondary_yaxis('right', functions=(lambda f: 2.0 * np.log10(np.maximum(1e-30, 1.0 / f)) , lambda y: y)) if False else None
plt.tight_layout(); plt.savefig(IMG + 'fig7_mu_fa_plane.png'); plt.close()
# quantitative: for several mu, largest f_a... i.e. weakest-coupling not required: report minimal f_a (strongest self-interaction) still excluded at 95%
si = {}
for n in list(BH) + ['combined']:
    mu, P = Z[n] if n != 'combined' else Zc
    rows = []
    for mu0 in {'M33 X-7': [3e-13, 1e-12, 3e-12, 6e-12], 'IRAS 09149-6206': [3e-19, 1e-18, 3e-18], 'combined': []}[n]:
        j = np.argmin(abs(np.log10(mu) - np.log10(mu0))); ex = (1 - P[:, j]) >= 0.95
        rows.append({'mu_eV': mu0, 'min_fa_GeV_excl95': float(FA[ex].min()) if ex.any() else None, 'Pex_at_fa=1e19': float(1 - P[-1, j]), 'Pex_at_fa=1e17': float(1 - P[np.argmin(abs(FA - 1e17)), j])})
    # 95% region area bounding box at various f_a
    for fa0 in (1e15, 1e16, 1e17, 1e18, 1e19):
        j = np.argmin(abs(np.log10(FA) - np.log10(fa0))); rows.append({'fa_GeV': fa0, 'excl95_log10mu': intervals(mu, P[j], 0.05)})
    si[n] = rows
res['self_interaction'] = si
# lambda mapping
res['notes'] = {'lambda': 'quartic coupling lambda = mu^2/f_a^2 (axion potential V=mu^2 f_a^2[1-cos(phi/f_a)] -> -lambda phi^4/4!)'}
json.dump(res, open(OUT + 'results.json', 'w'), indent=1, default=float)

# ----------------------------------------------------------------------------- 8. combined Bayesian posterior over mu
fig, ax = plt.subplots(figsize=(9, 4.5))
mu = np.logspace(-20, -10, 3000)
L = np.ones_like(mu)
for n in BH:
    L *= np.interp(np.log10(mu), np.log10(MU[n]), pal[n], left=1.0, right=1.0)
prior = np.ones_like(mu)  # log-uniform prior on mu
post = prior * L; post /= np.trapezoid(post, np.log10(mu))
ax.semilogx(mu, post, 'k', label='posterior (log-uniform prior on $\\mu$)'); ax.semilogx(mu, prior / np.trapezoid(prior, np.log10(mu)), 'C7--', label='prior')
for n in BH: ax.axvspan(*MU[n][[0, -1]], color=COL[n], alpha=0.07, label=f'{n} grid')
ax.set_xlabel('$\\mu$ [eV]'); ax.set_ylabel('$p(\\log_{10}\\mu\\,|\\,D)$'); ax.legend(fontsize=8); plt.tight_layout(); plt.savefig(IMG + 'fig8_combined_posterior.png'); plt.close()
res['combined'] = {'excl95_log10mu': intervals(mu, L, 0.05), 'excl68_log10mu': intervals(mu, L, 0.32), 'prior_prob_excluded_95_in_[1e-20,1e-10]': float(np.trapezoid((L < 0.05).astype(float), np.log10(mu)) / 10.0),
                   'posterior_mass_in_95_excluded_region': float(np.trapezoid(post * (L < 0.05), np.log10(mu)))}
json.dump(res, open(OUT + 'results.json', 'w'), indent=1, default=float)
print(json.dumps(res['fiducial'], indent=1, default=float)); print(res['combined']); print(json.dumps(si, indent=1, default=float))
