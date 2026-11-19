"""Figures/tables for the paper. Usage: python make_figs.py [which]"""
import sys, os
sys.path.insert(0, "/work/code")
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats
from analysis_lib import *
SIM = "/work/results/sim"; FIG = "/work/paper/figs"; TAB = "/work/paper/tables"
os.makedirs(FIG, exist_ok=True); os.makedirs(TAB, exist_ok=True)
C = dict(grid='#0072B2', random='#E69F00', sh='#009E73', minibatch='#CC79A7', greedy='#D55E00', k='#444444')
from matplotlib.ticker import NullFormatter
plt.rcParams.update({'font.size': 8, 'axes.titlesize': 8, 'axes.labelsize': 8, 'legend.fontsize': 7, 'xtick.labelsize': 7, 'ytick.labelsize': 7,
                     'axes.spines.top': False, 'axes.spines.right': False, 'figure.dpi': 150, 'savefig.bbox': 'tight'})

def mK(K, ns=400000, seed=0):
    return np.random.default_rng(seed).standard_normal((ns // 10, K)).max(1).mean() if K > 1 else 0.0

def fig_synth_collapse():
    d = pd.read_parquet(f"{SIM}/synth_sweep.parquet")
    g = d.groupby(['K', 'tau', 'sd_int', 'n']).agg(gap=('gap', 'mean'), sd_theta=('sd_theta', 'mean'), sig_n=('sig_n', 'mean'), corr=('corr', 'mean')).reset_index()
    g['ngap'] = g.gap / g.sig_n; g['snr'] = g.sd_theta / g.sig_n
    fig, ax = plt.subplots(1, 2, figsize=(6.8, 2.4))
    cols = plt.cm.viridis(np.linspace(0, 0.9, 5))
    for c, K in zip(cols, (2, 5, 10, 40, 160)):
        s = g[(g.K == K) & (g.sd_int == 0.8)]
        ax[0].scatter(s.snr, s.ngap, s=6, color=c, label=f'K={K}', alpha=.8)
        z = s[s.tau == 0]; pred = np.sqrt(1 - z['corr'].mean()) * mK(K)
        ax[0].axhline(pred, color=c, lw=.6, ls=':')
    ax[0].set_xscale('log'); ax[0].set_xlabel(r'signal-to-noise  $\mathrm{sd}(\theta_k)/\sigma_n$'); ax[0].set_ylabel(r'normalised optimism  gap$/\sigma_n$'); ax[0].legend(frameon=False, ncol=2)
    ax[0].set_title('(a) synthetic: collapse onto SNR; dotted: $\\sqrt{1-\\rho}\\,m_K$')
    # (b) effect of correlation at tau=0
    z = g[(g.tau == 0) & (g.n == 100)]
    for c, K in zip(cols, (2, 5, 10, 40, 160)):
        s = z[z.K == K].sort_values('corr'); ax[1].plot(s['corr'], s.ngap, 'o-', color=c, ms=3, lw=.8)
        rr = np.linspace(0, .9, 20); ax[1].plot(rr, np.sqrt(1 - rr) * mK(K), color=c, ls=':', lw=.6)
    ax[1].set_xlabel(r'mean pairwise outcome correlation $\rho$'); ax[1].set_ylabel(r'gap$/\sigma_n$ (equal-quality configs)'); ax[1].set_title('(b) equal configs: gap $=\\sigma_n\\sqrt{1-\\rho}\\,m_K$')
    fig.savefig(f"{FIG}/synth_collapse.pdf"); plt.close(fig)
    return g

WN = {'q15': 'World A: 1.5B, prompt/demo ($K{=}40$)', 'b05': 'World B: 0.5B, format/demo ($K{=}40$)', 'mix': 'World A$\\cup$B ($K{=}80$)', 'b15': 'World C: 1.5B, format/demo ($K{=}40$)', 's17': 'World D: SmolLM2-1.7B, format/demo ($K{=}40$)'}
def world_Y(w):
    if w == 'mix': return np.concatenate([np.load('/work/results/world_q15.npy'), np.load('/work/results/world_b05.npy')])
    return np.load(f'/work/results/world_{w}.npy')

def world_stats(w):
    Y = world_Y(w); th = Y.mean(1); C = np.corrcoef(Y)
    return dict(K=Y.shape[0], N=Y.shape[1], mean=th.mean(), sd=th.std(), best=th.max(), rho=C[np.triu_indices(len(th), 1)].mean())

def fig_gap(worlds=('q15', 'b05', 'mix'), fname='gap_vs_n'):
    fig, axs = plt.subplots(1, len(worlds), figsize=(6.9, 2.2), sharey=True)
    for ax, w in zip(np.atleast_1d(axs), worlds):
        d = pd.read_parquet(f"{SIM}/gap_{w}.parquet"); d['gap'] = (d.naive - d.theta) * 100
        for o in ('grid', 'random', 'sh', 'minibatch', 'greedy'):
            g = d[d.opt == o].groupby('n').gap.agg(['mean', 'sem'])
            ax.errorbar(g.index, g['mean'], yerr=1.96 * g['sem'], color=C[o], marker='o', ms=2.5, lw=1, capsize=1, label=o)
        ax.set_xscale('log'); ax.set_yscale('log'); ax.set_xlabel('dev-set size $n$'); ax.set_title(WN[w], fontsize=7); ax.set_yticks([0.5, 1, 2, 4, 8]); ax.set_yticklabels([0.5, 1, 2, 4, 8]); ax.yaxis.set_minor_formatter(NullFormatter()); ax.set_ylim(0.4, 13)
        ax.set_xticks([25, 50, 100, 200, 400, 800]); ax.set_xticklabels([25, 50, 100, 200, 400, 800]); ax.xaxis.set_minor_formatter(NullFormatter())
        ax.plot([25, 800], [d[(d.opt == 'grid') & (d.n == 25)].gap.mean() * np.sqrt(25 / np.array([25, 800]))[i] for i in range(2)], color='#999', ls=':', lw=.8)
    np.atleast_1d(axs)[0].set_ylabel('reported $-$ true accuracy (points)'); np.atleast_1d(axs)[0].legend(frameon=False)
    fig.savefig(f"{FIG}/{fname}.pdf"); plt.close(fig)

def gauss_pred(Y, n, R=20000, seed=0):
    """Gaussian plug-in prediction of exhaustive-search optimism: dev means ~ N(theta, Cov(Y)/n) with theta, Cov taken from the world."""
    rng = np.random.default_rng(seed); th = Y.mean(1); K = len(th)
    L = np.linalg.cholesky(np.cov(Y) / n + 1e-12 * np.eye(K))
    eps = rng.standard_normal((R, K)) @ L.T
    k = (th + eps).argmax(1); return eps[np.arange(R), k].mean()

def fig_collapse_real(worlds=('q15', 'b05', 'b15', 'mix')):
    syn = fig_synth_collapse_data()
    fig, ax = plt.subplots(1, 2, figsize=(6.8, 2.5))
    mk = dict(q15='o', b05='s', b15='^', mix='D'); rows = []
    for w in worlds:
        try: d = pd.read_parquet(f"{SIM}/gap_{w}.parquet")
        except Exception: continue
        Y = world_Y(w); th = Y.mean(1); st = world_stats(w)
        for n, g in d[d.opt == 'grid'].groupby('n'):
            sig = np.sqrt(np.mean(th * (1 - th)) / n); gap = (g.naive - g.theta).mean()
            pred = gauss_pred(Y, n)
            rows.append(dict(world=w, n=n, gap=gap, pred=pred, ngap=gap / sig, snr=th.std() / sig, K=len(th), rho=st['rho']))
            ax[0].scatter(th.std() / sig, gap / sig, marker=mk[w], s=14, color=plt.cm.viridis({'q15': .1, 'b05': .45, 'b15': .7, 'mix': .95}[w]), label=w if n == 25 else None)
    R = pd.DataFrame(rows); R.to_csv(f"{SIM}/collapse_real.csv", index=False)
    ax[0].set_xscale('log'); ax[0].set_xlabel(r'SNR $=\mathrm{sd}(\theta_k)/\sigma_n$'); ax[0].set_ylabel(r'gap$/\sigma_n$ (grid search, real worlds)'); ax[0].legend(frameon=False, title='world')
    ax[0].set_title('(a) real worlds, $n\\in\\{25,\\dots,800\\}$')
    for w in worlds:
        s = R[R.world == w]
        if len(s): ax[1].scatter(s.pred * 100, s.gap * 100, marker=mk[w], s=14, color=plt.cm.viridis({'q15': .1, 'b05': .45, 'b15': .7, 'mix': .95}[w]))
    lim = [0.3, 40]; ax[1].plot(lim, lim, color='#888', lw=.8, ls=':'); ax[1].set_xscale('log'); ax[1].set_yscale('log')
    ax[1].set_xlabel('Gaussian plug-in prediction (points)'); ax[1].set_ylabel('measured gap (points)'); ax[1].set_title('(b) predicted vs measured optimism')
    fig.savefig(f"{FIG}/collapse_real.pdf"); plt.close(fig); return R

def fig_synth_collapse_data(): return None

def fig_protocols(w='b05'):
    d = pd.read_parquet(f"{SIM}/gap_{w}.parquet"); d = d[d.opt == 'grid']
    names = ['Naive (dev score)', 'Holdout split (50/50)', '5-fold cross-fit', 'Replay bootstrap (opt.)', 'Empirical Bayes', 'Ladder ($n^{-1/2}$)']
    col = dict(zip(names, ['#444444', '#0072B2', '#56B4E9', '#E69F00', '#D55E00', '#999999']))
    T = {n: method_table(g).set_index('method') for n, g in d.groupby('n')}
    fig, ax = plt.subplots(1, 3, figsize=(6.9, 2.2))
    ns = sorted(T)
    for m in names:
        ax[0].plot(ns, [T[n].loc[m, 'bias'] * 100 for n in ns], marker='o', ms=2.5, lw=1, color=col[m], label=m)
        ax[1].plot(ns, [T[n].loc[m, 'rmse'] * 100 for n in ns], marker='o', ms=2.5, lw=1, color=col[m])
    for m, c, ls in [('Naive (dev score)', '#444444', '-'), ('Holdout split (50/50)', '#0072B2', '-'), ('Empirical Bayes', '#D55E00', '-'), ('Max-t simultaneous', '#009E73', '-'), ('Conditional (winner)', '#CC79A7', '-')]:
        ax[2].plot(ns, [T[n].loc[m, 'cover'] for n in ns], marker='o', ms=2.5, lw=1, color=c, label=m)
    ax[2].axhline(.95, color='#888', ls=':', lw=.8)
    for a in ax: a.set_xscale('log'); a.set_xlabel('$n$'); a.set_xticks(ns); a.set_xticklabels(ns); a.xaxis.set_minor_formatter(NullFormatter())
    ax[0].set_ylabel('bias (points)'); ax[1].set_ylabel('RMSE (points)'); ax[2].set_ylabel('95\\% interval coverage'); ax[1].set_yscale('log')
    ax[0].axhline(0, color='#888', lw=.5); ax[0].legend(frameon=False, fontsize=5.5); ax[2].legend(frameon=False, fontsize=5.5, loc='lower right')
    fig.savefig(f"{FIG}/protocols_{w}.pdf"); plt.close(fig)

DISP = {'q15': 'A', 'b05': 'B', 'b15': 'C', 's17': 'D', 'mix': 'A$\\cup$B'}
WCOL = dict(q15='#0072B2', b05='#D55E00', b15='#009E73', s17='#E69F00', mix='#CC79A7')
def fig_ksweep(worlds):
    fig, axs = plt.subplots(1, len(worlds), figsize=(6.9, 2.2), sharey=True)
    axs = np.atleast_1d(axs); cols = plt.cm.viridis(np.linspace(0, .9, 5))
    for ax, w in zip(axs, worlds):
        d = pd.read_parquet(f"{SIM}/ksweep_{w}.parquet"); d['gap'] = (d.naive - d.theta) * 100
        for c, n in zip(cols, (50, 100, 200, 400, 800)):
            g = d[d.n == n].groupby('K').gap.agg(['mean', 'sem']); g = g[g.index > 1]
            ax.errorbar(g.index, g['mean'], yerr=1.96 * g['sem'], color=c, marker='o', ms=2.5, lw=1, capsize=1, label=f'n={n}')
        Y = world_Y(w); st = world_stats(w); th = Y.mean(1)
        for c, n in zip(cols[1:2], (100,)):
            sig = np.sqrt(np.mean(th * (1 - th)) / n); Ks = np.array([2, 4, 8, 16, 32, 40])
            ax.plot(Ks, [100 * sig * np.sqrt(1 - st['rho']) * mK(k) for k in Ks], color=c, ls=':', lw=1)
        ax.set_xscale('log'); ax.set_xlabel('configs searched $K$'); ax.set_title(WN[w], fontsize=7); ax.set_xticks([2, 4, 8, 16, 32]); ax.set_xticklabels([2, 4, 8, 16, 32]); ax.xaxis.set_minor_formatter(NullFormatter())
    axs[0].set_ylabel('reported $-$ true accuracy (points)'); axs[0].legend(frameon=False, ncol=1)
    fig.savefig(f"{FIG}/gap_vs_K.pdf"); plt.close(fig)

def conclusions_tables(w):
    c = pd.read_parquet(f"{SIM}/conclusions_{w}.parquet"); th = world_Y(w).mean(1)
    l = c[c.kind == 'lift'].copy(); l['base'] = l.base.astype(int); l['rank'] = l.base.map(lambda x: int((th > th[x]).sum()))
    l['claim'] = l.naive_z > 1.645; l['claim_s'] = l.split_z > 1.645
    l['false'] = l.claim & (l.true_lift <= 0); l['false_s'] = l.claim_s & (l.split_k_true_lift <= 0)
    K = len(th); l['rb'] = pd.cut(l['rank'], [-1, 0, K // 8 - 1, K // 4 - 1, K // 2 - 1, K - 1], labels=['best', 'top 12%', 'top 25%', 'top 50%', 'bottom 50%'])
    b = c[c.kind == 'budget'].copy(); b['claim'] = b.naive_z > 1.645; b['claim_s'] = b.split_z > 1.645
    b['fc'] = b.claim & (b.true_diff <= 0); b['fc_s'] = b.claim_s & (b.split_true_diff <= 0)
    return l, b

def fig_conclusions(worlds):
    fig, ax = plt.subplots(1, 3, figsize=(6.9, 2.3))
    for w in worlds:
        l, b = conclusions_tables(w); col = WCOL[w]
        g = l[l.n == 100].groupby('rb', observed=True)[['false', 'false_s']].mean()
        x = np.arange(len(g)); ax[0].plot(x, g['false'], color=col, marker='o', ms=3, lw=1, label=DISP[w]); ax[0].plot(x, g['false_s'], color=col, marker='s', ms=3, lw=1, ls='--')
        ax[0].set_xticks(x); ax[0].set_xticklabels(g.index, rotation=30, ha='right', fontsize=6)
        m = l[(l['rank'] >= len(world_Y(w)) // 4) & (l['rank'] < len(world_Y(w)) // 2)].groupby('n')[['naive_lift', 'true_lift']].mean() * 100
        ax[1].plot(m.index, m.naive_lift, color=col, marker='o', ms=3, lw=1); ax[1].plot(m.index, m.true_lift, color=col, marker='o', ms=3, lw=1, ls='--', mfc='white')
        bb = b[(b.KA == 32) & (b.KB == 4)].groupby('n')[['naive_diff', 'true_diff']].mean() * 100
        ax[2].plot(bb.index, bb.naive_diff, color=col, marker='o', ms=3, lw=1); ax[2].plot(bb.index, bb.true_diff, color=col, marker='o', ms=3, lw=1, ls='--', mfc='white')
    ax[0].axhline(.05, color='#888', ls=':', lw=.8); ax[0].set_ylabel('false-claim rate (nominal 5\\%)'); ax[0].set_xlabel('true rank of the baseline'); ax[0].set_title('(a) "tuned beats baseline", $n{=}100$\nsolid: naive test, dashed: holdout', fontsize=7)
    ax[1].set_xscale('log'); ax[1].set_ylabel('lift (points)'); ax[1].set_xlabel('$n$'); ax[1].set_title('(b) lift over a top-25--50\\% baseline\nsolid: reported, dashed: true', fontsize=7)
    ax[2].set_xscale('log'); ax[2].set_ylabel('A$-$B (points)'); ax[2].set_xlabel('$n$'); ax[2].set_title('(c) A searches 32, B searches 4 configs\nsolid: reported, dashed: true', fontsize=7)
    for a in ax[1:]: a.set_xticks([50, 100, 200, 400]); a.set_xticklabels([50, 100, 200, 400]); a.xaxis.set_minor_formatter(NullFormatter())
    ax[0].legend(frameon=False, fontsize=6)
    fig.savefig(f"{FIG}/conclusions.pdf"); plt.close(fig)

def fig_split(worlds):
    fig, ax = plt.subplots(1, 2, figsize=(6.0, 2.2))
    for w in worlds:
        d = pd.read_parquet(f"{SIM}/gap_{w}.parquet"); d = d[d.opt == 'grid']; col = WCOL[w]
        for f, ls in ((0.3, ':'), (0.5, '-'), (0.7, '--')):
            g = d.groupby('n').apply(lambda x: pd.Series(dict(cost=(x.theta - x[f'split{f}_k_theta']).mean() * 100, rmse=np.sqrt(((x[f'split{f}_est'] - x[f'split{f}_k_theta']) ** 2).mean()) * 100)))
            ax[0].plot(g.index, g.cost, color=col, ls=ls, marker='o', ms=2, lw=1, label=f'{w} f={f}' if w == worlds[0] else None)
            ax[1].plot(g.index, g.rmse, color=col, ls=ls, marker='o', ms=2, lw=1)
    for a in ax: a.set_xscale('log'); a.set_xlabel('$n$'); a.set_xticks([25, 50, 100, 200, 400, 800]); a.set_xticklabels([25, 50, 100, 200, 400, 800]); a.xaxis.set_minor_formatter(NullFormatter())
    ax[0].set_ylabel('deployed-accuracy cost of splitting (pts)'); ax[1].set_ylabel('RMSE of the held-out score (pts)'); ax[1].set_yscale('log'); ax[0].legend(frameon=False, fontsize=6)
    fig.savefig(f"{FIG}/split_tradeoff.pdf"); plt.close(fig)

def optsens_table(w, n=100):
    d = pd.read_parquet(f"{SIM}/optsens_{w}.parquet"); d = d[d.n == n].copy(); d['gap'] = (d.naive - d.theta) * 100; d['regret'] = (d.theta_star - d.theta) * 100
    K = world_Y(w).shape[0]
    def budget(r):
        import ast; kw = ast.literal_eval(r.kw)
        if r.opt == 'random': return kw['B']
        if r.opt == 'sh': return kw['frac'] * K
        if r.opt == 'minibatch': return kw['T'] * kw['bfrac'] + r.nvis
        return r.nvis
    d['budget'] = d.apply(budget, axis=1)
    g = d.groupby(['opt', 'kw']).agg(gap=('gap', 'mean'), se=('gap', 'sem'), regret=('regret', 'mean'), budget=('budget', 'mean')).reset_index()
    return g

def fig_optsens(worlds):
    fig, ax = plt.subplots(1, 2, figsize=(6.6, 2.3))
    mk = dict(random='o', sh='s', minibatch='^', greedy='D')
    for w in worlds:
        g = optsens_table(w); d = pd.read_parquet(f"{SIM}/gap_{w}.parquet"); gg = d[(d.opt == 'grid') & (d.n == 100)]
        for o in mk:
            s = g[g.opt == o].sort_values('budget')
            ax[0].scatter(s.budget, s.gap, marker=mk[o], s=10, color=WCOL[w], alpha=.85, label=o if w == worlds[0] else None)
            ax[1].scatter(s.budget, s.regret, marker=mk[o], s=10, color=WCOL[w], alpha=.85)
        ax[0].scatter([len(world_Y(w))], [((gg.naive - gg.theta) * 100).mean()], marker='*', s=30, color=WCOL[w]); ax[1].scatter([len(world_Y(w))], [((gg.theta_star - gg.theta) * 100).mean()], marker='*', s=30, color=WCOL[w])
    for a in ax: a.set_xscale('log'); a.set_xlabel('search effort (full-dev-set passes, $n{=}100$)')
    ax[0].set_ylabel('reported $-$ true accuracy (pts)'); ax[1].set_ylabel('regret $\\theta^\\star-\\theta_{\\hat k}$ (pts)'); ax[0].legend(frameon=False, fontsize=6, title='marker: optimizer;  star: exhaustive', title_fontsize=5.5)
    fig.savefig(f"{FIG}/search_effort.pdf"); plt.close(fig)


def fig_theory(worlds=('q15', 'b05', 'mix')):
    d = pd.read_parquet(f"{SIM}/synth_sweep.parquet")
    g = d.groupby(['K', 'tau', 'sd_int', 'n']).agg(gap=('gap', 'mean'), sd_theta=('sd_theta', 'mean'), sig_n=('sig_n', 'mean'), corr=('corr', 'mean')).reset_index()
    g['ngap'] = g.gap / g.sig_n; g['snr'] = g.sd_theta / g.sig_n
    fig, ax = plt.subplots(1, 3, figsize=(6.9, 2.3)); cols = plt.cm.viridis(np.linspace(0, 0.9, 5)); Ks = (2, 5, 10, 40, 160)
    for c, K in zip(cols, Ks):
        s_ = g[(g.K == K) & (g.sd_int == 0.8)]
        ax[0].scatter(s_.snr, s_.ngap, s=5, color=c, label=f'$K$={K}', alpha=.8)
        ax[0].axhline(np.sqrt(1 - s_[s_.tau == 0]['corr'].mean()) * mK(K), color=c, lw=.6, ls=':')
    ax[0].set_xscale('log'); ax[0].set_xlabel(r'SNR $=\mathrm{sd}(\theta_k)/\sigma_n$'); ax[0].set_ylabel(r'gap$/\sigma_n$'); ax[0].legend(frameon=False, ncol=5, fontsize=5, loc='upper center', bbox_to_anchor=(0.5, 1.0), handletextpad=0.1, columnspacing=0.6); ax[0].set_ylim(0.2, 2.9); ax[0].set_title('(a) synthetic: optimism vs SNR', fontsize=7)
    z = g[(g.tau == 0) & (g.n == 100)]
    for c, K in zip(cols, Ks):
        s_ = z[z.K == K].sort_values('corr'); ax[1].plot(s_['corr'], s_.ngap, 'o', color=c, ms=3)
        rr = np.linspace(0, .9, 20); ax[1].plot(rr, np.sqrt(1 - rr) * mK(K), color=c, ls=':', lw=.8)
    ax[1].set_xlabel(r'outcome correlation $\rho$'); ax[1].set_ylabel(r'gap$/\sigma_n$ (equal configs)'); ax[1].set_title('(b) dotted: $\\sqrt{1-\\rho}\\,m_K$', fontsize=7)
    mk = dict(q15='o', b05='s', mix='D', b15='^', s17='v'); rows = []
    for w in worlds:
        dd = pd.read_parquet(f"{SIM}/gap_{w}.parquet"); Y = world_Y(w)
        for n, gg in dd[dd.opt == 'grid'].groupby('n'):
            rows.append(dict(world=w, n=n, gap=(gg.naive - gg.theta).mean(), pred=gauss_pred(Y, n)))
            ax[2].scatter(rows[-1]['pred'] * 100, rows[-1]['gap'] * 100, marker=mk[w], s=12, color=WCOL[w], label=DISP[w] if n == 25 else None)
    pd.DataFrame(rows).to_csv(f"{SIM}/collapse_real.csv", index=False)
    ax[2].plot([.8, 14], [.8, 14], color='#888', ls=':', lw=.8); ax[2].set_xscale('log'); ax[2].set_yscale('log')
    ax[2].set_xlabel('plug-in prediction (pts)'); ax[2].set_ylabel('measured gap (pts)'); ax[2].set_title('(c) real worlds, $n$=25--800', fontsize=7); ax[2].legend(frameon=False, fontsize=6)
    for a in (ax[2],): a.set_xticks([1, 2, 4, 8]); a.set_xticklabels([1, 2, 4, 8]); a.set_yticks([1, 2, 4, 8]); a.set_yticklabels([1, 2, 4, 8]); a.xaxis.set_minor_formatter(NullFormatter()); a.yaxis.set_minor_formatter(NullFormatter())
    fig.savefig(f"{FIG}/theory_check.pdf"); plt.close(fig)


if __name__ == "__main__":
    W = [w for w in ('q15', 'b05', 'mix') if os.path.exists(f"{SIM}/gap_{w}.parquet")]
    X = [w for w in ('b15', 's17') if os.path.exists(f"{SIM}/gap_{w}.parquet")]
    fig_gap(W); fig_ksweep(W); fig_conclusions(W); fig_optsens(W); fig_theory(W + X)
    for w in W + X: fig_protocols(w)
    if X: fig_gap(X, 'gap_vs_n_extra')
