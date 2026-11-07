"""Train-only Bayes curves: the factor model fitted on the TRAINING models of each fold (as in run_cv, same folds, targets and ranks) gives the
model-implied nMSE of random / greedy conditional-variance ('gv') / greedy log-det ('dopt') selection on that fold's target benchmarks.
Unlike theory_vs_real.py (covariance fitted on the whole matrix = in-sample) nothing here has seen the held-out models, so the gap to the realised
cross-validated error (same targets, same folds) is estimation error + misspecification only.
usage: python theory_train_only.py <name> [<name> ...]     -> results/theory/vs_real_trainonly_<name>.csv  (needs results/raw/B_<name>.json/_folds.parquet)
"""
import os, sys, json
import numpy as np, pandas as pd
import lib
from run_cv import make_folds
from theory_vs_real import cond_err

HERE = os.path.dirname(__file__)
RAW = os.path.join(HERE, '..', 'results', 'raw'); OUT = os.path.join(HERE, '..', 'results', 'theory'); SUM = os.path.join(HERE, '..', 'results', 'summary')
KS = [1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 24, 32]


def run(name, n_rand=10):
    cfg = json.load(open(os.path.join(RAW, f'B_{name}.json')))
    fo = pd.read_parquet(os.path.join(RAW, f'B_{name}_folds.parquet'))
    Y = np.load(os.path.join(HERE, '..', 'data', 'matrices', name + '.npz'), allow_pickle=True)['Y']
    M, N = Y.shape
    ntar = max(1, int(round(cfg['target_frac'] * N)))
    ks = [k for k in KS if k <= N - 1 - ntar]
    rows = []
    for rep in range(cfg['reps']):
        rng = np.random.default_rng(cfg['seed'] * 1000 + rep)
        folds = make_folds(cfg['split'], M, cfg['K'], rng)
        T0 = np.zeros(N, bool); T0[rng.choice(N, ntar, replace=False)] = True
        cand = ~T0; T = np.where(T0)[0]
        for fi, (tr, te) in enumerate(folds):
            Ztr, mu, sd, okc = lib.standardise(Y[tr].copy()); Ztr[:, ~okc] = np.nan
            r = int(fo[(fo.rep == rep) & (fo.fold == fi)]['rank'].iloc[0])
            fa = lib.FA(r, seed=rep).fit(Ztr)
            C = fa.cov()
            ords = {'gv': lib.greedy_cond_var(C, max(ks), cand=cand), 'dopt': lib.greedy_dopt(fa.W, fa.psi, max(ks), cand)}
            ci = np.where(cand)[0]
            for k in ks:
                for s, o in ords.items():
                    rows.append((rep, fi, s, k, cond_err(C, o[:k], T)))
                rows.append((rep, fi, 'random', k, np.mean([cond_err(C, rng.choice(ci, k, replace=False), T) for _ in range(n_rand)])))
    d = pd.DataFrame(rows, columns=['rep', 'fold', 'selector', 'k', 'nmse_bayes_trainfit'])
    out = d.groupby(['selector', 'k']).nmse_bayes_trainfit.agg(['mean', 'std']).reset_index().rename(columns={'mean': 'nmse_bayes_trainfit', 'std': 'sd_over_folds'})
    cur = pd.read_csv(os.path.join(SUM, f'curves_B_{name}.csv'))
    cur = cur[cur.method.isin(['fa', 'krr'])].assign(selector=lambda x: x.selector.replace({'gv_fa': 'gv'}))
    for m in ('fa', 'krr'):
        c = cur[cur.method == m][['selector', 'k', 'nmse']].rename(columns={'nmse': f'cv_nmse_{m}'})
        out = out.merge(c, on=['selector', 'k'], how='left')
    out.insert(0, 'dataset', name)
    os.makedirs(OUT, exist_ok=True)
    out.to_csv(os.path.join(OUT, f'vs_real_trainonly_{name}.csv'), index=False)
    print(name, out[out.k == 4].round(3).to_dict('records'), flush=True)


if __name__ == '__main__':
    for n in sys.argv[1:]:
        run(n)
