"""Fig. 4 (C5): sensitivity of held-out nMSE to data conditions on MTEB-56 (protocol B, random folds).
Columns: extra missing training cells (MCAR), number of training models, fixed factor rank (CV-chosen rank = 'CV').
Rows: k=4 and k=16 benchmarks run. Inference: kernel ridge (left, middle), factor-analysis posterior (right); crosses = column-mean error under the same condition. 95% bootstrap CI over held-out models. The rightmost/leftmost 'main' point is the main run (3 repetitions).
"""
from common import *

SELS = ['random', 'gv_fa', 'dopt']

def pull(run, k, rule):
    c = curves(run); c = c[(c.method == rule) & (c.k == k)].set_index('selector')
    m = read('conditions.csv'); m = m[(m.run == run) & (m.k == k)]
    base = m.nmse_mean_baseline.iloc[0] if len(m) else np.nan
    return c, base

def sweep(ax, runs, labels, k, xlab, title, rule):
    xs = np.arange(len(runs))
    for s in SELS:
        pts = [pull(r, k, rule)[0].loc[s] if exists(f'curves_{r}.csv') else None for r in runs]
        ok = [i for i, p in enumerate(pts) if p is not None]
        y = np.array([pts[i].nmse for i in ok]); lo = np.array([pts[i].nmse_lo for i in ok]); hi = np.array([pts[i].nmse_hi for i in ok])
        off = (SELS.index(s) - 1) * .06
        ax.errorbar(xs[ok] + off, y, yerr=[y - lo, hi - y], fmt='o-', ms=2.8, lw=.9, elinewidth=.7, capsize=1.2, color=SEL_COLOR[s], label=SEL_LABEL[s])
    bl = [pull(r, k, rule)[1] for r in runs]
    ax.plot(xs, bl, 'x', color='k', ms=3.5, label='column mean ($k=0$)')
    ax.set_yscale('log'); ax.set_xticks(xs); ax.set_xticklabels(labels); ax.set_xlabel(xlab)
    if title: ax.set_title(title)

def main():
    sweeps = [(['d56_miss0.8', 'd56_miss0.6', 'd56_miss0.3', 'B_mteb_dense56'], ['0.8', '0.6', '0.3', '0\n(main)'], 'extra missing training cells', 'krr'),
              (['d56_mtrain15', 'd56_mtrain30', 'd56_mtrain60', 'B_mteb_dense56'], ['15', '30', '60', '$\\approx$137\n(main)'], 'training models $M$', 'krr'),
              (['d56_rank2', 'd56_rank4', 'd56_rank8', 'B_mteb_dense56'], ['2', '4', '8', 'CV\n(main)'], 'factor rank of the FA model', 'fa')]
    fig, axs = plt.subplots(2, 3, figsize=(W, 3.5), sharey=True)
    for i, k in enumerate([4, 16]):
        for j, (runs, labels, xl, rule) in enumerate(sweeps):
            sweep(axs[i, j], runs, labels, k, xl if i == 1 else '', f'{METHOD_LABEL[rule]}' if i == 0 else None, rule)
            if j == 0: axs[i, j].set_ylabel(f'held-out nMSE, $k={k}$')
    h, l = axs[0, 0].get_legend_handles_labels()
    fig.legend(h, l, loc='lower center', ncol=4, frameon=False, bbox_to_anchor=(.5, -.03), columnspacing=1)
    fig.tight_layout(rect=(0, .04, 1, 1)); save(fig, 'fig4_conditions.pdf')

if __name__ == '__main__':
    main()
