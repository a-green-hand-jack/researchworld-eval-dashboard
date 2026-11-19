"""Natural perturbation on Arena-140k: first half vs second half of the votes by timestamp, compared with random
half splits of the same votes.  Only models with >=300 votes in each time half are kept (models that enter or leave
the arena mid-period would otherwise dominate).  Metrics: Kendall tau between the two half-fits; number of
pairs significant in the full fit (z>1.96) whose order differs between the halves.  Writes results/temporal_arena140k.csv"""
import numpy as np, pandas as pd
import datasets as ds
from exp_arena140k import kendall

if __name__ == "__main__":
    d = ds.arena140k_votes()
    order = np.argsort(d.timestamp.values, kind="stable"); half = len(d) // 2
    d = d.iloc[order].reset_index(drop=True)
    first, second = d.iloc[:half], d.iloc[half:]
    cnt = lambda x: pd.concat([x.model_a, x.model_b]).value_counts()
    c1, c2 = cnt(first), cnt(second)
    keep = sorted(m for m in set(c1.index) & set(c2.index) if c1[m] >= 300 and c2[m] >= 300)
    d = d[d.model_a.isin(keep) & d.model_b.isin(keep)].reset_index(drop=True)
    half = len(d) // 2; ts_cut = len(d) // 2
    print("models kept", len(keep), "of", len(set(d.model_a) | set(d.model_b)), "votes", len(d), flush=True)

    def fit(rows):
        dd = d.iloc[rows]
        b = ds._board_from_votes(dd.model_a.values, dd.model_b.values, dd.y.values, names=keep)
        return b.fit()[: b.m]
    full_b = ds._board_from_votes(d.model_a.values, d.model_b.values, d.y.values, names=keep)
    th = full_b.fit(); s = th[: full_b.m]
    sig = [(i, j) for i in range(len(keep)) for j in range(len(keep)) if s[i] > s[j] and (s[i] - s[j]) / full_b.ij_se(th, i, j) > 1.96]
    def n_rev(sa, sb):
        return int(sum((sa[i] > sa[j]) != (sb[i] > sb[j]) for i, j in sig))
    idx = np.arange(len(d))
    s1, s2 = fit(idx[:half]), fit(idx[half:])
    rows = [dict(kind="temporal", tau=kendall(s1, s2), rev=n_rev(s1, s2), nsig=len(sig), nmodels=len(keep), nvotes=len(d))]
    rng = np.random.default_rng(3)
    for r in range(200):
        perm = rng.permutation(len(d))
        sa, sb = fit(perm[:half]), fit(perm[half:])
        rows.append(dict(kind="random", tau=kendall(sa, sb), rev=n_rev(sa, sb), nsig=len(sig), nmodels=len(keep), nvotes=len(d)))
    out = pd.DataFrame(rows); out.to_csv("/work/results/temporal_arena140k.csv", index=False)
    t = out[out.kind == "temporal"].iloc[0]; r = out[out.kind == "random"]
    print(t.to_dict()); print("random tau %.3f +- %.3f, rev %.1f +- %.1f (max %d)" % (r.tau.mean(), r.tau.std(), r.rev.mean(), r.rev.std(), r.rev.max()))
