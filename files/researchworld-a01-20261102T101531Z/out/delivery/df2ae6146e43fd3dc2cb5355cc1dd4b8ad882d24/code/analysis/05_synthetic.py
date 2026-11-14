"""Synthetic one-factor leaderboards: how k*/n depends on #tasks n, task
correlation rho and the rule.  score_ij = clip(50 + 15*(sqrt(rho) z_i +
sqrt(1-rho) e_ij), 0, 100), m models, z,e ~ N(0,1) iid.  Target = model of
initial mean-rank 2 (the closest challenger) or 10.  delta in {10,25,100}.
  python 05_synthetic.py [reps]   -> results/synthetic.csv"""
import sys, time
from common import *
reps = int(sys.argv[1]) if len(sys.argv) > 1 else 100
m = 100; rng = np.random.default_rng(2024); rows = []; t0 = time.time()
for n in [5, 9, 15, 25, 57]:
    for rho in [0.0, 0.3, 0.6, 0.9]:
        for rep in range(reps):
            z = rng.normal(size=(m, 1)); e = rng.normal(size=(m, n))
            S = np.clip(50 + 15 * (np.sqrt(rho) * z + np.sqrt(1 - rho) * e), 0, 100)
            order = np.argsort(-S.mean(1))
            for rk in [1, 9]:
                t = int(order[rk])
                for rule in R.RULES:
                    for d in [10.0, 25.0, 100.0]:
                        k = V.min_k(S, t, rule, d)
                        rows.append((n, rho, rep, rk + 1, rule, d, k, initial_ranks(S, rule)[t]))
    print(n, round(time.time() - t0), flush=True)
pd.DataFrame(rows, columns=["n", "rho", "rep", "rank_mean", "rule", "delta", "k", "rank_rule"]).to_csv(f"{ROOT}/results/synthetic.csv", index=False)
