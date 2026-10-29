"""Per-judge leaderboard summaries on the 49,938 matched Arena battles: tie rate, score spread, agreement with human
leaderboard (Kendall tau among models with >=500 comparisons), 3-way agreement with the human vote."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, '/work/code')
from common import *
import loaders
from scipy.stats import kendalltau
hb = loaders.arena_judged('human'); th_h = hb.base_fit(); n = hb.comparisons_per_model(); ids = np.where(n >= 500)[0]
base = pd.read_json('/work/data/judges/train.single-turn.json')[['id', 'winner_model_a', 'winner_model_b', 'winner_tie']]
yh = np.where(base.winner_tie == 1, 'tie', np.where(base.winner_model_a == 1, 'A', 'B'))
rows = [dict(judge='human', tie_rate=float((yh == 'tie').mean()), theta_sd=float(np.std(th_h[ids])), tau=1.0, agree3=1.0)]
for jd in loaders.JUDGES:
    b = loaders.arena_judged(jd); th = b.base_fit()
    pr = pd.read_json(f'/work/data/judges/{jd}.jsonl', lines=True)[['id', 'winner_pred']].set_index('id').loc[base.id].winner_pred.values
    rows.append(dict(judge=jd, tie_rate=float((pr == 'tie').mean()), theta_sd=float(np.std(th[ids])),
                     tau=float(kendalltau(th[ids], th_h[ids])[0]), agree3=float((pr == yh).mean())))
pd.DataFrame(rows).to_csv(f'{RES}/judge_summary.csv', index=False); print(pd.DataFrame(rows).round(3))
