"""Gaussian-max check on the real correctness matrix. usage: real_theory.py MATRIX.npz REAL_SUMMARY.csv OUT.csv [M]
Predicted naive gap of random search with full evaluation (argmax over a random K-subset of the cached configs), using the matrix's own empirical
question-level covariance Sigma (K_pool x K_pool, n_items = N):
  iid arm      : tuning items drawn with replacement, truth = pool mean:           gap = E[eps_sel],  eps ~ N(0, Sigma/n)
  disjoint arm : tuning items without replacement, truth = accuracy on pool \\ T:   gap = N/(N-n) * E[eps'_sel],  eps' ~ N(0, (1-n/N) Sigma/n)
(finite-population correction; X_k - mu'_k = N/(N-n) (X_k - mu_k)).  Compared with the replayed naive bias of the argmax procedure (real_summary.csv)."""
import sys, numpy as np, pandas as pd
mat, summ, out = sys.argv[1:4]; M = int(sys.argv[4]) if len(sys.argv) > 4 else 40000
Y = np.load(mat, allow_pickle=True)["Y"]; Kp, N = Y.shape; mu = Y.mean(1); Sig = np.cov(Y.astype(float)) + 1e-12 * np.eye(Kp)
S = pd.read_csv(summ); S = S[(S.proc == "argmax") & (S.est_name == "naive")]
def pred(n, K, fpc, seed=0):
    rng = np.random.default_rng([seed, n, K]); sc = (1 - n / N) if fpc else 1.0
    L = np.linalg.cholesky(sc * Sig / n); g = np.empty(M)
    for m in range(M):
        c = np.arange(Kp) if K == Kp else rng.choice(Kp, K, replace=False); e = L @ rng.standard_normal(Kp); k = c[np.argmax(mu[c] + e[c])]; g[m] = e[k]
    f = N / (N - n) if fpc else 1.0
    return f * g.mean(), f * g.std() / np.sqrt(M)
rows = []
for _, r in S.iterrows():
    fpc = r.truth_arm == "disjoint"; p, pse = pred(int(r.n), int(r.K), fpc)
    rows.append(dict(K_pool=Kp, truth_arm=r.truth_arm, n=int(r.n), K=int(r.K), pred_gap=p, pred_mc_se=pse, replay_gap=r.bias, replay_se=r.bias_se, reps=int(r.reps),
                     diff=p - r.bias, z=(p - r.bias) / np.hypot(pse, r.bias_se)))
d = pd.DataFrame(rows).sort_values(["truth_arm", "n", "K"]); d.to_csv(out, index=False); print(d.to_string())
