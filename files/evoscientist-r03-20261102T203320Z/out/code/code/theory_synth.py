"""Synthetic checks of the theory (all data here are simulated from the stated factor model and labelled as such).

T1  Known loadings, homogeneous random design:  OLS error  sigma^2 (1 + r/(k-r-1))   (exact, Gaussian design)
                                                Bayes error >= sigma^2 (1 + r/(k+sigma^2))  (Jensen lower bound)
T2  Tail of the error across random subsets near k ~ r (OLS has infinite variance for k<=r+3, Bayes does not)
T3  Heterogeneous benchmarks: gain of optimal design (greedy I-opt) over random as a function of k/r
T4  Estimating the loadings from M training models (optionally with missing entries):  MSE vs M, compared with
    the heuristic sigma^2 (1 + r/k + r/M)
Usage: python code/theory_synth.py   (about 3-5 min on CPU); writes results/theory_*.csv
"""
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np, pandas as pd
import bsp

os.makedirs("results", exist_ok=True)


def t1_t2(seed=0, trials=4000):
    rng = np.random.default_rng(seed)
    rows = []
    for r in [3, 6]:
        for sig2 in [0.25, 1.0]:
            N = 400
            for k in [r + 1, r + 2, r + 3, r + 5, 2 * r, 3 * r, 5 * r, 10 * r]:
                e_ols, e_bayes = [], []
                for _ in range(trials // 4):
                    V = rng.standard_normal((N, r))
                    u = rng.standard_normal(r)
                    y = V @ u + np.sqrt(sig2) * rng.standard_normal(N)
                    S = rng.permutation(N)[:k]
                    T = np.setdiff1d(np.arange(N), S)
                    VS = V[S]
                    uo = np.linalg.lstsq(VS, y[S], rcond=None)[0]
                    ub = np.linalg.solve(np.eye(r) * sig2 + VS.T @ VS, VS.T @ y[S])
                    e_ols.append(np.mean((V[T] @ uo - y[T]) ** 2))
                    e_bayes.append(np.mean((V[T] @ ub - y[T]) ** 2))
                e_ols, e_bayes = np.array(e_ols), np.array(e_bayes)
                rows.append(dict(r=r, sig2=sig2, k=k,
                                 ols_mean=e_ols.mean(), ols_median=np.median(e_ols), ols_p99=np.quantile(e_ols, .99), ols_max=e_ols.max(),
                                 ols_formula=sig2 * (1 + r / (k - r - 1)) if k > r + 1 else np.inf,
                                 bayes_mean=e_bayes.mean(), bayes_median=np.median(e_bayes), bayes_p99=np.quantile(e_bayes, .99), bayes_max=e_bayes.max(),
                                 bayes_lb=sig2 * (1 + r / (k + sig2)), approx_floor_over_k=sig2 * (1 + r / k),
                                 n=len(e_ols)))
    pd.DataFrame(rows).to_csv("results/theory_t1t2.csv", index=False)
    return pd.DataFrame(rows)


def hetero_instance(rng, N=120, r=6, het=1.0):
    """Benchmarks differ in informativeness: loading scales and noise levels log-normal, loadings cluster in directions."""
    centers = rng.standard_normal((r, r))
    lab = rng.integers(0, r, N)
    V = centers[lab] * 0.7 + rng.standard_normal((N, r)) * 0.5
    V *= np.exp(het * rng.standard_normal(N))[:, None] * 0.6
    psi = 0.2 * np.exp(het * rng.standard_normal(N))
    return V, psi


def t3(seed=1, n_inst=60, n_models=200):
    rng = np.random.default_rng(seed)
    rows = []
    for het in [0.0, 0.5, 1.0]:
        for _ in range(n_inst):
            r = 6
            V, psi = hetero_instance(rng, r=r, het=het)
            N = V.shape[0]
            G = V.T @ V
            C = np.arange(N)
            orders = {"greedy_iopt": bsp.sel_greedy_iopt(C, 36, V, psi, G), "top_load": bsp.sel_top_load(C, 36, V, psi),
                      "piv_qr": bsp.sel_piv_qr(C, 36, V, psi)}
            U = rng.standard_normal((n_models, r))
            Y = U @ V.T + np.sqrt(psi)[None] * rng.standard_normal((n_models, N))
            for k in [2, 3, 4, 6, 8, 12, 18, 24, 36]:
                sets = {"random": [rng.permutation(N)[:k] for _ in range(10)], **{n: [o[:k]] for n, o in orders.items()}}
                for name, ss in sets.items():
                    errs = []
                    for S in ss:
                        T = np.setdiff1d(np.arange(N), S)
                        VS = V[S]; w = 1 / psi[S]
                        P = np.eye(r) + (VS * w[:, None]).T @ VS
                        Uh = np.linalg.solve(P, (VS * w[:, None]).T @ Y[:, S].T).T
                        errs.append(np.mean((Uh @ V[T].T - Y[:, T]) ** 2))
                    rows.append(dict(het=het, k=k, sel=name, mse=np.mean(errs), implied=bsp.implied_fa(V, psi, np.asarray(ss[0]))))
    d = pd.DataFrame(rows)
    d.to_csv("results/theory_t3.csv", index=False)
    return d


def t4(seed=2, reps=8):
    rng = np.random.default_rng(seed)
    rows = []
    N, r, sig2 = 100, 5, 0.3
    for miss in [0.0, 0.5]:
        for M in [20, 40, 80, 160, 320, 640]:
            for rep in range(reps):
                V = rng.standard_normal((N, r))
                U = rng.standard_normal((M, r))
                Z = U @ V.T + np.sqrt(sig2) * rng.standard_normal((M, N))
                Z = np.where(rng.random((M, N)) < miss, np.nan, Z)
                Vh, psih = bsp.fa_em(Z, r, iters=150)
                Ut = rng.standard_normal((300, r))
                Yt = Ut @ V.T + np.sqrt(sig2) * rng.standard_normal((300, N))
                for k in [3, 5, 10, 20]:
                    e_hat, e_or = [], []
                    for i in range(300):
                        S = rng.permutation(N)[:k]; T = np.setdiff1d(np.arange(N), S)
                        e_hat.append(np.mean((bsp.predict_fa(Vh, psih, S, Yt[i, S])[T] - Yt[i, T]) ** 2))
                        e_or.append(np.mean((bsp.predict_fa(V, np.full(N, sig2), S, Yt[i, S])[T] - Yt[i, T]) ** 2))
                    rows.append(dict(miss=miss, M=M, rep=rep, k=k, mse_est=np.mean(e_hat), mse_oracle=np.mean(e_or),
                                     heur=sig2 * (1 + r / k + r / (M * (1 - miss))), base=sig2 * (1 + r / k)))
    d = pd.DataFrame(rows)
    d.to_csv("results/theory_t4.csv", index=False)
    return d


if __name__ == "__main__":
    a = t1_t2(); print(a.round(3).to_string())
    b = t3(); print(b.groupby(["het", "k", "sel"]).mse.mean().unstack().round(3).to_string())
    c = t4(); print(c.groupby(["miss", "M", "k"])[["mse_est", "mse_oracle", "heur", "base"]].mean().round(3).to_string())
