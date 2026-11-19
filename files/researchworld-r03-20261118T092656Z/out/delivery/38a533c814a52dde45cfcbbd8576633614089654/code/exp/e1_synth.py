"""E1: synthetic matrices with known truth. Measured error(k) of the fitted plug-in (greedy A / random) versus
closed-form forecasts: oracle Bayes (a), naive plug-in, finite-M corrected (d).  usage: e1_synth.py REPS OUT"""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
import numpy as np, pandas as pd
import fa as FA, bselect as SEL, theory as TH

N = 48
KS = [1, 2, 3, 5, 8, 12, 20]


def make_truth(kind, h, rng):
    """unit-variance benchmarks: ||l_j||^2 + psi_j = 1, mean latent variance fraction h."""
    if kind == 'one':
        L = np.full((N, 1), np.sqrt(h))
    elif kind == 'block':
        L = np.zeros((N, 4))
        for j in range(N):
            L[j, j * 4 // N] = np.sqrt(h)
    elif kind == 'power':
        r = 12
        s2 = np.arange(1, r + 1) ** -1.5; s2 /= s2.sum()
        Q, _ = np.linalg.qr(rng.standard_normal((N, r)))
        L = np.sqrt(N * h * s2)[None, :] * Q
        nrm = (L ** 2).sum(1)
        L = L * np.sqrt(np.minimum(nrm, 0.97) / nrm)[:, None]     # keep psi >= 0.03
    psi = 1 - (L ** 2).sum(1)
    return L, psi


def sample(L, psi, n, rng):
    Z = rng.standard_normal((n, L.shape[1]))
    return Z @ L.T + np.sqrt(psi) * rng.standard_normal((n, len(psi)))


def run_cell(kind, h, M, rep, rng, n_test=1500, n_rand=30):
    L, psi = make_truth(kind, h, rng)
    Xh = sample(L, psi, M, rng); Xt = sample(L, psi, n_test, rng)
    obs = np.ones(Xh.shape, bool)
    mu = Xh.mean(0); sd = Xh.std(0, ddof=1)
    Xs = (Xh - mu) / sd; Xts = (Xt - mu) / sd
    # truth in the same standardised units (sd differs slightly from 1): rescale loadings
    r_cv, sc = FA.cv_select_rank(Xs, obs, [0, 1, 2, 3, 4, 6, 8, 12], seed=rep)
    par = FA.fit_fa(Xs, obs, r_cv, seed=rep)
    rtrue = L.shape[1]
    par_t = FA.fit_fa(Xs, obs, rtrue, seed=rep)                   # plug-in with the true rank
    Ls, ps = L / sd[:, None], psi / sd ** 2                      # truth in standardised units (mean shift is irrelevant)
    pb = psi.mean(); c = N / M
    rho_true = np.sort(np.linalg.svd(L, compute_uv=False) ** 2 / pb)[::-1]
    rank_eff = int((rho_true > np.sqrt(c)).sum())
    out = []
    order = SEL.greedy_design(par, range(N), max(KS), 'A_all')
    for tag, pr in (('cv', par), ('true_r', par_t)):
        order = SEL.greedy_design(pr, range(N), max(KS), 'A_comp') if pr['Lam'].shape[1] else np.arange(max(KS))
        for k in KS:
            S = order[:k]; T = np.setdiff1d(np.arange(N), S)
            pred = FA.predict_fa(pr, S, Xts[:, S])
            meas = float(((pred[:, T] - Xts[:, T]) ** 2).mean())
            row = dict(kind=kind, h=h, M=M, rep=rep, k=k, plug=tag, r_fit=pr['Lam'].shape[1], r_cv=r_cv,
                       rank_eff=rank_eff, r_true=rtrue, measured=meas,
                       oracle=TH.bayes_error(Ls, ps, S),            # (a) with the true parameters, the same S
                       naive=TH.bayes_error(pr['Lam'], pr['psi'], S) if pr['Lam'].shape[1] else float(pr['psi'][T].mean()),
                       fm_noinfl=TH.forecast_finite_m(pr['Lam'], pr['psi'], M, S, inflate=False),
                       fm=TH.forecast_finite_m(pr['Lam'], pr['psi'], M, S, inflate=True),
                       floor=TH.tail_floor(Ls, ps, S),
                       mean_pred=float((Xts[:, T] ** 2).mean()))
            out.append(row)
    return out


if __name__ == '__main__':
    reps, outdir = int(sys.argv[1]), sys.argv[2]
    shard = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    os.makedirs(outdir, exist_ok=True)
    rows = []
    t0 = time.time()
    for kind in ['one', 'block', 'power']:
        for h in [0.3, 0.6, 0.85]:
            for M in [30, 60, 125, 500]:
                for rep in range(reps):
                    rng = np.random.default_rng([shard, rep, M, int(h * 100), sum(map(ord, kind))])
                    rows += run_cell(kind, h, M, rep + 1000 * shard, rng)
        print(kind, round(time.time() - t0), flush=True)
        pd.DataFrame(rows).to_parquet(f"{outdir}/e1_shard{shard}.parquet")
