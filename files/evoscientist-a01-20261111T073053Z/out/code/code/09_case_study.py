"""Case study (OLLB-BBH24): the leaderboard's #1 under 7 of 8 rules is qingy2024/Benchmaxx-Llama-3.2-1B-Instruct, whose declared
base model (parent) meta-llama/Llama-3.2-1B-Instruct is also on the board.  Compare the OBSERVED per-task gain parent->child with the
MINIMAL investment our solvers need for the parent to be strictly first (rivals = all other models on the board, including the child
removed, i.e. the child is treated as absent so that the question is 'what would the parent have needed against the field').
Descriptive only: we have no direct evidence about the child's training data."""
import sys, os
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import data_utils as du
B = du.load_bbh(); names = B['models']; S = B['S']
child = 'qingy2024/Benchmaxx-Llama-3.2-1B-Instruct'; parent = 'meta-llama/Llama-3.2-1B-Instruct'
ic, ip = names.index(child), names.index(parent)
obs = S[ic] - S[ip]
out = [dict(quantity='observed', K=int((obs > 0).sum()), L1=float(obs.clip(min=0).sum()), max_gain=float(obs.max()), min_gain=float(obs.min()))]
keep = [i for i in range(len(names)) if i != ic]                      # board without the child
Sx = S[keep]; t = keep.index(ip)
mean = Sx.mean(axis=1); pool = np.argsort(-mean, kind='stable')[:100]
if t not in pool: pool = np.concatenate([pool[:99], [t]])
Sp = Sx[pool]; tp = int(np.where(pool == t)[0][0])
rows = []
for rule in RULES:
    if rule in CARDINAL:
        r = solve_cardinal(Sx[t], np.delete(Sx, t, axis=0), rule, 100.0)
        rows.append(dict(rule=rule, K_min=r['K'], L1_min=r['L1']))
    else:
        rk = solve_ordinal(Sp, tp, rule, 100.0, 'K', time_limit=120); rl = solve_ordinal(Sp, tp, rule, 100.0, 'L1', time_limit=120)
        rows.append(dict(rule=rule, K_min=rk['K'], L1_min=rl['L1']))
R = pd.DataFrame(rows); R['parent_mean_score'] = Sx[t].mean(); R['child_mean_score'] = S[ic].mean()
R.to_csv('results/case_study_benchmaxx.csv', index=False)
pd.DataFrame(out).to_csv('results/case_study_observed.csv', index=False)
print(pd.DataFrame(out).round(1).to_string()); print(R.round(2).to_string())
