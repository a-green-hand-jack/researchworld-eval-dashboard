"""Shared driver: k_min / G_min for every (target, rule, gain model, cost)."""
import time
from common import *

GAINS = ["G1", "G1_add10", "G1_add20", "G2_0.25", "G2_0.5", "G2_1", "ceil", "ceil_add10", "ceil_add20"]
RULE_META = {"mean": ("mean", ""), "geo": ("geomean", "0"), "median": ("median", ""), "min": ("min", ""),
             "trim": ("trimmed_mean", str(R.TRIM)), "borda": ("borda", ""), "plurality": ("plurality", ""),
             "copeland": ("copeland", ""), "condorcet": ("condorcet_winner", "")}
for _r in R.CARDINAL_POWER: RULE_META[_r] = ("power_mean", _r.split(":")[1])

def gain_vectors(s, best, spec):
    """per-task (delta, hi, h): max boost is min(delta, hi - s)^+; h = reference headroom."""
    ceil = spec.startswith("ceil")
    hi = np.full_like(s, 100.0) if ceil else np.minimum(100.0, best + 1.0)
    h = np.maximum(hi - s, 0.0)
    if spec in ("G1", "ceil"): delta = np.full_like(s, np.inf)
    elif "_add" in spec: delta = np.full_like(s, float(spec.split("_add")[1]))
    elif spec.startswith("G2_"): delta = float(spec.split("_")[1]) * h
    else: raise ValueError(spec)
    return delta, hi, h

def field_matrix(S, t, field):
    """leaderboard restricted to the top-N models by mean (plus the target)."""
    if field == "all": return S, t
    N = int(field.replace("top", ""))
    idx = list(np.argsort(-S.mean(1), kind="stable")[:N])
    if t not in idx: idx.append(t)
    idx = np.array(sorted(idx)); return S[idx], int(np.where(idx == t)[0][0])

def run(S, names, targets, rules, gains, costs=("linear", "headroom"), field="all", tag=None, verbose=True):
    tag = tag or {}
    m0, n = S.shape; rows = []; t0 = time.time()
    for ii, t0_ in enumerate(targets):
        X, t = field_matrix(S, int(t0_), field)
        best = X.max(0); s = X[t]; m = len(X)
        sc = {r: V._scores(X, r) for r in rules}
        for rule in rules:
            gap = float(np.delete(sc[rule], t).max() - sc[rule][t])
            irank = int((np.delete(sc[rule], t) >= sc[rule][t]).sum() + 1) if rule != "condorcet" else int(m - sc[rule][t])
            for gm in gains:
                delta, hi, h = gain_vectors(s, best, gm)
                kmin = V.min_k(X, t, rule, delta, hi)
                feas = bool(np.isfinite(kmin))
                u = np.maximum(np.minimum(delta, hi - s), 0.0)
                for cost in costs:
                    w = np.ones(n) if cost == "linear" else 1.0 / np.maximum(h, 1e-9)
                    if kmin == 0: g, kind = 0.0, "exact"
                    elif not feas: g, kind = np.inf, "exact"
                    elif rule in R.ORDINAL or rule in ("trim",) or rule.startswith("pmean:") and float(rule.split(":")[1]) > 1:
                        g, kind = np.nan, "na"
                    else:
                        g = V.g_min(X, t, rule, u, w); kind = "exact" if np.isfinite(g) or g == np.inf else "na"
                    ex = V.is_exact(rule, n)
                    rows.append(dict(rule=RULE_META[rule][0], rule_param=RULE_META[rule][1], gain_model=gm, cost=cost,
                                     target_id=names[t0_], init_rank=irank, incumbent_gap=gap, n_tasks=n, n_models=m,
                                     k_min=(int(kmin) if feas else np.nan), G_min=(g if np.isfinite(g) else np.nan),
                                     G_min_kind=kind, feasible=int(feas), exact=int(ex), field=field, **tag))
        if verbose and ii % 20 == 0: print(tag, field, ii, len(targets), round(time.time() - t0), "s", flush=True)
    return pd.DataFrame(rows)
