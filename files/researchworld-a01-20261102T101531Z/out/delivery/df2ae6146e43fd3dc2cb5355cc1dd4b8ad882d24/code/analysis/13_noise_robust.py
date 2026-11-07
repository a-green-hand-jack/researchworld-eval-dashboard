"""Noise-robust investment: probability that the target is strictly first after the attack when every cell of the
leaderboard is re-measured with evaluation noise.
Attack set: the k_min set of the noise-free solver (gain G1: boost to best+1 on every task of the set); for
k > k_min the set is extended by the tasks of largest remaining headroom.  Noise: Gaussian approximation of the
binomial item-level error, se_ij = 100*sqrt(p(1-p)/n_eval_j) at the observed score (HELM: n_eval per subject from
the release; OLB: published test-set sizes, se = slope of normalised score on raw accuracy (points per unit accuracy) times the binomial se of the accuracy), common random
numbers over k, B draws.  Boosted cells keep the se of the observed cell (conservative for HELM near 100).
Output: results/noise_robust_<board>.csv with p_first_noise(k).   python 13_noise_robust.py helm|olb [B]"""
import sys, time
from common import *
board = sys.argv[1]; B = int(sys.argv[2]) if len(sys.argv) > 2 else 200
rng = np.random.default_rng(424242)
if board == "helm":
    df = load_helm(); S = df.values; names = df.index.values
    N = pd.read_csv(f"{ROOT}/data/processed/helm_mmlu_neval.csv", index_col=0).loc[df.index].values.astype(float)
    p = np.clip(S / 100, 0, 1); SE = 100 * np.sqrt(p * (1 - p) / N)
    ranks = list(range(0, 40)); rules = ["mean", "median", "min", "trim", "borda", "plurality"]
else:
    o, S = load_olb("main"); names = o["fullname"].values
    Sraw = load_olb("main", raw=True)[1] / 100
    nq = np.array([541, 6511, 1324, 448, 756, 12032]); slope = np.array([np.polyfit(Sraw[:, j], S[:, j], 1)[0] for j in range(6)])
    SE = slope * np.sqrt(np.clip(Sraw, 0, 1) * (1 - np.clip(Sraw, 0, 1)) / nq)
    ranks = [0, 1, 2, 3, 4, 5, 7, 9, 14, 19, 29, 49, 99, 199, 499, 999]; rules = ["mean", "median", "min", "trim", "borda", "plurality"]
    B = min(B, 100)
m, n = S.shape; best = S.max(0); hi = np.minimum(100.0, best + 1.0)
order = np.argsort(-S.mean(1), kind="stable"); tg = [int(order[r]) for r in ranks]
Z = rng.standard_normal((B, m, n)).astype(np.float32)
mean_rank = initial_ranks(S, "mean")
def p_first(t, rule, T):
    X = S.copy(); X[t, T] = np.maximum(X[t, T], hi[T]); ok = 0
    for b in range(B):
        Y = np.clip(X + SE * Z[b], 0, 100); ok += R.is_first(Y, t, rule)
    return ok / B
rows = []; t0 = time.time()
for ii, t in enumerate(tg):
    s = S[t]; head = np.maximum(hi - s, 0)
    for rule in rules:
        res = V.min_k(S, t, rule, np.inf, hi, return_set=True)
        if not isinstance(res, tuple): continue
        kmin, T0 = res
        rest = [j for j in np.argsort(-head) if j not in set(T0.tolist())]
        done = False
        for extra in [0, 1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48]:
            k = kmin + extra
            if k > n: break
            T = np.concatenate([T0, np.array(rest[:extra], int)]).astype(int)
            pf = p_first(t, rule, T); rows.append((names[t], int(mean_rank[t]), rule, int(kmin), k, pf, B))
            if pf >= 0.99: break
    print(ii, len(tg), round(time.time() - t0), flush=True)
pd.DataFrame(rows, columns=["target_id", "init_rank_mean", "rule", "k_det", "k", "p_first_noise", "n_draws"]).to_csv(f"{ROOT}/results/noise_robust_{board}.csv", index=False)
print("done")
