"""Minimal total score points (no per-task cap other than the ceiling 100)
for the cardinal rules, every model as target.  Also the gap that must be
closed in each rule's own units.  results/l1_<board>.csv"""
from common import *
rows = []
for board in ["helm", "olb"]:
    if board == "helm": df = load_helm(); S = df.values; names = df.index.values
    else: o, S = load_olb("main"); names = o["fullname"].values
    n = S.shape[1]
    rules = ["mean", "geo", "min"] + (["median"] if n % 2 else [])
    br = {r: initial_ranks(S, r) for r in rules}
    sc = {r: R.scores(S, r) for r in rules}
    for t in range(len(S)):
        for r in rules:
            c = np.delete(sc[r], t).max()
            rows.append((board, names[t], r, int(br[r][t]), V.l1_cost(S, t, r), c - sc[r][t]))
out = pd.DataFrame(rows, columns=["board", "model", "rule", "rank_rule", "l1_points", "gap_agg_units"])
out.to_csv(f"{ROOT}/results/l1_cost.csv", index=False)
print(out.groupby(["board", "rule"]).l1_points.describe())
