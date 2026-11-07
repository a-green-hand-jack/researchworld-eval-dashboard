"""Fig. 1 (C1): held-out nMSE vs number of benchmarks run k, protocol B, selector x inference rule.
Rows: datasets; columns: inference rule. Horizontal references: column mean (k=0) and the same rule's full-information floor.
Band = 95% bootstrap CI over held-out models.
"""
from common import *

RULES = ['ridge', 'krr', 'fa']
SELS = ['random', 'gv_fa', 'dopt']

def draw(ax, run, rule, sels, floor):
    cur = curves(run)
    for s in sels:
        d = cur[(cur.selector == s) & (cur.method == rule)]
        if len(d): band(ax, d, color=SEL_COLOR[s], label=SEL_LABEL[s], marker='o' if s != 'random' else 's')
    f = floor.set_index('method')
    ax.axhline(f.loc['mean_k0', 'nmse_floor'], color='k', ls=(0, (4, 2)), lw=.8, label='column mean ($k=0$)')
    if rule in f.index:
        ax.axhline(f.loc[rule, 'nmse_floor'], color='k', ls=':', lw=.9, label='full-information floor (same rule)')
    kticks(ax, kmax=cur[cur.method == rule].k.max())

def main():
    rows = [('B_mteb_dense56', 'mteb_dense56'), ('B_mteb_dense', 'mteb_dense')]
    rows = [r for r in rows if exists(f'floor_{r[0]}.csv')]
    fig, axs = plt.subplots(len(rows), len(RULES), figsize=(W, 1.9 * len(rows) + .3), sharex=True, sharey=True, squeeze=False)
    for i, (run, ds) in enumerate(rows):
        floor = read(f'floor_{run}.csv')
        for j, rule in enumerate(RULES):
            draw(axs[i, j], run, rule, SELS, floor)
            if i == 0: axs[i, j].set_title(METHOD_LABEL[rule])
            if i == len(rows) - 1: axs[i, j].set_xlabel('benchmarks run, $k$')
        axs[i, 0].set_ylabel('held-out nMSE\n' + DATASET_LABEL[ds].split(' (')[0])
    axs[0, 0].set_ylim(0, 1.15)
    h, l = axs[0, 0].get_legend_handles_labels()
    fig.legend(h, l, loc='lower center', ncol=3, frameon=False, bbox_to_anchor=(.5, -.06 - .02 * len(rows)))
    fig.tight_layout(rect=(0, 0, 1, 1))
    save(fig, 'fig1_main_curves.pdf')

if __name__ == '__main__':
    main()
