"""Fig. 3 (C2): paired difference in held-out nMSE, selector minus random-k, same inference rule (kernel ridge).
Negative = informed selection better. Band = paired 95% bootstrap over held-out models; dashed lines (random-fold panels) = bootstrap over strict families. Includes the shift splits (leave-family-out, temporal)."""
from common import *

PANELS = [('B_mteb_dense56', 'MTEB-56, random folds'), ('B_mteb_dense', 'MTEB-275, random folds'),
          ('B_helm_mmlu', 'HELM-MMLU, random folds'), ('d56_group', 'MTEB-56, leave-family-out'),
          ('d56_temporal', 'MTEB-56, temporal split')]
SELS = ['gv_fa', 'dopt']
RULE = 'krr'

def main():
    pan = [p for p in PANELS if exists(f'paired_{p[0]}.csv')]
    nc = 3; nr = -(-len(pan) // nc)
    fig, axs = plt.subplots(nr, nc, figsize=(W, 1.9 * nr + .3), squeeze=False, sharey=False)
    for ax, (run, title) in zip(axs.flat, pan):
        d = read(f'paired_{run}.csv'); d = d[d.method == RULE]
        for s in SELS:
            band(ax, d[d.selector == s], col='diff', lo='lo', hi='hi', color=SEL_COLOR[s], label=SEL_LABEL[s])
        if exists(f'cluster_paired_{run}.csv'):   # family-cluster bootstrap CI (random-fold panels), lighter dashed lines
            cp = read(f'cluster_paired_{run}.csv'); cp = cp[(cp.cluster == 'family') & (cp.method == RULE) & (cp.b == 'random')]
            for s in SELS:
                q = cp[cp.a == s].sort_values('k')
                for col in ('lo', 'hi'): ax.plot(q.k, q[col], '--', color=SEL_COLOR[s], lw=.6, alpha=.8)
        ax.axhline(0, color=SEL_COLOR['random'], lw=.9)
        ax.set_title(title, fontsize=6.8); kticks(ax, kmax=d.k.max())
    for ax in axs.flat[len(pan):]: ax.axis('off')
    for ax in axs[-1]: ax.set_xlabel('benchmarks run, $k$')
    for r in axs: r[0].set_ylabel('nMSE(selector) $-$ nMSE(random)')
    h, l = axs[0, 0].get_legend_handles_labels()
    axs.flat[-1].legend(h + [plt.Line2D([], [], color=SEL_COLOR['random']), plt.Line2D([], [], color='k', ls='--', lw=.6)], l + ['random (reference, 0)', 'family-cluster 95% CI (random-fold panels)'], loc='center', frameon=False)
    fig.tight_layout()
    save(fig, 'fig3_paired_vs_random.pdf')

if __name__ == '__main__':
    main()
