"""E1/E3 runner: price of first place per (target, rule, budget, incumbent set, objective) on one board."""
import time, numpy as np, pandas as pd
from . import rules as R, solvers as SV

RULE_LIST = ["mean", "zmean", "median", "min", "borda", "plurality", "copeland"]


def unit_costs(unit, S, t, ceil):
    """(kappa, gamma) of the cost sum_j (kappa_j delta_j)^gamma for a cost unit."""
    sg = S.std(axis=0)
    if unit == "points": return np.ones(S.shape[1]), 1
    if unit == "sigma": return 1.0 / sg, 1
    if unit == "convex2": return 1.0 / sg, 2
    if unit == "headroom": return 1.0 / np.maximum(ceil - S[t], 1e-9), 1
    raise ValueError(unit)


def incumbents(Aoff, t, K):
    A = np.asarray(Aoff, float).copy(); A[t] = -np.inf
    return np.argsort(-A, kind="stable")[:K]


def uniform_depth(S, t, rule, ceil, rivals, sigma, eps_agg, w=None):
    """Smallest uniform boost u (all tasks, clipped at the ceiling) making t first; total depth = sum_j min(u, headroom_j)."""
    kw = dict(sigma=sigma) if rule == "zmean" else ({"w": w} if (rule == "mean" and w is not None) else {})
    head = ceil - S[t]
    riv = np.delete(np.arange(S.shape[0]), t) if rivals is None else np.asarray(rivals)
    def first(u):
        if rule == "copeland":
            C = R.copeland_after_boost(S, t, S[t] + np.minimum(u, head), R.copeland_cached(S))
            return bool(C[t] > C[riv].max())
        S2 = S.copy(); S2[t] = S2[t] + np.minimum(u, head)
        return R.is_first(S2, t, rule, rivals, eps_agg=eps_agg, **kw)
    if first(0.0): return 0.0
    if not first(float(head.max())): return np.inf
    lo, hi = 0.0, float(head.max())
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if first(mid): hi = mid
        else: lo = mid
    return float(np.minimum(hi, head).sum())


def min_budget(rule, S, t, rivals, ceil, kappa, gamma, bmax, tol, tl, sigma=None, w=None):
    """B* = smallest per-task budget at which first place is feasible (bisection; inf if infeasible at bmax)."""
    f = lambda B: SV.price(rule, S, t, B, ceil=ceil, kappa=kappa, gamma=gamma, rivals=rivals, objective="breadth", time_limit=tl, sigma=sigma, w=w)
    if not f(bmax)["feasible"]: return np.inf
    lo, hi = 0.0, bmax
    if f(0.0)["feasible"]: return 0.0
    while hi - lo > tol:
        mid = 0.5 * (lo + hi)
        if f(mid)["feasible"]: hi = mid
        else: lo = mid
    return hi


def run_board(board, targets, rules=RULE_LIST, budgets=(2, 5, 10, 20), modes=("own", "common"), K=5, unit="points",
              official="mean", tl=30.0, bstar=True, bmax=100.0, tol=0.01, log=None):
    """board: dict(S points (N x m), ceil, names). Budgets are per-task caps in points (scalar) or ('sigma', b) multiples of sigma_j."""
    S = board["S"]; ceil = np.broadcast_to(np.asarray(board.get("ceil", 100.0), float), (S.shape[1],)).copy(); sig = S.std(axis=0)
    rows = []
    Aoff = board["official"] if "official" in board else R.scores(S, official, kw_cache=True)
    wh = board.get("w_h")
    for t in targets:
        kappa, gamma = unit_costs(unit, S, t, ceil)
        for mode in modes:
            rivals = None if mode == "own" else incumbents(Aoff, t, K)
            for rule in rules:
                rr, wt = ("mean", wh) if rule == "meanh" else (rule, None)
                kw = dict(ceil=ceil, kappa=kappa, gamma=gamma, rivals=rivals, sigma=sig if rule == "zmean" else None, time_limit=tl, w=wt)
                A = R.scores(S, rr, kw_cache=True, **({"sigma": sig} if rule == "zmean" else ({"w": wt} if wt is not None else {})))
                riv = np.delete(np.arange(S.shape[0]), t) if rivals is None else rivals
                lead = int(riv[np.argmax(A[riv])])
                base = dict(target=int(t), rule=rule, mode=mode, unit=unit, rank_official=int((Aoff > Aoff[t]).sum() + 1),
                            rank_rule=int((A > A[t]).sum() + 1), gap0=float(A[riv].max() - A[t]), leader=lead)
                # reference: no budget cap (B = bmax): the targeted optimum
                p_inf = SV.price(rr, S, t, bmax, objective="depth", **kw)
                pu = uniform_depth(S, t, rr, ceil, rivals, sig, SV.EPS_AGG, w=wt)
                base.update(uniform_depth=pu, targeted_depth_inf=p_inf["depth"], mult=(pu / p_inf["depth"]) if p_inf["feasible"] and p_inf["depth"] > 0 else np.nan)
                if bstar:
                    base["Bstar"] = min_budget(rr, S, t, rivals, ceil, kappa, gamma, bmax, tol, tl, sigma=kw["sigma"], w=wt)
                for B in list(budgets) + [bmax]:
                    Bv = B if np.isscalar(B) else B
                    for obj in ("depth", "breadth"):
                        p = SV.price(rr, S, t, Bv, objective=obj, **kw)
                        rows.append(dict(base, B=float(np.max(Bv)), objective=obj, feasible=p["feasible"], depth=p["depth"], cost=p["cost"],
                                         breadth=p["breadth"] if p["feasible"] else np.nan, status=p["status"], mip_gap=p["mip_gap"],
                                         verified=p["verified"], seconds=p["seconds"]))
        if log: log(f"target {t} done ({len(rows)} rows)")
    return pd.DataFrame(rows)
