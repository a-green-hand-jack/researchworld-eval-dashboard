"""Aggregation ablation (MTEB main_score = mean over subsets vs first-subset score).  python exp/analyze_agg.py -> results/E2/agg_paired.csv
Same blocks, same selectors; targets differ, so compare the selection gain over random and the FA/mean-predictor RMSE under each aggregation."""
import sys, os, glob
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
import numpy as np, pandas as pd
import analysis as A
rows = []
for m in ('A1', 'A2'):
    for tag, d in (('mean_over_subsets', m), ('first_subset', f'{m}_first')):
        pm = A.per_model(A.load(f'results/{d}'))
        ks = [k for k in (3, 8, 12, 20) if k in set(pm.k)]
        for sel in ('greedyA', 'greedyAcomp'):
            t = A.paired(pm, (sel, 'fa'), ('random', 'fa'), 'mse', ks=ks); t['matrix'] = m; t['aggregation'] = tag; t['selector'] = sel
            # rmse of each arm
            for k in ks:
                a = pm[(pm.selector == sel) & (pm.method == 'fa') & (pm.k == k)].groupby('model').mse.mean()
                r = pm[(pm.selector == 'random') & (pm.method == 'fa') & (pm.k == k)].groupby('model').mse.mean()
                b = pm[(pm.selector == 'random') & (pm.method == 'mean') & (pm.k == k)].groupby('model').mse.mean()
                t.loc[t.k == k, ['rmse_sel', 'rmse_random', 'rmse_meanpred']] = [np.sqrt(a.mean()), np.sqrt(r.mean()), np.sqrt(b.mean())]
            rows.append(t)
R = pd.concat(rows, ignore_index=True)
os.makedirs('results/E2', exist_ok=True); R.to_csv('results/E2/agg_paired.csv', index=False)
pd.set_option('display.width', 220)
print(R[['matrix', 'aggregation', 'selector', 'k', 'diff', 'rel', 'lo', 'hi', 'p', 'rmse_sel', 'rmse_random', 'rmse_meanpred', 'n_models']].round(3).to_string())
