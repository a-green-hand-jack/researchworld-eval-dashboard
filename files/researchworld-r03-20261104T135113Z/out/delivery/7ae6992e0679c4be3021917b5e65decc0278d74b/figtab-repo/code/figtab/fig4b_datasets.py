"""Fig. 4b (C5): the same comparison on every real leaderboard matrix (protocol B, random folds).
Inference rule: kernel ridge where it was run, else ridge (named in each title). Dashed = column mean, dotted = full-information floor of that rule.
Axes in k are not comparable across panels (N differs from 6 to 472)."""
from common import *

RUNS = ['mteb_dense56', 'mteb_dense', 'mteb_mid', 'mteb_sparse', 'helm_mmlu', 'helm', 'helm_lite_ext', 'livebench', 'olb']
SELS = ['random', 'gv_fa', 'dopt']

def main():
    runs = [r for r in RUNS if exists(f'curves_B_{r}.csv')]
    nc = 3 if len(runs) > 8 else 4; nr = -(-len(runs) // nc)
    fig, axs = plt.subplots(nr, nc, figsize=(W, 1.75 * nr + .4), squeeze=False)
    for ax, r in zip(axs.flat, runs):
        cur = curves(f'B_{r}'); rule = 'krr' if (cur.method == 'krr').any() else 'ridge'
        for s in SELS:
            d = cur[(cur.selector == s) & (cur.method == rule)]
            if len(d): band(ax, d, color=SEL_COLOR[s], label=SEL_LABEL[s], marker='o' if s != 'random' else 's')
        if exists(f'floor_B_{r}.csv'):
            f = read(f'floor_B_{r}.csv').set_index('method')
            ax.axhline(f.loc['mean_k0', 'nmse_floor'], color='k', ls=(0, (4, 2)), lw=.8, label='column mean ($k=0$)')
            if rule in f.index: ax.axhline(f.loc[rule, 'nmse_floor'], color='k', ls=':', lw=.9, label='full-information floor')
        ax.set_title(f"{DATASET_LABEL[r].split(' (')[0]}, {rule}", fontsize=6.5)
        kticks(ax, kmax=cur.k.max()); ax.set_xlabel('$k$')
    for ax in axs.flat[len(runs):]: ax.axis('off')
    for a in axs[:, 0]: a.set_ylabel('held-out nMSE')
    h, l = [], []
    for a in axs.flat:
        for hh, ll in zip(*a.get_legend_handles_labels()):
            if ll not in l: h.append(hh); l.append(ll)
    fig.legend(h, l, loc='lower center', ncol=3, frameon=False, bbox_to_anchor=(.5, -.04 * nr))
    fig.tight_layout(); save(fig, 'fig4b_datasets.pdf')

if __name__ == '__main__':
    main()
