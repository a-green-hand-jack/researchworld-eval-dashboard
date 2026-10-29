"""Compare the human-vote leaderboard with leaderboards built from LLM-judge labels on the *same*
single-turn Arena battles.  Output: results/judge_agreement.csv, results/judge_pair_reversal.csv
Usage: python code/exp_judge_agreement.py"""
import os, sys
os.environ["OMP_NUM_THREADS"] = "1"
import numpy as np, pandas as pd
from scipy.stats import kendalltau, spearmanr
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bt
from common import load, ROOT

JUDGES = ["Athene-70B", "Meta-Llama-3-70B-Instruct", "Qwen2-72B-Instruct", "Mistral-7B-Instruct-v0.2", "dolphin-2.1-mistral-7b"]
Dh = load("arenaST_human")
th_h = bt.fit_data(Dh)[:Dh.M]
rows, prow = [], []
# human-side pair statistics: all pairs within the human leaderboard (adjacent..distance<=5 as in the main run)
pairs = pd.read_csv(os.path.join(ROOT, "results", "pairs_judges.csv"))
ph = pairs[pairs.board == "arenaST_human"][["i", "j", "z", "k_drop", "gap"]]
for jn in JUDGES:
    Dj = load("arenaST_judge_" + jn)
    assert Dj.names == Dh.names
    th_j = bt.fit_data(Dj)[:Dj.M]
    tau = kendalltau(th_h, th_j)[0]
    rho = spearmanr(th_h, th_j)[0]
    idx = {n: k for k, n in enumerate(Dh.names)}
    gj = np.array([th_j[idx[a]] - th_j[idx[b]] for a, b in zip(ph.i, ph.j)])
    rev = gj <= 0
    rows.append(dict(judge=jn, kendall_tau=tau, spearman=rho,
                     frac_rev_all=rev.mean(), frac_rev_z_gt2=rev[ph.z.values > 2].mean(),
                     frac_rev_z_gt3=rev[ph.z.values > 3].mean(), n_z_gt2=int((ph.z.values > 2).sum()),
                     acc3=float((Dj.y == Dh.y).mean())))
    for z, k, r in zip(ph.z, ph.k_drop, rev):
        prow.append(dict(judge=jn, z=z, k_drop=k, reversed=bool(r)))
pd.DataFrame(rows).to_csv(os.path.join(ROOT, "results", "judge_agreement.csv"), index=False)
pd.DataFrame(prow).to_csv(os.path.join(ROOT, "results", "judge_pair_reversal.csv"), index=False)
print(pd.DataFrame(rows).round(3).to_string())
