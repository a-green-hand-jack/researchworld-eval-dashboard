import numpy as np, pandas as pd

def per_model(df):
    """average over reps/folds: one row per (model, selector, method, k) with pooled sums."""
    g = df.groupby(['model', 'selector', 'method', 'k'])[['n_t', 'sse_z', 'sse_pts', 'sae_pts']].mean().reset_index()
    return g

def boot_metric(g, keys, n_boot=1000, seed=0, metric='nmse', labels=None):
    """bootstrap over models (labels=None) or over clusters (labels = dict model -> cluster). returns DataFrame indexed by keys with mean, lo, hi."""
    rng = np.random.default_rng(seed)
    models = np.sort(g.model.unique())
    idx = {m: i for i, m in enumerate(models)}
    g = g.assign(mi=g.model.map(idx))
    out = []
    cnt = _bootstrap_counts(len(models), n_boot, seed, None if labels is None else [labels[m] for m in models])
    for key, sub in g.groupby(keys):
        num = np.zeros(len(models)); den = np.zeros(len(models))
        col = {'nmse': 'sse_z', 'mse_pts': 'sse_pts', 'mae_pts': 'sae_pts'}[metric]
        num[sub.mi.values] = sub[col].values; den[sub.mi.values] = sub.n_t.values
        est = num.sum() / den.sum()
        bs = (cnt @ num) / (cnt @ den)
        if metric == 'mse_pts':
            est, bs = np.sqrt(est), np.sqrt(bs)
        out.append((*(key if isinstance(key, tuple) else (key,)), est, np.percentile(bs, 2.5), np.percentile(bs, 97.5)))
    return pd.DataFrame(out, columns=[*([keys] if isinstance(keys, str) else keys), 'est', 'lo', 'hi'])

def paired_diff(g, a, b, keys=('method', 'k'), metric='sse_z', n_boot=1000, seed=0):
    """selector a minus selector b, paired by model, bootstrap CI on pooled-error difference (negative = a better)."""
    rng = np.random.default_rng(seed)
    A = g[g.selector == a].set_index(['model', *keys]); Bm = g[g.selector == b].set_index(['model', *keys])
    j = A[[metric, 'n_t']].join(Bm[[metric, 'n_t']], rsuffix='_b', how='inner')
    rows = []
    for key, sub in j.groupby(level=list(range(1, 1 + len(keys)))):
        n = len(sub)
        num_a, num_b, den_a, den_b = sub[metric].values, sub[metric + '_b'].values, sub.n_t.values, sub.n_t_b.values
        est = num_a.sum() / den_a.sum() - num_b.sum() / den_b.sum()
        bi = rng.integers(0, n, (n_boot, n))
        bs = num_a[bi].sum(1) / den_a[bi].sum(1) - num_b[bi].sum(1) / den_b[bi].sum(1)
        rows.append((*(key if isinstance(key, tuple) else (key,)), est, np.percentile(bs, 2.5), np.percentile(bs, 97.5)))
    return pd.DataFrame(rows, columns=[*keys, 'diff', 'lo', 'hi'])


def _bootstrap_counts(n_models, n_boot, seed, labels=None):
    """(n_boot x n_models) resampling weights.  labels=None: models are resampled one by one; otherwise whole clusters
    (e.g. organisations) are resampled with replacement and every model gets the number of times its cluster was drawn."""
    rng = np.random.default_rng(seed)
    if labels is None:
        B = rng.integers(0, n_models, (n_boot, n_models))
        cnt = np.zeros((n_boot, n_models))
        for b in range(n_boot):
            cnt[b] = np.bincount(B[b], minlength=n_models)
        return cnt
    labels = np.asarray(labels)
    uc, inv = np.unique(labels, return_inverse=True)
    B = rng.integers(0, len(uc), (n_boot, len(uc)))
    cc = np.zeros((n_boot, len(uc)))
    for b in range(n_boot):
        cc[b] = np.bincount(B[b], minlength=len(uc))
    return cc[:, inv]


def paired_diff_cl(g, a, b, labels, keys=('method', 'k'), metric='sse_z', n_boot=1000, seed=0):
    """As paired_diff, but the bootstrap resamples clusters: labels = dict model -> cluster label."""
    A = g[g.selector == a].set_index(['model', *keys]); Bm = g[g.selector == b].set_index(['model', *keys])
    j = A[[metric, 'n_t']].join(Bm[[metric, 'n_t']], rsuffix='_b', how='inner')
    models = np.sort(j.index.get_level_values(0).unique())
    mi = {m: i for i, m in enumerate(models)}
    cnt = _bootstrap_counts(len(models), n_boot, seed, [labels[m] for m in models])
    rows = []
    for key, sub in j.groupby(level=list(range(1, 1 + len(keys)))):
        ii = np.array([mi[m] for m in sub.index.get_level_values(0)])
        na, nb = np.zeros(len(models)), np.zeros(len(models)); da, db = np.zeros(len(models)), np.zeros(len(models))
        na[ii], nb[ii], da[ii], db[ii] = sub[metric].values, sub[metric + '_b'].values, sub.n_t.values, sub.n_t_b.values
        est = na.sum() / da.sum() - nb.sum() / db.sum()
        bs = (cnt @ na) / (cnt @ da) - (cnt @ nb) / (cnt @ db)
        rows.append((*(key if isinstance(key, tuple) else (key,)), est, *np.percentile(bs, [2.5, 97.5])))
    return pd.DataFrame(rows, columns=[*keys, 'diff', 'lo', 'hi'])


def gap_closed(g, gf, n_boot=1000, seed=0, base_sel='random', k_floor=999, labels=None, return_boot=False):
    """Gap-closed fraction G(k) = (E_mean - E_k) / (E_mean - E_floor)  (pre-fixed k criterion).

    E_mean : column-mean predictor (k = 0), pooled nMSE on the same targets and models.
    E_floor: full-information predictor (all observed non-target benchmarks revealed, k label 999), same inference rule
             ('own', primary) or the best inference rule at full information ('best', secondary).
    g, gf  : per-model tables (analysis_lib.per_model) of the B_* run and of the matching F_* run.
    Cluster bootstrap over held-out models (jointly for numerator and denominator).
    Returns (G table with CI, floor table).  k*(g) = smallest k whose lower CI bound of G is >= g.
    """
    models = np.sort(np.intersect1d(g.model.unique(), gf.model.unique()))
    idx = {m: i for i, m in enumerate(models)}
    cnt = _bootstrap_counts(len(models), n_boot, seed, None if labels is None else [labels[m] for m in models])
    boots = {}

    def vec(sub):
        sub = sub[sub.model.isin(idx)]
        num = np.zeros(len(models)); den = np.zeros(len(models))
        ii = sub.model.map(idx).values
        num[ii] = sub.sse_z.values; den[ii] = sub.n_t.values
        return num, den

    def pooled(num, den):
        return num.sum() / den.sum(), (cnt @ num) / (cnt @ den)

    gf = gf[gf.k == k_floor]
    fl = {m: pooled(*vec(sub)) for m, sub in gf.groupby('method')}
    best_boot = np.min([b for _, b in fl.values()], axis=0)
    best_est = min(e for e, _ in fl.values())
    frows = [(m, e, *np.percentile(b, [2.5, 97.5])) for m, (e, b) in fl.items()]
    frows.append(('best', best_est, *np.percentile(best_boot, [2.5, 97.5])))
    gm = g[(g.method == 'mean') & (g.selector == base_sel)]
    mean_by_k = {k: pooled(*vec(sub)) for k, sub in gm.groupby('k')}
    mrow = pooled(*vec(gm[gm.k == gm.k.min()])) if len(gm) else None
    if mrow is not None:
        frows.append(('mean_k0', mrow[0], *np.percentile(mrow[1], [2.5, 97.5])))
    rows = []
    for (sel, meth, k), sub in g.groupby(['selector', 'method', 'k']):
        if meth == 'mean' or k not in mean_by_k:
            continue
        num, den = vec(sub)
        ek, eb = pooled(num, den)
        em, emb = mean_by_k[k]
        out = [sel, meth, k, ek]
        for tag, (fe, fb) in (('own', (fl[meth][0], fl[meth][1]) if meth in fl else (np.nan, None)), ('best', (best_est, best_boot))):
            if fb is None:     # rule without a full-information partner run: no same-rule floor
                out += [np.nan] * 3; continue
            d0 = em - fe
            G = (em - ek) / d0 if d0 > 0 else np.nan
            Gb = (emb - eb) / (emb - fb)
            out += [G, *np.percentile(Gb, [2.5, 97.5])]
            boots[(sel, meth, k, tag)] = Gb
        rows.append(out)
    cols = ['selector', 'method', 'k', 'nmse', 'G_own', 'G_own_lo', 'G_own_hi', 'G_best', 'G_best_lo', 'G_best_hi']
    res = pd.DataFrame(rows, columns=cols), pd.DataFrame(frows, columns=['method', 'nmse_floor', 'lo', 'hi'])
    return (*res, boots) if return_boot else res
