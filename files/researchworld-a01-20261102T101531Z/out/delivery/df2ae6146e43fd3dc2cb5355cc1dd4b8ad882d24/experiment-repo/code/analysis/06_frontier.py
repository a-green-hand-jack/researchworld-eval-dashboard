"""Investment frontier: for each target, rule and number of targeted tasks k,
the smallest uniform per-task boost Delta*(k) (points; bisection, tol 0.05)
such that boosting k well-chosen tasks by at most Delta makes the target
strictly first.  total(k) = k*Delta*(k) is an upper bound on the minimal total
points needed with k tasks (exact for the mean rule when the headroom does not
bind).  cap in {ceiling (100), sota+1 (best score on the task + 1)}.
  python 06_frontier.py {helm|olb} [--raw]  -> results/frontier_<board>.csv"""
import sys, time
from common import *
board = sys.argv[1]; raw = "--raw" in sys.argv
if board == "helm":
    df = load_helm(); S = df.values; names = df.index.values; tg = np.arange(len(S)); KS = [1, 2, 3, 5, 8, 12, 20, 29, 40, 57]
else:
    o, S = load_olb("main", raw); names = o["fullname"].values; tg, _ = pick_targets(S, 300); KS = [1, 2, 3, 4, 5, 6]
m, n = S.shape; best = S.max(0)
caps = {"ceiling": np.full(n, 100.0), "sota+1": np.minimum(100.0, best + 1.0)}
rank_mean = initial_ranks(S, "mean")
def dstar(t, rule, k, hi):
    if V.min_k(S, t, rule, 100.0, hi) > k: return np.inf
    if V.min_k(S, t, rule, 0.0, hi) <= k: return 0.0
    lo, up = 0.0, 100.0
    while up - lo > 0.05:
        mid = (lo + up) / 2
        if V.min_k(S, t, rule, mid, hi) <= k: up = mid
        else: lo = mid
    return up
rows = []; t0 = time.time()
for ii, t in enumerate(tg):
    t = int(t)
    for rule in R.RULES:
        for cap, hi in caps.items():
            for k in KS:
                if k > n: continue
                rows.append((names[t], t, int(rank_mean[t]), rule, cap, k, dstar(t, rule, k, hi)))
    if ii % 10 == 0: print(ii, len(tg), round(time.time() - t0), flush=True)
out = pd.DataFrame(rows, columns=["model", "idx", "rank_mean", "rule", "cap", "k", "delta_star"])
out["total_points"] = out.k * out.delta_star
out.to_csv(f"{ROOT}/results/frontier_{board}{'_raw' if raw else ''}.csv", index=False)
print("done", round(time.time() - t0))
