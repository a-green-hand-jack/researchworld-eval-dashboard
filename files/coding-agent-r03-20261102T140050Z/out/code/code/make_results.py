"""Produce every table (CSV + LaTeX fragments) and figure (PDF) of the paper from /work/out/results and /work/out/synth.
Usage: python make_results.py        -> /work/paper/figs/*.pdf, /work/paper/tables/*.tex|csv , /work/out/summary.json"""
import os, sys, json, pickle
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze_lib import *
from bsel import select as sel
from bsel import predict as P

FIG = '/work/paper/figs'; TAB = '/work/paper/tables'; SYN = '/work/out/synth'
os.makedirs(FIG, exist_ok=True); os.makedirs(TAB, exist_ok=True)
PROC = '/work/data/proc'

plt.rcParams.update({'font.size': 8, 'axes.titlesize': 8.5, 'axes.labelsize': 8, 'legend.fontsize': 6.5, 'xtick.labelsize': 7, 'ytick.labelsize': 7,
                     'axes.spines.top': False, 'axes.spines.right': False, 'axes.linewidth': 0.6, 'grid.linewidth': 0.4, 'grid.color': '#e5e4e0',
                     'lines.linewidth': 1.3, 'lines.markersize': 3.5, 'figure.dpi': 150, 'pdf.fonttype': 42})
INK = '#0b0b0b'; INK2 = '#52514e'
# fixed colour per entity (categorical slots of the reference palette) + marker/linestyle redundancy
STY = {'random': ('#8a8984', 'o', '-', 'random'), 'popular': ('#1baf7a', 's', '--', 'most-evaluated'),
       'central': ('#6250d6', 'v', '--', 'most-correlated'), 'kmedoids': ('#eb6834', '^', '-', 'k-medoids'),
       'greedy_mi': ('#e87ba4', 'D', '-', 'greedy-MI'), 'greedy_pivot': ('#eda100', 'P', '-', 'greedy-maxvar'),
       'greedy_var': ('#2a78d6', 'o', '-', 'greedy variance-reduction'), 'top_snr': ('#008300', 'x', '--', 'top-SNR')}
NAMES = {'mteb_main': 'MTEB-main', 'mteb_dense': 'MTEB-dense', 'mteb_eng': 'MTEB-eng', 'openllm': 'OpenLLM-LB', 'helm_fine': 'HELM-Lite-22',
         'helm_core10': 'HELM-Lite-10', 'livebench': 'LiveBench-7'}
summary = {}


def save(fig, name):
    fig.savefig(f'{FIG}/{name}.pdf'); os.makedirs('/work/out/figpng', exist_ok=True); fig.savefig(f'/work/out/figpng/{name}.png', dpi=130)


def style_ax(ax):
    ax.grid(True, axis='y'); ax.tick_params(length=2.5, width=0.5, colors=INK2)


def curves(ds, split, pred='gauss', sels=None, metric='mse_z', balanced_panel=True):
    d = load(ds, split)
    if balanced_panel: d, ks = balanced(d)
    else: ks = sorted(d.k.unique())
    pm = per_model(d, metric)
    return d, pm, ks


# ------------------------------------------------------------------ dataset table + spectrum
def dataset_table():
    rows = []
    for ds in ['mteb_main', 'mteb_dense', 'mteb_eng', 'helm_fine', 'helm_core10', 'livebench', 'openllm']:
        X = pd.read_csv(f'{PROC}/{ds}.csv', index_col=0).values
        Z = (X - np.nanmean(X, 0)) / np.nanstd(X, 0)
        C = P.pairwise_corr(Z); lam = np.sort(np.linalg.eigvalsh(C))[::-1]
        pr = lam.sum() ** 2 / (lam ** 2).sum()
        n90 = int(np.searchsorted(np.cumsum(lam) / lam.sum(), 0.9) + 1)
        off = C[np.triu_indices(len(C), 1)]
        rows.append(dict(dataset=NAMES[ds], models=X.shape[0], benchmarks=X.shape[1], density=np.mean(~np.isnan(X)),
                         top_eig_share=lam[0] / lam.sum(), part_ratio=pr, n90=n90, mean_corr=off.mean(), median_corr=np.median(off)))
    t = pd.DataFrame(rows); t.to_csv(f'{TAB}/datasets.csv', index=False); summary['datasets'] = t.round(3).to_dict('records')
    with open(f'{TAB}/datasets.tex', 'w') as f:
        f.write('\\begin{tabular}{lrrrrrrr}\\toprule\nDataset & Models & Bench. & Density & $\\lambda_1/N$ & PR & $n_{90}$ & mean $\\rho$ \\\\\\midrule\n')
        for r in rows:
            f.write(f"{r['dataset']} & {r['models']} & {r['benchmarks']} & {r['density']:.2f} & {r['top_eig_share']:.2f} & {r['part_ratio']:.1f} & {r['n90']} & {r['mean_corr']:.2f} \\\\\n")
        f.write('\\bottomrule\\end{tabular}\n')


# ------------------------------------------------------------------ main curves
def ci_gain(A, R, B, seed=0, nb=NB):
    """CI for (mean(R)-mean(A))/mean(B): R^2 gain of method A over random R, models resampled jointly."""
    A, R, B = [np.asarray(x, float) for x in (A, R, B)]; n = A.shape[0]
    idx = boot_idx(n, np.random.default_rng(seed), nb)
    bm = (R[idx].mean(1) - A[idx].mean(1)) / B[idx].mean(1)
    return (R.mean(0) - A.mean(0)) / B.mean(0), np.percentile(bm, 2.5, axis=0), np.percentile(bm, 97.5, axis=0)


def xticks_for(ax, ks):
    tk = [k for k in (1, 2, 3, 5, 10, 20, 40) if k in ks]
    ax.set_xscale('log'); ax.set_xticks(tk); ax.set_xticklabels([str(k) for k in tk]); ax.minorticks_off()


def curves_fig(panels, fname, show=('random', 'popular', 'kmedoids', 'greedy_var'), width=7.0):
    n = len(panels)
    fig, axs = plt.subplots(2, n, figsize=(width, 3.9), squeeze=False)
    for c, (ds, sp) in enumerate(panels):
        d, pm, ks = curves(ds, sp)
        B = wide(pm, 'mean', 'random').values; R = wide(pm, 'gauss', 'random').values
        ax = axs[0, c]; ax2 = axs[1, c]
        for s in show:
            A = wide(pm, 'gauss', s).values
            r2, lo, hi = ci_ratio(A, B)
            col, mk, ls, lab = STY[s]
            ax.plot(ks, r2, color=col, marker=mk, ls=ls, label=lab, zorder=3 if s == 'greedy_var' else 2)
            if s in ('random', 'greedy_var'): ax.fill_between(ks, lo, hi, color=col, alpha=0.18, lw=0)
            if s != 'random':
                g, glo, ghi = ci_gain(A, R, B)
                ax2.plot(ks, 100 * g, color=col, marker=mk, ls=ls, zorder=3 if s == 'greedy_var' else 2)
                ax2.fill_between(ks, 100 * glo, 100 * ghi, color=col, alpha=0.15, lw=0)
        ax.set_title(f'{NAMES[ds]} ({B.shape[0]} test models)', fontsize=8)
        ax2.axhline(0, color=INK2, lw=0.6)
        xticks_for(ax, ks); xticks_for(ax2, ks)
        ax2.set_xlabel('k (benchmarks run)'); style_ax(ax); style_ax(ax2)
        ax.set_ylim(0, 0.9)
        if c == 0: ax.set_ylabel('$R^2$ vs. mean baseline'); ax2.set_ylabel('$R^2$ gain over random (points)')
    h, l = axs[0, 0].get_legend_handles_labels()
    fig.tight_layout(rect=(0, 0.06, 1, 1)); fig.legend(h, l, loc='lower center', ncol=len(l), frameon=False, handlelength=2.2, fontsize=6.5)
    save(fig, fname); plt.close(fig)


def main_curves():
    curves_fig([('mteb_main', 'rand'), ('helm_fine', 'rand'), ('openllm', 'rand')], 'main_curves')
    curves_fig([('mteb_dense', 'rand'), ('mteb_eng', 'rand'), ('helm_core10', 'rand'), ('livebench', 'rand')], 'curves_appendix', width=7.4,
               show=('random', 'popular', 'kmedoids', 'greedy_var', 'central'))


def result_tables():
    """R^2 (=1-MSE/MSE_mean-baseline) with bootstrap CIs, relative reduction of greedy vs random with paired CI & Wilcoxon p."""
    rows = []; red = []
    cfg = [('mteb_main', 'rand'), ('mteb_main', 'org'), ('mteb_main', 'time'), ('mteb_dense', 'rand'), ('mteb_eng', 'rand'),
           ('helm_fine', 'rand'), ('helm_core10', 'rand'), ('livebench', 'rand'), ('openllm', 'rand'), ('openllm', 'time')]
    for ds, sp in cfg:
        if not os.path.exists(f'{RES}/{ds}__{sp}.parquet'): continue
        d, pm, ks = curves(ds, sp)
        B = wide(pm, 'mean', 'random').values
        for pr in ['gauss', 'fa']:
            for s in ['random', 'popular', 'central', 'kmedoids', 'greedy_pivot', 'greedy_mi', 'top_snr', 'greedy_var', 'greedy_var@oracle', 'greedy_var@fa' if pr == 'gauss' else 'greedy_var@gauss']:
                try: A = wide(pm, pr, s).values
                except Exception: continue
                if A.shape[0] == 0: continue
                r2, lo, hi = ci_ratio(A, B); m, mlo, mhi = ci_mean(A)
                raw = d[(d.predictor == pr) & (d.selector == s)].groupby('k').mse_raw.mean().reindex(ks).values
                for j, k in enumerate(ks):
                    rows.append(dict(dataset=ds, split=sp, predictor=pr, selector=s, k=k, n_models=A.shape[0], mse_z=m[j], mse_lo=mlo[j], mse_hi=mhi[j],
                                     r2=r2[j], r2_lo=lo[j], r2_hi=hi[j], rmse_pts=np.sqrt(raw[j])))
        R = wide(pm, 'gauss', 'random').values
        for s in ['greedy_var', 'kmedoids', 'popular', 'central', 'greedy_mi']:
            A = wide(pm, 'gauss', s).values
            rr, lo, hi = ci_rel_reduction(A, R)
            for j, k in enumerate(ks):
                try: p = stats.wilcoxon(A[:, j], R[:, j]).pvalue
                except Exception: p = np.nan
                red.append(dict(dataset=ds, split=sp, selector=s, k=k, rel_red=rr[j], lo=lo[j], hi=hi[j], p=p, frac_models_better=np.mean(A[:, j] < R[:, j])))
    T = pd.DataFrame(rows); T.to_csv(f'{TAB}/all_results.csv', index=False)
    Rr = pd.DataFrame(red); Rr.to_csv(f'{TAB}/relative_reduction.csv', index=False)
    return T, Rr


def fmt(m, lo, hi, d=2): return f'{m:.{d}f} [{lo:.{d}f}, {hi:.{d}f}]'


def latex_main_table(T, Rr):
    """R^2 [CI] at selected k for random / most-evaluated / k-medoids / greedy (Gaussian predictor); main text and appendix versions."""
    def build(panels, fname):
        out = ['\\begin{tabular}{llcccc}\\toprule', 'Dataset (split) & Selector & $k{=}1$ & $k{=}3$ & $k{=}5$ & $k{=}10$ \\\\\\midrule']
        for ds, sp in panels:
            t = T[(T.dataset == ds) & (T.split == sp) & (T.predictor == 'gauss')]
            if t.empty: continue
            first = True
            for s in ['random', 'popular', 'kmedoids', 'greedy_var']:
                x = t[t.selector == s].set_index('k')
                cells = []
                for k in (1, 3, 5, 10):
                    if k in x.index:
                        r = x.loc[k]; best = max(t[(t.selector == s2) & (t.k == k)].r2.iloc[0] for s2 in ['random', 'popular', 'kmedoids', 'greedy_var'])
                        v = f"{r.r2:.2f}"; v = f"\\textbf{{{v}}}" if round(r.r2, 2) >= round(best, 2) else v
                        cells.append(v + f" \\scriptsize[{r.r2_lo:.2f},{r.r2_hi:.2f}]")
                    else: cells.append('--')
                name = f'{NAMES[ds]} ({sp})' if first else ''
                out.append(f"{name} & {STY[s][3]} & " + ' & '.join(cells) + ' \\\\')
                first = False
            out.append('\\midrule')
        out[-1] = '\\bottomrule'; out.append('\\end{tabular}')
        open(f'{TAB}/{fname}', 'w').write('\n'.join(out) + '\n')
    build([('mteb_main', 'rand'), ('helm_fine', 'rand'), ('openllm', 'rand'), ('livebench', 'rand')], 'main_r2.tex')
    build([('mteb_dense', 'rand'), ('mteb_eng', 'rand'), ('helm_core10', 'rand')], 'main_r2_app.tex')


# ------------------------------------------------------------------ predictors
def predictor_table():
    rows = []
    for ds, sp in [('mteb_main', 'rand'), ('helm_fine', 'rand'), ('openllm', 'rand')]:
        if not os.path.exists(f'{RES}/{ds}__{sp}.parquet'): continue
        d, pm, ks = curves(ds, sp)
        B = wide(pm, 'mean', 'random').values
        for s in ['random', 'greedy_var']:
            for pr in ['avgshift', 'knn', 'isvd', 'fa', 'gauss', 'hybrid']:
                A = wide(pm, pr, s).values
                r2, lo, hi = ci_ratio(A, B)
                for j, k in enumerate(ks):
                    rows.append(dict(dataset=ds, selector=s, predictor=pr, k=k, r2=r2[j], lo=lo[j], hi=hi[j]))
    t = pd.DataFrame(rows); t.to_csv(f'{TAB}/predictors.csv', index=False)
    return t


# ------------------------------------------------------------------ calibration of the model-implied error
def calibration_fig():
    fig, axs = plt.subplots(1, 3, figsize=(7.0, 2.3))
    for ax, ds in zip(axs, ['mteb_main', 'helm_fine', 'openllm']):
        if not os.path.exists(f'{RES}/{ds}__rand.parquet'): continue
        d, _ = balanced(load(ds, 'rand'))
        d = d[d.predictor == 'gauss']
        for s, ls in [('greedy_var', '-'), ('random', '--')]:
            x = d[d.selector == s].groupby(['k', 'model'])[['mse_z', 'exp_mse_z']].mean().reset_index().groupby('k')[['mse_z', 'exp_mse_z']].mean()
            col = STY[s][0]
            ax.plot(x.index, x.mse_z, color=col, marker='o', ls='-', label=f'{STY[s][3]}: held-out')
            ax.plot(x.index, x.exp_mse_z, color=col, marker='', ls=':', lw=1.6, label=f'{STY[s][3]}: model-implied')
        xticks_for(ax, sorted(x.index)); ax.set_title(NAMES[ds]); ax.set_xlabel('k'); style_ax(ax); ax.set_ylim(bottom=0)
    axs[0].set_ylabel('standardized MSE'); axs[0].legend(frameon=False, loc='upper right', fontsize=5.5)
    h_, l_ = axs[0].get_legend_handles_labels(); axs[0].get_legend().remove()
    fig.tight_layout(rect=(0, 0.14, 1, 1)); fig.legend(h_, l_, loc='lower center', ncol=4, frameon=False, fontsize=6)
    cal = {}
    for ds in ['mteb_main', 'helm_fine', 'openllm', 'mteb_dense', 'mteb_eng', 'helm_core10', 'livebench']:
        if not os.path.exists(f'{RES}/{ds}__rand.parquet'): continue
        d, _ = balanced(load(ds, 'rand')); d = d[d.predictor == 'gauss']
        for s_ in ['greedy_var', 'random']:
            x = d[d.selector == s_].groupby(['k', 'model'])[['mse_z', 'exp_mse_z']].mean().reset_index().groupby('k')[['mse_z', 'exp_mse_z']].mean()
            cal[f'{ds}/{s_}'] = dict(mean_ratio_model_over_heldout=float((x.exp_mse_z / x.mse_z).mean()), min_ratio=float((x.exp_mse_z / x.mse_z).min()), max_ratio=float((x.exp_mse_z / x.mse_z).max()))
    summary['calibration'] = cal
    save(fig, 'calibration'); plt.close(fig)


# ------------------------------------------------------------------ k needed
def k_needed(T):
    rows = []
    for (ds, sp), g in T[(T.predictor == 'gauss')].groupby(['dataset', 'split']):
        for s in ['random', 'greedy_var', 'kmedoids']:
            x = g[g.selector == s].sort_values('k')
            for th in (0.6, 0.7, 0.75, 0.8):
                k = k_to_reach(x.k.values, 1 - x.r2.values, 1 - th)
                rows.append(dict(dataset=ds, split=sp, selector=s, r2_target=th, k_needed=k if k is not None else np.nan, kmax=x.k.max(),
                                 r2_at_kmax=x.r2.values[-1]))
    t = pd.DataFrame(rows); t.to_csv(f'{TAB}/k_needed.csv', index=False)
    return t


# ------------------------------------------------------------------ real-data spectral tail bound, greedy vs random in-sample, floor
def spectral_fig():
    fig, axs = plt.subplots(1, 3, figsize=(7.0, 2.2))
    out = {}
    for ax, ds in zip(axs, ['mteb_main', 'helm_fine', 'openllm']):
        X = pd.read_csv(f'{PROC}/{ds}.csv', index_col=0).values
        Z = (X - np.nanmean(X, 0)) / np.nanstd(X, 0)
        C = P.pairwise_corr(Z); C = 0.95 * C + 0.05 * np.eye(len(C)); N = len(C)
        lam = np.sort(np.linalg.eigvalsh(C))[::-1]
        kmax = min(60, N - 2)
        ks = np.arange(1, kmax + 1)
        order = sel.greedy_var(C, kmax)
        g = np.array([sel.objective(C, order[:k]) / (N - k) for k in ks])
        rng = np.random.default_rng(0)
        r = np.array([np.mean([sel.objective(C, rng.permutation(N)[:k]) for _ in range(40)]) / (N - k) for k in ks])
        tail = np.array([lam[k:].sum() / (N - k) for k in ks])
        loo = 1.0 / np.diag(np.linalg.inv(C))
        floor = np.array([np.mean(np.delete(loo, order[:k])) for k in ks])
        ax.plot(ks, r, color=STY['random'][0], marker='', ls='-', label='random S')
        ax.plot(ks, g, color=STY['greedy_var'][0], label='greedy S')
        ax.plot(ks, tail, color=INK, ls='--', label=r'tail bound $\sum_{i>k}\lambda_i/(N-k)$')
        ax.plot(ks, floor, color=INK2, ls=':', label='floor: all other benchmarks known')
        ax.set_title(NAMES[ds]); ax.set_xlabel('k'); style_ax(ax); ax.set_ylim(bottom=0)
        if N > 12: ax.set_xscale('log')
        out[ds] = dict(floor_at={int(k): float(floor[k - 1]) for k in (1, 5, 10, 20, 40) if k <= kmax}, greedy_at={int(k): float(g[k - 1]) for k in (1, 5, 10, 20, 40) if k <= kmax}, tail_at={int(k): float(tail[k - 1]) for k in (1, 5, 10, 20, 40) if k <= kmax},
                       random_at={int(k): float(r[k - 1]) for k in (1, 5, 10, 20, 40) if k <= kmax})
    axs[0].set_ylabel('mean residual variance per target'); axs[0].legend(frameon=False, fontsize=5.5, loc='upper right')
    fig.tight_layout(); save(fig, 'spectral'); plt.close(fig)
    summary['spectral'] = out


def greedy_picks_table():
    df = pd.read_csv(f'{PROC}/mteb_main.csv', index_col=0)
    info = pd.read_csv(f'{PROC}/mteb_task_info.csv', index_col=0).reindex(df.columns)
    X = df.values; Z = (X - np.nanmean(X, 0)) / np.nanstd(X, 0)
    C = 0.95 * P.pairwise_corr(Z) + 0.05 * np.eye(X.shape[1])
    order = sel.greedy_var(C, 12)
    rows = []
    for k, j in enumerate(order, 1):
        rows.append(dict(rank=k, task=df.columns[j], type=info.type.iloc[j], langs=info.langs.iloc[j], resid_after=sel.objective(C, order[:k]) / len(C)))
    t = pd.DataFrame(rows); t.to_csv(f'{TAB}/greedy_picks_mteb_main.csv', index=False)
    with open(f'{TAB}/greedy_picks.tex', 'w') as f:
        f.write('\\begin{tabular}{rllr}\\toprule\n$j$ & Task & Type / languages & resid.\\ var. \\\\\\midrule\n')
        for r in rows:
            nm = r['task'].replace('_', '\\_'); lg = str(r['langs']).replace(';', ',')
            lg = lg if len(lg) < 14 else lg[:11] + '...'
            f.write(f"{r['rank']} & {nm} & {r['type']} / {lg} & {r['resid_after']:.2f} \\\\\n")
        f.write('\\bottomrule\\end{tabular}\n')


# ------------------------------------------------------------------ conditions
def conditions_fig():
    p = f'{RES}/conditions__mteb_main.parquet'
    if not os.path.exists(p): return
    d = pd.read_parquet(p)
    d = d[d.predictor == 'gauss'].copy()
    d.loc[(d.cond == 'n_train') & d.level.isin(['151', '152']), 'level'] = 'all'
    d['cell'] = d.fold.astype(str) + '|' + d.model.astype(str) + '|' + d.t0.astype(str)
    rows = []
    for (cond, level), g in d.groupby(['cond', 'level']):
        ks = sorted(g.k.unique())
        cnt = g[g.selector == 'greedy_var'].groupby('cell').k.nunique(); keep = cnt[cnt == len(ks)].index; g = g[g.cell.isin(keep)]
        pm = g.groupby(['selector', 'k', 'model', 'cell']).mse_z.mean().reset_index().groupby(['selector', 'k', 'model']).mse_z.mean().reset_index()
        base = g.groupby(['k', 'model', 'cell']).mse0_z.mean().reset_index().groupby('model').mse0_z.mean()
        for k in ks:
            R = pm[(pm.selector == 'random') & (pm.k == k)].set_index('model').mse_z.sort_index()
            Bv = base.reindex(R.index).values
            for s in ['greedy_var', 'kmedoids', 'popular', 'greedy_var@oracle']:
                A = pm[(pm.selector == s) & (pm.k == k)].set_index('model').mse_z.reindex(R.index)
                rr, lo, hi = ci_rel_reduction(A.values[:, None], R.values[:, None])
                r2, r2lo, r2hi = ci_ratio(A.values[:, None], Bv[:, None])
                r2r, r2rlo, r2rhi = ci_ratio(R.values[:, None], Bv[:, None])
                rows.append(dict(cond=cond, level=level, selector=s, k=k, mse=A.mean(), mse_random=R.mean(), rel_red=rr[0], lo=lo[0], hi=hi[0],
                                 r2=r2[0], r2lo=r2lo[0], r2hi=r2hi[0], r2_random=r2r[0], r2_random_lo=r2rlo[0], r2_random_hi=r2rhi[0], n=len(R)))
    t = pd.DataFrame(rows); t.to_csv(f'{TAB}/conditions.csv', index=False)
    order = [('t0_frac', '0.1', 'targets: 10% of observed'), ('t0_frac', '0.5', 'targets: 50% of observed'), ('family', 'disjoint', 'targets: whole task families'), ('n_train', '25', 'history: 25 models'), ('n_train', '50', 'history: 50 models'), ('n_train', '100', 'history: 100 models'), ('n_train', 'all', 'history: all (~151) models'),
             ('drop_train_cells', '0.0', 'history cells dropped: 0%'), ('drop_train_cells', '0.3', 'history cells dropped: 30%'), ('drop_train_cells', '0.6', 'history cells dropped: 60%'),
             ('pool', 'retrieval(N=100)', 'pool: retrieval only (100)'), ('pool', 'classification(N=59)', 'pool: classification only (59)'),
             ('pool', 'clustering+sts+pair(N=81)', 'pool: clust.+STS+pair (81)'), ('pool', 'english-only(N=84)', 'pool: English only (84)'), ('pool', 'non-english(N=196)', 'pool: non-English (196)'),
             ('transform', 'none', 'scores: raw'), ('transform', 'logit', 'scores: logit-transformed')]
    kk = 10
    fig, ax = plt.subplots(1, 2, figsize=(7.0, 3.7))
    y = np.arange(len(order))[::-1]
    lab = []
    for yy, (c, l, name) in zip(y, order):
        g = t[(t.cond == c) & (t.level == l) & (t.k == kk)]
        gv = g[g.selector == 'greedy_var']
        if gv.empty: continue
        gv = gv.iloc[0]
        ax[0].errorbar([gv.rel_red], [yy], xerr=[[gv.rel_red - gv.lo], [gv.hi - gv.rel_red]], fmt='o', color=STY['greedy_var'][0], capsize=2, lw=1)
        ax[1].errorbar([gv.r2], [yy], xerr=[[gv.r2 - gv.r2lo], [gv.r2hi - gv.r2]], fmt='o', color=STY['greedy_var'][0], capsize=2, lw=1)
        ax[1].errorbar([gv.r2_random], [yy + 0.0], xerr=[[gv.r2_random - gv.r2_random_lo], [gv.r2_random_hi - gv.r2_random]], fmt='s', color=STY['random'][0], capsize=2, lw=1)
        lab.append(name)
    ax[0].set_yticks(y); ax[0].set_yticklabels([o[2] for o in order], fontsize=6.5); ax[0].axvline(0, color=INK2, lw=0.6)
    ax[0].set_xlabel('relative MSE reduction, greedy vs. random (k=10)')
    ax[1].set_yticks(y); ax[1].set_yticklabels([]); ax[1].set_xlabel(r'$R^2$ at $k=10$: greedy (circle), random (square)')
    for a_ in ax: style_ax(a_); a_.grid(True, axis='x'); a_.grid(False, axis='y'); a_.tick_params(axis='y', length=0)
    fig.tight_layout(); save(fig, 'conditions'); plt.close(fig)


# ------------------------------------------------------------------ synthetic (theory) figures
def synth_figs():
    fig, axs = plt.subplots(1, 4, figsize=(7.0, 2.1))
    e1 = pd.read_csv(f'{SYN}/e1_formula_check.csv')
    ax = axs[0]
    for s, col in [('random', STY['random'][0]), ('greedy', STY['greedy_var'][0])]:
        x = e1[e1.sel == s]
        ax.plot(x.formula, x.mc, 'o', color=col, label=s)
    lim = [1, 3.1]; ax.plot(lim, lim, color=INK2, lw=0.6, ls=':'); ax.set_xlabel('closed-form MSE'); ax.set_ylabel('Monte-Carlo MSE'); ax.legend(frameon=False); style_ax(ax)
    ax.set_title('(a) Prop. 1 vs. Monte Carlo', fontsize=7.5)
    e2 = pd.read_csv(f'{SYN}/e2_k_scaling.csv')
    ax = axs[1]
    cols = {1: '#2a78d6', 2: '#eb6834', 4: '#1baf7a', 8: '#e87ba4', 16: '#6250d6'}
    for r in (1, 2, 4, 8, 16):
        x = e2[(e2.r == r) & (e2.g == 10.0)]
        ax.plot(x.k / r, x.excess_random, color=cols[r], marker='o', label=f'r={r}')
        ax.plot(x.k / r, x.excess_greedy, color=cols[r], ls='--')
    ax.set_xscale('log'); ax.set_yscale('log'); ax.set_xlim(0.8, 60); ax.set_ylim(1e-3, 30); ax.set_xlabel('k / r'); ax.set_ylabel('excess MSE over noise floor'); ax.legend(frameon=False, ncol=1); style_ax(ax)
    ax.set_title('(b) random: solid, greedy: dashed', fontsize=7.5)
    ax = axs[2]
    x = e2[(e2.r == 4) & (e2.g == 10.0)]
    ax.plot(x.k, x.excess_random, 'o-', color=STY['random'][0], label='random (simulated)')
    ax.plot(x.k, x.jensen, color=INK, ls=':', label='lower bound')
    ax.plot(x.k, x.invwishart, color=INK, ls='--', label='upper bound r/(k-r-1)')
    ax.set_xscale('log'); ax.set_yscale('log'); ax.set_ylim(1e-3, 30); ax.set_xlabel('k  (r=4)'); ax.legend(frameon=False, fontsize=5.5); style_ax(ax); ax.set_title('(c) bounds of Prop. 2')
    a = pd.read_csv(f'{SYN}/e4a_ols_inflation.csv')
    ax = axs[3]
    ax.plot(a.predicted_inflation, a.measured_inflation, 'o', color=STY['kmedoids'][0]); lim = [0.95, 2.9]; ax.plot(lim, lim, color=INK2, ls=':')
    ax.set_xlabel('predicted inflation'); ax.set_ylabel('measured OLS / oracle MSE'); style_ax(ax); ax.set_title('(d) Prop. 4: OLS inflation', fontsize=7.5)
    fig.tight_layout(); save(fig, 'synthetic_theory'); plt.close(fig)
    # summary numbers
    e3 = pd.read_csv(f'{SYN}/e3_greedy_vs_opt.csv')
    summary['e3'] = dict(min_ratio=float(e3.V_ratio.min()), mean_ratio=float(e3.V_ratio.mean()), mean_random_ratio=float(e3.V_ratio_random.mean()),
                         bound_mean=float(e3.bound.mean()), tail_bound_violations=int((e3.F_opt < e3['tail'] - 1e-9).sum()), tail_tightness_mean=float((e3['tail'] / e3.F_opt).mean()), frac_ge_095=float((e3.V_ratio >= 0.95).mean()), n=int(len(e3)))
    e3b = pd.read_csv(f'{SYN}/e3b_greedy_vs_swap.csv')
    summary['e3b'] = dict(swap_improvement_mean=float((1 - e3b.F_swap / e3b.F_greedy).mean()), swap_improvement_max=float((1 - e3b.F_swap / e3b.F_greedy).max()),
                          greedy_vs_random=float((e3b.F_random / e3b.F_greedy).mean()),
                          pivot_vs_greedy=float((e3b.F_pivot / e3b.F_greedy).mean()), mi_vs_greedy=float((e3b.F_mi / e3b.F_greedy).mean()), central_vs_greedy=float((e3b.F_central / e3b.F_greedy).mean()))
    e1s = e1.assign(err=(e1.mc - e1.formula).abs()); summary['e1_max_abs_err'] = float(e1s.err.max())
    summary['e4a_max_rel_dev'] = float(((a.measured_inflation - a.predicted_inflation).abs() / a.predicted_inflation).max())
    summary['e4a_mean_abs_dev'] = float((a.measured_inflation - a.predicted_inflation).abs().mean())
    e4b = pd.read_csv(f'{SYN}/e4b_fa_vs_ols.csv')
    summary['e4b'] = e4b.groupby(['M', 'k'])[['fa', 'ols', 'oracle']].mean().round(3).reset_index().to_dict('records')
    e2s = e2[e2.k >= e2.r + 2]
    summary['e2_sandwich_frac'] = float(((e2s.excess_random >= e2s.jensen - 3 * e2s.excess_random_se - 1e-9) & (e2s.excess_random <= e2s.invwishart + 3 * e2s.excess_random_se + 1e-9)).mean()); summary['e2_cells'] = int(len(e2s))
    e6 = pd.read_csv(f'{SYN}/e6_k_star.csv'); summary['e6'] = dict(cells=int(len(e6)), within=int(((e6.k_star >= e6.lower - 1e-9) & (e6.k_star <= e6.upper + 1e-9)).sum()),
                                                                      max_excess_over_upper=float((e6.k_star - e6.upper).max()), greedy_over_random_ratio=dict(min=float((e6.k_star_greedy / e6.k_star).min()), median=float((e6.k_star_greedy / e6.k_star).median()), max=float((e6.k_star_greedy / e6.k_star).max())), r8_eps01=e6[(e6.r == 8) & (e6.eps == 0.1)].to_dict('records'))
    e5 = pd.read_csv(f'{SYN}/e5_gain_conditions.csv'); e5['gain'] = 1 - e5.F_greedy / e5.F_random
    t5 = e5[e5.k == 8].groupby(['r', 'g', 'kappa']).gain.mean().unstack('kappa').round(3)
    t5.to_csv(f'{TAB}/e5_gain_k8.csv'); summary['e5_gain_k8'] = t5.reset_index().to_dict('records')
    return


def extra_tables(T, Rr):
    """LaTeX tables: protocols (random split / new organisation / later release), predictors, protocol pitfall, aggregate error."""
    KS = (1, 3, 5, 10, 20)
    # --- (1) shift protocols
    out = ['\\begin{tabular}{llccccc}\\toprule', 'Protocol & Selector & ' + ' & '.join(f'$k{{=}}{k}$' for k in KS) + ' \\\\\\midrule']
    for sp, nm in [('rand', 'random models'), ('org', 'new organisation'), ('time', 'later release')]:
        t = T[(T.dataset == 'mteb_main') & (T.split == sp) & (T.predictor == 'gauss')]
        first = True
        for s_ in ['random', 'popular', 'kmedoids', 'greedy_var']:
            x = t[t.selector == s_].set_index('k')
            cells = [f"{x.loc[k].r2:.2f}" if k in x.index else '--' for k in KS]
            out.append(f"{nm if first else ''} & {STY[s_][3]} & " + ' & '.join(cells) + ' \\\\'); first = False
        out.append('\\midrule')
    out[-1] = '\\bottomrule'; out.append('\\end{tabular}')
    open(f'{TAB}/shift.tex', 'w').write('\n'.join(out) + '\n')
    # --- (2) predictors, MTEB-main
    pt = pd.read_csv(f'{TAB}/predictors.csv'); pt = pt[pt.dataset == 'mteb_main']
    KP = (1, 5, 10, 20, 40)
    out = ['\\begin{tabular}{llccccc}\\toprule', 'Selection & Predictor & ' + ' & '.join(f'$k{{=}}{k}$' for k in KP) + ' \\\\\\midrule']
    nm = {'avgshift': 'AvgShift', 'knn': 'kNN', 'isvd': 'ISVD', 'fa': 'FA', 'gauss': 'Gauss', 'hybrid': 'Hybrid'}
    for s_ in ['random', 'greedy_var']:
        first = True
        for pr in ['avgshift', 'knn', 'isvd', 'fa', 'gauss', 'hybrid']:
            x = pt[(pt.selector == s_) & (pt.predictor == pr)].set_index('k')
            out.append(f"{STY[s_][3] if first else ''} & {nm[pr]} & " + ' & '.join(f"{x.loc[k].r2:.2f}" for k in KP) + ' \\\\'); first = False
        out.append('\\midrule')
    out[-1] = '\\bottomrule'; out.append('\\end{tabular}')
    open(f'{TAB}/predictors.tex', 'w').write('\n'.join(out) + '\n')
    # --- (3) protocol pitfall
    rows = []
    for ds in ['helm_fine', 'mteb_main']:
        p = f'{RES}/bias__{ds}.parquet'
        if not os.path.exists(p): continue
        b = pd.read_parquet(p); g = b.groupby(['selector', 'k'])[['mse_fixed', 'mse_complement']].mean().reset_index(); g['dataset'] = ds; rows.append(g)
    if rows:
        B = pd.concat(rows); B.to_csv(f'{TAB}/bias.csv', index=False)
        out = ['\\begin{tabular}{llccccc}\\toprule', 'Dataset & Scoring targets & Selector & ' .replace('Selector & ', '') + ' $k_1$ & $k_2$ & $k_3$ \\\\\\midrule'][:0]
        out = ['\\begin{tabular}{lllccc}\\toprule', 'Dataset & Targets & Selector & small $k$ & mid $k$ & large $k$ \\\\\\midrule']
        for ds, ksel in [('helm_fine', (2, 5, 12)), ('mteb_main', (2, 10, 40))]:
            for col, cn in [('mse_fixed', 'fixed $T_0$'), ('mse_complement', 'complement $C\\!\\setminus\\!S$')]:
                for s_ in ['random', 'greedy_var']:
                    x = B[(B.dataset == ds) & (B.selector == s_)].set_index('k')[col]
                    out.append(f"{NAMES[ds]} ($k{{=}}{ksel[0]},{ksel[1]},{ksel[2]}$) & {cn} & {STY[s_][3]} & " + ' & '.join(f'{x.loc[k]:.2f}' for k in ksel) + ' \\\\')
            out.append('\\midrule')
        out[-1] = '\\bottomrule'; out.append('\\end{tabular}')
        open(f'{TAB}/bias.tex', 'w').write('\n'.join(out) + '\n')
    # --- (4) aggregate error (|error of the mean of the held-out scores|, in score points), MTEB-main random split
    d = load('mteb_main', 'rand'); d, ks = balanced(d)
    d0 = d[(d.predictor == 'mean') & (d.selector == 'random')]
    d = d[d.predictor == 'gauss']
    pm = per_model(d, 'agg_err'); pr_ = per_model(d, 'mse_raw')
    rows = []
    for s_ in ['random', 'greedy_var']:
        for k in (1, 3, 5, 10, 20):
            a = pm[(pm.selector == s_) & (pm.k == k)].agg_err.values; m = pr_[(pr_.selector == s_) & (pr_.k == k)].mse_raw.values
            lo, hi = np.percentile([np.random.default_rng(i).choice(a, len(a)).mean() for i in range(500)], [2.5, 97.5])
            rows.append(dict(selector=s_, k=k, mean_abs_err_of_average=a.mean(), lo=lo, hi=hi, rmse_per_benchmark=np.sqrt(m.mean())))
    pm0 = per_model(d0, 'agg_err'); pr0 = per_model(d0, 'mse_raw')
    rows.append(dict(selector='mean-baseline', k=0, mean_abs_err_of_average=pm0[pm0.k == 1].agg_err.mean(), lo=np.nan, hi=np.nan, rmse_per_benchmark=np.sqrt(pr0[pr0.k == 1].mse_raw.mean())))
    pd.DataFrame(rows).to_csv(f'{TAB}/aggregate_error_mteb_main.csv', index=False)
    # --- (5) k needed (compact)
    kn = pd.read_csv(f'{TAB}/k_needed.csv')
    out = ['\\begin{tabular}{llccc}\\toprule', 'Dataset (protocol) & Selector & $R^2\\ge0.6$ & $R^2\\ge0.7$ & $R^2\\ge0.75$ \\\\\\midrule']
    for (ds, sp), g in kn.groupby(['dataset', 'split'], sort=False):
        if ds not in ('mteb_main', 'mteb_dense', 'mteb_eng', 'helm_fine', 'openllm'): continue
        first = True
        for s_ in ['random', 'greedy_var']:
            x = g[g.selector == s_].set_index('r2_target').k_needed
            cells = [(str(int(x.loc[th])) if th in x.index and not np.isnan(x.loc[th]) else f'$>${int(g.kmax.iloc[0])}') for th in (0.6, 0.7, 0.75)]
            out.append(f"{NAMES[ds] + ' (' + sp + ')' if first else ''} & {STY[s_][3]} & " + ' & '.join(cells) + ' \\\\'); first = False
    out.append('\\bottomrule'); out.append('\\end{tabular}')
    open(f'{TAB}/k_needed.tex', 'w').write('\n'.join(out) + '\n')


def rank_corr_table():
    """Per-benchmark Spearman correlation between predicted and actual scores across held-out models (pooled predictions stored for k in 5,10,20)."""
    rows = []
    for ds in ['mteb_main', 'mteb_dense', 'helm_fine']:
        p = f'{RES}/{ds}__rand.pkl'
        if not os.path.exists(p): continue
        pk = pickle.load(open(p, 'rb'))
        acc = {}
        for fo in pk['pooled']:
            df = pd.DataFrame(fo['rows'], columns=['model', 'bench', 'sel', 'k', 'pred', 'true'])
            for (sel_, k, b), g in df.groupby(['sel', 'k', 'bench']):
                if len(g) >= 8 and g.pred.std() > 0 and g.true.std() > 0:
                    acc.setdefault((sel_, k), []).append(stats.spearmanr(g.pred, g.true)[0])
        for (sel_, k), v in sorted(acc.items()):
            rows.append(dict(dataset=ds, selector=sel_, k=k, mean_spearman=float(np.mean(v)), n_benchmark_folds=len(v)))
    t = pd.DataFrame(rows); t.to_csv(f'{TAB}/rank_corr.csv', index=False); return t


def stability():
    """Stability of the greedy selection across the 15 training folds of the MTEB-main random splits (all columns as candidates)."""
    import itertools
    df = pd.read_csv(f'{PROC}/mteb_main.csv', index_col=0); X = df.values; M, N = X.shape
    sets = {5: [], 10: [], 20: []}; freq = np.zeros(N)
    for r in range(3):
        perm = np.random.default_rng(100 + r).permutation(M); folds = np.array_split(perm, 5)
        for f in range(5):
            tr = np.concatenate([folds[g] for g in range(5) if g != f])
            mu = np.nanmean(X[tr], 0); sd = np.nanstd(X[tr], 0); C = P.pairwise_corr((X[tr] - mu) / sd); C = 0.95 * C + 0.05 * np.eye(N)
            o = sel.greedy_var(C, 20)
            for k in sets: sets[k].append(set(o[:k]))
            freq[o[:10]] += 1
    out = {}
    for k, L in sets.items():
        jac = [len(a & b) / len(a | b) for a, b in itertools.combinations(L, 2)]
        out[f'k={k}'] = dict(mean_jaccard=float(np.mean(jac)), random_jaccard_expected=float(k / (2 * N - k)))
    top = np.argsort(-freq)[:10]
    out['top_picks_k10'] = [(df.columns[j], int(freq[j])) for j in top]
    summary['greedy_stability'] = out


def appendix_tables(T):
    # --- predictors with CIs and paired difference to Gauss (MTEB-main, random splits)
    d = load('mteb_main', 'rand'); d, ks = balanced(d); pm = per_model(d); B = wide(pm, 'mean', 'random').values
    KP = (1, 5, 10, 20, 40); ji = [ks.index(k) for k in KP]
    nm = {'avgshift': 'AvgShift', 'knn': 'kNN', 'isvd': 'ISVD', 'fa': 'FA', 'gauss': 'Gauss', 'hybrid': 'Hybrid'}
    out = ['\\begin{tabular}{llccccc}\\toprule', 'Selection & Predictor & ' + ' & '.join(f'$k{{=}}{k}$' for k in KP) + ' \\\\\\midrule']
    for s_ in ['random', 'greedy_var']:
        G = wide(pm, 'gauss', s_).values; first = True
        for pr in ['avgshift', 'knn', 'isvd', 'fa', 'gauss', 'hybrid']:
            A = wide(pm, pr, s_).values
            if pr == 'gauss':
                r2, lo, hi = ci_ratio(A, B)
                cells = [f"{r2[j]:.3f} [{lo[j]:.3f},{hi[j]:.3f}]" for j in ji]
            else:
                idx = boot_idx(A.shape[0], np.random.default_rng(1))
                bm = (G[idx].mean(1) - A[idx].mean(1)) / B[idx].mean(1)
                dm = (G.mean(0) - A.mean(0)) / B.mean(0); l_ = np.percentile(bm, 2.5, 0); h_ = np.percentile(bm, 97.5, 0)
                cells = [f"{dm[j]:+.3f} [{l_[j]:+.3f},{h_[j]:+.3f}]" for j in ji]
            out.append(f"{STY[s_][3] if first else ''} & {nm[pr]} & " + ' & '.join(cells) + ' \\\\'); first = False
        out.append('\\midrule')
    out[-1] = '\\bottomrule'; out.append('\\end{tabular}')
    open(f'{TAB}/ci_pred.tex', 'w').write('\n'.join(out) + '\n')
    # --- oracle covariance vs training-row covariance (relative MSE reduction of oracle-greedy over greedy)
    rows = []
    for ds in ['mteb_main', 'mteb_dense', 'mteb_eng', 'helm_fine']:
        dd = load(ds, 'rand'); dd, kk = balanced(dd); p = per_model(dd)
        G = wide(p, 'gauss', 'greedy_var').values; O = wide(p, 'gauss', 'greedy_var@oracle').values; F = wide(p, 'gauss', 'greedy_var@fa').values
        for nm_, A in [('oracle covariance', O), ('FA covariance', F)]:
            rr, lo, hi = ci_rel_reduction(A, G)
            rows.append((NAMES[ds], nm_, [(k, rr[kk.index(k)], lo[kk.index(k)], hi[kk.index(k)]) for k in (1, 3, 5, 10, 20) if k in kk]))
    out = ['\\begin{tabular}{llccccc}\\toprule', 'Dataset & Selection covariance & $k{=}1$ & $k{=}3$ & $k{=}5$ & $k{=}10$ & $k{=}20$ \\\\\\midrule']
    for ds_, nm_, lst in rows:
        cells = [f"{100 * v:+.1f}\\,[{100 * l:+.1f},{100 * h:+.1f}]" for _, v, l, h in lst]
        cells += ['--'] * (5 - len(cells))
        out.append(f"{ds_} & {nm_} & " + ' & '.join(cells) + ' \\\\')
    out.append('\\bottomrule'); out.append('\\end{tabular}')
    open(f'{TAB}/oracle.tex', 'w').write('\n'.join(out) + '\n')
    # --- e5 table
    e5 = pd.read_csv(f'{TAB}/e5_gain_k8.csv')
    out = ['\\begin{tabular}{rrcccc}\\toprule', '$r$ & $g$ & $\\kappa{=}0$ & $\\kappa{=}0.5$ & $\\kappa{=}1$ & $\\kappa{=}1.5$ \\\\\\midrule']
    for _, r_ in e5.iterrows():
        out.append(f"{int(r_.r)} & {r_.g:g} & " + ' & '.join(f"{100 * r_[c]:.0f}\\%" for c in ['0.0', '0.5', '1.0', '1.5']) + ' \\\\')
    out.append('\\bottomrule'); out.append('\\end{tabular}')
    open(f'{TAB}/e5.tex', 'w').write('\n'.join(out) + '\n')


if __name__ == '__main__':
    dataset_table()
    synth_figs()
    stability()
    spectral_fig()
    greedy_picks_table()
    if os.path.exists(f'{RES}/mteb_main__rand.parquet'):
        main_curves()
        T, Rr = result_tables()
        latex_main_table(T, Rr)
        predictor_table()
        calibration_fig()
        kn = k_needed(T)
        conditions_fig()
        extra_tables(T, Rr)
        appendix_tables(T)
        rank_corr_table()
    json.dump(summary, open('/work/out/summary.json', 'w'), indent=1, default=float)
    print('ok')
