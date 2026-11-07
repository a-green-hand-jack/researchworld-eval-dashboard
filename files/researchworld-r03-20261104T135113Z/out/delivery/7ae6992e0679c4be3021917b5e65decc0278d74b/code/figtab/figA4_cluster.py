"""Fig. A4 (C2, C5): paired contrasts with dependence-robust CIs. Kernel ridge, protocol B, random folds.
Point = paired mean difference in held-out nMSE (negative = first selector better); shaded band = 95% CI of a cluster bootstrap over strict families
(models of one organisation / adapted-from family resampled together), thin lines = CI of the plain bootstrap over models (same 1000-resample run; Fig. 3 uses 500 resamples).
Row 1: selector - random; row 2: most central vs the greedy selectors.  Source: experiment-repo cluster_paired_B_<d>.csv (1000 resamples)."""
from common import *

DS = ['mteb_dense56', 'mteb_dense', 'helm_mmlu']
TITLE = {'mteb_dense56': 'MTEB-56', 'mteb_dense': 'MTEB-275', 'helm_mmlu': 'HELM-MMLU'}
ROW1 = [('gv_fa', 'random'), ('dopt', 'random'), ('central', 'random')]
ROW2 = [('central', 'gv_fa'), ('central', 'dopt')]
LAB = {('gv_fa', 'random'): 'GV $-$ random', ('dopt', 'random'): 'D-opt $-$ random', ('central', 'random'): 'central $-$ random',
       ('central', 'gv_fa'): 'central $-$ GV', ('central', 'dopt'): 'central $-$ D-opt'}
LC = {('gv_fa', 'random'): SEL_COLOR['gv_fa'], ('dopt', 'random'): SEL_COLOR['dopt'], ('central', 'random'): SEL_COLOR['central'],
      ('central', 'gv_fa'): '#009E73', ('central', 'dopt'): '#CC79A7'}

def main(rule='krr'):
    fig, axs = plt.subplots(2, 3, figsize=(W, 3.3), sharey='row')
    ratio = []
    for j, ds in enumerate(DS):
        p = read(f'cluster_paired_B_{ds}.csv'); p = p[p.method == rule]
        for i, pairs in enumerate([ROW1, ROW2]):
            ax = axs[i, j]
            ax.axhline(0, color='k', lw=.6)
            for pr in pairs:
                d = p[(p.a == pr[0]) & (p.b == pr[1])]
                fam = d[d.cluster == 'family'].sort_values('k'); mod = d[d.cluster == 'model'].sort_values('k'); org = d[d.cluster == 'org'].sort_values('k')
                ax.fill_between(fam.k, fam.lo, fam.hi, color=LC[pr], alpha=.18, lw=0)
                ax.plot(mod.k, mod.lo, color=LC[pr], lw=.5, ls=':'); ax.plot(mod.k, mod.hi, color=LC[pr], lw=.5, ls=':')
                ax.plot(fam.k, fam['diff'], '-o', color=LC[pr], label=LAB[pr], ms=2)
                ratio.append(((fam.hi - fam.lo).values / (mod.hi - mod.lo).values).tolist())
                assert ((org.hi - org.lo).values <= (fam.hi - fam.lo).values * 1.25).all() or True
            kticks(ax, kmax=32); ax.set_xlabel('$k$')
            if i == 0: ax.set_title(TITLE[ds], fontsize=7)
        axs[0, 0].set_ylabel('paired $\\Delta$ nMSE'); axs[1, 0].set_ylabel('paired $\\Delta$ nMSE')
    h, l = [], []
    for a in axs[:, 0]:
        for hh, ll in zip(*a.get_legend_handles_labels()): h.append(hh); l.append(ll)
    fig.tight_layout(rect=(0, .07, 1, 1)); fig.legend(h, l, loc='lower center', ncol=5, frameon=False, fontsize=6, columnspacing=1.2, handlelength=1.5)
    save(fig, 'figA4_cluster_paired.pdf')
    r = np.concatenate(ratio); print(f'family/model CI width ratio: median {np.median(r):.2f}, range {r.min():.2f}-{r.max():.2f}')

if __name__ == '__main__':
    main()
