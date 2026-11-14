"""Builds all figures/tables of the paper from results/*.csv.gz (run summarize.py first). Outputs to /work/figs and /work/paper/tables."""
import sys, os, numpy as np, pandas as pd, matplotlib, matplotlib.ticker
matplotlib.use('Agg'); import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dgps import SynthQuad, SynthLogit, asym_vars
R = '/work/results/'; F = '/work/figs/'; T = '/work/paper/tables/'; os.makedirs(F, exist_ok=True); os.makedirs(T, exist_ok=True)
plt.rcParams.update({'font.size': 8, 'axes.spines.top': False, 'axes.spines.right': False, 'axes.grid': True, 'grid.alpha': .25, 'grid.linewidth': .5,
                     'figure.dpi': 150, 'savefig.bbox': 'tight', 'legend.frameon': False, 'legend.fontsize': 7})
COL = {'classical': '#7f7e78', 'ppi': '#eb6834', 'ppipp': '#2a78d6', 'ppipp_u': '#2a78d6', 'lin': '#e87ba4', 'iso': '#6250d6', 'spl': '#1baf7a', 'bin10': '#eda100', 'auto': '#1baf7a', 'theory': '#0b0b0b'}
MK = {'classical': 's', 'ppi': 'v', 'ppipp': 'o', 'ppipp_u': 'o', 'lin': 'x', 'iso': '^', 'spl': 'D', 'bin10': 'P', 'auto': 'o'}
NAME = {'classical': 'classical', 'ppi': 'PPI ($\\lambda{=}1$)', 'ppipp': 'PPI++ (ppi_py, clipped)', 'ppipp_u': 'PPI++ (unclipped $\\lambda$)', 'lin': 'cross-fit linear', 'iso': 'cross-fit isotonic',
        'spl': 'cross-fit spline', 'bin10': 'cross-fit 10 bins', 'auto': 'cross-fit auto'}
def save(fig, name):
    fig.savefig(F + name + '.pdf'); os.makedirs('/tmp/figprev', exist_ok=True); fig.savefig('/tmp/figprev/' + name + '.png', dpi=110); plt.close(fig)

def load(exp): return pd.read_csv(f'{R}summary_{exp}.csv')

def fig_theory():   # E3a: width ratio vs nonlinear share, theory vs empirical
    s = load('E3a'); s['c'] = s.dgp.str.extract(r'c=([0-9.]+)')[0].astype(float)
    fig, axs = plt.subplots(1, 3, figsize=(7.2, 2.3), sharey=True)
    cs = np.linspace(0, 2.2, 100)
    for ax, N in zip(axs, [500, 5000, 50000]):
        th = []
        for c in cs:
            a = asym_vars(SynthQuad(1.0, c, 1.0).moments(), 500, N); th.append(np.sqrt(a['eff'] / a['ppipp']))
        ax.plot(cs ** 2 / (1 + cs ** 2), th, color=COL['theory'], ls='--', lw=1, label='efficiency bound (theory)')
        for m, off in [('lin', -.012), ('iso', 0), ('auto', .012)]:
            d = s[(s.N == N) & (s.method == m)].sort_values('c'); x = d.c ** 2 / (1 + d.c ** 2) + off
            ax.errorbar(x, d.ratio_u, yerr=1.96 * d.ratio_u_se, color=COL[m], marker=MK[m], ms=3.5, lw=0, elinewidth=.8, capsize=1.5, label=NAME[m])
        ax.axhline(1, color=COL['ppipp'], lw=.8); ax.set_title(f'$n{{=}}500$, $N{{=}}{N}$'); ax.set_xlabel('nonlinear share $s$')
    axs[0].set_ylabel('width / width of PPI++'); axs[0].legend(loc='lower left')
    save(fig, 'fig_theory')

def fig_smalln():   # E3b: small-n behaviour, coverage and width ratio
    s = load('E3b'); s['c'] = s.dgp.str.extract(r'c=([0-9.]+)')[0].astype(float)
    fig, axs = plt.subplots(2, 2, figsize=(5.6, 4.0), sharex=True)
    for j, c in enumerate([0.0, 1.0]):
        for m in ['lin', 'bin10', 'iso', 'spl', 'auto']:
            d = s[(s.c == c) & (s.method == m)].sort_values('n')
            axs[0, j].errorbar(d.n, d.ratio_u, yerr=1.96 * d.ratio_u_se, color=COL[m], marker=MK[m], ms=3, lw=.9, capsize=1.2, label=NAME[m])
        for m in ['classical', 'ppi', 'ppipp', 'auto']:
            d = s[(s.c == c) & (s.method == m)].sort_values('n')
            lo = d.cover - d.cover_lo; hi = d.cover_hi - d.cover
            axs[1, j].errorbar(d.n * (1 + .04 * ['classical', 'ppi', 'ppipp', 'auto'].index(m)), d.cover, yerr=[lo, hi], color=COL[m], marker=MK[m], ms=3, lw=.9, capsize=1.2, label=NAME[m])
        axs[0, j].axhline(1, color=COL['ppipp'], lw=.8); axs[1, j].axhline(.95, color='k', lw=.6, ls=':')
        axs[0, j].set_title(['$E[Y|f]$ linear ($c{=}0$)', '$E[Y|f]$ quadratic ($c{=}1$, $s{=}0.5$)'][j]); axs[1, j].set_xlabel('labeled $n$ ($N{=}20000$)'); axs[1, j].set_xscale('log')
    axs[0, 0].set_ylabel('width / width of PPI++'); axs[1, 0].set_ylabel('coverage (Wilson 95%)'); axs[0, 1].legend(ncol=1, loc='upper right'); h, l = axs[1, 1].get_legend_handles_labels(); fig.legend(h, l, loc='lower center', ncol=4, bbox_to_anchor=(0.5, -0.06))
    axs[1, 0].set_ylim(.9, .99); axs[1, 1].set_ylim(.9, .99)
    save(fig, 'fig_smalln')


DSNAME = {'galaxies': 'Galaxies', 'forest': 'Forest', 'alphafold': 'AlphaFold', 'gene_expression': 'Gene expr.', 'census_income': 'Census income',
          'census_healthcare': 'Census health ins.', 'census_education': 'Census education'}
def _small_multiples(exp, theory_file, keys, titles, methods, fname, ylim=None, ncol=4):
    s = load(exp); th = pd.read_csv(R + theory_file)
    nrow = int(np.ceil((len(keys) + 1) / ncol)); fig, axs = plt.subplots(nrow, ncol, figsize=(7.4, 1.95 * nrow), sharex=True); axs = axs.ravel()
    for ax, key, ttl in zip(axs, keys, titles):
        for m in methods:
            d = s[(s.dgp == key) & (s.method == m)].sort_values('n')
            if len(d) == 0: continue
            ax.errorbar(d.n, d.ratio_u, yerr=1.96 * d.ratio_u_se, color=COL[m], marker=MK[m], ms=2.8, lw=.9, capsize=1, label=NAME[m])
        t = th[th.dataset == (key if exp != 'E1a' else key.split('|')[0])].sort_values('n') if 'dataset' in th else None
        if t is not None and len(t): ax.plot(t.n, t.r_eff_ppu, color=COL['theory'], ls='--', lw=1, label='efficiency bound (theory)')
        ax.axhline(1, color=COL['ppipp'], lw=.8); ax.set_xscale('log'); ax.set_title(ttl, fontsize=8)
        if ylim: ax.set_ylim(*ylim)
    h, l = axs[0].get_legend_handles_labels(); axs[len(keys)].axis('off'); axs[len(keys)].legend(h, l, loc='center', fontsize=7)
    for ax in axs[len(keys) + 1:]: ax.axis('off')
    for ax in axs[-ncol:]: ax.set_xlabel('labeled $n$')
    for i in range(0, len(axs), ncol): axs[i].set_ylabel('width / PPI++')
    save(fig, fname)

def fig_real():
    keys = [f'{d}|id' for d in DSNAME]; _small_multiples('E1a', 'theory_E1.csv', keys, list(DSNAME.values()), ['iso', 'spl', 'auto'], 'fig_real', ylim=(.95, 1.2))
def fig_distort():
    keys = ['galaxies|logit', 'galaxies|pow3', 'alphafold|logit', 'forest|logit', 'gene_expression|exp', 'census_healthcare|logit', 'census_income|sqrt']
    ttl = ['Galaxies, logit score', 'Galaxies, score$^3$', 'AlphaFold, logit score', 'Forest, logit score', 'Gene expr., exp(score/4)', 'Census health ins., logit', 'Census income, $\\sqrt{\\rm score}$']
    _small_multiples('E2', 'theory_E2.csv', keys, ttl, ['iso', 'spl', 'auto'], 'fig_distort', ylim=(.6, 1.12))

if __name__ == '__main__':
    which = sys.argv[1:] or ['theory', 'smalln']
    for w in which: globals()['fig_' + w]()
