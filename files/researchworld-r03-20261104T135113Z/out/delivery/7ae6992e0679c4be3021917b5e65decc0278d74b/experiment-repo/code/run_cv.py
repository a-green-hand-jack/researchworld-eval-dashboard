"""Cross-validated 'new model' protocol.

For every fold, a selection ordering is computed from the TRAIN models only; each held-out model reveals only its first
k selected benchmarks (among those it has scores for) and all its other observed benchmarks are predicted and compared
to the measured values.  See README for the protocol.

usage: python run_cv.py --data mteb_dense --out results/raw/mteb_dense_main.parquet [options]
"""
import argparse, json, os, time
import numpy as np, pandas as pd
from scipy.stats import rankdata
import lib

COST = None
ALL_SEL = ['random', 'popular', 'rawvar', 'central', 'kcenter', 'lev', 'qr', 'dopt', 'gv_fa', 'gv_emp']
SCALE = {'olb': 1.0}      # raw units -> 0-100 points


def pts_scale(name):
    return SCALE.get(name, 100.0)


def make_folds(split, M, K, rng, groups=None, dates=None):
    idx = np.arange(M)
    if split == 'lomo':
        return [(np.delete(idx, i), np.array([i])) for i in range(M)]
    if split == 'kfold':
        p = rng.permutation(M)
        return [(np.setdiff1d(idx, f), np.sort(f)) for f in np.array_split(p, K)]
    if split == 'group':       # leave-groups-out (e.g. organisation): groups are assigned to K folds at random
        ug = np.unique(groups)
        gp = rng.permutation(ug)
        gf = {g: i % K for i, g in enumerate(gp)}
        f_of = np.array([gf[g] for g in groups])
        return [(idx[f_of != k], idx[f_of == k]) for k in range(K) if (f_of == k).any()]
    if split == 'temporal':    # train on the earliest (1-1/K) of dated models, test on the latest 1/K ; one fold
        ok = ~pd.isna(dates)
        o = idx[ok][np.argsort(np.asarray(dates)[ok])]
        cut = int(len(o) * (1 - 1.0 / K))
        return [(np.concatenate([o[:cut], idx[~ok]]), o[cut:])]
    raise ValueError(split)


def orderings(name, Ztr, Ytr, fa, kmax, rng, n_rand, selectors, leakZ=None, ks_=(), cand=None):
    """selection orderings computed from the training matrix only."""
    N = Ztr.shape[1]
    Zc = fa.complete(Ztr if leakZ is None else leakZ)
    out = {}
    for s in selectors:
        if s == 'random':
            out[s] = [list(rng.permutation(N)) for _ in range(n_rand)]
        elif s == 'popular':
            out[s] = [lib.popular_order(Ytr)]
        elif s == 'rawvar':
            out[s] = [lib.rawvar_order(Ytr)]
        elif s == 'central':
            out[s] = [lib.central_order(Zc)]
        elif s == 'kcenter':
            out[s] = [lib.kcenter_order(Zc)]
        elif s == 'lev':
            out[s] = [lib.leverage_order(Zc, fa.r)]
        elif s == 'qr':
            out[s] = [lib.qr_pivot_order(Zc, fa.r)]
        elif s.startswith('lev_r') or s.startswith('qr_r'):     # leverage / pivoted QR with a chosen rank (diagnostic of their failure)
            rr = int(s.split('_r')[1])
            out[s] = [(lib.leverage_order if s.startswith('lev') else lib.qr_pivot_order)(Zc, rr)]
        elif s == 'dopt':
            out[s] = [lib.greedy_dopt(fa.W, fa.psi, kmax, cand)]
        elif s == 'gv_fa':
            out[s] = [lib.greedy_cond_var(fa.cov(), kmax, cand=cand)]
        elif s == 'exh':      # per-k exhaustive best subset (small N only)
            out[s] = {k: [lib.exhaustive_order(Zc, k)] for k in ks_}
        elif s == 'gvc_fa':   # cost-aware greedy: conditional-variance reduction per second of evaluation
            out[s] = [lib.greedy_cond_var(fa.cov(), kmax, cand=cand, cost=COST)]
        elif s == 'cheap':
            out[s] = [list(np.argsort(COST, kind='stable'))]
        elif s == 'gv_emp':
            out[s] = [lib.greedy_cond_var(lib.emp_cov(Zc), kmax, cand=cand)]
        elif s == 'oracle':   # per-model, computed in run() from the held-out row itself (upper bound on selection)
            out[s] = [None]
        else:
            raise ValueError(s)
    if cand is not None:     # candidates only (target benchmarks are never selected)
        for s, v in out.items():
            if s == 'oracle':
                continue
            f = lambda o: [j for j in o if cand[j]]
            out[s] = {k: [f(o) for o in ol] for k, ol in v.items()} if isinstance(v, dict) else [f(o) for o in v]
    return out


def run(args):
    z = np.load(os.path.join(args.matdir, args.data + '.npz'), allow_pickle=True)
    Y = z['Y']
    M, N = Y.shape
    full = 100.0 if args.data == 'olb' else 1.0     # raw scale of a full score
    if args.transform == 'logit':
        Yw = np.log(np.clip(Y / full, 0.005, 0.995) / (1 - np.clip(Y / full, 0.005, 0.995)))
        inv = lambda w: full / (1 + np.exp(-w))
    else:
        Yw, inv = Y, (lambda w: w)
    sc = pts_scale(args.data)
    meta = None
    mp = os.path.join(args.matdir, args.data + '_models.csv')
    if os.path.exists(mp):
        meta = pd.read_csv(mp, index_col=0)
    ntar = max(1, int(round(args.target_frac * N))) if args.target_frac > 0 else 1
    ks = [k for k in args.ks if k <= N - 1 - ntar] if args.target_frac > 0 else [k for k in args.ks if k <= N - 2]
    if args.floor:      # full-information floor: every observed non-target benchmark is revealed (k label 999)
        ks = [999]
    kmax = max(ks)
    global COST
    if args.budgets:
        c = pd.read_csv(os.path.join(args.matdir, '..', args.cost_file), index_col=0).iloc[:, 0]
        COST = np.maximum(c.reindex(z['benches'].astype(str)).fillna(c.median()).values.astype(float), 1.0)
        ks = list(args.budgets)       # budget in per-mille of the total cost of the candidate benchmarks
        kmax = N
    methods = args.methods
    selectors = args.selectors
    rows, rank_rows, rinfo = [], [], []
    t0 = time.time()
    for rep in range(args.reps):
        rng = np.random.default_rng(args.seed * 1000 + rep)
        groups = dates = None
        if args.split == 'group':
            if args.group_col == 'family':      # strict family: organisations linked through in-matrix base models (lib.family_labels)
                groups = lib.family_labels(meta['org'].fillna('NA').astype(str).values, meta['adapted_from'].values, meta['name'].values)
            else:
                groups = meta[args.group_col].fillna('NA').astype(str).values
            # unlabelled / placeholder family values ('NA', 'Removed') are not one family: make each such model its own group
            groups = np.array([f'single_{i}' if g in ('NA', 'Removed', '', 'nan') else g for i, g in enumerate(groups)])
        if args.split == 'temporal':
            dates = pd.to_datetime(meta['release_date' if 'release_date' in meta else 'Submission Date'], errors='coerce').values
        folds = make_folds(args.split, M, args.K, rng, groups, dates)
        P = {}   # predictions for rank metrics
        T0 = np.zeros(N, bool)
        if args.target_frac > 0:   # fixed held-out target benchmarks (never selected) so that all k are scored on the same targets
            T0[rng.choice(N, max(1, int(round(args.target_frac * N))), replace=False)] = True
        cand = ~T0 if args.target_frac > 0 else None
        for fi, (tr, te) in enumerate(folds):
            if args.m_train and args.m_train < len(tr):
                tr = rng.choice(tr, args.m_train, replace=False)
            Ytr = Yw[tr].copy()
            if args.extra_missing > 0:
                Ytr[rng.random(Ytr.shape) < args.extra_missing] = np.nan
            Ztr, mu, sd, okc = lib.standardise(Ytr)
            Ztr[:, ~okc] = np.nan
            if args.rank == 'auto':
                ranks = [r for r in [1, 2, 3, 4, 6, 8, 12, 16, 24] if r <= max(1, min(Ztr.shape) // 3)]
                r, _ = lib.holdout_rank(Ztr, ranks, seed=rep * 100 + fi)
            else:
                r = int(args.rank)
            fa = lib.FA(r, seed=rep).fit(Ztr)
            pred = lib.Predictor(Ztr, fa)
            leakZ = None
            if args.leak:    # selection sees the test models too (diagnostic of optimism)
                Zall = (Yw - mu) / sd
                Zall[:, ~okc] = np.nan
                leakZ = Zall
            fa_sel = fa
            if args.leak:    # the selection model is also fitted on the test rows (incl. their target scores); inference stays train-only
                fa_sel = lib.FA(r, seed=rep).fit(leakZ)
            ords = orderings(args.data, Ztr, Ytr, fa_sel, kmax, rng, args.n_rand, selectors, leakZ, ks, cand)
            Zte = (Yw[te] - mu) / sd
            Zte[:, ~okc] = np.nan
            Yte = Y[te]
            sd0 = sd if args.transform == 'none' else np.where(okc, np.nanstd(Y[tr], 0) + 1e-12, 1.0)
            obs = ~np.isnan(Zte)
            oracle = None
            if 'oracle' in ords:   # greedy forward selection on the held-out model's OWN target error (uses its target scores: upper bound, not a method)
                oracle = {}
                ko = min(kmax, 16)
                for a in range(len(te)):
                    tm = obs[a] & T0
                    av = [j for j in range(N) if obs[a, j] and not T0[j]]
                    S = []
                    for _ in range(min(ko, len(av))):
                        best, bj = np.inf, None
                        for j in av:
                            if j in S:
                                continue
                            e = ((fa.predict_from(Zte[a, S + [j]][None], S + [j])[0] - Zte[a])[tm] ** 2).sum()
                            if e < best:
                                best, bj = e, j
                        S.append(bj)
                    oracle[a] = S
            for sel, olist in ords.items():
                for method in methods:
                    for k in ks:
                        pred._cache.clear()
                        acc = np.zeros((len(te), 3)); cnt = np.zeros(len(te)); szs = np.zeros(len(te))
                        Pm = np.full(Zte.shape, np.nan)
                        for order in (olist[k] if isinstance(olist, dict) else olist):
                            # first k available benchmarks per test model
                            groups_S = {}
                            for a in range(len(te)):
                                if sel == 'oracle':
                                    if k > 16:
                                        continue
                                    order = np.asarray(oracle[a], int)
                                order = np.asarray(order)
                                av = order[obs[a, order]]
                                if args.budgets:
                                    cum = np.cumsum(COST[av])
                                    tot = COST[~T0].sum() if args.target_frac > 0 else COST.sum()
                                    av = av[:max(1, int(np.searchsorted(cum, k / 1000.0 * tot, 'right')))]
                                else:
                                    av = av[:k]
                                groups_S.setdefault(tuple(av), []).append(a)
                            for S, members in groups_S.items():
                                if not args.budgets and not args.floor and len(S) < k:    # model has fewer than k scores: skip
                                    continue
                                members = np.array(members)
                                Zp = pred.predict(method, list(S), Zte[members][:, list(S)])
                                tmask = obs[members].copy()
                                tmask[:, list(S)] = False
                                if args.target_frac > 0:
                                    tmask[:, ~T0] = False
                                Praw = inv(Zp * sd + mu)
                                eraw = np.where(tmask, Praw - Yte[members], 0.0)
                                acc[members, 0] += ((eraw / sd0) ** 2).sum(1)
                                acc[members, 1] += (eraw ** 2 * sc ** 2).sum(1)
                                acc[members, 2] += (np.abs(eraw) * sc).sum(1)
                                szs[members] += len(S) * (tmask.sum(1) > 0)
                                cnt[members] += tmask.sum(1)
                                Pm[members] = np.where(tmask, Praw, Pm[members])
                        nrep = len(olist[k] if isinstance(olist, dict) else olist)
                        for a in range(len(te)):
                            if cnt[a] > 0:
                                rows.append((rep, fi, int(te[a]), sel, method, k, cnt[a] / nrep, acc[a, 0] / nrep, acc[a, 1] / nrep, acc[a, 2] / nrep, szs[a] / nrep))
                        if args.rank_metrics and sel in args.rank_sel and method in args.rank_meth and k in args.rank_k:
                            P.setdefault((sel, method, k), np.full((M, N), np.nan))
                            msk = ~np.isnan(Pm)
                            P[(sel, method, k)][te[:, None].repeat(N, 1)[msk], np.tile(np.arange(N), (len(te), 1))[msk]] = Pm[msk]
            rinfo.append((rep, fi, r, len(tr), len(te)))
            print(f'rep {rep} fold {fi}/{len(folds)} r={r} ntr={len(tr)} nte={len(te)} t={time.time()-t0:.0f}s', flush=True)
        for (sel, method, k), Pm in P.items():
            rho = []
            for j in range(N):
                m = ~np.isnan(Pm[:, j]) & ~np.isnan(Y[:, j])
                if m.sum() >= 8:
                    rho.append(np.corrcoef(rankdata(Pm[m, j]), rankdata(Y[m, j]))[0, 1])
            rank_rows.append((rep, sel, method, k, float(np.nanmean(rho)), len(rho)))
    df = pd.DataFrame(rows, columns=['rep', 'fold', 'model', 'selector', 'method', 'k', 'n_t', 'sse_z', 'sse_pts', 'sae_pts', 'size'])
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    df.to_parquet(args.out)
    if rank_rows:
        pd.DataFrame(rank_rows, columns=['rep', 'selector', 'method', 'k', 'spearman', 'n_bench']).to_parquet(args.out.replace('.parquet', '_rank.parquet'))
    pd.DataFrame(rinfo, columns=['rep', 'fold', 'rank', 'n_train', 'n_test']).to_parquet(args.out.replace('.parquet', '_folds.parquet'))
    json.dump(vars(args), open(args.out.replace('.parquet', '.json'), 'w'))
    print('done', len(df), time.time() - t0, flush=True)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', required=True)
    ap.add_argument('--matdir', default=os.path.join(os.path.dirname(__file__), '..', 'data', 'matrices'))
    ap.add_argument('--out', required=True)
    ap.add_argument('--split', default='kfold', choices=['kfold', 'lomo', 'group', 'temporal'])
    ap.add_argument('--K', type=int, default=10)
    ap.add_argument('--reps', type=int, default=3)
    ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--ks', type=int, nargs='+', default=[1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 24, 32, 48, 64])
    ap.add_argument('--selectors', nargs='+', default=ALL_SEL)
    ap.add_argument('--methods', nargs='+', default=lib.METHODS)
    ap.add_argument('--n_rand', type=int, default=10)
    ap.add_argument('--rank', default='auto')
    ap.add_argument('--m_train', type=int, default=0)
    ap.add_argument('--extra_missing', type=float, default=0.0)
    ap.add_argument('--group_col', default='org', help="column of the models table, or 'family' (strict families)")
    ap.add_argument('--target_frac', type=float, default=0.0)
    ap.add_argument('--transform', default='none', choices=['none', 'logit'])
    ap.add_argument('--budgets', type=int, nargs='*', default=None)
    ap.add_argument('--cost_file', default='mteb_task_cost_seconds.csv')
    ap.add_argument('--floor', action='store_true')
    ap.add_argument('--leak', action='store_true')
    ap.add_argument('--rank_metrics', action='store_true')
    ap.add_argument('--rank_sel', nargs='+', default=['random', 'gv_fa', 'gv_emp'])
    ap.add_argument('--rank_meth', nargs='+', default=['fa', 'ridge'])
    ap.add_argument('--rank_k', type=int, nargs='+', default=[2, 4, 8, 16])
    run(ap.parse_args())
