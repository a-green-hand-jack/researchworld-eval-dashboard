"""Descriptives: dataset sizes, additive-fit residual SD (anchor for synthetic experiment), winners per rule, rank agreement (Kendall tau)."""
import sys, os
import numpy as np, pandas as pd
from scipy.stats import kendalltau
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import data_utils as du
from exp_utils import additive_residual_sd
rows = []; win = []; taus = []
for k, f in du.LOADERS.items():
    B = f(); S = B['S']; M, n = S.shape
    mean = S.mean(axis=1); pool = du.pool_for_ordinal(B, mean); Sp = S[pool]
    rows.append(dict(bench=B['name'], models=M, tasks=n, pool_ordinal=len(pool), mean_score=S.mean(), sd_across_models_of_mean=mean.std(),
                     additive_resid_sd=additive_residual_sd(S), top_gap_mean=np.sort(mean)[-1] - np.sort(mean)[-2]))
    sc = {r: (rule_scores(S, r) if r in CARDINAL else rule_scores(Sp, r)) for r in RULES}
    for r in RULES:
        nm = B['models'][int(np.argmax(sc[r]))] if r in CARDINAL else B['models'][int(pool[np.argmax(sc[r])])]
        win.append(dict(bench=B['name'], rule=r, winner=nm, top_score=float(sc[r].max())))
    # agreement within the ordinal pool (all rules on same models)
    full = {r: rule_scores(Sp, r) for r in RULES}
    K = np.zeros((len(RULES), len(RULES)))
    for i, a in enumerate(RULES):
        for j, b in enumerate(RULES): K[i, j] = kendalltau(full[a], full[b])[0]
    t = pd.DataFrame(K, index=RULES, columns=RULES); t.to_csv(f'results/kendall_{k}.csv')
pd.DataFrame(rows).to_csv('results/descriptives.csv', index=False); pd.DataFrame(win).to_csv('results/winners.csv', index=False)
print(pd.DataFrame(rows).round(2).to_string()); print(pd.DataFrame(win).to_string())
