"""Fig. A5 (C2, C4, C5): extra selectors and extra inference rules (experiment-repo `xrun.py`, same folds, targets and seeds as the base runs).
Top: selectors at k in {1,2,4,8,16}, kernel ridge, random folds: the base selectors plus forward selection by cross-validated ridge on the shared set (fwd_ridge), multi-task lasso path (mtl) and
the adaptive local-Gaussian conditional-variance greedy (adapt_loc: re-fits after each revealed score).
Bottom: inference rules under shift (selector gv_fa): plain rules, unshrunk OLS, soft-impute, and linear-trend terms (trend_fa, trend_ols)."""
from common import *

SELS = ['random', 'gv_fa', 'dopt', 'central', 'fwd_ridge', 'mtl', 'adapt_loc']
SC = dict(SEL_COLOR, fwd_ridge='#F0E442', mtl='#000000', adapt_loc='#44AA99')
SL = dict(SEL_LABEL, fwd_ridge='forward sel. (ridge CV)', mtl='multi-task lasso', adapt_loc='adaptive cond. variance', gv_fa='greedy cond. variance (FA)')
SM = dict(random='s', gv_fa='o', dopt='o', central='^', fwd_ridge='v', mtl='D', adapt_loc='P')
RULES = ['krr', 'fa', 'ols', 'softimpute', 'trend_fa', 'trend_ols']
RC = dict(krr='#0072B2', fa='#009E73', ols='#E69F00', softimpute='#CC79A7', trend_fa='#D55E00', trend_ols='#56B4E9')
RL = dict(krr='kernel ridge', fa='FA posterior', ols='OLS (unshrunk)', softimpute='soft-impute', trend_fa='FA + time trend', trend_ols='OLS + time trend')

def main():
    top = [('B_mteb_dense56', 'MTEB-56'), ('B_mteb_dense', 'MTEB-275'), ('B_helm_mmlu', 'HELM-MMLU')]
    bot = [('d56_group', 'MTEB-56, org. leave-out'), ('d56_temporal', 'MTEB-56, temporal'), ('d275_temporal', 'MTEB-275, temporal')]
    fig, axs = plt.subplots(2, 3, figsize=(W, 3.7))
    for ax, (run, t) in zip(axs[0], top):
        d = read(f'xcurves_sel_{run}.csv'); d = d[d.method == 'krr']
        for s in SELS:
            q = d[d.selector == s]
            if len(q): band(ax, q, color=SC[s], marker=SM[s], label=SL[s], alpha=.0 if s not in ('random', 'gv_fa') else .12)
        f = read(f'floor_{run}.csv').set_index('method')
        ax.axhline(f.loc['krr', 'nmse_floor'], color='k', ls=':', lw=.9, label='full-information floor (KRR)')
        ax.set_title(t, fontsize=7); kticks(ax, ks=(1, 2, 4, 8, 16)); ax.set_xlabel('$k$')
    axs[0, 0].set_ylabel('held-out nMSE (KRR)')
    for ax, (run, t) in zip(axs[1], bot):
        d = read(f'xcurves_rules_{run}.csv'); d = d[d.selector == 'gv_fa']
        for m in RULES:
            q = d[d.method == m]
            if len(q): band(ax, q, color=RC[m], label=RL[m], alpha=.0)
        f = read(f'xfloor_rules_{run}.csv').set_index('method')
        ax.axhline(f.loc['mean_k0', 'nmse_floor'], color='k', ls=(0, (4, 2)), lw=.8, label='column mean ($k=0$)')
        ax.set_yscale('log'); ax.set_title(t, fontsize=7); kticks(ax, ks=(2, 4, 8, 16)); ax.set_xlabel('$k$')
        ax.set_yticks([.2, .5, 1, 2, 5]); ax.set_yticklabels(['0.2', '0.5', '1', '2', '5']); ax.minorticks_off()
    axs[1, 0].set_ylabel('held-out nMSE (selector: GV)')
    h1, l1 = axs[0, 0].get_legend_handles_labels(); h2, l2 = axs[1, 0].get_legend_handles_labels()
    fig.tight_layout(rect=(0, .19, 1, 1))
    fig.legend(h1, l1, loc='lower center', ncol=3, frameon=False, fontsize=6, bbox_to_anchor=(.5, .06), columnspacing=1, title='top row: selectors', title_fontsize=6)
    fig.legend(h2, l2, loc='lower center', ncol=4, frameon=False, fontsize=6, bbox_to_anchor=(.5, -.045), columnspacing=1, title='bottom row: inference rules', title_fontsize=6)
    save(fig, 'figA5_extra_baselines.pdf')

if __name__ == '__main__':
    main()
