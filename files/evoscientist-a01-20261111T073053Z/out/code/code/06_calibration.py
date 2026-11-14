"""Calibration of per-task gain caps from naturally occurring fine-tuning gains (OLLB `contents`), and feasibility of reaching
first place when every task may be raised by at most the empirical q90, q99 or max gain observed on that task.
Pairs: non-merged, original-weight fine-tuned/chat models whose `Base Model` is itself on the leaderboard (score_ft - score_base)."""
import sys, os, warnings
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import data_utils as du
T = du.OLLB6
df = pd.read_csv('data/processed/ollb_contents_full.csv')
idx = df.drop_duplicates('fullname').set_index('fullname')
d = df[df['Type'].isin(['🔶 fine-tuned on domain-specific datasets', '💬 chat models (RLHF, DPO, IFT, ...)']) & (df['Merged'] == False) & (df['Weight type'] == 'Original')]
d = d[d['Base Model'].isin(idx.index) & (d['Base Model'] != d['fullname'])].drop_duplicates('fullname')
Gn = pd.DataFrame({t: d[t].values - idx.loc[d['Base Model'], t].values for t in T}, index=d['fullname'].values)
Gn_all = Gn.copy(); Gn_all.to_csv('results/finetune_gains_all_pairs.csv')
tuned = ['🔶 fine-tuned on domain-specific datasets', '💬 chat models (RLHF, DPO, IFT, ...)']
d_tt = d[idx.loc[d['Base Model'], 'Type'].isin(tuned).values]          # base model itself already tuned (excludes base->instruct jumps)
Gn = pd.DataFrame({t: d_tt[t].values - idx.loc[d_tt['Base Model'], t].values for t in T}, index=d_tt['fullname'].values)
Gn.to_csv('results/finetune_gains_tuned_pairs.csv')
def qt(G, name): return pd.DataFrame({'pairs': name, 'n_pairs': len(G), 'median_gain': G.median(), 'frac_positive': (G > 0).mean(), 'q90': G.quantile(.9), 'q99': G.quantile(.99), 'max': G.max()}).round(2)
q = pd.concat([qt(Gn_all, 'all (base may be pretrained)'), qt(Gn, 'tuned->tuned (primary)')])
q.to_csv('results/finetune_gain_quantiles.csv'); print(q)
# feasibility with heterogeneous caps
B = du.load_ollb6(); S = B['S']; mean = S.mean(axis=1); pool = du.pool_for_ordinal(B, mean); Sp = S[pool]
rows = []
for pairs_name, GG in [('tuned_to_tuned', Gn), ('all_pairs', Gn_all)]:
    caps = {'q90': GG.quantile(.9).clip(lower=0).values, 'q99': GG.quantile(.99).clip(lower=0).values, 'max': GG.max().clip(lower=0).values}
    for rule in RULES:
        Sx = S if rule in CARDINAL else Sp
        agg = rule_scores(Sx, rule); order = np.argsort(-agg, kind='stable')
        for rank in range(2, 22):
            t = int(order[rank - 1]); a = Sx[t]; rec = dict(pairs=pairs_name, rule=rule, rank=rank)
            for name, c in caps.items():
                dl = np.minimum(c, UB - a); rec[f'feasible_{name}'] = bool(is_first(Sx, t, rule, dl))
            rows.append(rec)
R = pd.DataFrame(rows); R.to_csv('results/calibrated_feasibility_ollb6.csv', index=False)
print(R.groupby(['pairs', 'rule'], sort=False)[[c for c in R.columns if c.startswith('feasible')]].mean().round(2))
