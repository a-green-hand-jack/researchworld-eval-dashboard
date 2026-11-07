"""Fig. 2 (C0): spectrum of each standardised score matrix (PCA on the completed matrix, experiment-repo `describe_data.py`).
(a) variance share per component; (b) cumulative share. Real leaderboards only; synthetic matrices are in the appendix figure."""
from common import *

DS = ['mteb_dense56', 'mteb_dense', 'mteb_mid', 'mteb_sparse', 'helm_mmlu', 'helm', 'helm_lite_ext', 'livebench', 'olb']
COL = dict(zip(DS, ['#0072B2', '#56B4E9', '#009E73', '#bcbd22', '#D55E00', '#CC79A7', '#8c564b', '#E69F00', '#000000']))
LS = {'helm': ':', 'helm_lite_ext': '--', 'livebench': ':', 'olb': ':'}

def draw(DS, out, w=W):
    s = read('scree.csv'); datasets = read('datasets.csv').set_index('dataset')
    fig, axs = plt.subplots(1, 2, figsize=(w, 2.3))
    for d in DS:
        g = s[s.dataset == d].sort_values('component')
        if g.empty: continue
        g = g[g.component <= 30]
        lab = f"{d.replace('_', '-')} ({int(datasets.loc[d, 'M'])}$\\times${int(datasets.loc[d, 'N'])})"
        axs[0].plot(g.component, g.var_share, marker='o', ms=1.8, color=COL.get(d, None), ls=LS.get(d, '-'), label=lab)
        axs[1].plot(g.component, g.cum_share, marker='o', ms=1.8, color=COL.get(d, None), ls=LS.get(d, '-'))
    axs[0].set_yscale('log'); axs[0].set_ylabel('variance share'); axs[1].set_ylabel('cumulative variance share')
    for a in axs: a.set_xlabel('principal component'); a.set_xscale('log'); a.set_xticks([1, 2, 4, 8, 16, 30]); a.set_xticklabels([1, 2, 4, 8, 16, 30]); a.minorticks_off()
    axs[1].axhline(.9, color='k', lw=.5, ls=':'); axs[1].set_ylim(0, 1.02)
    axs[0].set_title('(a) scree', loc='left', fontsize=6.8); axs[1].set_title('(b) cumulative', loc='left', fontsize=6.8)
    axs[1].legend(*axs[0].get_legend_handles_labels(), loc='lower right', frameon=False, fontsize=5.5, ncol=2, columnspacing=.8, handlelength=1.5)
    fig.tight_layout(); save(fig, out)

if __name__ == '__main__':
    draw(DS, 'fig2_scree.pdf')
