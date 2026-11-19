"""Figures and LaTeX tables for the paper -> paper/figs/*.pdf, paper/tables/*.tex"""
import sys, os
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import RULES, CARDINAL, ORDINAL, RULE_LABEL
os.makedirs('paper/figs', exist_ok=True); os.makedirs('paper/tables', exist_ok=True)
plt.rcParams.update({'font.size': 8, 'axes.titlesize': 8, 'axes.labelsize': 8, 'legend.fontsize': 6.5, 'figure.dpi': 150,
                     'axes.spines.top': False, 'axes.spines.right': False})
COL = {'mean': '#1f77b4', 'geo': '#17becf', 'harm': '#2ca02c', 'min': '#d62728', 'median': '#ff7f0e',
       'borda': '#9467bd', 'copeland': '#8c564b', 'plurality': '#7f7f7f'}
LS = {r: ('-' if r in CARDINAL else '--') for r in RULES}
MK = {'mean': 'o', 'geo': 's', 'harm': '^', 'min': 'v', 'median': 'D', 'borda': 'P', 'copeland': 'X', 'plurality': '*'}
SHORT = {'mean': 'Mean', 'geo': 'Geo', 'harm': 'Harm', 'min': 'Min', 'median': 'Median', 'borda': 'Borda', 'copeland': 'Copeland', 'plurality': 'Plurality'}
BENCH = [('helm', 'HELM-MMLU (n=57)'), ('ollb6', 'OLLB-6 (n=6)'), ('bbh24', 'OLLB-BBH24 (n=24)')]
G = [2, 5, 10, 20, 50, 100]
main = {b: pd.read_csv(f'results/main_{b}.csv') for b, _ in BENCH}

def iqr(x): return f'{x.median():.1f} [{x.quantile(.25):.1f}, {x.quantile(.75):.1f}]'

# ---------------- Fig 1: requirement vs initial rank
fig, ax = plt.subplots(3, 3, figsize=(7.2, 6.0))
for c, (b, title) in enumerate(BENCH):
    d = main[b]
    for r in RULES:
        x = d[d.rule == r].sort_values('rank')
        for row, (col, ylab) in enumerate([('K_100', 'min. breadth $K^*$ (#tasks)'), ('L1_100', 'min. magnitude $L^*$ (points)'), ('gstar', 'min. depth $g^*$ (points / task)')]):
            ax[row, c].plot(x['rank'], x[col].clip(lower=1e-2) if col != 'K_100' else x[col], LS[r], color=COL[r], marker=MK[r], ms=2.2, lw=1.0, label=SHORT[r])
            if c == 0: ax[row, c].set_ylabel(ylab)
    ax[0, c].set_title(title)
    for row in (1, 2): ax[row, c].set_yscale('log')
    ax[2, c].set_xlabel('initial rank $r$ of target')
h, l = ax[0, 0].get_legend_handles_labels(); fig.legend(h, l, ncol=8, frameon=False, loc='lower center', columnspacing=0.8, handlelength=1.5)
plt.tight_layout(rect=(0, 0.04, 1, 1)); plt.savefig('paper/figs/fig_rank_sweep.pdf'); plt.savefig('results/prev_fig_rank_sweep.png', dpi=110); plt.close()

# ---------------- Fig 2: K*(g) among contenders ranks 2..11, and feasibility
fig, ax = plt.subplots(2, 3, figsize=(7.2, 3.9))
for c, (b, title) in enumerate(BENCH):
    d = main[b]; d = d[d['rank'] <= 11]
    for r in RULES:
        x = d[d.rule == r]
        med = [x[f'K_{g}'].median() if x[f'K_{g}'].notna().mean() >= 0.5 else np.nan for g in G]
        fr = [x[f'K_{g}'].notna().mean() for g in G]
        ax[0, c].plot(G, med, LS[r], color=COL[r], marker=MK[r], ms=2.5, lw=1.0, label=SHORT[r])
        ax[1, c].plot(G, fr, LS[r], color=COL[r], marker=MK[r], ms=2.5, lw=1.0)
    ax[0, c].set_title(title); ax[0, c].set_xscale('log'); ax[1, c].set_xscale('log'); ax[0, c].set_yscale('log')
    ax[1, c].set_xlabel('per-task gain cap $g$ (points)')
    if c == 0: ax[0, c].set_ylabel('median $K^*(g)$ (if >=50% feasible)'); ax[1, c].set_ylabel('fraction of contenders\nfor which #1 is reachable')
h, l = ax[0, 0].get_legend_handles_labels(); fig.legend(h, l, ncol=8, frameon=False, loc='lower center', columnspacing=0.8, handlelength=1.5)
plt.tight_layout(rect=(0, 0.05, 1, 1)); plt.savefig('paper/figs/fig_cap_sweep.pdf'); plt.savefig('results/prev_fig_cap_sweep.png', dpi=110); plt.close()

# ---------------- Fig 3: noise
dr = pd.read_csv('results/noise_helm_draws.csv'); wn = pd.read_csv('results/noise_helm_winner.csv')
obs = main['helm']; obs = obs[obs['rank'] <= 11].groupby('rule').median(numeric_only=True)
fig, ax = plt.subplots(1, 4, figsize=(7.2, 2.3))
for k, (col, lab, lg) in enumerate([('K_100', 'median $K^*$ (#tasks)', False), ('L1_100', 'median $L^*$ (points)', True), ('gstar', 'median $g^*$ (points)', False)]):
    for i, r in enumerate(RULES):
        v = dr[dr.rule == r][col].dropna()
        ax[k].plot([i, i], [v.quantile(.025), v.quantile(.975)], color=COL[r], lw=1.5)
        ax[k].plot(i, v.median(), 'o', color=COL[r], ms=3)
        ax[k].plot(i, obs.loc[r, col], 'x', color='k', ms=3)
    ax[k].set_xticks(range(8)); ax[k].set_xticklabels([SHORT[r] for r in RULES], rotation=60, ha='right'); ax[k].set_ylabel(lab)
    if lg: ax[k].set_yscale('log')
st = wn.groupby('rule')['same'].mean().reindex(RULES)
ax[3].bar(range(8), st.values, color=[COL[r] for r in RULES]); ax[3].set_xticks(range(8)); ax[3].set_xticklabels([SHORT[r] for r in RULES], rotation=60, ha='right')
ax[3].set_ylabel('P(observed winner\nstays #1)'); ax[3].set_ylim(0, 1)
plt.tight_layout(); plt.savefig('paper/figs/fig_noise.pdf'); plt.savefig('results/prev_fig_noise.png', dpi=110); plt.close()

# ---------------- Fig 4: task subsampling
sb = pd.read_csv('results/subsample_helm.csv')
full = main['helm']; full = full[full['rank'] <= 11].groupby('rule').median(numeric_only=True)
fig, ax = plt.subplots(1, 3, figsize=(7.2, 2.3))
for k, (col, lab, lg) in enumerate([('K_100', '$K^*$ (#tasks)', False), ('L1_100', '$L^*$ per task (points)', True), ('gstar', '$g^*$ (points)', False)]):
    for r in RULES:
        ms = sorted(sb.m.unique()); y = []; lo = []; hi = []
        for m in ms:
            v = sb[(sb.rule == r) & (sb.m == m)][col].dropna() / (m if col == 'L1_100' else 1)
            y.append(v.median()); lo.append(v.quantile(.1)); hi.append(v.quantile(.9))
        xs = ms + [57]; v57 = full.loc[r, col] / (57 if col == 'L1_100' else 1)
        ax[k].plot(xs, y + [v57], LS[r], color=COL[r], marker=MK[r], ms=2.5, lw=1.0, label=SHORT[r])
    ax[k].set_xlabel('number of tasks $m$'); ax[k].set_ylabel(lab)
    ax[k].set_xscale('log'); ax[k].set_xticks([6, 12, 24, 40, 57]); ax[k].get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter()); ax[k].minorticks_off()
    if lg: ax[k].set_yscale('log')
h, l = ax[0].get_legend_handles_labels(); fig.legend(h, l, ncol=8, frameon=False, loc='lower center', columnspacing=0.8, handlelength=1.5)
plt.tight_layout(rect=(0, 0.1, 1, 1)); plt.savefig('paper/figs/fig_subsample.pdf'); plt.savefig('results/prev_fig_subsample.png', dpi=110); plt.close()

# ---------------- Fig 5: synthetic
sy = pd.read_csv('results/synthetic.csv')
fig, ax = plt.subplots(2, 3, figsize=(7.2, 3.9))
for row, n in enumerate([12, 57]):
    for k, (col, lab, lg) in enumerate([('K_100', '$K^*$ / n', False), ('L1_100', '$L^*$ per task (points)', True), ('gstar', '$g^*$ (points)', True)]):
        for r in RULES:
            s = sy[(sy.n == n) & (sy.rule == r)]
            y = s.groupby('sigma')[col].median(); den = n if col in ('K_100',) else (n if col == 'L1_100' else 1)
            ax[row, k].plot(y.index, y.values / den, LS[r], color=COL[r], marker=MK[r], ms=2.5, lw=1.0, label=SHORT[r])
        ax[row, k].set_xscale('log'); 
        if lg: ax[row, k].set_yscale('log')
        ax[row, k].set_ylabel(lab + f'  (n={n})')
        if row == 1: ax[row, k].set_xlabel('task-specific SD $\\sigma$ (points)')
h, l = ax[0, 0].get_legend_handles_labels(); fig.legend(h, l, ncol=8, frameon=False, loc='lower center', columnspacing=0.8, handlelength=1.5)
plt.tight_layout(rect=(0, 0.05, 1, 1)); plt.savefig('paper/figs/fig_synthetic.pdf'); plt.savefig('results/prev_fig_synthetic.png', dpi=110); plt.close()

# ---------------- Fig 6: calibrated feasibility (OLLB-6)
cf = pd.read_csv('results/calibrated_feasibility_ollb6.csv'); cf = cf[cf.pairs == 'tuned_to_tuned']
fig, ax = plt.subplots(figsize=(3.4, 2.2)); w = 0.27
for i, (c, lab) in enumerate([('feasible_q90', 'q90'), ('feasible_q99', 'q99'), ('feasible_max', 'max')]):
    v = cf.groupby('rule')[c].mean().reindex(RULES); ax.bar(np.arange(8) + (i - 1) * w, v.values, w, label=lab)
ax.set_xticks(range(8)); ax.set_xticklabels([SHORT[r] for r in RULES], rotation=60, ha='right'); ax.set_ylabel('fraction of ranks 2-21\nthat can reach #1'); ax.legend(title='per-task cap =', frameon=False, ncol=3, loc='lower center', bbox_to_anchor=(0.5, 1.0))
plt.tight_layout(); plt.savefig('paper/figs/fig_calibrated.pdf'); plt.savefig('results/prev_fig_calibrated.png', dpi=110); plt.close()

# ---------------- Tables
rows = []
for b, title in BENCH:
    d = main[b]; d = d[d['rank'] <= 11]
    for r in RULES:
        x = d[d.rule == r]
        rows.append(dict(bench=title, rule=SHORT[r], gstar=iqr(x['gstar']), K100=iqr(x['K_100']), K10=(iqr(x['K_10']) + (f" ({x['K_10'].notna().mean() * 100:.0f}\\% feas.)" if x['K_10'].notna().mean() < 1 else '')) if x['K_10'].notna().any() else 'infeasible',
                         L100=iqr(x['L1_100'])))
T = pd.DataFrame(rows); T.to_csv('results/table_main_summary.csv', index=False)
with open('paper/tables/main_summary.tex', 'w') as f:
    f.write('\\begin{tabular}{llcccc}\\toprule\nBenchmark & Rule & $g^*$ & $K^*$ ($g{=}100$) & $K^*$ ($g{=}10$) & $L^*$ ($g{=}100$)\\\\\\midrule\n')
    last = None
    for _, r in T.iterrows():
        if last is not None and r.bench != last: f.write('\\midrule\n')
        f.write(f"{r.bench if r.bench != last else ''} & {r.rule} & {r.gstar} & {r.K100} & {r.K10} & {r.L100}\\\\\n"); last = r.bench
    f.write('\\bottomrule\\end{tabular}\n')
print('figures + tables written')
