"""Allocation baselines (breadth budget k and point budget G), gain model G1
(+1 above the best score on each task).  For target t and budget k:
  optimal : solver (min_k <= k)
  greedy  : the k tasks with the largest headroom h_j (naive 'biggest gap first')
  random  : P(first) when k tasks are drawn uniformly (100 draws, seed fixed)
For point budget G (mean and geomean rules, exact G_min): optimal = G_min <= G;
uniform = G/n added to every task (capped at best+1).
  python 10_baselines.py helm|olb  -> results/baselines_<board>.csv"""
import sys
from grid import *
board = sys.argv[1]
rng = np.random.default_rng(99)
if board == "helm":
    df = load_helm(); S = df.values; names = df.index.values; tg = np.arange(len(S)); rules = R.RULES
    tag = dict(leaderboard="helm_mmlu", granularity="headline", population="all")
else:
    o, S = load_olb("main"); names = o["fullname"].values; tg, _ = pick_targets(S, 300)
    rules = [r for r in R.RULES if r != "copeland"]; tag = dict(leaderboard="openllm_v2", granularity="headline", population="no_flagged")
n = S.shape[1]; best = S.max(0); KS = [k for k in [1, 2, 3, 4, 5, 8, 12, 20, 29, 40] if k <= n]
rows = []
def first_after(X, t, rule, T, v):
    X2 = X.copy(); X2[t, T] = v[T]; return R.is_first(X2, t, rule)
for ii, t in enumerate(tg):
    t = int(t); s = S[t]; delta, hi, h = gain_vectors(s, best, "G1"); v = np.maximum(s, hi)  # full boost to best+1
    for rule in rules:
        kmin = V.min_k(S, t, rule, delta, hi)
        gred = np.argsort(-h)
        for k in KS:
            rnd = np.mean([first_after(S, t, rule, rng.choice(n, k, replace=False), v) for _ in range(100)])
            rows.append((names[t], rule, "k", k, "optimal", float(kmin <= k)))
            rows.append((names[t], rule, "k", k, "greedy_headroom", float(first_after(S, t, rule, gred[:k], v))))
            rows.append((names[t], rule, "k", k, "random", float(rnd)))
    for rule in ["mean", "geo"]:
        u = np.maximum(np.minimum(delta, hi - s), 0)
        gm = V.g_min(S, t, rule, u, np.ones(n))
        for G in [1, 2, 5, 10, 20, 50, 100, 200]:
            rows.append((names[t], rule, "G", G, "optimal", float(gm <= G)))
            x = np.minimum(G / n, u); S2 = S.copy(); S2[t] = s + x
            rows.append((names[t], rule, "G", G, "uniform", float(R.is_first(S2, t, rule))))
    if ii % 20 == 0: print(ii, len(tg), flush=True)
d = pd.DataFrame(rows, columns=["target_id", "rule", "budget_type", "budget", "strategy", "success"])
d = d.assign(**tag, rank_mean=initial_ranks(S, "mean")[pd.Index(names).get_indexer(d.target_id)] if board == "helm" else np.nan)
d.to_csv(f"{ROOT}/results/baselines_raw_{board}.csv", index=False); print("done")
