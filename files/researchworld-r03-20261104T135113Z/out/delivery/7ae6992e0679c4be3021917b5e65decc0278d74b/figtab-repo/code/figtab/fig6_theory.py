"""Fig. 6 (C7) and appendix Fig. A3: theory vs experiment.
(a-c) random-k excess error over the noise floor, Monte-Carlo (Bayes-optimal inference, known factor model) with the Jensen lower and Wishart upper bound.
(d)   greedy conditional-variance / log-det vs brute-force optimum on N=16 synthetic matrices: fraction of the random->optimal gap closed.
(e,f) model-implied (Bayes) nMSE of the fitted Gaussian factor model next to the cross-validated nMSE of the factor-analysis inference rule.
SYNTHETIC panels are labelled. Real-data Bayes curves use the covariance fitted in-sample, so they are optimistic.
"""
import sys
from common import *

SEL_MAP = {'random': 'random', 'gv': 'gv_fa', 'dopt': 'dopt'}
R_COLOR = {1: '#0072B2', 3: '#D55E00', 8: '#009E73'}

def panel_A(ax, a, snr):
    d = a[a.snr == snr]
    for r, g in d.groupby('r'):
        g = g.sort_values('k'); c = R_COLOR[r]
        ax.plot(g.k, g.excess_mc, 'o', color=c, label=f'$r={r}$ Monte Carlo')
        ax.plot(g.k, g.lower, '-', color=c, lw=.8)
        gu = g.dropna(subset=['upper'])
        ax.plot(gu.k, gu.upper, '--', color=c, lw=.8)
    ax.set_yscale('log'); kticks(ax, ks=(4, 8, 16, 32, 64)); ax.set_title(f'synthetic, random $k$, SNR={snr:g}', fontsize=6.8)
    ax.set_xlabel('benchmarks run, $k$')

def panel_B(ax):
    b = read('theory_B_greedy.csv', THEORY)
    kinds = ['iid', 'hetero', 'cluster']; kc = {'iid': '#0072B2', 'hetero': '#D55E00', 'cluster': '#009E73'}
    for i, kind in enumerate(kinds):
        for off, col, mk in [(-.07, 'closed_cv', 'o'), (.07, 'closed_dopt', 's')]:
            g = b[b.kind == kind].groupby('k')[col]
            x = g.mean().index.values + off + (i - 1) * .2
            ax.plot(x, g.mean().values, mk, ms=3, color=kc[kind], mfc=kc[kind] if mk == 'o' else 'none')
            ax.plot(x, g.min().values, 'x', ms=2.5, color=kc[kind], alpha=.6)
    ax.axhline(1, color='k', lw=.5); ax.set_xticks([2, 3, 4, 5]); ax.set_ylim(0, 1.05)
    ax.set_title('synthetic: greedy vs optimum', fontsize=6.8); ax.set_xlabel('$k$'); ax.set_ylabel('random$\\to$optimal gap closed')
    ax.legend(handles=[plt.Line2D([], [], marker='o', ls='', color='k', ms=3, label='cond. variance, mean'), plt.Line2D([], [], marker='s', mfc='none', ls='', color='k', ms=3, label='log-det, mean'),
                       plt.Line2D([], [], marker='x', ls='', color='k', ms=3, label='worst instance (40)')] +
                      [plt.Line2D([], [], marker='o', ls='', color=kc[k], ms=3, label=k) for k in kinds], fontsize=5, frameon=False, loc='lower right', ncol=2, columnspacing=.8, handletextpad=.2)

def panel_vs(ax, ds, title, synth):
    t = read(f'vs_real_{ds}.csv', THEORY); cur = curves(f'B_{ds}')
    tr = read(f'vs_real_trainonly_{ds}.csv', THEORY) if exists(f'vs_real_trainonly_{ds}.csv', THEORY) else None
    ax.set_title(title, fontsize=6.8)
    for bs, s in SEL_MAP.items():
        g = t[t.selector == bs].sort_values('k')
        if tr is not None:
            h = tr[tr.selector == bs].sort_values('k')
            ax.plot(g.k, g.nmse_bayes, ':', color=SEL_COLOR[s], lw=.7, alpha=.7)   # fitted on all models (in-sample, optimistic)
            ax.plot(h.k, h.nmse_bayes_trainfit, '--', color=SEL_COLOR[s], lw=1)    # fitted on each fold's training models
            ax.fill_between(h.k, h.nmse_bayes_trainfit - h.sd_over_folds, h.nmse_bayes_trainfit + h.sd_over_folds, color=SEL_COLOR[s], alpha=.13, lw=0)   # +-1 sd over folds
        else:
            ax.plot(g.k, g.nmse_bayes, '--', color=SEL_COLOR[s], lw=1)
        c = cur[(cur.selector == s) & (cur.method == 'fa')]
        if len(c): band(ax, c, color=SEL_COLOR[s], marker='o')
    kticks(ax, kmax=cur.k.max()); ax.set_xlabel('benchmarks run, $k$')

def main_fig():
    a = read('theory_A_random.csv', THEORY)
    fig, axs = plt.subplots(2, 3, figsize=(W, 4.4))
    for ax, snr in zip(axs[0], [0.5, 2.0, 8.0]):
        panel_A(ax, a, snr)
    axs[0, 0].set_ylabel('excess error $(\\mathrm{MSE}-\\psi)/\\psi$')
    h = [plt.Line2D([], [], marker='o', ls='', color=R_COLOR[r]) for r in (1, 3, 8)] + [plt.Line2D([], [], color='k', lw=.8), plt.Line2D([], [], color='k', ls='--', lw=.8)]
    l = ['$r=1$ (MC)', '$r=3$ (MC)', '$r=8$ (MC)', 'Jensen lower bound', 'Wishart upper bound']
    fig.legend(h, l, loc='center', ncol=5, frameon=False, bbox_to_anchor=(.5, .505), fontsize=6)
    panel_B(axs[1, 0])
    panel_vs(axs[1, 1], 'syn_base', 'synthetic rank 3: Bayes vs CV', True)
    panel_vs(axs[1, 2], 'mteb_dense56', 'MTEB-56: train-fit Bayes vs CV', False)
    axs[1, 1].set_ylabel('nMSE')
    hh = [plt.Line2D([], [], color=SEL_COLOR[s], marker='o', label=SEL_LABEL[s].split(' (')[0]) for s in ['random', 'gv_fa', 'dopt']] + \
         [plt.Line2D([], [], color='k', ls='--', label='Bayes, train-fit ($\\pm$1 sd over folds)'), plt.Line2D([], [], color='k', ls=':', lw=.7, label='Bayes, fitted on all models')]
    fig.legend(handles=hh, loc='lower center', ncol=5, frameon=False, fontsize=5.8, columnspacing=1.1, handlelength=1.6)
    for ax, lt in zip(axs.flat, 'abcdef'): t = ax.get_title(); ax.set_title(''); ax.set_title(f'({lt}) ' + t, fontsize=6.3, loc='left')
    fig.tight_layout(h_pad=4.2, rect=(0, .04, 1, 1)); save(fig, 'fig6_theory.pdf')

def appendix_fig():
    ds = [('syn_base', 'syn. base (r=3)'), ('syn_noisy', 'syn. noisy'), ('syn_clust', 'syn. clustered'), ('syn_hetero', 'syn. heterogeneous'), ('syn_r8', 'syn. rank 8'),
          ('syn_M30', 'syn. M=30'), ('mteb_dense56', 'MTEB-56'), ('mteb_dense', 'MTEB-275'), ('mteb_mid', 'MTEB-357'), ('mteb_sparse', 'MTEB-472 (sparse)'), ('helm_mmlu', 'HELM-MMLU')]
    ds = [d for d in ds if exists(f'vs_real_{d[0]}.csv', THEORY) and exists(f'curves_B_{d[0]}.csv')]
    fig, axs = plt.subplots(4, 3, figsize=(W, 6.6), sharey=True)
    for ax, (d, t) in zip(axs.flat, ds):
        panel_vs(ax, d, t, d.startswith('syn')); ax.set_xlabel('')
    for ax in axs[-1]: ax.set_xlabel('benchmarks run, $k$')
    for ax in axs[:, 0]: ax.set_ylabel('nMSE')
    for ax in axs.flat[len(ds):]: ax.axis('off')
    fig.tight_layout(); save(fig, 'figA3_theory_vs_cv_all.pdf')

if __name__ == '__main__':
    main_fig(); appendix_fig()
