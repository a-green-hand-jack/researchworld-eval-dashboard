"""Tables 1-3 (+ appendix k* table) as LaTeX tabular files in tables/.
T1 datasets (C0); T2 k* under the pre-fixed gap-closed criterion (C3); T3 selector x inference at fixed k (C4); TA1 k* with G vs best floor and absolute tolerances.
"""
from common import *

def tex(df_rows, header, colfmt, path, pre=None):
    os.makedirs(TABDIR, exist_ok=True)
    lines = ['\\begin{tabular}{%s}' % colfmt, '\\toprule'] + ([pre] if pre else []) + [' & '.join(header) + ' \\\\', '\\midrule']
    for r in df_rows:
        lines.append(r if (r.endswith('\\\\') or r.startswith(('\\midrule', '\\cmidrule'))) else r + ' \\\\')
    lines += ['\\bottomrule', '\\end{tabular}']
    open(os.path.join(TABDIR, path), 'w').write('\n'.join(lines) + '\n')
    print('wrote', path)

def fmt(x, nd=2):
    return '--' if pd.isna(x) else f'{x:.{nd}f}'

def ks(x):
    return '$>$grid' if pd.isna(x) else str(int(x))

def pre(labels):
    return ' & & & ' + ' & '.join(f'\\multicolumn{{3}}{{c}}{{{l}}}' for l in labels) + ' \\\\\n' + \
        ''.join(f'\\cmidrule(lr){{{4+3*i}-{6+3*i}}}' for i in range(len(labels)))

def table1():
    d = read('datasets.csv')
    d = d[~d.dataset.str.startswith('syn_')].copy()
    order = ['mteb_dense56', 'mteb_dense', 'mteb_mid', 'mteb_sparse', 'helm_mmlu', 'helm', 'helm_lite_ext', 'livebench', 'olb']
    d['o'] = d.dataset.map({k: i for i, k in enumerate(order)}); d = d.sort_values('o')
    rows = []
    for _, r in d.iterrows():
        nz = fmt(r.noise_nmse_z_covered, 3) if not pd.isna(r.noise_nmse_z_covered) else '--'
        fr = '--' if pd.isna(r.fa_rank_cv_median) else str(int(r.fa_rank_cv_median))
        rows.append(f"{r.dataset.replace('_', '-')} & {int(r.M)} & {int(r.N)} & {100*r.observed_frac:.1f} & {100*r.share_pc1:.0f} & {int(r.pc_for_80)} / {int(r.pc_for_90)} & {fmt(r.eff_rank_pr, 1)} & {fr} & {nz}")
    tex(rows, ['dataset', '$M$', '$N$', 'obs.\\ \\%', 'PC1 \\%', 'PCs 80/90\\%', 'PR rank', 'FA rank (CV)', 'noise nMSE'],
        'lrrrrrrrr', 'table1_datasets.tex')

def kstar_rows(crit_cols, floor_col, sels=('random', 'gv_fa', 'dopt'), rules=('krr', 'fa'), runs=None):
    t = read('kstar_table.csv')
    runs = runs or [r for r in ['B_mteb_dense56', 'B_mteb_dense', 'B_mteb_mid', 'B_mteb_sparse', 'B_helm_mmlu', 'B_helm', 'B_helm_lite_ext', 'B_livebench', 'B_olb'] if r in set(t.run)]
    rows = []
    for run in runs:
        for rule in rules:
            sub = t[(t.run == run) & (t.method == rule)].set_index('selector')
            if sub.empty: continue
            cells = [run[2:].replace('_', '-'), rule, fmt(sub[floor_col].iloc[0])]
            for c in crit_cols:
                cells += [ks(sub.loc[s, c]) if s in sub.index else '--' for s in sels]
            rows.append(' & '.join(cells))
    return rows

def table2():
    c = ['k*G_own>=0.8', 'k*G_own>=0.9']
    rows = kstar_rows(c, 'nmse_floor_own')
    tex(rows, ['dataset', 'rule', 'floor'] + [s for _ in c for s in ('rand.', 'GV', 'D-opt')],
        'llr' + 'rrr' * len(c), 'table2_kstar.tex', pre=pre(['$G\\geq0.8$', '$G\\geq0.9$']))

def tableA1():
    c = ['k*G_best>=0.8', 'k*G_best>=0.9', 'nmse<=0.5', 'nmse<=0.25']
    rows = kstar_rows(c, 'nmse_floor_own')
    tex(rows, ['dataset', 'rule', 'floor'] + [s for _ in c for s in ('rand.', 'GV', 'D-opt')],
        'llr' + 'rrr' * len(c), 'tableA1_kstar_best_and_absolute.tex',
        pre=pre(['$G_\\mathrm{best}\\geq0.8$', '$G_\\mathrm{best}\\geq0.9$', 'nMSE$\\leq0.5$', 'nMSE$\\leq0.25$']))

SHORT = {'avgreg': 'avg-reg.', 'knn': 'kNN', 'ridge': 'ridge', 'krr': 'KRR', 'fa': 'FA'}

def table3(run='B_mteb_dense56', ksel=(4, 16), rules=('avgreg', 'knn', 'ridge', 'krr', 'fa'),
           sels=('random', 'gv_fa', 'dopt', 'gv_emp', 'kcenter', 'lev', 'qr', 'central', 'rawvar', 'popular'), out='table3_crossing.tex'):
    cur = curves(run)
    rows = []
    for k in ksel:
        rows.append(f'\\multicolumn{{{len(rules)+1}}}{{l}}{{\\emph{{$k={k}$}}}} \\\\')
        sub = cur[cur.k == k]
        best = {m: sub[(sub.method == m) & sub.selector.isin(sels)].nmse.min() for m in rules}
        for s in sels:
            cells = [SEL_LABEL[s]]
            for m in rules:
                r = sub[(sub.selector == s) & (sub.method == m)]
                if r.empty: cells.append('--'); continue
                r = r.iloc[0]; v = f'{r.nmse:.2f}\\,{{\\scriptsize$\\pm${(r.nmse_hi - r.nmse_lo)/2:.2f}}}'
                cells.append(f'\\textbf{{{v}}}' if np.isclose(r.nmse, best[m]) else v)
            rows.append(' & '.join(cells) + ' \\\\')
    tex(rows, ['selector'] + [SHORT[m] for m in rules], 'l' + 'r' * len(rules), out)

def pm(r, est='nmse', lo='nmse_lo', hi='nmse_hi', bold=False):
    v = f'{r[est]:.2f}\\,{{\\scriptsize$\\pm${(r[hi] - r[lo]) / 2:.2f}}}'
    return f'\\textbf{{{v}}}' if bold else v

def tableA3_oracle(ksel=(2, 4, 8), rule='krr'):
    """Oracle selection (uses the held-out model's own target scores) vs deployable selectors, same runs/reps."""
    rows = []
    for ds in ['mteb_dense56', 'helm_mmlu', 'helm', 'livebench', 'olb']:
        if not exists(f'oracle_{ds}.csv'): continue
        o = read(f'oracle_{ds}.csv'); o = o[o.method == rule]
        cells = []
        for k in ksel:
            d = o[o.k == k].set_index('selector')
            cells.append([pm(d.loc[s], 'est', 'lo', 'hi') if s in d.index else '--' for s in ['random', 'gv_fa', 'dopt', 'oracle']])
        for j, k in enumerate(ksel):
            rows.append(' & '.join([ds.replace('_', '-') if j == 0 else '', str(k)] + cells[j]))
        rows.append('\\midrule')
    rows = rows[:-1]
    tex(rows, ['dataset', '$k$', 'random', 'GV', 'D-opt', 'oracle'], 'lrrrrr', 'tableA3_oracle.tex')

def tableA4_leak(ksel=(2, 4, 8, 16), rule='krr'):
    """Selector fitted on training models only vs also on the held-out rows."""
    rows = []
    for ds in ['mteb_dense56', 'helm_mmlu']:
        if not exists(f'leak_{ds}.csv'): continue
        l = read(f'leak_{ds}.csv'); l = l[l.method == rule]
        for s in ['random', 'gv_fa', 'dopt']:
            cells = []
            for k in ksel:
                t = l[(l.selector == s) & (l.k == k) & (l.run == 'train_only')]; q = l[(l.selector == s) & (l.k == k) & (l.run == 'leak')]
                cells.append(f"{t.est.iloc[0]:.3f} / {q.est.iloc[0]:.3f}" if len(t) and len(q) else '--')
            rows.append(' & '.join([ds.replace('_', '-'), SEL_LABEL[s]] + cells))
    tex(rows, ['dataset', 'selector'] + [f'$k={k}$' for k in ksel], 'll' + 'r' * len(ksel), 'tableA4_leakage.tex')

def tableA5_synthetic(ksel=(2, 4, 8), rule='fa'):
    """SYNTHETIC matrices only: controlled data conditions (known truth). Never evidence about a real leaderboard."""
    c = read('conditions.csv'); c = c[c.run.str.startswith('B_syn') & (c.method == rule)]
    rows = []
    for run in sorted(c.run.unique()):
        for k in ksel:
            d = c[(c.run == run) & (c.k == k)].set_index('selector')
            if 'random' not in d.index: continue
            cells = [pm(d.loc[s]) if s in d.index else '--' for s in ['random', 'gv_fa', 'dopt']]
            rows.append(' & '.join([('syn.\\ ' + run[6:].replace('_', '-')) if k == ksel[0] else '', str(k), fmt(d.nmse_mean_baseline.iloc[0])] + cells))
        rows.append('\\midrule')
    tex(rows[:-1], ['SYNTHETIC matrix', '$k$', 'col.\\ mean', 'random', 'GV', 'D-opt'], 'lrrrrr', 'tableA5_synthetic.tex')

def kc(x):
    return '$>$32' if pd.isna(x) else str(int(x))

def tableA6_cluster_kstar(runs=('mteb_dense56', 'mteb_dense', 'mteb_mid', 'mteb_sparse', 'helm_mmlu'), sels=('random', 'gv_fa', 'dopt', 'central'), rules=('krr', 'fa'), gs=(0.8, 0.9)):
    """k* with dependence-robust intervals: CI rule (smallest k whose CI lower bound of G_own >= g) under the plain model bootstrap and the strict-family
    cluster bootstrap, and the range of the point k* over the repetitions (fold-assignment draws)."""
    rows = []; nsame = 0; n = 0
    for run in runs:
        c = read(f'cluster_kstar_B_{run}.csv')
        for rule in rules:
            for g in gs:
                sub = c[(c.method == rule) & (c.g == g)]
                cells = [f"{run.replace('_', '-')}" if (rule == rules[0] and g == gs[0]) else '', rule, f'{g:.1f}']
                a, b = [], []
                for s_ in sels:
                    q = sub[sub.selector == s_]
                    km = q[q.cluster == 'model'].kstar_ci.iloc[0]; kf = q[q.cluster == 'family'].kstar_ci.iloc[0]; ko = q[q.cluster == 'org'].kstar_ci.iloc[0]
                    a.append(f'{kc(km)}/{kc(kf)}')
                    rp = q[q.cluster.str.startswith('rep')].kstar_point.dropna()
                    lo_, hi_ = (rp.min() if len(rp) else np.nan), (rp.max() if len(rp) else np.nan)
                    b.append(kc(lo_) if (lo_ == hi_ or pd.isna(lo_) or pd.isna(hi_)) and not (pd.isna(lo_) != pd.isna(hi_)) else f'{kc(lo_)}--{kc(hi_)}')
                rows.append(' & '.join(cells + a + b))
        rows.append('\\midrule')
    lab = ['rand.', 'GV', 'D-opt', 'central']
    hdr = ['dataset', 'rule', '$g$'] + lab + lab
    p = ' & & & \\multicolumn{4}{c}{$k^\\star$ (CI rule): model / family} & \\multicolumn{4}{c}{point $k^\\star$ over repetitions} \\\\\n\\cmidrule(lr){4-7}\\cmidrule(lr){8-11}'
    tex(rows[:-1], hdr, 'llr' + 'r' * 8, 'tableA6_cluster_kstar.tex', pre=p)

def tableA7_kstar_shift(sels=('random', 'gv_fa', 'dopt'), rules=('krr', 'fa'), g='k*G_own>=0.8'):
    """k*(G_own >= 0.8) under random folds and under the three shift splits (same selectors, rules, protocol B)."""
    t = read('kstar_table.csv'); gc = read('group_counts.csv').set_index('run')
    spl = [('random folds', 'B_mteb_dense56', 'B_mteb_dense', None), ('org.\\ leave-out', 'd56_group', 'd275_group', 'group'),
           ('family leave-out', 'd56_famgroup', 'd275_famgroup', 'famgroup'), ('temporal', 'd56_temporal', 'd275_temporal', None)]
    rows = []
    for dname, col in [('MTEB-56', 1), ('MTEB-275', 2)]:
        for lab, *runs, _ in spl:
            run = runs[col - 1]
            for rule in rules:
                sub = t[(t.run == run) & (t.method == rule)].set_index('selector')
                cells = [dname if (lab == spl[0][0] and rule == rules[0]) else '', lab if rule == rules[0] else '', rule, fmt(sub.nmse_floor_own.iloc[0]), fmt(sub.nmse_mean_k0.iloc[0])]
                cells += [ks(sub.loc[s_, g]) if s_ in sub.index else '--' for s_ in sels]
                rows.append(' & '.join(cells))
        rows.append('\\midrule')
    tex(rows[:-1], ['matrix', 'split', 'rule', 'floor', 'col.\\ mean', 'rand.', 'GV', 'D-opt'], 'lllrrrrr', 'tableA7_kstar_shift.tex',
        pre=' & & & & & \\multicolumn{3}{c}{$k^\\star(G\\geq0.8)$} \\\\\n\\cmidrule(lr){6-8}')

def tableA8_ood(ks_=(4, 8, 16), rule='krr'):
    """Out-of-range detector: Mahalanobis distance of the k revealed scores (flag: chi-square 95%) against the model's own nMSE (selector gv_fa; experiment-repo ood_detector.py)."""
    runs = [('MTEB-56', 'random folds', 'ood_B_mteb_dense56.csv'), ('MTEB-56', 'org.\\ leave-out', 'ood_d56_group.csv'), ('MTEB-56', 'family leave-out', 'ood_d56_famgroup.csv'),
            ('MTEB-56', 'temporal', 'ood_d56_temporal.csv'), ('MTEB-275', 'random folds', 'ood_B_mteb_dense.csv'), ('MTEB-275', 'org.\\ leave-out', 'ood_d275_group.csv'),
            ('MTEB-275', 'temporal', 'ood_d275_temporal.csv')]
    rows = []
    for ds, sp, f in runs:
        d = read(f); d = d[d.method == rule]
        for j, k in enumerate(ks_):
            r = d[d.k == k].iloc[0]
            ci = lambda v, lo, hi: f'{v:.2f} {{\\scriptsize[{lo:.2f}, {hi:.2f}]}}'
            rows.append(' & '.join([f'{ds}, {sp}' if j == 0 else '', str(k), f'{int(r.n_flagged)}/{int(r.n_models)}', f'{r.auc_top_tercile:.2f}',
                                    (ci(r.nmse_flagged, r.nmse_flagged_lo, r.nmse_flagged_hi) if r.n_flagged >= 3 else f'{r.nmse_flagged:.2f} {{\\scriptsize[n/a]}}') if r.n_flagged > 0 else '--', ci(r.nmse_unflagged, r.nmse_unflagged_lo, r.nmse_unflagged_hi)]))
        rows.append('\\midrule')
    tex(rows[:-1], ['matrix, split', '$k$', 'flagged', 'AUC', 'nMSE flagged', 'nMSE unflagged'], 'lrrrcc', 'tableA8_ood_detector.tex')

def mm(x):
    return f'{x:.2f}'.replace('-', '$-$')

def tableA9_kstar_split(sels=('random', 'gv_fa', 'dopt', 'central'), rules=('krr', 'fa'), g=0.8):
    """k*(G_own >= g) by split and clustering: random folds with the CI rule under the model / organisation / strict-family cluster bootstrap and
    [2.5, 97.5]% of the point k* over the bootstrap resamples; then the three shift splits (CI rule of the plain bootstrap, as Table 2)."""
    col = f'k*G_own>={g}'
    sets = [('MTEB-56', 'mteb_dense56', 'd56'), ('MTEB-275', 'mteb_dense', 'd275'), ('MTEB-472', 'mteb_sparse', None), ('HELM-MMLU', 'helm_mmlu', None)]
    rows = []
    for name, d, sh in sets:
        c = read(f'cluster_kstar_B_{d}.csv'); c = c[c.g == g]
        shift = {s_: read(f'kstar_gap_{sh}_{s_}.csv').set_index(['selector', 'method']) if sh else None for s_ in ('group', 'famgroup', 'temporal')}
        for rule in rules:
            for sel in sels:
                cells = [name if (rule == rules[0] and sel == sels[0]) else '', rule if sel == sels[0] else '', SHORT_SEL[sel]]
                for cl in ('model', 'org', 'family'):
                    q = c[(c.cluster == cl) & (c.selector == sel) & (c.method == rule)].iloc[0]
                    cells.append(f'{kc(q.kstar_ci)} {{\\scriptsize[{kc(q.boot_lo)}--{kc(q.boot_hi)}]}}')
                for s_ in ('group', 'famgroup', 'temporal'):
                    t = shift[s_]
                    cells.append('--' if (t is None or (sel, rule) not in t.index) else ks(t.loc[(sel, rule), col]))
                rows.append(' & '.join(cells))
            rows.append('\\cmidrule(lr){2-9}' if rule != rules[-1] else '\\midrule')
    pre_ = (' & & & \\multicolumn{3}{c}{random folds: $k^\\star$ [95\\% interval of point $k^\\star$]} & \\multicolumn{3}{c}{shift splits} \\\\\n'
            '\\cmidrule(lr){4-6}\\cmidrule(lr){7-9}')
    tex(rows[:-1], ['matrix', 'rule', 'selector', 'model CI', 'org. CI', 'family CI', 'org. out', 'family out', 'temporal'], 'lllcccrrr', 'tableA9_kstar_split.tex', pre=pre_)

SHORT_SEL = {'random': 'random', 'gv_fa': 'GV', 'dopt': 'D-opt', 'central': 'central', 'adapt_loc': 'adaptive GV', 'fwd_ridge': 'fwd. ridge', 'mtl': 'multi-task lasso'}

def tableA10_extra_selectors(ds=(('MTEB-56', 'mteb_dense56'), ('MTEB-275', 'mteb_dense'), ('HELM-MMLU', 'helm_mmlu')), ksel=(1, 2, 4, 8, 16),
                             sels=('random', 'central', 'gv_fa', 'dopt', 'adapt_loc', 'fwd_ridge', 'mtl'), rule='krr'):
    """nMSE (95% bootstrap CI half-width over models) of every selector at k in ksel (kernel ridge, random folds), and in a second file the paired
    difference to random and to GV (* = family-cluster 95% CI excludes 0)."""
    rows, prow = [], []
    for name, d in ds:
        c = read(f'xcurves_sel_B_{d}.csv'); c = c[c.method == rule]
        p = read(f'xpaired_sel_B_{d}.csv'); p = p[(p.method == rule) & (p.cluster == 'family')]
        rows.append(f'\\multicolumn{{{1 + len(ksel)}}}{{l}}{{\\emph{{{name}}}}} \\\\'); prow.append(f'\\multicolumn{{{1 + 2 * len(ksel)}}}{{l}}{{\\emph{{{name}}}}} \\\\')
        for s_ in sels:
            cells = [SHORT_SEL[s_]]
            for k in ksel:
                r = c[(c.selector == s_) & (c.k == k)].iloc[0]
                cells.append(f'{r.nmse:.2f}\\,{{\\scriptsize$\\pm${(r.nmse_hi - r.nmse_lo) / 2:.2f}}}')
            rows.append(' & '.join(cells))
            if s_ == 'random': continue
            pc = [SHORT_SEL[s_]]
            for ref in ('random', 'gv_fa'):
                for k in ksel:
                    q = p[(p.a == s_) & (p.b == ref) & (p.k == k)]
                    if s_ == ref or s_ == 'random' or q.empty: pc.append('--'); continue
                    q = q.iloc[0]; star = '$^*$' if (q.hi < 0 or q.lo > 0) else ''
                    pc.append(mm(q['diff']) + star)
            prow.append(' & '.join(pc))
        rows.append('\\midrule'); prow.append('\\midrule')
    tex(rows[:-1], ['selector'] + [str(k) for k in ksel], 'l' + 'r' * len(ksel), 'tableA10_extra_selectors.tex', pre=' & \\multicolumn{%d}{c}{nMSE (KRR), number of benchmarks run $k$} \\\\\n\\cmidrule(lr){2-%d}' % (len(ksel), 1 + len(ksel)))
    tex(prow[:-1], ['selector'] + [str(k) for _ in range(2) for k in ksel], 'l' + 'r' * (2 * len(ksel)), 'tableA10c_extra_selectors_paired.tex',
        pre=' & \\multicolumn{%d}{c}{$\\Delta$ nMSE vs random} & \\multicolumn{%d}{c}{$\\Delta$ nMSE vs GV} \\\\\n\\cmidrule(lr){2-%d}\\cmidrule(lr){%d-%d}' % (len(ksel), len(ksel), 1 + len(ksel), 2 + len(ksel), 1 + 2 * len(ksel)))

def tableA10b_extra_rules(ds=(('MTEB-56', 'mteb_dense56'), ('MTEB-275', 'mteb_dense'), ('HELM-MMLU', 'helm_mmlu')), ksel=(2, 4, 8, 16),
                          rules=('krr', 'fa', 'fa_r1', 'fa_r2', 'ols', 'softimpute'), sels=('random', 'gv_fa')):
    RN = {'krr': 'kernel ridge', 'fa': 'FA (CV rank)', 'fa_r1': 'FA, $r=1$', 'fa_r2': 'FA, $r=2$', 'ols': 'OLS', 'softimpute': 'soft-impute'}
    rows = []
    for name, d in ds:
        c = read(f'xcurves_sel_B_{d}.csv')
        rows.append(f'\\multicolumn{{9}}{{l}}{{\\emph{{{name}}}}} \\\\')
        for m in rules:
            cells = [RN[m]]
            for s_ in sels:
                for k in ksel:
                    r = c[(c.selector == s_) & (c.method == m) & (c.k == k)].iloc[0]
                    cells.append(f'{r.nmse:.2f}{{\\tiny$\\pm${(r.nmse_hi - r.nmse_lo) / 2:.2f}}}')
            rows.append(' & '.join(cells))
        rows.append('\\midrule')
    pr = ' & \\multicolumn{4}{c}{random selection} & \\multicolumn{4}{c}{greedy cond. variance} \\\\\n\\cmidrule(lr){2-5}\\cmidrule(lr){6-9}'
    tex(rows[:-1], ['rule'] + [str(k) for _ in sels for k in ksel], 'l' + 'r' * 8, 'tableA10b_extra_rules.tex', pre=pr)

def tableA11_temporal_drift(ks_=(2, 4, 8, 16)):
    """(a) single temporal fold (selector GV): inference rules incl. unshrunk and trend; (b) rolling-origin evaluation (4 origins pooled), random vs GV selection."""
    ds = [('MTEB-56', 'd56_temporal', 'mteb_dense56'), ('MTEB-275', 'd275_temporal', 'mteb_dense')]
    RN = {'fa': 'FA', 'krr': 'KRR', 'ols': 'OLS (unshrunk)', 'trend_fa': 'FA + trend', 'trend_ols': 'OLS + trend', 'avgreg': 'avg.-score regression', 'softimpute': 'soft-impute',
          'mean': 'column mean ($k=0$)', 'trend': 'column mean + trend ($k=0$)'}
    def cell(r): return f'{r.nmse:.2f}{{\\tiny$\\pm${(r.hi - r.lo) / 2:.2f}}}'
    rows = ['\\multicolumn{9}{l}{\\emph{(a) single temporal fold, selector GV, test = newest $\\approx$20\\% of dated models}} \\\\']
    xc = {r: read(f'xcurves_rules_{r}.csv') for _, r, _ in ds}; xf = {r: read(f'xfloor_rules_{r}.csv').set_index('method') for _, r, _ in ds}
    for m in ['fa', 'krr', 'ols', 'softimpute', 'trend_fa', 'trend_ols', 'avgreg']:
        cells = [RN[m]]
        for _, r, _ in ds:
            c = xc[r]; c = c[(c.selector == 'gv_fa') & (c.method == m)]
            for k in ks_:
                q = c[c.k == k]
                cells.append('--' if q.empty else f'{q.iloc[0].nmse:.2f}{{\\tiny$\\pm${(q.iloc[0].nmse_hi - q.iloc[0].nmse_lo) / 2:.2f}}}')
        rows.append(' & '.join(cells))
    cells = [RN['mean']]
    for _, r, _ in ds: cells.append(f'\\multicolumn{{4}}{{c}}{{{xf[r].loc["mean_k0", "nmse_floor"]:.2f}}}')
    rows.append(' & '.join(cells)); rows.append('\\midrule')
    e = read('extra_temporal_summary.csv'); e = e[e.split == 'temporal']
    rows.append('\\multicolumn{9}{l}{\\emph{(b) rolling origin (cutoffs 55/65/75/85\\%, next 15\\% as test), pooled}} \\\\')
    for sel, sl in [('random', 'random'), ('gv_fa', 'GV')]:
        for m in ['fa', 'krr', 'softimpute', 'trend_fa']:
            cells = [f'{RN.get(m, m)}, {sl}']
            for _, _, d in ds:
                q = e[(e.dataset == d) & (e.sel == sel) & (e.method == m)]
                for k in ks_:
                    z = q[q.k == k]; cells.append('--' if z.empty else cell(z.iloc[0]))
            rows.append(' & '.join(cells))
    for m in ['mean', 'trend']:
        cells = [RN[m]]
        for _, _, d in ds:
            z = e[(e.dataset == d) & (e.method == m) & (e.k == 0)]
            cells.append('--' if z.empty else f'\\multicolumn{{4}}{{c}}{{{z.iloc[0].nmse:.2f}}}')
        rows.append(' & '.join(cells))
    pr = ' & \\multicolumn{4}{c}{MTEB-56} & \\multicolumn{4}{c}{MTEB-275} \\\\\n\\cmidrule(lr){2-5}\\cmidrule(lr){6-9}'
    tex(rows, ['rule'] + [str(k) for _ in ds for k in ks_], 'l' + 'r' * 8, 'tableA11_temporal_drift.tex', pre=pr)

if __name__ == '__main__':
    table1(); table2(); tableA1(); table3()
    table3(ksel=(2, 4, 8, 16), sels=('random', 'gv_fa', 'dopt', 'kcenter', 'lev', 'central'), out='table3_crossing.tex')
    table3(ksel=(2, 4, 8, 16), out='tableA2_crossing_all.tex')
    tableA3_oracle(); tableA4_leak(); tableA5_synthetic(); tableA6_cluster_kstar(); tableA7_kstar_shift(); tableA8_ood(); tableA9_kstar_split(); tableA10_extra_selectors(); tableA10b_extra_rules(); tableA11_temporal_drift()
