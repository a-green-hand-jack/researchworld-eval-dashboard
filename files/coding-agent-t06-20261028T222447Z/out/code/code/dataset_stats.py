"""Table 1 inputs: size / density / tie statistics of every leaderboard -> results/dataset_stats.csv"""
import numpy as np, pandas as pd
import boards, bt

rows = []
for name, spec in boards.get_all().items():
    d = spec["load"](); P = bt.Problem(d); p = P.p
    cnt = np.zeros(p)
    np.add.at(cnt, d["a"], 1); np.add.at(cnt, d["b"], 1)
    pairs = len(set(zip(np.minimum(d["a"], d["b"]), np.maximum(d["a"], d["b"]))))
    th = P.fit()
    rows.append(dict(board=name, design=spec["design"], p=p, N=len(d["a"]), tie_rate=float(np.mean(d["y"] == 0.5)),
                     median_per_item=float(np.median(cnt)), min_per_item=float(cnt.min()),
                     pair_coverage=pairs / (p * (p - 1) / 2), score_sd=float(np.std(th[:p])),
                     score_range=float(th[:p].max() - th[:p].min()),
                     eta=float(th[p]) if P.has_h else np.nan))
pd.DataFrame(rows).to_csv("/work/results/dataset_stats.csv", index=False)
print(pd.DataFrame(rows).round(3).to_string())
