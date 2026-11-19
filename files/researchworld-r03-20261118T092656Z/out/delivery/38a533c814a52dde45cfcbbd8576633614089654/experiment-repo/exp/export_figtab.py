"""Export result files in the long-form schema of figtab-repo/schema.md into figdata/ (README written alongside).
python exp/export_figtab.py [--only curves,references,...]
All CIs: percentile bootstrap (B=2000) over held-out models (the unit of replication); for quantities that exist only per
cross-fit unit (forecasts, synthetic cells) the bootstrap is over those units. Metrics are in standardised units.
Every function skips what has not been computed; nothing is filled in."""
import sys, os, glob, json, argparse, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
import numpy as np, pandas as pd
import analysis as A

OUT = 'figdata'
B = 2000
MAIN = ['A1', 'A2', 'B', 'OLMB40', 'HELMMMLU', 'HELMLITE', 'OLMB6', 'LIVEBENCH']
LLM = ['OLMB40', 'HELMMMLU', 'HELMLITE', 'OLMB6', 'LIVEBENCH']
SPARSE = ['B', 'LIVEBENCH']
NRAND = {'OLMB40': 30}
os.makedirs(OUT, exist_ok=True)


def setting_of(m): return 'B' if m in SPARSE else 'A'
def split_of(m): return 'family' if m in LLM else 'random'


def boot(V, f=lambda x: x, seed=0):
    """V (n_units, ...) per-unit values; returns mean, lo, hi of f(mean over resampled units)."""
    idx = A.boot_idx(len(V), B, seed)
    est = V.mean(0); bs = V[idx].mean(1)
    lo, hi = np.percentile(bs, [2.5, 97.5], axis=0)
    return f(est), f(lo), f(hi)


def load_pm(d):
    if not glob.glob(f"results/{d}/rec_rep*.parquet"): return None
    return A.per_model(A.load(f"results/{d}"))


def curve_rows(pm, matrix, target, split, setting, nrand):
    rows = []
    for (sel, me), g in pm.groupby(['selector', 'method']):
        ndr = nrand if sel == 'random' else 1
        P = {c: g.pivot(index='model', columns='k', values=c) for c in ('mse', 'pw_acc', 'spear', 't10_tp', 't10_fp', 't10_fn')}
        ks = P['mse'].columns
        for metric, src in (('rmse', 'mse'), ('pair_acc', 'pw_acc'), ('spearman', 'spear')):
            Q = P[src].dropna(axis=0, how='any')
            if len(Q) < 3: continue
            m, lo, hi = boot(Q.values, np.sqrt if metric == 'rmse' else (lambda x: x))
            for j, k in enumerate(Q.columns):
                rows.append((matrix, setting, split, target, sel, me, int(k), metric, m[j], lo[j], hi[j], len(Q), ndr))
        T = [P[c].reindex(columns=ks) for c in ('t10_tp', 't10_fp', 't10_fn')]
        ok = T[0].dropna(axis=0, how='any').index
        if len(ok) >= 3 and T[0].loc[ok].values.sum() + T[1].loc[ok].values.sum() > 0:
            tp, fp, fn = [t.loc[ok].values for t in T]
            idx = A.boot_idx(len(ok), B, 1)
            f1 = lambda a, b, c: 2 * a / np.maximum(2 * a + b + c, 1e-12)
            est = f1(tp.sum(0), fp.sum(0), fn.sum(0))
            bs = f1(tp[idx].sum(1), fp[idx].sum(1), fn[idx].sum(1))
            lo, hi = np.percentile(bs, [2.5, 97.5], axis=0)
            for j, k in enumerate(ks):
                rows.append((matrix, setting, split, target, sel, me, int(k), 'top10', est[j], lo[j], hi[j], len(ok), ndr))
    return rows


COLS = ['matrix', 'setting', 'split', 'target', 'selector', 'inference', 'k', 'metric', 'mean', 'ci_lo', 'ci_hi', 'n_models', 'n_draws']


def do_curves():
    rows = []
    for m in MAIN:
        pm = load_pm(m)
        if pm is not None: rows += curve_rows(pm, m, 'all', split_of(m), setting_of(m), NRAND.get(m, 100))
    for d in sorted(glob.glob('results/A[12]_tgt*')):
        name = os.path.basename(d); m, grp = name.split('_tgt')
        pm = load_pm(name)
        if pm is not None: rows += curve_rows(pm, m, f'group:{grp}', 'random', 'A', 100)
    for name in ('A1_cost', 'A2_cost', 'A1_costA', 'A2_costA'):
        pm = load_pm(name)
        if pm is not None: rows += curve_rows(pm, name.split('_')[0], 'cost', 'random', 'A', 100)
    df = pd.DataFrame(rows, columns=COLS); df.to_csv(f'{OUT}/curves.csv', index=False)
    # inference ablation: every inference method on one fixed selector
    ab = df[(df.target == 'all') & (df.selector.isin(['greedyAcomp', 'random']))]
    ab[['matrix', 'selector', 'inference', 'k', 'metric', 'mean', 'ci_lo', 'ci_hi', 'n_models']].to_csv(f'{OUT}/inference_ablation.csv', index=False)
    print('curves', len(df))


def do_references():
    rows = []
    for m in MAIN:
        d = f'results/{m}'
        pm = load_pm(m)
        if pm is None: continue
        sp, st = split_of(m), setting_of(m)
        # mean predictor (history mean): selector-independent, take the selector 'random' cell
        g = pm[(pm.selector == 'random') & (pm.method == 'mean')]
        if len(g):
            P = g.pivot(index='model', columns='k', values='mse').dropna()
            mm, lo, hi = boot(P.values, np.sqrt)
            for j, k in enumerate(P.columns):
                rows.append((m, st, sp, int(k), 'rmse', 'mean_predictor', mm[j], lo[j], hi[j]))
        # empirical floor: all other benchmarks of the model (e_floor.py), constant in k
        if os.path.exists(f'{d}/floor.csv'):
            F = pd.read_csv(f'{d}/floor.csv').groupby('model').mse.mean().values
            mm, lo, hi = boot(F[:, None], np.sqrt)
            ks = sorted(pm.k.unique())
            for k in ks: rows.append((m, st, sp, int(k), 'rmse', 'empirical_floor', mm[0], lo[0], hi[0]))
        if os.path.exists(f'{d}/h1.csv'):
            R = pd.read_csv(f'{d}/h1.csv')
            for kind, col in (('forecast', 'fm'), ('forecast_noinfl', 'fm_noinfl'), ('forecast_naive', 'naive'), ('lower_bound', 'floor')):
                for k, g in R.groupby('k'):
                    mm, lo, hi = boot(g[[col]].values, np.sqrt)
                    rows.append((m, st, sp, int(k), 'rmse', kind, mm[0], lo[0], hi[0]))
    df = pd.DataFrame(rows, columns=['matrix', 'setting', 'split', 'k', 'metric', 'kind', 'value', 'ci_lo', 'ci_hi'])
    df.to_csv(f'{OUT}/references.csv', index=False); print('references', len(df))


def do_synth():
    fs = sorted(glob.glob('results/E1/e1_shard*.parquet'))
    if not fs: return
    D = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    D = D[D.plug == 'cv']
    rows = []
    for (kind, h, M, k), g in D.groupby(['kind', 'h', 'M', 'k']):
        for fc in ('fm', 'naive', 'oracle', 'fm_noinfl'):
            if g[fc].isna().all(): continue
            ok = g.dropna(subset=[fc, 'measured'])
            pm_ = np.sqrt(ok[fc].mean())
            mm, lo, hi = boot(ok[['measured']].values, np.sqrt)
            rows.append((kind, M, round(h / (1 - h), 4), h, k, 'greedyAcomp', fc, pm_, mm[0], lo[0], hi[0], ok.rep.nunique()))
    df = pd.DataFrame(rows, columns=['spectrum', 'M', 'snr', 'latent_var_frac', 'k', 'selector', 'forecast', 'predicted_rmse', 'measured_rmse', 'ci_lo', 'ci_hi', 'n_rep'])
    df.to_csv(f'{OUT}/synthetic_grid.csv', index=False); print('synthetic', len(df))


def do_paired():
    rows = []
    for m in MAIN:
        pm = load_pm(m)
        if pm is None: continue
        P = f'results/{m}/primary.csv'
        cells = set(zip(pm.selector, pm.method))
        if os.path.exists(P):
            T = pd.read_csv(P)
            for _, r in T.iterrows():
                fam = 'primary'
                base = pm[(pm.selector == 'random') & (pm.method == 'fa')]  # only for naming
                rows.append((fam, r.test + (' [post-pilot]' if r.post_pilot else ''), m, 'all', int(r.k), 'mse', r['diff'], r.lo, r.hi, r.p_holm, 'holm'))
                rows.append((fam, r.test + (' [post-pilot]' if r.post_pilot else ''), m, 'all', int(r.k), 'rel_mse', r.rel, r.lo * r.rel / r['diff'] if r['diff'] != 0 else np.nan,
                             r.hi * r.rel / r['diff'] if r['diff'] != 0 else np.nan, r.p_holm, 'holm'))
        # exploratory: each (selector, FA) vs random (FA), and each inference method vs FA at greedyAcomp; BH over the family
        ex = []
        for s in sorted({s for s, me in cells if me == 'fa' and s != 'random'}):
            ex.append((f'{s}+fa vs random+fa', (s, 'fa'), ('random', 'fa')))
        for me in sorted({me for s, me in cells if s == 'greedyAcomp' and me != 'fa'}):
            ex.append((f'greedyAcomp: {me} vs fa', ('greedyAcomp', me), ('greedyAcomp', 'fa')))
        if ('greedyAcomp', 'fa') in cells and ('greedyA', 'fa') in cells:
            ex.append(('greedyAcomp+fa vs greedyA+fa', ('greedyAcomp', 'fa'), ('greedyA', 'fa')))
        er = []
        for name, a_, b_ in ex:
            ks = [k for k in sorted(pm.k.unique()) if k in (1, 2, 3, 5, 8, 12, 20)]
            t = A.paired(pm, a_, b_, 'mse', ks=ks)
            t['test'] = name; er.append(t)
        if er:
            E = pd.concat(er, ignore_index=True)
            # Benjamini-Hochberg over the exploratory family of this matrix
            p = E.p.values; o = np.argsort(p); n = len(p); adj = np.empty(n); run = 1.0
            for rank in range(n - 1, -1, -1):
                run = min(run, p[o[rank]] * n / (rank + 1)); adj[o[rank]] = run
            E['p_bh'] = adj
            for _, r in E.iterrows():
                rows.append(('exploratory', r.test, m, 'all', int(r.k), 'mse', r['diff'], r.lo, r.hi, r.p_bh, 'bh'))
                s_ = r.rel / r['diff'] if r['diff'] != 0 else np.nan
                rows.append(('exploratory', r.test, m, 'all', int(r.k), 'rel_mse', r.rel, r.lo * s_, r.hi * s_, r.p_bh, 'bh'))
    df = pd.DataFrame(rows, columns=['family', 'comparison', 'matrix', 'target', 'k', 'metric', 'diff', 'ci_lo', 'ci_hi', 'p_adj', 'adj'])
    df.to_csv(f'{OUT}/paired.csv', index=False); print('paired', len(df))


def participation_ratio(m):
    from settings import mteb_setting, llm_setting
    s = llm_setting(m) if m in LLM else mteb_setting(m)
    X, obs = s['X'], s['obs']
    cnt = obs.sum(0).clip(min=1); mu = np.where(obs, X, 0).sum(0) / cnt
    sd = np.sqrt((np.where(obs, X - mu, 0) ** 2).sum(0) / np.maximum(cnt - 1, 1)).clip(min=1e-8)
    Z = np.where(obs, (X - mu) / sd, 0.0)
    # pairwise-complete correlation
    O = obs.astype(float); num = Z.T @ Z; cn = O.T @ O
    C = num / np.maximum(cn, 1)
    ev = np.clip(np.linalg.eigvalsh((C + C.T) / 2), 0, None)
    return X.shape, obs.mean(), float(ev.sum() ** 2 / (ev ** 2).sum()), float(ev.max() / ev.sum())


def do_data_table():
    meta = {
        'A1': ('MTEB results repo (embeddings-benchmark/results), peeled complete block', 'git 6dabbcc68c28', 'CC0-1.0 (GitHub repository licence, checked via API 2026-11-18)'),
        'A2': ('MTEB results repo, 30 most-covered tasks', 'git 6dabbcc68c28', 'as A1'),
        'B': ('MTEB results repo, sparse block', 'git 6dabbcc68c28', 'as A1'),
        'OLMB40': ('Open LLM Leaderboard v2 per-subtask results (HF open-llm-leaderboard/results)', 'commit aa81ecc38fdc', 'none stated on dataset'),
        'OLMB6': ('Open LLM Leaderboard v2 contents (HF)', 'commit 9c09a7cae433', 'none stated on dataset card'),
        'HELMMMLU': ('HELM MMLU 57 subjects (crfm-helm-public)', 'v1.13.0', 'none stated in bucket; HELM code Apache-2.0'),
        'HELMLITE': ('HELM Lite (crfm-helm-public)', 'v1.13.0', 'none stated in bucket; HELM code Apache-2.0'),
        'LIVEBENCH': ('LiveBench model_judgment (HF), 7-task snapshot', 'commit 9704e5da7bfb', 'none stated on dataset card'),
    }
    rows = []
    for m in MAIN:
        (M, N), dens, pr, top = participation_ratio(m)
        r = ''
        fr = f'results/{m}/fa_rank.csv'
        if os.path.exists(fr):
            x = pd.read_csv(fr); r = float(x.r.median())
        rows.append((m, M, N, round(float(dens), 4), r, round(pr, 2), *meta[m]))
    df = pd.DataFrame(rows, columns=['matrix', 'M', 'N', 'density', 'rank_heldout_ll', 'participation_ratio', 'source', 'version', 'licence'])
    df['top_eig_share'] = [round(participation_ratio(m)[3], 3) for m in MAIN]
    df.to_csv(f'{OUT}/data_table.csv', index=False); print('data_table', len(df))


def do_conditions():
    """Per real matrix: FA latent share of variance h (as latent_var_frac in synthetic_grid: sum Lam^2 / (sum Lam^2 + sum psi) on
    history-standardised columns) and fitted rank, over every stored fold fit."""
    rows = []
    for m in MAIN:
        h, r = [], []
        for f in sorted(glob.glob(f'results/{m}/fit_*.npz')):
            z = np.load(f, allow_pickle=True); L = z['Lam']; p = z['psi']
            h.append((L ** 2).sum() / ((L ** 2).sum() + p.sum())); r.append(L.shape[1])
        if not h: continue
        rows.append((m, len(h), np.median(h), np.min(h), np.max(h), np.median(r), np.min(r), np.max(r)))
    pd.DataFrame(rows, columns=['matrix', 'n_fits', 'latent_var_frac', 'latent_var_frac_min', 'latent_var_frac_max',
                                'fa_rank', 'fa_rank_min', 'fa_rank_max']).to_csv(f'{OUT}/real_conditions.csv', index=False)
    print('conditions', len(rows))


def meanpred_kstar_rows():
    """Real-matrix k* on the synthetic axis: first k with sqrt(MSE(greedyAcomp, FA) / MSE(mean predictor)) <= tau (empirical, ratio of
    unit-mean MSEs), and the model rule sqrt(mean fm / MSE(mean predictor)) for the matrices with a forecast (h1.csv)."""
    out = []
    for m in MAIN:
        pm = load_pm(m)
        if pm is None: continue
        a = pm[(pm.selector == 'greedyAcomp') & (pm.method == 'fa')].pivot(index='model', columns='k', values='mse').dropna()
        b = pm[(pm.selector == 'random') & (pm.method == 'mean')].pivot(index='model', columns='k', values='mse').dropna()
        ks = sorted(set(a.columns) & set(b.columns))
        if not ks: continue
        a, b = a[ks], b[ks]; idx = a.index.intersection(b.index)
        ratio = {'empirical': np.sqrt(a.loc[idx].mean().values / b.loc[idx].mean().values)}
        if os.path.exists(f'results/{m}/h1.csv'):
            R = pd.read_csv(f'results/{m}/h1.csv').groupby('k').fm.mean()
            ok = [k for k in ks if k in R.index]
            ratio['model'] = np.array([np.sqrt(R[k] / b.loc[idx, k].mean()) if k in R.index else np.nan for k in ks])
        kmax = max(ks)
        for rule, v in ratio.items():
            for tau in (0.5, 0.7):
                hit = [k for k, x in zip(ks, v) if x <= tau]
                out.append((f'{m}|{split_of(m)}', '', '', '', 0.0, rule, 'rmse_over_meanpred', tau, hit[0] if hit else kmax + 1,
                            np.nan, np.nan, 'greedyAcomp', 'fa', np.nan, np.nan, np.nan, np.nan, 0.0 if hit else 1.0, len(idx)))
    return out


def do_shift_kstar_cost():
    # shift.csv + kstar.csv (E6, E1, E8) + cost.csv (E2)
    f = 'results/E6/shift_summary.csv'
    ks_rows = []
    if os.path.exists(f):
        S = pd.read_csv(f); U = pd.read_csv('results/E6/stopping_error.csv')
        ref = U[U.tol == 0.6].set_index(['matrix', 'split', 'selector', 'inference', 'rule'])
        def kst(r, rule):
            key = (r.matrix, r.split, r.selector, r.inference, rule)
            return ref.kstar_rule_median.get(key, np.nan) if key in ref.index else np.nan
        S['kstar_model'] = [kst(r, 'model') for r in S.itertuples()]
        S['kstar_conformal'] = [kst(r, 'conformal') for r in S.itertuples()]
        out = S.rename(columns={'rmse_lo': 'ci_lo', 'rmse_hi': 'ci_hi'})[['matrix', 'split', 'selector', 'inference', 'k', 'rmse', 'ci_lo', 'ci_hi', 'coverage', 'coverage_lo', 'coverage_hi',
                                                                          'coverage_conformal', 'nominal', 'rmse_meanpred', 'pred_rmse', 'kstar_model', 'kstar_conformal', 'n_units']]
        out.to_csv(f'{OUT}/shift.csv', index=False)
        for r in U.itertuples():
            ks_rows.append((f'{r.matrix}|{r.split}', '', '', '', 0.0, f'{r.rule}', 'rmse_std' if r.rule != 'conformal_q' else 'rmse_std_q90', r.tol, r.kstar_rule_median, np.nan, np.nan,
                            r.selector, r.inference, r.kstar_true_median, r.mean_signed_log2_ratio, r.lo, r.hi, r.frac_censored, r.n_units))
    g = 'results/E8/gap_cells.csv'
    if os.path.exists(g):
        G = pd.read_csv(g)
        for eps in (0.5, 0.6, 0.7):
            for (st, M, mk), d in G.groupby(['setting', 'M', 'mask']):
                d = d.sort_values('k')
                for rule, col in (('empirical', 'rmse_measured'), ('model', 'fm')):
                    v = d[col].values if col == 'rmse_measured' else np.sqrt(d[col].values)
                    ok = d.k.values[v <= eps]
                    ks_rows.append((st, '', '', M, mk, rule, 'rmse_std', eps, int(ok[0]) if len(ok) else 60, np.nan, np.nan, 'greedyAcomp', 'fa', np.nan, np.nan, np.nan, np.nan, np.nan, int(d.n_rep.iloc[0])))
    h = 'results/E1/h5_cells.csv'
    if os.path.exists(h):
        G = pd.read_csv(h); G = G[G.plug == 'cv']
        for tau in (0.7, 0.5):
            for (kd, hh, M), d in G.groupby(['kind', 'h', 'M']):
                d = d.sort_values('k')
                for rule, col in (('empirical', 'measured'), ('model', 'fm'), ('oracle', 'oracle')):
                    ok = d.k.values[np.sqrt(d[col].values / d.mean_pred.values) <= tau]
                    ks_rows.append(('synthetic', kd, hh, M, 0.0, rule, 'rmse_over_meanpred', tau, int(ok[0]) if len(ok) else 21, np.nan, np.nan, 'greedyAcomp', 'fa', np.nan, np.nan, np.nan, np.nan, np.nan, int(d.n_rep.iloc[0])))
    ks_rows += meanpred_kstar_rows()
    if ks_rows:
        pd.DataFrame(ks_rows, columns=['matrix/scenario', 'spectrum', 'snr', 'M', 'missingness', 'rule', 'metric', 'tol', 'kstar', 'ci_lo', 'ci_hi', 'selector', 'inference',
                                       'kstar_truth', 'mean_signed_log2_ratio_vs_truth', 'ratio_ci_lo', 'ratio_ci_hi', 'frac_censored', 'n_units']).to_csv(f'{OUT}/kstar.csv', index=False)
    c = 'results/E2/cost_curve.csv'
    if os.path.exists(c):
        C = pd.read_csv(c)
        nm = {('greedyAcost', 'fa'): 'cost_aware', ('greedyA', 'fa'): 'cost_ignorant', ('random', 'fa'): 'random'}
        C['selector_schema'] = [nm.get((r.selector, r.inference), f'{r.selector}|{r.inference}') for r in C.itertuples()]
        C.rename(columns={'budget_sec': 'budget'})[['matrix', 'selector_schema', 'selector', 'inference', 'budget', 'budget_frac', 'rmse', 'ci_lo', 'ci_hi', 'n_models']].rename(columns={'selector_schema': 'selector_class'}).to_csv(f'{OUT}/cost.csv', index=False)
    if os.path.exists('results/B/primary.csv'):      # setting B primary family (Holm over 33 tests; cluster/leverage not run on B)
        pd.read_csv('results/B/primary.csv').to_csv(f'{OUT}/primary_B.csv', index=False)
    for src, dst in (('group_paired', 'group_paired'), ('cost_paired', 'cost_paired')):   # E2 paired tests (families G, P4), columns as in results/E2
        if os.path.exists(f'results/E2/{src}.csv'):
            pd.read_csv(f'results/E2/{src}.csv').to_csv(f'{OUT}/{dst}.csv', index=False)
    print('shift/kstar/cost done', len(ks_rows))


def do_h3():
    """selector x inference cross (H3r/H3k) and FA-vs-nonlinear imputer comparisons (H3); produced by exp/analyze_h3.py"""
    import shutil
    for src, dst in (('results/H3r/h3r_means.csv', 'h3_selector_x_inference.csv'), ('results/H3r/h3r_paired.csv', 'h3_selector_x_inference_paired.csv'),
                     ('results/H3/h3_paired.csv', 'h3_imputers_paired.csv')):
        if os.path.exists(src): shutil.copy(src, f'{OUT}/{dst}')
    print('h3 copied')


def do_h3c():
    """Full-grid FA / ExtraTrees / kernel ridge under greedyAcomp and random (H3 fold protocol; results/H3c): per-model MSE averaged over reps, bootstrap over models."""
    rows = []
    for m in ('A1', 'A2'):
        fs = sorted(glob.glob(f'results/H3c/{m}/h3_rep*.parquet'))
        if not fs: continue
        D = pd.concat([pd.read_parquet(f) for f in fs]); D = D[D.method.isin(['fa', 'extratrees', 'kernelridge']) & D.selector.isin(['greedyAcomp', 'random'])]
        pm = D.groupby(['selector', 'method', 'model', 'k']).mse.mean().reset_index()
        for (sel, me), g in pm.groupby(['selector', 'method']):
            P = g.pivot(index='model', columns='k', values='mse').dropna()
            mm, lo, hi = boot(P.values, np.sqrt)
            for j, k in enumerate(P.columns):
                rows.append((m, sel, {'extratrees': 'extratrees', 'kernelridge': 'kernelridge', 'fa': 'fa'}[me], int(k), 'rmse', mm[j], lo[j], hi[j], len(P), D.rep.nunique()))
    pd.DataFrame(rows, columns=['matrix', 'selector', 'inference', 'k', 'metric', 'mean', 'ci_lo', 'ci_hi', 'n_models', 'n_rep']).to_csv(f'{OUT}/inference_ablation_nonlinear.csv', index=False)
    print('h3c', len(rows))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--only', default=''); a = ap.parse_args()
    fns = dict(curves=do_curves, references=do_references, synthetic=do_synth, paired=do_paired, data_table=do_data_table, shift=do_shift_kstar_cost, h3=do_h3, conditions=do_conditions, h3c=do_h3c)
    for n, f in fns.items():
        if not a.only or n in a.only.split(','): f()
