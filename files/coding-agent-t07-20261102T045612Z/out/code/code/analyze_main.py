"""Produce all tables/figures of the main experiment from results/raw_main. Usage: python -I analyze_main.py"""
import sys, os, pickle, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import wilcoxon
from analyze_lib import *

OUT_T = '/work/results/tables'; OUT_F = '/work/figs'
os.makedirs(OUT_T, exist_ok=True); os.makedirs(OUT_F, exist_ok=True)
REG_LABEL = {'iid': 'IID split', 'up50': 'Extrapolation (top 50\\% from bottom 50\\%)', 'up75': 'Extrapolation (top 25\\% from bottom 75\\%)'}
REG_SHORT = {'iid': 'IID', 'up50': 'Extrap-50', 'up75': 'Extrap-25', 'fam': 'Family hold-out'}
NAME = {
    'rand/mean': 'Random + mean', 'strat/mean': 'Stratified (difficulty) + mean',
    'anchor/mean': 'Anchor points + weighted mean', 'anchor_irt/mean': 'Anchor-IRT + weighted mean',
    'dopt/mean': 'D-optimal + mean', 'maxvar/mean': 'Max-variance + mean',
    'rand/ridge': 'Random + ridge regression', 'rand/knn': 'Random + kNN over models',
    'rand/pirt': 'Random + p-IRT', 'rand/gpirt': 'Random + gp-IRT', 'anchor_irt/gpirt': 'Anchor-IRT + gp-IRT (tinyBench.-style)',
    'anchor/pirt': 'Anchor points + p-IRT', 'dopt/pirt': 'D-optimal + p-IRT',
    'rand/cf': 'Random + CF', 'strat/cf': 'Stratified + CF', 'rand/eb0': 'Random + CF-EB0', 'strat/eb0': 'Stratified + CF-EB0',
    'rand/eb1': 'Random + CF-EB1', 'strat/eb1': 'Stratified + CF-EB1', 'rand/plugin_cf': 'Random + cross-fit plug-in',
    'rand/pirt_cal': 'Random + p-IRT (recalibrated)', 'strat/pirt_cal': 'Stratified + p-IRT (recal.)',
    'anchor/pirt_cal': 'Anchor points + p-IRT (recal.)', 'anchor_irt/pirt_cal': 'Anchor-IRT + p-IRT (recal.)',
    'dopt/pirt_cal': 'D-optimal + p-IRT (recal.)', 'maxvar/pirt_cal': 'Max-variance + p-IRT (recal.)',
    'rand/cf_cal': 'Random + CF (recal.)', 'strat/cf_cal': 'Stratified + CF (recal.)',
    'rand/eb0_cal': 'Random + CF-EB0 (recal.)', 'strat/eb0_cal': 'Stratified + CF-EB0 (recal.)',
}
MAIN = ['rand/mean', 'strat/mean', 'anchor/mean', 'anchor_irt/mean', 'dopt/mean', 'maxvar/mean',
        'rand/ridge', 'rand/knn', 'rand/pirt', 'rand/gpirt', 'anchor_irt/gpirt', 'dopt/pirt',
        'rand/cf', 'strat/cf', 'rand/eb0', 'strat/eb0', 'rand/eb1']
ALL = MAIN + ['anchor/pirt', 'strat/eb1', 'rand/plugin_cf', 'rand/pirt_cal', 'strat/pirt_cal', 'anchor/pirt_cal', 'anchor_irt/pirt_cal',
                'dopt/pirt_cal', 'maxvar/pirt_cal', 'rand/cf_cal', 'strat/cf_cal', 'rand/eb0_cal', 'strat/eb0_cal']
REGS = ['iid', 'up50', 'up75', 'fam']


def fmt_ci(pt, lo, hi, p=3):
    return f'{pt:.{p}f} \\scriptsize[{lo:.{p}f},{hi:.{p}f}]'


def table_regime(df, regime, k, combos, fh):
    """rows: combos; cols: RelRMSE (CI), MAE, Spearman (CI), Kendall, Bias."""
    _, R = cube(df, regime, k, combos, 'rmse'); _, M = cube(df, regime, k, combos, 'mae')
    _, Sp = cube(df, regime, k, combos, 'spearman'); _, Kt = cube(df, regime, k, combos, 'kendall'); _, Bi = cube(df, regime, k, combos, 'bias')
    rel = boot(R, make_rel(0), B=1000); mae = stat_mean(M); sp = boot(Sp, stat_mean, B=1000); kt = stat_mean(Kt); bi = stat_mean(Bi)
    best_rel = np.min(rel[0]); best_sp = np.max(sp[0])
    out = {}
    for i, c in enumerate(combos):
        r = fmt_ci(rel[0][i], rel[1][i], rel[2][i], 2) if i else '1 (ref.)'
        s = fmt_ci(sp[0][i], sp[1][i], sp[2][i], 3)
        fh.write(f'{NAME[c]} & {r} & {mae[i]:.2f} & {s} & {kt[i]:.3f} & {bi[i]:+.2f} \\\\\n')
        out[c] = dict(rel=rel[0][i], lo=rel[1][i], hi=rel[2][i], mae=mae[i], sp=sp[0][i], kt=kt[i], bias=bi[i])
    return out


def main():
    df, info = load_rows()
    print('rows', len(df), 'reps per regime', df.groupby('regime').rep.nunique().to_dict())
    nreps = int(info.groupby(['bench', 'regime']).size().min())
    # ---- main tables per regime and k
    summary = {}
    for k in [10, 25, 50, 100, 200]:
        for reg in [r for r in REGS if r in set(df.regime)]:
            with open(f'{OUT_T}/main_{reg}_k{k}.tex', 'w') as fh:
                summary[(reg, k)] = table_regime(df, reg, k, ALL if k != 50 else ALL, fh)
    pickle.dump(summary, open('/work/results/summary_main.pkl', 'wb'))
    # ---- significance across benchmarks (Wilcoxon on rep-averaged RMSE vs rand/mean), pooled over k
    rows = []
    cmp = [c for c in ALL if c != 'rand/mean']
    for reg in [r for r in REGS if r in set(df.regime)]:
        for k in [25, 50, 100]:
            bn, R = cube(df, reg, k, ['rand/mean'] + cmp, 'rmse')
            m = R.mean(1)
            for i, c in enumerate(cmp):
                d = m[:, i + 1] - m[:, 0]
                try: p = wilcoxon(d).pvalue
                except Exception: p = np.nan
                rows.append(dict(regime=reg, k=k, combo=c, wins=int((d < 0).sum()), nb=len(d), p=p, rel=float(np.exp(np.mean(np.log(m[:, i + 1] / m[:, 0]))))))
    sig = pd.DataFrame(rows); sig.to_csv('/work/results/significance.csv', index=False)
    # ---- figure 1: relative RMSE vs k
    ks = [10, 25, 50, 100, 200]
    show = ['strat/mean', 'anchor_irt/gpirt', 'rand/pirt', 'rand/pirt_cal', 'rand/ridge', 'rand/cf', 'rand/eb0', 'strat/eb0']
    sty = {'strat/mean': ('tab:green', '-', 's'), 'anchor_irt/gpirt': ('tab:purple', '--', 'v'), 'rand/pirt': ('tab:red', '--', 'o'),
           'rand/pirt_cal': ('tab:orange', '--', '^'), 'rand/ridge': ('tab:brown', ':', 'x'), 'rand/cf': ('tab:blue', '-', 'o'),
           'rand/eb0': ('tab:cyan', '-', 'D'), 'strat/eb0': ('tab:olive', '-', 'P')}
    fig, axs = plt.subplots(1, 3, figsize=(11, 3.2), sharey=True)
    for ax, reg in zip(axs, ['iid', 'up50', 'up75']):
        for c in show:
            pts = []
            for k in ks:
                _, R = cube(df, reg, k, ['rand/mean', c], 'rmse')
                pt, lo, hi = boot(R, make_rel(0), B=500)
                pts.append((pt[1], lo[1], hi[1]))
            pts = np.array(pts)
            col, ls, mk = sty[c]
            ax.plot(ks, pts[:, 0], color=col, ls=ls, marker=mk, ms=3.5, lw=1.2, label=NAME[c])
            ax.fill_between(ks, pts[:, 1], pts[:, 2], color=col, alpha=0.12, lw=0)
        ax.axhline(1, color='k', lw=0.8)
        ax.set_xscale('log'); ax.set_yscale('log'); ax.set_xticks(ks); ax.set_xticklabels(ks)
        ax.set_title(REG_SHORT[reg]); ax.set_xlabel('subset size $k$')
        ax.set_yticks([0.5, 0.7, 1, 1.5, 2, 3]); ax.set_yticklabels(['0.5', '0.7', '1', '1.5', '2', '3'])
        ax.set_ylim(0.45, 3.5)
    axs[0].set_ylabel('RMSE relative to Random + mean')
    for ax in axs: ax.minorticks_off()
    h, l = axs[0].get_legend_handles_labels()
    fig.legend(h, l, loc='lower center', ncol=4, fontsize=7, frameon=False)
    plt.tight_layout(rect=(0, 0.13, 1, 1)); plt.savefig(f'{OUT_F}/fig_relrmse_vs_k.pdf'); plt.close()
    # ---- figure 2: per-benchmark heatmap (k=50)
    hm = ['strat/mean', 'rand/pirt', 'rand/gpirt', 'rand/cf', 'rand/eb0', 'strat/eb0']
    fig, axs = plt.subplots(1, 3, figsize=(11, 3.4), sharey=True)
    for ax, reg in zip(axs, ['iid', 'up50', 'up75']):
        bn, R = cube(df, reg, 50, ['rand/mean'] + hm, 'rmse')
        m = R.mean(1); M = np.log2(m[:, 1:] / m[:, [0]])
        im = ax.imshow(M, cmap='RdBu_r', vmin=-1.2, vmax=1.2, aspect='auto')
        ax.set_xticks(range(len(hm))); ax.set_xticklabels([NAME[c].replace(' + ', '\n+ ') for c in hm], rotation=90, fontsize=6.5)
        ax.set_title(REG_SHORT[reg])
        if reg == 'iid':
            ax.set_yticks(range(len(bn))); ax.set_yticklabels([BENCH_LABEL[b] for b in bn], fontsize=7)
        for i in range(M.shape[0]):
            for j in range(M.shape[1]):
                ax.text(j, i, f'{2**M[i, j]:.2f}', ha='center', va='center', fontsize=5.5)
    plt.tight_layout(); plt.savefig(f'{OUT_F}/fig_heatmap_k50.pdf'); plt.close()
    # ---- figure 3: signed error vs target strength (detail, rand selection, k=100)
    ests = [('mean', 'Random mean'), ('pirt', 'p-IRT'), ('pirt_cal', 'p-IRT recal.'), ('cf', 'CF'), ('eb0', 'CF-EB0')]
    fig, axs = plt.subplots(1, 2, figsize=(3.4, 2.8), sharey=True)
    files = glob.glob('/work/results/raw_main2/*.pkl')
    acc = {(reg, e): [] for reg in ['iid', 'up50', 'up75'] for e, _ in ests}
    nb = 10
    for f in files:
        d = pickle.load(open(f, 'rb')); reg = d['info']['regime']; true = d['detail']['true']
        if reg not in ('iid', 'up50', 'up75'): continue
        pct = (np.argsort(np.argsort(true)) + 0.5) / len(true)
        bins = np.minimum((pct * nb).astype(int), nb - 1)
        for e, _ in ests:
            if (100, e) not in d['detail']: continue
            err = (d['detail'][(100, e)] - true) * 100
            acc[(reg, e)].append((d['info']['bench'], np.array([err[bins == j].mean() if (bins == j).any() else np.nan for j in range(nb)])))
    for ax, reg in zip(axs, ['iid', 'up50']):
        for e, lab in ests:
            per = {}
            for b, v in acc[(reg, e)]: per.setdefault(b, []).append(v)
            M = np.array([np.nanmean(np.array(v), 0) for v in per.values()])  # bench x bins
            ax.plot((np.arange(nb) + 0.5) / nb, np.nanmean(M, 0), marker='o', ms=3, lw=1.2, label=lab)
        ax.axhline(0, color='k', lw=0.8); ax.set_title(REG_SHORT[reg]); ax.set_xlabel('target percentile', fontsize=8); ax.set_xticks([0.25, 0.75])
    axs[0].set_ylabel('mean signed error (pts)'); axs[0].legend(fontsize=5.5, frameon=False, loc='lower left')
    plt.tight_layout(); plt.savefig(f'{OUT_F}/fig_bias_by_strength.pdf'); plt.close()
    print('nreps', nreps)


BENCHES_ORDER = ['arc_challenge', 'bbh', 'gpqa', 'ifeval', 'mmlu_pro', 'musr', 'openllm_math', 'commonsense', 'gsm', 'legalbench', 'math', 'med_qa', 'mmlu']

if __name__ == '__main__':
    main()
