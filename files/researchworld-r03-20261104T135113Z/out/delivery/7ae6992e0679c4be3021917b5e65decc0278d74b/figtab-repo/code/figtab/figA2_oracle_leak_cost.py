"""Fig. A2 (C2/C8, appendix) on MTEB-56, protocol B.
(a) oracle selection (uses the held-out model's own target scores: an optimistic upper bound, not a method) vs deployable selectors, factor-analysis inference.
(b) leakage check: selection model fitted on training models only (solid) vs also on the held-out rows (dashed), factor-analysis inference.
(c) cost-aware budget: nMSE vs evaluation budget (per-mille of the total evaluation time of the candidate benchmarks), kernel ridge; 'cheap' = cheapest-first, 'gvc' = conditional variance per unit cost."""
from common import *

def main():
    fig, axs = plt.subplots(1, 3, figsize=(W, 2.3))
    ax = axs[0]
    if exists('oracle_mteb_dense56.csv'):
        o = read('oracle_mteb_dense56.csv'); o = o[o.method == 'fa']
        for s in ['random', 'gv_fa', 'dopt', 'oracle']:
            d = o[o.selector == s]
            if len(d): band(ax, d, col='est', lo='lo', hi='hi', color=SEL_COLOR[s], label=SEL_LABEL[s], ls=':' if s == 'oracle' else '-')
        ax.set_title('(a) oracle upper bound', loc='left', fontsize=6.8); ax.set_ylim(.05, 1.1); kticks(ax, kmax=16); ax.set_xlabel('benchmarks run, $k$'); ax.set_ylabel('held-out nMSE (FA inference)')
        ax.legend(frameon=False, fontsize=5.5, loc='upper right')
    ax = axs[1]
    if exists('leak_mteb_dense56.csv'):
        l = read('leak_mteb_dense56.csv'); l = l[l.method == 'fa']
        for s in ['random', 'gv_fa', 'dopt']:
            for run, ls in [('train_only', '-'), ('leak', '--')]:
                d = l[(l.selector == s) & (l.run == run)]
                if len(d): band(ax, d, col='est', lo='lo', hi='hi', color=SEL_COLOR[s], ls=ls, alpha=.08)
        ax.set_title('(b) leakage check', loc='left', fontsize=6.8); ax.set_ylim(.1, .85); kticks(ax, kmax=32); ax.set_xlabel('benchmarks run, $k$')
        ax.legend(handles=[plt.Line2D([], [], color='k', ls='-', label='train-only selection'), plt.Line2D([], [], color='k', ls='--', label='leaky (held-out rows)')], frameon=False, fontsize=5.5, loc='upper right')
    ax = axs[2]
    if exists('curves_C_d56.csv'):
        c = curves('C_d56'); c = c[c.method == 'krr']
        for s, col, lab in [('random', SEL_COLOR['random'], 'random'), ('gv_fa', SEL_COLOR['gv_fa'], 'cond. variance'), ('gvc_fa', '#CC79A7', 'cond. variance / cost'), ('cheap', '#E69F00', 'cheapest first')]:
            d = c[c.selector == s]
            if len(d): band(ax, d, color=col, label=lab)
        ax.set_xscale('log'); ax.set_title('(c) cost-aware budget', loc='left', fontsize=6.8); ax.set_xlabel('budget (per-mille of total eval. time)'); ax.legend(frameon=False, fontsize=5.5)
    fig.tight_layout(); save(fig, 'figA2_oracle_leak_cost.pdf')

if __name__ == '__main__':
    main()
