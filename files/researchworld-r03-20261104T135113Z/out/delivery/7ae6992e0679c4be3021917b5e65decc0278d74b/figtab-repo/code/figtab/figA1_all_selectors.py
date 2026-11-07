"""Fig. A1 (C1, appendix): every selector, kernel ridge, protocol B. Shows the negative result: leverage, pivoted QR, highest-variance (and k-center,
most-central at small k) do not beat random k."""
from common import *

def main():
    runs = [('B_mteb_dense56', 'MTEB-56'), ('B_mteb_dense', 'MTEB-275'), ('B_helm_mmlu', 'HELM-MMLU')]
    runs = [r for r in runs if exists(f'curves_{r[0]}.csv')]
    sels = ['random', 'gv_fa', 'dopt', 'gv_emp', 'kcenter', 'central', 'lev', 'qr', 'rawvar', 'popular']
    fig, axs = plt.subplots(1, len(runs), figsize=(W, 2.5), sharey=True, squeeze=False)
    for ax, (run, t) in zip(axs[0], runs):
        cur = curves(run)
        for s in sels:
            d = cur[(cur.selector == s) & (cur.method == 'krr')].sort_values('k')
            if len(d): ax.plot(d.k, d.nmse, '-' if s in ('random', 'gv_fa', 'dopt') else '--', marker='o', ms=2, color=SEL_COLOR[s], lw=1.6 if s == 'random' else 1, label=SEL_LABEL[s])
        ax.set_title(t); ax.set_xlabel('benchmarks run, $k$'); kticks(ax, kmax=cur.k.max())
    axs[0, 0].set_ylabel('held-out nMSE (kernel ridge)')
    fig.legend(*axs[0, 0].get_legend_handles_labels(), loc='lower center', ncol=4, frameon=False, bbox_to_anchor=(.5, -.2), fontsize=6)
    fig.tight_layout(); save(fig, 'figA1_all_selectors.pdf')

if __name__ == '__main__':
    main()
