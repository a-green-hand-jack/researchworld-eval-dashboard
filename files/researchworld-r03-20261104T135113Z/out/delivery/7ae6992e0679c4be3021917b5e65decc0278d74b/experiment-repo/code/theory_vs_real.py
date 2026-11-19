"""Model-implied (Bayes) error curves of the Gaussian factor model next to the realised CV curves (claim C7).

For a covariance C of the standardised scores (C = W W' + diag(psi): TRUE for synthetic matrices, FITTED by factor analysis on the
whole matrix for real ones), the posterior-mean predictor given an observed set S has expected squared error on target j
   C_jj - C_jS C_SS^-1 C_Sj ,   reported as nMSE = mean_j cond_var_j / C_jj  over targets (z-scale, same normalisation as the CV runs).
Targets T: random 25% of the benchmarks (as protocol B), S is selected among the non-targets: random, greedy conditional variance
('gv', = gv_fa), greedy log-det ('dopt').  For real data the covariance is fitted in-sample, so the curve is the model's
own optimistic prediction; the gap to the CV curve = estimation error (finite M, missingness) + misspecification (non-Gaussian,
non-linear, heterogeneous).

usage: python theory_vs_real.py <name> [<name> ...]     -> results/theory/vs_real_<name>.csv
"""
import os, sys
import numpy as np, pandas as pd
import lib

HERE = os.path.dirname(__file__)
KS = [1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 24, 32]


def cond_err(C, S, T):
    S = list(S)
    if not S:
        return float(np.mean(np.diag(C)[T] / np.diag(C)[T]))
    A = np.linalg.solve(C[np.ix_(S, S)] + 1e-8 * np.eye(len(S)), C[np.ix_(S, T)])
    cv = np.diag(C)[T] - np.einsum('st,st->t', C[np.ix_(S, T)], A)
    return float(np.mean(cv / np.diag(C)[T]))


def run(name, n_T=20, n_S=20, seed=0):
    mat = os.path.join(HERE, '..', 'data', 'matrices')
    z = np.load(os.path.join(mat, name + '.npz'), allow_pickle=True)
    Y = z['Y']; N = Y.shape[1]
    tp = os.path.join(mat, name + '_truth.npz')
    if os.path.exists(tp):
        t = np.load(tp); W, psi = t['W'], t['psi']
        C = W @ W.T + np.diag(psi); src = 'truth'; r = W.shape[1]; Wd, pd_ = W, psi
    else:
        fp = os.path.join(HERE, '..', 'results', 'raw', 'B_' + name + '.json')
        fo = os.path.join(HERE, '..', 'results', 'raw', 'B_' + name + '_folds.parquet')
        r = int(np.median(pd.read_parquet(fo)['rank'])) if os.path.exists(fo) else 2
        Z, mu, sd, ok = lib.standardise(Y)
        fa = lib.FA(r).fit(Z[:, ok])
        C = fa.cov(); src = 'fit'; Wd, pd_ = fa.W, fa.psi
        N = C.shape[0]
    rng = np.random.default_rng(seed)
    rows = []
    ntar = max(1, int(round(0.25 * N)))
    for _ in range(n_T):
        T = np.sort(rng.choice(N, ntar, replace=False)); cand = np.ones(N, bool); cand[T] = False
        kmax = max(k for k in KS if k <= N - 1 - ntar)
        orders = {'gv': lib.greedy_cond_var(C, kmax, cand=cand), 'dopt': lib.greedy_dopt(Wd, pd_, kmax, cand)}
        ci = np.where(cand)[0]
        for k in KS:
            if k > N - 1 - ntar:
                continue
            for s, o in orders.items():
                rows.append((s, k, cond_err(C, o[:k], T)))
            for _ in range(n_S):
                rows.append(('random', k, cond_err(C, rng.choice(ci, k, replace=False), T)))
    df = pd.DataFrame(rows, columns=['selector', 'k', 'nmse_bayes']).groupby(['selector', 'k']).nmse_bayes.mean().reset_index()
    df.insert(0, 'dataset', name); df.insert(1, 'cov_source', src); df['rank'] = r
    os.makedirs(os.path.join(HERE, '..', 'results', 'theory'), exist_ok=True)
    df.to_csv(os.path.join(HERE, '..', 'results', 'theory', f'vs_real_{name}.csv'), index=False)
    print(name, src, 'rank', r, df[df.k == 4].set_index('selector').nmse_bayes.round(3).to_dict(), flush=True)


if __name__ == '__main__':
    for n in sys.argv[1:]:
        run(n)
