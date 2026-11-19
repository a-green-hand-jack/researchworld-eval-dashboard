"""E6 summaries: shift effect on error and coverage, and the two stopping rules.  python exp/analyze_e6.py
Units = (rep, fold) of a split (the held-out block). Writes results/E6/{shift_summary,kstar_units,stopping_error}.csv.
Rules (tolerance eps in standardised RMSE; k = smallest grid k meeting the condition, censored at KCEN if never):
 model      : predicted RMSE of the fitted model (sqrt(mean predictive variance) on calibration rows) <= eps       [target: mean RMSE of the block]
 conformal  : mean leave-out RMSE of the calibration models (proper-train fit) <= eps                               [target: mean RMSE of the block]
 conformal_q: split-conformal 90% quantile of per-model RMSE on calibration models <= eps                          [target: 90% of the new models reach eps]
 truth      : empirical_mean: test mean RMSE <= eps ;  empirical_q: fraction of test models with RMSE <= eps is >= 0.9"""
import sys, glob, json
import numpy as np, pandas as pd
KCEN = 60
EPS = (0.5, 0.6, 0.7)
D = pd.concat([pd.read_parquet(f).assign(rep=int(f.split('rep')[-1].split('.')[0])) for f in sorted(glob.glob('results/E6/*/e6_*_rep*.parquet'))], ignore_index=True)
D['unit'] = D.rep.astype(str) + '_' + D.split + '_' + D.fold.astype(str)
rng = np.random.default_rng(0)


def ci(x, B=2000):
    x = np.asarray(x, float); idx = rng.integers(0, len(x), (B, len(x))); b = x[idx].mean(1)
    return x.mean(), *np.percentile(b, [2.5, 97.5])


rows = []
for (st, sp, sel, me, k), g in D.groupby(['setting', 'split', 'selector', 'method', 'k']):
    r = dict(matrix=st, split=sp, selector=sel, inference=me, k=k, n_units=len(g), nominal=0.9)
    for c, nm in (('test_rmse_mean', 'rmse'), ('test_rmse_k0', 'rmse_meanpred'), ('cov_gauss', 'coverage'), ('cov_conf', 'coverage_conformal'),
                  ('cov_model_conf', 'frac_models_under_q'), ('pred_rmse', 'pred_rmse'), ('cal_rmse_mean', 'cal_rmse')):
        m, lo, hi = ci(g[c].values); r[nm] = m
        if nm in ('rmse', 'coverage', 'coverage_conformal'): r[nm + '_lo'], r[nm + '_hi'] = lo, hi
    rows.append(r)
S = pd.DataFrame(rows)
S.to_csv('results/E6/shift_summary.csv', index=False)


def kstar(g, col, op, thr):
    g = g.sort_values('k'); ok = g[op(g[col].values, thr)]
    return int(ok.k.iloc[0]) if len(ok) else KCEN


units = []
for (st, sp, sel, me, u), g in D.groupby(['setting', 'split', 'selector', 'method', 'unit']):
    for e in EPS:
        fb = g.assign(fb=g.frac_models_below.map(lambda s: json.loads(s)[str(e)]))
        units.append(dict(matrix=st, split=sp, selector=sel, inference=me, unit=u, tol=e,
                          k_model=kstar(g, 'pred_rmse', np.less_equal, e), k_conformal=kstar(g, 'cal_rmse_mean', np.less_equal, e),
                          k_empirical=kstar(g, 'test_rmse_mean', np.less_equal, e),
                          k_conformal_q=kstar(g, 'q_model', np.less_equal, e), k_empirical_q=kstar(fb, 'fb', np.greater_equal, 0.9)))
U = pd.DataFrame(units); U.to_csv('results/E6/kstar_units.csv', index=False)
er = []
for (st, sp, sel, me, e), g in U.groupby(['matrix', 'split', 'selector', 'inference', 'tol']):
    for rule, truth in (('model', 'k_empirical'), ('conformal', 'k_empirical'), ('conformal_q', 'k_empirical_q')):
        kr, kt = g['k_' + rule].values, g[truth].values
        cens = ((kr >= KCEN) | (kt >= KCEN))
        d = np.log2(kr) - np.log2(kt)
        m, lo, hi = ci(d)
        er.append(dict(matrix=st, split=sp, selector=sel, inference=me, tol=e, rule=rule, n_units=len(g), kstar_rule_median=float(np.median(kr)),
                       kstar_true_median=float(np.median(kt)), mean_signed_log2_ratio=m, lo=lo, hi=hi,
                       mean_abs_log2_ratio=float(np.abs(d).mean()), frac_censored=float(cens.mean()), frac_rule_too_small=float((kr < kt).mean())))
E_ = pd.DataFrame(er); E_.to_csv('results/E6/stopping_error.csv', index=False)
pd.set_option('display.width', 220)
print(S[S.selector.isin(['greedyA', 'greedyGauss']) & S.k.isin([3, 8, 20])][['matrix', 'split', 'selector', 'k', 'n_units', 'rmse', 'rmse_meanpred', 'pred_rmse', 'coverage', 'coverage_conformal']].round(3).to_string())
print(E_[(E_.selector == 'greedyGauss') | (E_.selector == 'greedyA')][['matrix', 'split', 'selector', 'tol', 'rule', 'kstar_rule_median', 'kstar_true_median', 'mean_signed_log2_ratio', 'mean_abs_log2_ratio', 'frac_censored']].round(2).to_string())
