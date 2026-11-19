"""E2: the m-effect. Random task subsets of one board (same models, different granularity), prices in sigma units, paired across rules."""
import numpy as np, pandas as pd
from . import rules as R, solvers as SV

RULES2 = ["mean", "zmean", "median", "min", "borda", "plurality", "copeland"]  # "meanh": mean with hierarchical weights wh (OLLB sub-tasks)
BIG = 1e4  # per-task budget that is never binding: only ceilings bind


def _kw(rule, sig, wh):
    """price() keyword arguments and the rule name it understands ('meanh' is the mean with weights wh)."""
    return ("mean", wh) if rule == "meanh" else (rule, None)


def sigma_bstar(rule, S, t, sig, ceil, tl, bmax=20.0, tol=0.002, rivals=None, w=None):
    """Smallest b (per-task cap b*sigma_j) at which first place is feasible; inf if infeasible even with b=bmax (clipped at ceilings)."""
    kw = dict(ceil=ceil, kappa=1.0 / sig, gamma=1, rivals=rivals, objective="breadth", time_limit=tl, sigma=sig, w=w)
    f = lambda b: SV.price(rule, S, t, b * sig, **kw)["feasible"]
    if not f(bmax): return np.inf
    if f(0.0): return 0.0
    lo, hi = 0.0, bmax
    while hi - lo > tol:
        mid = 0.5 * (lo + hi)
        if f(mid): hi = mid
        else: lo = mid
    return hi


def run_draw(S, targets, sig, ceil, rules=RULES2, bgrid=(1.0, 2.0, 4.0), tl=30.0, meta=None, wh=None):
    """S is the (N x m) subset board. For each target and rule: B* (sigma), breadth/depth at b in bgrid, breadth with ceilings only.
    Rule 'meanh' needs wh (weights of the hierarchical mean)."""
    rows = []
    for t in targets:
        for rule in rules:
            rr, w = _kw(rule, sig, wh)
            A = R.scores(S, rr, kw_cache=False, **({"sigma": sig} if rr == "zmean" else ({"w": w} if w is not None else {})))
            gap0 = float(np.delete(A, t).max() - A[t])
            base = dict(meta or {}, target=int(t), rule=rule, gap0=gap0, m=S.shape[1])
            kw = dict(ceil=ceil, kappa=1.0 / sig, gamma=1, time_limit=tl, sigma=sig, w=w)
            base["Bstar"] = sigma_bstar(rr, S, t, sig, ceil, tl, w=w)
            pk = SV.price(rr, S, t, BIG, objective="breadth", **kw)
            base.update(k_inf=pk["breadth"] if pk["feasible"] else np.nan, feas_inf=pk["feasible"])
            pd_ = SV.price(rr, S, t, BIG, objective="depth", **kw)
            base.update(depth_inf=pd_["cost"] if pd_["feasible"] else np.nan)
            for b in bgrid:
                out = dict(base, b=b)
                for obj in ("breadth", "depth"):
                    p = SV.price(rr, S, t, b * sig, objective=obj, **kw)
                    out[f"feas_{obj}"] = p["feasible"]
                    out[f"k_{obj}"] = p["breadth"] if p["feasible"] else np.nan
                    out[f"cost_{obj}"] = p["cost"] if p["feasible"] else np.nan
                    out[f"gap_{obj}"] = p["mip_gap"]
                rows.append(out)
    return rows
