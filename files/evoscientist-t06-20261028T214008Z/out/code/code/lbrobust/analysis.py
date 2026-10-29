"""Dataset-level fragility analysis built on perturb.Searcher."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import kendalltau

from .bt import CompData, fit_bt
from .perturb import Searcher, FAMILIES

Z95 = 1.959963984540054


def pair_cost(S: Searcher, hi, lo, fam, step_frac=0.5, methods=("greedy", "amip")):
    out = {}
    best = np.inf
    if "greedy" in methods:
        g = S.greedy(hi, lo, fam, step_frac=step_frac)
        out["greedy"] = g["cost"] if g["success"] else np.inf
        out["greedy_refits"] = g["refits"]
        best = min(best, out["greedy"])
    if "amip" in methods:
        a = S.amip(hi, lo, fam)
        out["amip_pred"] = a["pred"]
        out["amip"] = a["cost"] if a["success"] else np.inf
        best = min(best, out["amip"])
    out["best"] = best
    return out


def analyze_dataset(d: CompData, families=FAMILIES, top1_cands=5, sig_cands=20, lam=1e-2,
                    adjacent=True, step_frac=0.5, methods=("greedy", "amip")):
    """Returns (pairs DataFrame, summary dict).

    pairs rows: role in {adjacent, top1, sig}; hi/lo indices; ranks; gap/se/z/leverage;
    per-family costs (greedy, amip, best) in counts.
    """
    S = Searcher(d, lam=lam)
    f = S.fit0
    K = d.K
    N = d.N
    order = f.ranking(K)
    rank = np.empty(K, int)
    rank[order] = np.arange(1, K + 1)
    rows = {}

    def do(hi, lo, role):
        key = (int(hi), int(lo))
        if key in rows:
            rows[key]["roles"].add(role)
            return rows[key]
        r = dict(hi=int(hi), lo=int(lo), hi_name=d.names[hi], lo_name=d.names[lo],
                 rank_hi=int(rank[hi]), rank_lo=int(rank[lo]), roles={role})
        r.update(S.leverage(hi, lo))
        for fam in families:
            c = pair_cost(S, hi, lo, fam, step_frac=step_frac, methods=methods)
            for k, v in c.items():
                r[f"{fam}_{k}"] = v
        rows[key] = r
        return r

    # adjacent pairs
    if adjacent:
        for r_ in range(K - 1):
            do(order[r_], order[r_ + 1], "adjacent")
    # top-1: challengers with smallest first-order estimate, per family
    top = order[0]
    lev_all = {int(j): S.leverage(top, j) for j in order[1:]}
    cands = set()
    for fam in families:
        srt = sorted(lev_all, key=lambda j: lev_all[j][f"klin_{fam}"])
        cands |= set(srt[:top1_cands])
    for j in cands:
        do(top, j, "top1")
    # significant pairs (z >= 1.96): candidates by first-order estimate
    sig = []
    for a_ in range(K):
        for b_ in range(a_ + 1, K):
            hi, lo = (order[a_], order[b_])
            lv = S.leverage(hi, lo)
            if lv["z"] >= Z95:
                sig.append((hi, lo, lv))
    sig_c = set()
    for fam in families:
        srt = sorted(sig, key=lambda t: t[2][f"klin_{fam}"])
        sig_c |= {(int(h), int(l)) for h, l, _ in srt[:sig_cands]}
    for h, l in sig_c:
        do(h, l, "sig")
    df = pd.DataFrame(list(rows.values()))
    df["roles"] = df["roles"].apply(lambda s: ",".join(sorted(s)))
    df["N"] = N
    df["dataset"] = d.meta.get("name", "")
    summ = dict(dataset=d.meta.get("name", ""), design=d.meta.get("design", ""), N=N, K=K,
                n_types=int((d.n > 0).sum()), top1=d.names[top], top1_z_min=None,
                n_sig_pairs=len(sig), n_pairs=K * (K - 1) // 2)
    t1 = df[df.roles.str.contains("top1")]
    summ["top1_z_min"] = float(t1.z.min())
    for fam in families:
        summ[f"top1_{fam}"] = float(t1[f"{fam}_best"].min())
        summ[f"top1_{fam}_frac"] = summ[f"top1_{fam}"] / N
        s_ = df[df.roles.str.contains("sig")]
        summ[f"sig_{fam}"] = float(s_[f"{fam}_best"].min()) if len(s_) else np.inf
        summ[f"sig_{fam}_frac"] = summ[f"sig_{fam}"] / N
        if adjacent:
            a_ = df[df.roles.str.contains("adjacent")]
            summ[f"adj_{fam}_median"] = float(a_[f"{fam}_best"].median())
            summ[f"adj_{fam}_median_frac"] = summ[f"adj_{fam}_median"] / N
    # top1 z of the runner-up
    ru = df[(df.hi == top) & (df.lo == order[1])]
    summ["z_top12"] = float(ru.z.iloc[0])
    summ["rho_top12"] = float(np.sqrt(ru.neff_drop.iloc[0] / N))
    return df, summ


# ------------------------------------------------------------------------------------------
def _subsample_counts(rng, n, m):
    """Uniformly choose m of the sum(n) units without replacement; returns removed counts."""
    return rng.multivariate_hypergeometric(n.astype(np.int64), int(m))


def random_perturb(d: CompData, kind, rate, seed, lam=1e-2, base_fit=None, S=None):
    """Random (non-adversarial) perturbation of a fraction `rate` of comparisons.

    kind: 'drop' (delete random comparisons), 'flip' (re-label random comparisons:
          win<->loss, tie->random decisive), 'add' (insert random decisive comparisons on
          pairs drawn from the empirical schedule with a fair coin label).
    Returns dict: top1_changed, kendall_tau, frac_sig_reversed.
    """
    rng = np.random.default_rng(seed)
    if S is None:
        S = Searcher(d, lam=lam)
    tab = S.tab
    n0 = tab.n0
    N = n0.sum()
    m = int(round(rate * N))
    n = n0.copy()
    if kind == "drop":
        n = n - _subsample_counts(rng, n0, m)
    elif kind == "flip":
        chosen = _subsample_counts(rng, n0, m)
        n = n - chosen
        y = tab.base.y
        for t in np.where(chosen > 0)[0]:
            c = chosen[t]
            if y[t] == 1.0:
                n[S.t_y0[t]] += c
            elif y[t] == 0.0:
                n[S.t_y1[t]] += c
            else:
                k1 = rng.binomial(c, 0.5)
                n[S.t_y1[t]] += k1
                n[S.t_y0[t]] += c - k1
    elif kind == "add":
        # pairs from the empirical schedule
        pair_n = np.bincount(tab.pair_id, weights=n0)
        pairs = rng.choice(len(pair_n), size=m, p=pair_n / pair_n.sum())
        labs = rng.integers(0, 2, size=m)
        for p_, l_ in zip(pairs, labs):
            t = S.tab.lab_type[(int(p_), float(l_))]
            n[t] += 1
    else:
        raise ValueError(kind)
    f0 = S.fit0
    f1 = S.fit(n, theta0=f0.theta)
    K = d.K
    th0, th1 = f0.theta[:K], f1.theta[:K]
    top_changed = int(np.argmax(th0) != np.argmax(th1))
    tau = kendalltau(th0, th1).statistic
    # significant pairs (original fit) reversed
    se = np.sqrt(np.maximum(np.add.outer(np.diag(f0.Hinv)[:K], np.diag(f0.Hinv)[:K]) - 2 * f0.Hinv[:K, :K], 1e-300))
    g0 = np.subtract.outer(th0, th0)
    g1 = np.subtract.outer(th1, th1)
    sig = (g0 / se >= Z95)
    rev = sig & (g1 < 0)
    frac_rev = rev.sum() / max(sig.sum(), 1)
    return dict(top1_changed=top_changed, kendall_tau=float(tau), frac_sig_reversed=float(frac_rev),
                any_sig_reversed=int(rev.sum() > 0))


def bootstrap_data(d: CompData, seed):
    rng = np.random.default_rng(seed)
    n = rng.multinomial(int(d.N), d.n / d.n.sum()).astype(float)
    keep = n > 0
    out = CompData(d.i[keep], d.j[keep], d.y[keep], n[keep], list(d.names),
                   None if d.home is None else d.home[keep], dict(d.meta))
    return out


def subsample_data(d: CompData, frac, seed):
    rng = np.random.default_rng(seed)
    m = int(round(frac * d.N))
    n = rng.multivariate_hypergeometric(d.n.astype(np.int64), m).astype(float)
    keep = n > 0
    return CompData(d.i[keep], d.j[keep], d.y[keep], n[keep], list(d.names),
                    None if d.home is None else d.home[keep], dict(d.meta))


def present_players(d: CompData):
    """Drop players with zero comparisons (after subsampling) and reindex."""
    used = np.unique(np.concatenate([d.i[d.n > 0], d.j[d.n > 0]]))
    if len(used) == d.K:
        return d
    m = -np.ones(d.K, int)
    m[used] = np.arange(len(used))
    keep = d.n > 0
    return CompData(m[d.i[keep]], m[d.j[keep]], d.y[keep], d.n[keep], [d.names[u] for u in used],
                    None if d.home is None else d.home[keep], dict(d.meta))
