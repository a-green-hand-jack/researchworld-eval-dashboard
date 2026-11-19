"""Family-aware uncertainty for the MTEB matrices (review finding): headline RMSE at k = 3/8/20 and the P1/P7/forward-regression/k-medoids
comparisons under four regimes
  main_model    : random folds (results/M), bootstrap over held-out models           (the main tables)
  main_family   : random folds (results/M), bootstrap over organisations (families)  (family-clustered CI)
  famfold_model : family-held-out folds (results/M_fam), bootstrap over models
  famfold_family: family-held-out folds (results/M_fam), bootstrap over organisations
  famfoldx_*    : the same without the one family that carries more than 30% of the summed mean-predictor MSE of the held-out folds
                  (a sensitivity analysis: on A2 the 8 codefuse-ai models are outliers for every method; printed as 'dropped family')
python3 exp/analyze_fam.py [A1 A2 B]  ->  results/FAM/{curves,paired}.csv
Holm: within each (matrix, regime), over the comparisons listed here. P1 and P7 are the pre-declared / post-pilot tests of the main tables; the
complement-error greedy vs forward regression and vs k-medoids are exploratory (outside the declared family, flagged 'exploratory')."""
import sys, os, glob
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
import numpy as np, pandas as pd
import analysis as A
from settings import mteb_setting

KS = [3, 8, 20]
mats = sys.argv[1:] or ['A1', 'A2', 'B']
cur, par = [], []
for m in mats:
    fam = mteb_setting(m)['groups']
    for regime, dirs in (('main', [m, m + '_cluster']), ('famfold', [m + '_fam', m + '_famcluster']), ('famfoldx', [m + '_fam', m + '_famcluster'])):
        pms = [A.per_model(A.load(f'results/{d}')) for d in dirs if os.path.isdir(f'results/{d}') and (glob.glob(f'results/{d}/rec_rep*.parquet') or os.path.exists(f'results/{d}/per_model.parquet'))]
        if not pms: continue
        pm = pd.concat(pms, ignore_index=True)
        pm = pm.drop_duplicates(['model', 'k', 'selector', 'method'])
        if regime == 'famfoldx':
            mm = pm[(pm.method == 'mean') & (pm.selector == 'random') & (pm.k == 8)].groupby('model').mse.mean()
            share = mm.groupby(fam[mm.index.values]).sum() / mm.sum()
            top = share.idxmax()
            if share.max() <= 0.30: continue
            print(f'{m}: dropped family {top} ({share.max():.0%} of the mean-predictor MSE, {int((fam[mm.index.values] == top).sum())} models)')
            pm = pm[fam[pm.model.values] != top]
        cells = set(zip(pm.selector, pm.method))
        for boot, groups in (('model', None), ('family', fam)):
            R = f'{regime}_{boot}'
            for s in ('random', 'greedyA', 'greedyAcomp', 'fwdreg', 'cluster', 'pivqr'):
                if (s, 'fa') in cells:
                    c = A.curve(pm, s, 'fa', 'mse', rmse=True, groups=groups); c = c[c.k.isin(KS)]
                    c['matrix'] = m; c['regime'] = R; c['selector'] = s; cur.append(c)
            tests = [('P1 greedyA vs random', 'greedyA', 'random', 'declared'),
                     ('P7 greedyAcomp vs random', 'greedyAcomp', 'random', 'post-pilot'),
                     ('P7 greedyAcomp vs greedyA', 'greedyAcomp', 'greedyA', 'post-pilot'),
                     ('X1 greedyAcomp vs fwdreg', 'greedyAcomp', 'fwdreg', 'exploratory'),
                     ('X2 greedyAcomp vs cluster', 'greedyAcomp', 'cluster', 'exploratory')]
            rows = []
            for tag, x, y, status in tests:
                if (x, 'fa') in cells and (y, 'fa') in cells:
                    t = A.paired(pm, (x, 'fa'), (y, 'fa'), 'mse', ks=KS, groups=groups)
                    t['test'] = tag; t['status'] = status; rows.append(t)
            if rows:
                P = pd.concat(rows, ignore_index=True); P['p_holm'] = A.holm(P.p.values); P['holm_family'] = len(P)
                P['matrix'] = m; P['regime'] = R; P['n_families'] = len(np.unique(fam[pm.model.unique()]))
                if regime == 'famfoldx': P['dropped_family'] = top
                par.append(P)
os.makedirs('results/FAM', exist_ok=True)
C = pd.concat(cur); C.to_csv('results/FAM/curves.csv', index=False)
P = pd.concat(par); P.to_csv('results/FAM/paired.csv', index=False)
pd.set_option('display.width', 220)
print(C.pivot_table(index=['matrix', 'regime', 'selector'], columns='k', values='est').round(3).to_string())
print(P[['matrix', 'regime', 'test', 'k', 'diff', 'rel', 'lo', 'hi', 'p_holm', 'n_models', 'n_families']].round(3).to_string())
