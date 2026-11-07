"""Tables and figures for the paper from results/*.csv.  Run after exp1_main.py and exp2_sweeps.py.
Writes figs/*.pdf and results/tables.tex fragments + results/summary.json (all numbers quoted in the paper)."""
import json, numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
import common as K

R = K.RES; FIG = f'{K.ROOT}/figs'; import os; os.makedirs(FIG, exist_ok=True)
plt.rcParams.update({'font.size': 8, 'axes.spines.top': False, 'axes.spines.right': False, 'figure.dpi': 150})
NAMES = {'mean': 'Mean', 'trim25': 'Trim-25%', 'median': 'Median', 'max': 'Max', 'min': 'Min', 'geomean': 'Geo-mean',
         'harmonic': 'Harmonic', 'borda': 'Borda', 'condorcet': 'Condorcet', 'plurality': 'Plurality'}
DSN = {'helm57': 'HELM-MMLU (m=57)', 'oll6': 'OLL-6 (m=6)', 'oll39': 'OLL-leaf (m=39)'}
SUM = {}
rng = np.random.default_rng(0)

def boot_ci(x, B=2000, stat=np.median):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    if len(x) == 0: return (np.nan, np.nan, np.nan)
    bs = [stat(rng.choice(x, len(x))) for _ in range(B)]
    return stat(x), np.percentile(bs, 2.5), np.percentile(bs, 97.5)

P = pd.read_csv(f'{R}/exp1_point.csv'); Rp = pd.read_csv(f'{R}/exp1_reps.csv')
# ---------------------------------------------------------------- Table 1: main
rows = []
for ds in K.DATASETS:
    for r in K.RULES:
        q = P[(P.dataset == ds) & (P.rule == r)]
        q1 = q[q.target_rank == 2]
        qt = Rp[(Rp.dataset == ds) & (Rp.rule == r) & (Rp.kind == 'task')]; qn = Rp[(Rp.dataset == ds) & (Rp.rule == r) & (Rp.kind == 'noise')]
        # median over targets per replicate, then CI over replicates
        mt = qt.groupby('rep').eq_pp.median(); mn = qn.groupby('rep').eq_pp.median()
        rows.append(dict(dataset=ds, rule=r, eq_runner=q1.eq_pp.iloc[0], eq_med=q.eq_pp.median(), eq_max=q.eq_pp.max(),
                         touched_med=q.touched.median(), feas=q.feasible.mean(), base_rank_med=q.base_rank.median(),
                         task_lo=np.percentile(mt, 2.5) if len(mt) else np.nan, task_hi=np.percentile(mt, 97.5) if len(mt) else np.nan,
                         noise_lo=np.percentile(mn, 2.5) if len(mn) else np.nan, noise_hi=np.percentile(mn, 97.5) if len(mn) else np.nan,
                         task_inf=(~qt.feasible).mean() if len(qt) else np.nan, opt_frac=q.opt.mean() if 'opt' in q else np.nan))
T1 = pd.DataFrame(rows); T1.to_csv(f'{R}/table_main.csv', index=False)
SUM['main'] = T1.round(4).to_dict('records')
SUM['n_reps'] = dict(task=int(Rp[Rp.kind == 'task'].rep.nunique()), noise=int(Rp[Rp.kind == 'noise'].rep.nunique()))
SUM['nonopt_rows'] = int((~Rp.opt).sum() + (~P.opt).sum()) if 'opt' in P else None
SUM['nonopt_rows_by_rule'] = pd.concat([P, Rp]).query('~opt').groupby('rule').size().to_dict() if 'opt' in P else None

def f(x, d=2): return '--' if pd.isna(x) else f'{x:.{d}f}'
tex = ['\\begin{tabular}{l' + 'rr' * 3 + '}', '\\toprule', ' & ' + ' & '.join(f'\\multicolumn{{2}}{{c}}{{{DSN[d]}}}' for d in K.DATASETS) + '\\\\',
       'Rule & ' + ' & '.join('pp [95\\% CI] & $k$' for _ in K.DATASETS) + '\\\\', '\\midrule']
for r in K.RULES:
    cells = []
    for ds in K.DATASETS:
        a = T1[(T1.dataset == ds) & (T1.rule == r)].iloc[0]
        cells += [f'{f(a.eq_med)} [{f(a.task_lo)}, {f(a.task_hi)}]', f'{a.touched_med:.0f}']
    tex.append(NAMES[r] + ' & ' + ' & '.join(cells) + '\\\\')
tex += ['\\bottomrule', '\\end{tabular}']
open(f'{R}/table_main.tex', 'w').write('\n'.join(tex))

# ---------------------------------------------------------------- Fig 1: eq_pp by rule, per dataset (point values + task-bootstrap spread)
fig, ax = plt.subplots(1, 3, figsize=(7.0, 2.6), sharex=False)
for a, ds in zip(ax, K.DATASETS):
    q = P[P.dataset == ds]; qt = Rp[(Rp.dataset == ds) & (Rp.kind == 'task')]
    for k, r in enumerate(K.RULES):
        v = q[q.rule == r].eq_pp.dropna().values + 1e-4
        a.scatter(v, np.full(len(v), k) + rng.uniform(-.18, .18, len(v)), s=6, alpha=.7, color='C0', lw=0)
        mt = qt[qt.rule == r].groupby('rep').eq_pp.median().values + 1e-4
        if len(mt): a.plot([np.percentile(mt, 2.5), np.percentile(mt, 97.5)], [k, k], color='C3', lw=2, alpha=.6)
    a.set_xscale('log'); a.set_yticks(range(len(K.RULES))); a.set_yticklabels([NAMES[r] if ds == 'helm57' else '' for r in K.RULES])
    a.invert_yaxis(); a.set_title(DSN[ds], fontsize=8); a.set_xlabel('required gain (mean-equiv. pp, log)')
plt.tight_layout(); plt.savefig(f'{FIG}/fig_main.pdf'); plt.close()

# ---------------------------------------------------------------- breadth: tasks touched vs m (exp2 scaling) + lower bound
Sc = pd.read_csv(f'{R}/exp2_scaling.csv')
SUM['scaling'] = Sc[Sc.target_rank.isna() if 'target_rank' in Sc else Sc.target.notna()].groupby(['dataset', 'm', 'rule']).agg(
    eq=('eq_pp', 'median'), touched=('touched', 'median')).round(4).reset_index().to_dict('records')
fig, ax = plt.subplots(1, 2, figsize=(6.5, 2.4))
for a, ds in zip(ax, ['helm57', 'oll39']):
    q = Sc[Sc.dataset == ds]
    for r, c in zip(['mean', 'trim25', 'median', 'min', 'condorcet', 'plurality'], ['C0', 'C1', 'C2', 'C3', 'C4', 'C5']):
        g = q[q.rule == r].groupby('m').eq_pp.median()
        a.plot(g.index, g.values, marker='o', ms=3, color=c, label=NAMES[r])
    a.set_xscale('log'); a.set_yscale('log'); a.set_xlabel('number of tasks $m$'); a.set_ylabel('required gain (pp)'); a.set_title(DSN[ds], fontsize=8)
ax[0].legend(fontsize=6, frameon=False); plt.tight_layout(); plt.savefig(f'{FIG}/fig_scaling.pdf'); plt.close()

# ---------------------------------------------------------------- pool size
Po = pd.read_csv(f'{R}/exp2_pool.csv')
fig, ax = plt.subplots(1, 3, figsize=(7.0, 2.2), sharey=False)
for a, ds in zip(ax, K.DATASETS):
    q = Po[Po.dataset == ds]
    for r, c in zip(['mean', 'trim25', 'median', 'min', 'condorcet', 'plurality', 'borda'], ['C0', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6']):
        g = q[q.rule == r].groupby('pool').eq_pp.median()
        if len(g): a.plot(g.index, g.values + 1e-4, marker='o', ms=3, color=c, label=NAMES[r])
    a.set_xscale('log'); a.set_yscale('log'); a.set_xlabel('pool size $N$ (top-$N$ models)'); a.set_title(DSN[ds], fontsize=8)
ax[0].set_ylabel('required gain (pp)'); ax[0].legend(fontsize=5.5, frameon=False); plt.tight_layout(); plt.savefig(f'{FIG}/fig_pool.pdf'); plt.close()
SUM['pool'] = Po.groupby(['dataset', 'pool', 'rule']).eq_pp.median().round(4).reset_index().to_dict('records')

# ---------------------------------------------------------------- kmax
Km = pd.read_csv(f'{R}/exp2_kmax.csv')
SUM['kmax'] = Km.groupby(['dataset', 'rule', 'kmax']).agg(feas=('feasible', 'mean'), eq=('eq_pp', 'median')).round(4).reset_index().to_dict('records')
fig, ax = plt.subplots(1, 3, figsize=(7.0, 2.2))
for a, ds in zip(ax, K.DATASETS):
    q = Km[Km.dataset == ds]
    for r, c in zip(['mean', 'trim25', 'median', 'borda', 'condorcet'], ['C0', 'C1', 'C2', 'C6', 'C4']):
        g = q[q.rule == r].groupby('kmax').feasible.mean()
        if len(g): a.plot(g.index, g.values, marker='o', ms=3, color=c, label=NAMES[r])
    a.set_xlabel('max tasks touched $k$'); a.set_title(DSN[ds], fontsize=8); a.set_ylim(-.05, 1.05)
ax[0].set_ylabel('fraction of targets that can reach rank 1'); ax[0].legend(fontsize=6, frameon=False); plt.tight_layout(); plt.savefig(f'{FIG}/fig_kmax.pdf'); plt.close()

# ---------------------------------------------------------------- cost-model variants
Co = pd.read_csv(f'{R}/exp2_cost.csv')
SUM['cost'] = Co.groupby(['dataset', 'variant', 'rule']).agg(cost=('cost', 'median'), eq=('eq_pp', 'median'), touched=('touched', 'median')).round(4).reset_index().to_dict('records')

# ---------------------------------------------------------------- spillover
Sp = pd.read_csv(f'{R}/exp2_spill.csv')
Sp['first'] = (Sp.rank_after == 1)
M = Sp.groupby(['dataset', 'opt_for', 'eval_under'])['first'].mean().reset_index()
SUM['spill'] = M.round(3).to_dict('records')
Mm = M.groupby(['opt_for', 'eval_under'])['first'].mean().unstack().reindex(index=K.RULES, columns=K.RULES)
Mm = Mm.dropna(how='all').dropna(axis=1, how='all')
fig, a = plt.subplots(figsize=(3.6, 3.2)); im = a.imshow(Mm.values, vmin=0, vmax=1, cmap='viridis')
a.set_xticks(range(Mm.shape[1])); a.set_xticklabels([NAMES[c] for c in Mm.columns], rotation=60, ha='right'); a.set_yticks(range(Mm.shape[0])); a.set_yticklabels([NAMES[c] for c in Mm.index])
a.set_xlabel('evaluated under'); a.set_ylabel('investment optimised for'); plt.colorbar(im, fraction=.046); plt.tight_layout(); plt.savefig(f'{FIG}/fig_spill.pdf'); plt.close()
SUM['spill_matrix_mean_over_datasets'] = Mm.round(3).to_dict()

json.dump(SUM, open(f'{R}/summary.json', 'w'), indent=1, default=float)
print('ok')
