"""C5: task-count dependence by subsampling tasks.  For each board and n' a number of random task subsets
(seeded) is drawn; in each sub-board the targets are the models at mean-rank 2, 5, 10, 20 (so the initial rank is
held fixed while n varies).  Gain model G1 (+1 above the best on each sub-board task), linear cost.
  python 12_subsample.py helm|olb_subtask -> results/subsample_raw_<board>.csv  (per target; summarised by 11_collect.py)"""
import sys
from grid import *
board = sys.argv[1]; SEED = 20261103
if board == "helm":
    df = load_helm(); S = df.values; NS = [5, 10, 15, 20, 30, 40, 50, 57]; REPS = 20; rules = [r for r in R.RULES]
    tag = dict(leaderboard="helm_mmlu", granularity="headline", population="all")
else:
    df = pd.read_csv(f"{ROOT}/data/processed/olb_subtask.csv", index_col=0); S = df.values; NS = [3, 6, 10, 15, 20, 30, 39]; REPS = 20
    rules = [r for r in R.RULES if r != "copeland"]; tag = dict(leaderboard="openllm_v2", granularity="subtask", population="subtask_pool_699")
RANKS = [2, 5, 10, 20]; out = []
for n in NS:
    reps = 1 if n == S.shape[1] else REPS
    for rep in range(reps):
        rng = np.random.default_rng([SEED, n, rep]); cols = np.sort(rng.choice(S.shape[1], n, replace=False)) if reps > 1 else np.arange(n)
        X = S[:, cols]; order = np.argsort(-X.mean(1), kind="stable")
        d = run(X, np.arange(len(X)), [int(order[r - 1]) for r in RANKS], rules, ["G1"], costs=("linear",), tag=dict(tag, rep=rep, seed=SEED), verbose=False)
        d["target_rank"] = np.repeat(RANKS, len(rules))
        out.append(d); print(n, rep, flush=True)
pd.concat(out).to_csv(f"{ROOT}/results/subsample_raw_{board}.csv", index=False); print("done")
