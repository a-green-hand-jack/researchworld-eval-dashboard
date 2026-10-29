"""Produce all tables (paper/tables/*.tex) and figures (paper/figs/*.pdf) plus results/summary.json from results/*.csv.
Run: python analyze.py   (seconds)"""
import os, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
RES = os.path.join(ROOT, 'results')
TAB = os.path.join(ROOT, 'paper', 'tables')
FIG = os.path.join(ROOT, 'paper', 'figs')
os.makedirs(TAB, exist_ok=True); os.makedirs(FIG, exist_ok=True)
rng = np.random.default_rng(0)
S = {}  # summary numbers

GROUPS = ['arena55k', 'arena140k', 'mt_human', 'mt_gpt4', 'mt_gpt4_matched', 'nba']
GLABEL = {'arena55k': 'Arena-55k', 'arena140k': 'Arena-140k', 'mt_human': 'MT-Bench human',
          'mt_gpt4': 'MT-Bench GPT-4', 'mt_gpt4_matched': 'MT-Bench GPT-4 (matched)', 'nba': 'NBA seasons'}
DESIGN = {'arena55k': 'crowd', 'arena140k': 'crowd', 'mt_human': 'expert', 'mt_gpt4': 'LLM judge',
          'mt_gpt4_matched': 'LLM judge', 'nba': 'sports'}
COL = {'arena55k': 'tab:blue', 'arena140k': 'tab:cyan', 'mt_human': 'tab:green', 'mt_gpt4': 'tab:red',
       'mt_gpt4_matched': 'tab:orange', 'nba': 'tab:purple'}


def grp(df):
    df['grp'] = np.where(df.board.str.startswith('nba'), 'nba', df.board)
    return df


def boot_ci(x, f=np.median, B=2000):
    x = np.asarray(x)
    if len(x) < 3:
        return (np.nan, np.nan)
    bs = [f(rng.choice(x, len(x))) for _ in range(B)]
    return tuple(np.percentile(bs, [2.5, 97.5]))


def fmt(x, d=1):
    return '--' if (x is None or (isinstance(x, float) and np.isnan(x))) else f'{x:.{d}f}'


claims = grp(pd.read_csv(f'{RES}/claims.csv'))
pairs = grp(pd.read_csv(f'{RES}/pairs_top10.csv'))
for df in (claims, pairs):
    df['pc'] = df['p_rev_boot_cluster'].fillna(df['p_rev_boot'])
    df['pred'] = df.gap / df.se_fisher ** 2
    df['kap'] = df.K_flip / df.N
    df['resolved'] = df.pc < 0.025
# union of adjacent claims (any rank) and top-10 pair claims for the law
adj = claims[claims.claim_type == 'adj']
allc = pd.concat([pairs, adj[~adj.set_index(['board', 'rank_hi', 'rank_lo']).index.isin(
    pairs.set_index(['board', 'rank_hi', 'rank_lo']).index)]], ignore_index=True)
allc = allc[~allc.cens_flip & (allc.gap > 0)]
S['n_claims_law'] = int(len(allc))
S['n_pairs_top10'] = int(len(pairs))
S['n_adj'] = int(len(adj))

# ------------------------------------------------------------------ Table 1: datasets
rows = []
for g in GROUPS:
    c = claims[(claims.grp == g) & (claims.claim_type == 'adj')]
    p = pairs[pairs.grp == g]
    boards = c.board.nunique()
    rows.append(dict(g=g, design=DESIGN[g], boards=boards, N=c.groupby('board').N.first().median(),
                     ents=c.groupby('board').n_ent.first().median(), nadj=len(c), npair=len(p),
                     res_adj=c.resolved.mean(), res_pair=p.resolved.mean()))
t1 = pd.DataFrame(rows)
with open(f'{TAB}/datasets.tex', 'w') as f:
    f.write('\\begin{tabular}{llrrrrrr}\n\\toprule\n Leaderboard & Design & \\#boards & median $N$ & median \\#ent. & \\#adj. claims & resolved adj. & resolved top-10 pairs \\\\\n\\midrule\n')
    for r in t1.itertuples():
        f.write(f'{GLABEL[r.g]} & {r.design} & {r.boards} & {int(r.N):,} & {int(r.ents)} & {r.nadj} & {100*r.res_adj:.0f}\\% & {100*r.res_pair:.0f}\\% \\\\\n'.replace(',', '{,}'))
    f.write('\\bottomrule\n\\end{tabular}\n')
S['datasets'] = t1.to_dict('records')

# ------------------------------------------------------------------ Table 2 + Fig 1: the law K ~ Delta * I_Delta
rows = []
for g in GROUPS:
    d = allc[allc.grp == g]
    big = d[d.pred >= 10]
    ratio = big.K_flip / big.pred
    rr = d[(d.pred >= 3)].K_flip / d[(d.pred >= 3)].pred
    sp = d[['K_flip', 'pred']].corr('spearman').iloc[0, 1]
    # share of claims in which direct votes are enough (n_direct >= K)
    rows.append(dict(g=g, n=len(d), spearman=sp, n10=len(big), med=ratio.median() if len(big) else np.nan,
                     q1=ratio.quantile(.25) if len(big) else np.nan, q3=ratio.quantile(.75) if len(big) else np.nan,
                     lo_min=rr.min() if len(rr) else np.nan))
t2 = pd.DataFrame(rows)
with open(f'{TAB}/law.tex', 'w') as f:
    f.write('\\begin{tabular}{lrrrrr}\n\\toprule\n Leaderboard & \\#claims & Spearman$(K^\\star,\\hat K)$ & \\#claims $\\hat K\\!\\ge\\!10$ & median $K^\\star/\\hat K$ & [IQR] \\\\\n\\midrule\n')
    for r in t2.itertuples():
        f.write(f'{GLABEL[r.g]} & {r.n} & {r.spearman:.3f} & {r.n10} & {fmt(r.med,2)} & [{fmt(r.q1,2)}, {fmt(r.q3,2)}] \\\\\n')
    f.write('\\bottomrule\n\\end{tabular}\n')
S['law'] = t2.to_dict('records')
big = allc[allc.pred >= 10]
S['law_all_ratio_median'] = float((big.K_flip / big.pred).median())
S['law_all_ratio_min'] = float((allc[allc.pred >= 3].K_flip / allc[allc.pred >= 3].pred).min())
S['law_loglog_pearson'] = float(np.corrcoef(np.log(big.K_flip), np.log(big.pred))[0, 1])
S['law_spearman_all'] = float(allc[['K_flip', 'pred']].corr('spearman').iloc[0, 1])
# normalised fragility K*/(z sqrt(n_loc)) per group
rows = []
for g in GROUPS:
    d = allc[(allc.grp == g) & (allc.pred >= 10)]
    e = d.K_flip.div((d.gap.div(d.se_fisher)) * np.sqrt(d.n_loc))
    rows.append(dict(g=g, n=len(d), med=float(e.median()), q1=float(e.quantile(.25)), q3=float(e.quantile(.75))))
S['norm_fragility'] = rows
# ratio vs direct-vote availability
big = big.assign(dir_ok=big.n_direct >= 0) if 'n_direct' in big else big
cl2 = adj[(~adj.cens_flip) & (adj.gap > 0) & (adj.gap / adj.se_fisher ** 2 >= 5)].copy()
cl2['ratio'] = cl2.K_flip / (cl2.gap / cl2.se_fisher ** 2)
cl2['feasible_direct'] = np.isfinite(cl2.K_direct_flip)
S['ratio_direct_feasible_median'] = float(cl2[cl2.feasible_direct].ratio.median())
S['ratio_direct_infeasible_median'] = float(cl2[~cl2.feasible_direct].ratio.median())
S['n_ratio_direct_feasible'] = int(cl2.feasible_direct.sum()); S['n_ratio_direct_infeasible'] = int((~cl2.feasible_direct).sum())

fig, ax = plt.subplots(1, 2, figsize=(7.0, 3.1))
for g in GROUPS:
    d = allc[allc.grp == g]
    ax[0].scatter(d.pred, d.K_flip, s=7 if g == 'nba' else 14, alpha=0.35 if g == 'nba' else 0.8, c=COL[g], label=GLABEL[g], lw=0)
xs = np.logspace(-1, 3.5, 10)
ax[0].plot(xs, xs, 'k-', lw=0.8); ax[0].plot(xs, 2 * xs, 'k--', lw=0.8)
ax[0].set_xscale('log'); ax[0].set_yscale('log'); ax[0].set_ylim(0.8, 1000); ax[0].set_xlim(0.1, 1000)
ax[0].set_xlabel(r'$\hat K=\Delta/\sigma_\Delta^2$ (gap $\times$ Fisher information)'); ax[0].set_ylabel(r'exact minimal flips $K^\star$')
ax[0].legend(fontsize=5.5, loc='upper left', frameon=False)
r = (allc.K_flip / allc.pred)[allc.pred >= 10]
for g in GROUPS:
    d = allc[(allc.grp == g) & (allc.pred >= 3)]
    ax[1].scatter(d.pred, d.K_flip / d.pred, s=7 if g == 'nba' else 14, alpha=0.35 if g == 'nba' else 0.8, c=COL[g], lw=0)
ax[1].axhline(1, c='k', lw=0.8); ax[1].axhline(2, c='k', ls='--', lw=0.8)
ax[1].set_xscale('log'); ax[1].set_ylim(0.8, 3.2)
ax[1].set_xlabel(r'$\hat K$ (claims with $\hat K\geq 3$)'); ax[1].set_ylabel(r'$K^\star/\hat K$')
plt.tight_layout(); plt.savefig(f'{FIG}/law.pdf'); plt.close()

# ------------------------------------------------------------------ Table 3: attack types
cl = claims[claims.claim_type.isin(['adj', 'top1']) & ~claims.cens_flip & (claims.K_flip >= 10)]
rows = []
for g in GROUPS:
    d = cl[cl.grp == g]
    if len(d) == 0:
        continue
    rows.append(dict(g=g, n=len(d), rem=(d.K_remove / d.K_flip).median(), ins=(d.K_insert / d.K_flip).median(),
                     lin=(d.K_lin_flip / d.K_flip).median(), direct=(d.K_direct_flip / d.K_flip).replace(np.inf, np.nan).median(),
                     inf=np.isinf(d.K_direct_flip).mean()))
t3 = pd.DataFrame(rows)
tg = pd.read_csv(f'{RES}/claims_target.csv'); tg = grp(tg)
tg = tg[(tg.K_flip >= 10) & ~tg.cens_flip]
tgg = tg.groupby('grp').apply(lambda d: pd.Series(dict(tins=(d.K_insert / d.K_flip).median(), ttar=(d.K_insert_target / d.K_flip).median(),
                                                     ncl=len(d))), include_groups=False)
with open(f'{TAB}/attacks.tex', 'w') as f:
    f.write('\\begin{tabular}{lrrrrrr}\n\\toprule\n Leaderboard & \\#claims & remove & insert (any) & insert (challenger only) & first-order flip & direct-only flip (infeasible) \\\\\n\\midrule\n')
    for r in t3.itertuples():
        ti = tgg.loc[r.g] if (r.g in tgg.index and tgg.loc[r.g].ncl >= 3) else None
        f.write(f'{GLABEL[r.g]} & {r.n} & {r.rem:.2f} & {r.ins:.2f} & {fmt(ti.ttar, 2) if ti is not None else "--"} & {r.lin:.2f} & {r.direct:.2f} ({100*r.inf:.0f}\\%) \\\\\n')
    f.write('\\bottomrule\n\\end{tabular}\n')
S['attacks'] = t3.to_dict('records'); S['attacks_target'] = tgg.reset_index().to_dict('records')

# ------------------------------------------------------------------ Table 4: resolved claims
rows = []
for g in GROUPS:
    d = pairs[(pairs.grp == g)]
    r = d[d.resolved]
    ci = boot_ci(r.K_flip)
    rows.append(dict(g=g, n=len(d), nres=len(r), Kmed=r.K_flip.median(), Kci=ci, q1=r.K_flip.quantile(.25), q3=r.K_flip.quantile(.75),
                     kap=100 * r.kap.median(), kq1=100 * r.kap.quantile(.25), kq3=100 * r.kap.quantile(.75),
                     z=(r.gap / r.se_boot).median() if g != 'nba' else (r.gap / r.se_boot).median()))
t4 = pd.DataFrame(rows)
with open(f'{TAB}/resolved.tex', 'w') as f:
    f.write('\\begin{tabular}{lrrrrr}\n\\toprule\n Leaderboard & \\#pairs & \\#resolved & median $K^\\star$ [IQR] & median $K^\\star/N$ (\\%) [IQR] \\\\\n\\midrule\n')
    for r in t4.itertuples():
        f.write(f'{GLABEL[r.g]} & {r.n} & {r.nres} & {r.Kmed:.0f} [{r.q1:.0f}, {r.q3:.0f}] & {r.kap:.2f} [{r.kq1:.2f}, {r.kq3:.2f}] \\\\\n')
    f.write('\\bottomrule\n\\end{tabular}\n')
S['resolved'] = t4.to_dict('records')

# ------------------------------------------------------------------ sensitivity curve (Table 5, Fig 2)
eps_grid = [0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05]
rows = []
for g in GROUPS:
    d = pairs[pairs.grp == g]
    rows.append(dict(g=g, **{f'e{e}': float((d.kap <= e).mean()) for e in eps_grid},
                     **{f'r{e}': float(((d.kap <= e) & d.resolved).sum() / max(1, d.resolved.sum())) for e in eps_grid}))
t5 = pd.DataFrame(rows)
with open(f'{TAB}/curve.tex', 'w') as f:
    f.write('\\begin{tabular}{l' + 'r' * len(eps_grid) + '}\n\\toprule\n Leaderboard & ' + ' & '.join(f'{100*e:g}\\%' for e in eps_grid) + ' \\\\\n\\midrule\n')
    for r in t5.itertuples(index=False):
        f.write(GLABEL[r[0]] + ' & ' + ' & '.join(f'{100*getattr(r, f"e{e}".replace(".", "_")) if False else 100*t5.loc[t5.g==r[0], f"e{e}"].iloc[0]:.0f}' for e in eps_grid) + ' \\\\\n')
    f.write('\\bottomrule\n\\end{tabular}\n')
S['curve'] = t5.to_dict('records')

fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.9))
for g in GROUPS:
    d = pairs[pairs.grp == g]
    x = np.sort(d.kap.values); y = np.arange(1, len(x) + 1) / len(x)
    ax[0].step(np.maximum(x, 1e-5), y, c=COL[g], label=GLABEL[g], lw=1.3, where='post')
    dr = d[d.resolved]
    if len(dr):
        x = np.sort(dr.kap.values); y = np.arange(1, len(x) + 1) / len(x)
        ax[1].step(np.maximum(x, 1e-5), y, c=COL[g], lw=1.3, where='post')
for a_, t in zip(ax, ['all top-10 pairwise claims', 'statistically resolved claims only']):
    a_.set_xscale('log'); a_.set_xlabel(r'budget $K^\star/N$ (fraction of votes flipped)'); a_.set_title(t, fontsize=8)
    a_.set_xlim(1e-4, 0.3)
ax[0].set_ylabel('fraction of claims reversed'); ax[0].legend(fontsize=5.5, frameon=False, loc='upper left')
plt.tight_layout(); plt.savefig(f'{FIG}/curve.pdf'); plt.close()

# ------------------------------------------------------------------ headline claims: dethroning rank 1
h = claims[claims.rank_hi == 1].copy()
rows = []
for b, d in h.groupby('board'):
    i = d.K_flip.idxmin()
    rows.append(dict(board=b, grp=d.grp.iloc[0], N=d.N.iloc[0], Kmin=d.K_flip.min(), K12=d[(d.rank_lo == 2)].K_flip.iloc[0],
                     gap12=d[(d.rank_lo == 2)].gap.iloc[0], pc12=d[(d.rank_lo == 2)].pc.iloc[0], K_remove12=d[(d.rank_lo == 2)].K_remove.iloc[0],
                     K_insert12=d[(d.rank_lo == 2)].K_insert.iloc[0]))
hd = pd.DataFrame(rows)
hd['kap12'] = hd.K12 / hd.N
nb_ = hd[hd.grp == 'nba']
S['headline_nonnba'] = hd[hd.grp != 'nba'].to_dict('records')
S['headline_nba'] = dict(n=len(nb_), K12_median=float(nb_.K12.median()), K12_q1=float(nb_.K12.quantile(.25)), K12_q3=float(nb_.K12.quantile(.75)),
                         kap12_median=float(nb_.kap12.median()), frac_unresolved=float((nb_.pc12 >= 0.025).mean()),
                         K12_le3=float((nb_.K12 <= 3).mean()), N_median=float(nb_.N.median()))
with open(f'{TAB}/headline.tex', 'w') as f:
    f.write('\\begin{tabular}{llrrrrr}\n\\toprule\n Leaderboard & ranks 1 vs 2 & gap $\\Delta$ & reversal prob. & $K^\\star$ flip & remove & insert \\\\\n\\midrule\n')
    for r in hd[hd.grp != 'nba'].itertuples():
        d = h[(h.board == r.board) & (h.rank_lo == 2)].iloc[0]
        f.write(f'{GLABEL[r.grp]} & {d.ent_hi} vs {d.ent_lo} & {d.gap:.3f} & {d.pc:.3f} & {int(r.K12)} ({100*r.kap12:.2f}\\%) & {int(r.K_remove12)} & {int(r.K_insert12)} \\\\\n'.replace('_', '\\_'))
    n = S['headline_nba']
    f.write(f'NBA seasons (n={n["n"]}) & champion-by-BT vs runner-up & -- & -- & median {n["K12_median"]:.0f} [{n["K12_q1"]:.0f},{n["K12_q3"]:.0f}] ({100*n["kap12_median"]:.2f}\\%) & -- & -- \\\\\n')
    f.write('\\bottomrule\n\\end{tabular}\n')

# ------------------------------------------------------------------ cluster vs iid SE
rows = []
for g in ['arena55k', 'arena140k', 'mt_human', 'mt_gpt4', 'mt_gpt4_matched']:
    d = pairs[pairs.grp == g]
    rr = d.se_boot_cluster / d.se_boot
    rf = d.se_boot / d.se_fisher
    rows.append(dict(g=g, clu_over_iid=rr.median(), iid_over_fisher=rf.median(),
                     res_iid=float((d.p_rev_boot < 0.025).mean()), res_clu=(float((d.p_rev_boot_cluster < 0.025).mean()) if d.p_rev_boot_cluster.notna().any() else np.nan)))
t6 = pd.DataFrame(rows)
S['se_ratios'] = t6.to_dict('records')
rows = []
d = pairs[pairs.grp == 'nba']
S['nba_se_iid_over_fisher'] = float((d.se_boot / d.se_fisher).median())

# ------------------------------------------------------------------ random noise vs adversary
rn = grp(pd.read_csv(f'{RES}/random_noise.csv'))
agg = rn.groupby(['grp', 'kind', 'eps']).agg(tau=('tau', 'mean'), top1=('top1_same', 'mean'), top3=('top3_same', 'mean')).reset_index()
S['random_noise'] = agg.to_dict('records')
fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.7), sharey=True)
for k, kind in enumerate(['flip', 'remove']):
    for g in GROUPS:
        d = agg[(agg.grp == g) & (agg.kind == kind)]
        ax[k].plot(100 * d.eps, d.tau, 'o-', c=COL[g], ms=3, lw=1.2, label=GLABEL[g])
    ax[k].set_xlabel(f'% of votes {"flipped" if kind=="flip" else "removed"} at random'); ax[k].set_xscale('log')
ax[0].set_ylabel('Kendall $\\tau$ vs. original ranking'); ax[0].legend(fontsize=5.5, frameon=False, loc='lower left')
plt.tight_layout(); plt.savefig(f'{FIG}/noise.pdf'); plt.close()

# adversarial budget vs random noise on global ranking: fraction of top-10 pair claims adversary can reverse with eps*N flips
# ------------------------------------------------------------------ size scaling
sz = pd.read_csv(f'{RES}/size_scaling.csv')
sz['pred'] = sz.gap.div(sz.se_fisher ** 2)
sz['kap'] = sz.K_flip.div(sz.N)
sz = sz[sz.gap > 0]
sa = sz.groupby('frac').agg(N=('N', 'first'), kap_med=('kap', 'median'), kap_q1=('kap', lambda x: x.quantile(.25)),
                            kap_q3=('kap', lambda x: x.quantile(.75)), n=('kap', 'size')).reset_index()
sa['ratio_med'] = [float((sz[sz.frac == f].K_flip.div(sz[sz.frac == f].pred)).median()) for f in sa.frac]
S['size_scaling'] = sa.to_dict('records')
S['size_npairs'] = int(sz.groupby(['i', 'j']).ngroups)
fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.6))
for (i, j), d in sz.groupby(['i', 'j']):
    dd = d.groupby('N').K_flip.median()
    ax[0].plot(dd.index, dd.values, '-', c='tab:blue', alpha=0.35, lw=0.8)
ax[0].plot(sa.N, sa.kap_med.mul(sa.N), 'k-o', ms=3, lw=1.5)
ax[0].set_xscale('log'); ax[0].set_yscale('log')
ax[0].set_xlabel('votes $N$ (random subsample of Arena-55k)'); ax[0].set_ylabel(r'$K^\star$ (per pair; black: median)')
ax[1].plot(sa.N, 100 * sa.kap_med, 'k-o', ms=3); ax[1].fill_between(sa.N, 100 * sa.kap_q1, 100 * sa.kap_q3, color='gray', alpha=0.3)
ax[1].set_xscale('log'); ax[1].set_ylim(0, 1.0)
ax[1].set_xlabel('votes $N$'); ax[1].set_ylabel(r'$K^\star/N$ (%), median and IQR over pairs')
plt.tight_layout(); plt.savefig(f'{FIG}/size.pdf'); plt.close()

# ------------------------------------------------------------------ bootstrap uncertainty of K*
bk = grp(pd.read_csv(f'{RES}/boot_K.csv'))
bk1 = bk[(bk.rank_hi <= 5) & (bk.draw > 0)]
base = bk[(bk.rank_hi <= 5) & (bk.draw == 0)]
rows = []
for g in GROUPS:
    d = bk1[bk1.grp == g]
    # per (board, rank) coefficient of variation of K across bootstrap draws; median over (board, rank)
    cv = d.groupby(['board', 'rank_hi']).K_flip.agg(lambda x: x.std(ddof=1) / max(x.mean(), 1e-9))
    rows.append(dict(g=g, cv_med=float(cv.median()), n=int(len(cv))))
S['bootK_cv'] = rows
# ------------------------------------------------------------------ ties sensitivity
ts = pd.read_csv(f'{RES}/ties_sens.csv')
base = claims[claims.claim_type == 'adj'][['board', 'rank_hi', 'K_flip', 'gap']]
m = ts.merge(base, on=['board', 'rank_hi'], suffixes=('_nt', ''))
m = m[(m.K_flip >= 10) | (m.K_flip_noties >= 10)]
S['ties_sens'] = dict(n=int(len(m)), ratio_median=float((m.K_flip_noties / m.K_flip).median()),
                      ratio_q=[float(x) for x in (m.K_flip_noties / m.K_flip).quantile([.25, .75])])
S['ties_by_board'] = m.assign(r=m.K_flip_noties / m.K_flip).groupby('board').r.median().to_dict()
json.dump(S, open(f'{RES}/summary.json', 'w'), indent=1, default=float)
print(json.dumps({k: S[k] for k in ['n_claims_law', 'law_all_ratio_median', 'law_all_ratio_min', 'law_loglog_pearson', 'law_spearman_all',
                                     'ratio_direct_feasible_median', 'ratio_direct_infeasible_median', 'ties_sens', 'headline_nba']}, indent=1))
print(t1); print(t2); print(t3); print(tgg); print(t4); print(t5.round(2)); print(t6); print(sa); print(S['bootK_cv']); print(S['ties_by_board'])
print(hd)
