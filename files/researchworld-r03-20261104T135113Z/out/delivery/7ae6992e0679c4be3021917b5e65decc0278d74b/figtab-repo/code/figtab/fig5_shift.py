"""Fig. 5 (C6): distribution shift. Held-out nMSE vs k (kernel ridge) under random folds, leave-family-out and temporal split
(train on the earliest 4/5 of dated models, test on the newest 1/5: ONE fold, ~30 test models). Log y: the column-mean baseline is far higher under temporal shift.
Dotted = full-information floor where available. 95% CI = bootstrap over held-out models."""
from common import *

SPLITS = [('random folds', {'mteb_dense56': 'B_mteb_dense56', 'mteb_dense': 'B_mteb_dense'}),
          ('leave-family-out', {'mteb_dense56': 'd56_group', 'mteb_dense': 'd275_group'}),
          ('temporal (newest 1/5)', {'mteb_dense56': 'd56_temporal', 'mteb_dense': 'd275_temporal'})]
SELS = ['random', 'gv_fa', 'dopt']; RULE = 'krr'

def main():
    fig, axs = plt.subplots(2, 3, figsize=(W, 3.6), sharey='row', squeeze=False)
    for i, ds in enumerate(['mteb_dense56', 'mteb_dense']):
        for j, (name, runs) in enumerate(SPLITS):
            ax = axs[i, j]; run = runs[ds]
            if not exists(f'curves_{run}.csv'): ax.axis('off'); continue
            cur = curves(run)
            for s in SELS:
                d = cur[(cur.selector == s) & (cur.method == RULE)]
                if len(d): band(ax, d, color=SEL_COLOR[s], label=SEL_LABEL[s], marker='o' if s != 'random' else 's')
            m = read('conditions.csv'); m = m[m.run == run]
            if len(m): ax.axhline(m.nmse_mean_baseline.iloc[0], color='k', ls=(0, (4, 2)), lw=.8, label='column mean ($k=0$)')
            fl = f'floor_{run}.csv'
            if exists(fl):
                f = read(fl).set_index('method')
                if RULE in f.index: ax.axhline(f.loc[RULE, 'nmse_floor'], color='k', ls=':', lw=.9, label='full-information floor')
            ax.set_yscale('log'); ax.set_yticks([.1, .2, .5, 1, 2, 4]); ax.set_yticklabels(['0.1', '0.2', '0.5', '1', '2', '4']); ax.minorticks_off(); ax.set_ylim(.09, 6); kticks(ax, ks=(1, 2, 4, 8, 16, 32, 64), kmax=cur.k.max())
            if i == 0: ax.set_title(name)
            if i == 1: ax.set_xlabel('benchmarks run, $k$')
        axs[i, 0].set_ylabel(f"held-out nMSE\n{DATASET_LABEL[ds].split(' (')[0]}")
    h, l = [], []
    for a in axs.flat:
        for hh, ll in zip(*a.get_legend_handles_labels()):
            if ll not in l: h.append(hh); l.append(ll)
    fig.legend(h, l, loc='lower center', ncol=3, frameon=False, bbox_to_anchor=(.5, -.07))
    fig.tight_layout(rect=(0, .03, 1, 1)); save(fig, 'fig5_shift.pdf')

if __name__ == '__main__':
    main()
