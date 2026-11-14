"""Is 'the minimum rule is cheaper than the mean' an artefact of the linear cost (every point costs the same)?  Re-solve the minimum-investment problem exactly under convex per-task costs
(ceiling cap, same targets and margin eps=1e-3 as the main grids; rules mean, geomean, harmonic -- power means of score+1, see scorerules -- and min).
Cost of raising task j from x_j to y_j (score points on the 0-100 scale):
  linear    c = y - x                      (validation: reproduces the L1 of results/helm_main.csv / ollb_score.csv)
  quadratic c = (y - x)^2                  (cost rises with the size of the jump)
  loghead   c = ln((100 - x)/(100 - y))    (cost per point rises as the headroom closes; infinite at 100)
Exact solutions. min: every task below tau+eps is raised to it (cost sum c(max(x,T)); infeasible if T > 100 or the cost is infinite). Mean-like rules (g concave increasing: g=y, ln(y+1),
-1/(y+1)): minimise sum c_j(y_j) s.t. sum g(y_j) >= n*g(T); the KKT condition c'(y)=lam*g'(y) gives y(lam) per task (vectorised bisection, clipped to [x,100]); lam by outer bisection.
Output per target: results/convex_cost.csv; summary results/summary/convex_cost.csv (ratio of min to each score rule, median, share min cheaper, CV terciles, Spearman with CV).
Usage: python3 src/convex_cost.py"""
import sys, pathlib, numpy as np, pandas as pd
from scipy.stats import rankdata, spearmanr
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mti import data as dt, scorerules as sr
R = pathlib.Path(__file__).resolve().parents[1] / "results"; EPS = 1e-3; TOP = 100
CAPV = 100.0
G = {"mean": (lambda y: y, lambda y: np.ones_like(y)), "geomean": (lambda y: np.log(y + 1), lambda y: 1 / (y + 1)), "harmonic": (lambda y: -1 / (y + 1), lambda y: 1 / (y + 1) ** 2)}
GT = {"mean": lambda T: T, "geomean": lambda T: np.log(T + 1), "harmonic": lambda T: -1 / (T + 1)}
CP = {"quadratic": lambda x, y: (y - x) ** 2, "loghead": lambda x, y: np.log((100 - x) / np.maximum(100 - y, 1e-300)), "linear": lambda x, y: y - x}
DCP = {"quadratic": lambda x, y: 2 * (y - x), "loghead": lambda x, y: 1 / np.maximum(100 - y, 1e-300), "linear": lambda x, y: np.ones_like(y)}

def y_of_lam(x, lam, cost, rule):
    """per-task minimiser of c(y) - lam*g(y) over [x, 100]: root of c'(y) - lam*g'(y) (increasing in y), clipped; vectorised bisection"""
    g, dg = G[rule]; lo = x.copy(); hi = np.full_like(x, CAPV)
    f = lambda y: DCP[cost](x, y) - lam * dg(y)
    for _ in range(70):
        mid = (lo + hi) / 2; up = f(mid) < 0; lo = np.where(up, mid, lo); hi = np.where(up, hi, mid)
    y = (lo + hi) / 2; y = np.where(f(x) >= 0, x, y)          # marginal cost at x already above lam*g': stay
    return np.clip(y, x, CAPV)

def mean_like_cost(x, T, cost, rule):
    """min total cost s.t. sum g(y) >= n g(T); np.inf if T cannot be reached below the cap, 0 if already satisfied"""
    g, dg = G[rule]; need = len(x) * GT[rule](T)
    if g(x).sum() >= need: return 0.0
    if g(np.full_like(x, CAPV)).sum() < need: return np.inf
    lo, hi = 0.0, 1.0
    while g(y_of_lam(x, hi, cost, rule)).sum() < need:
        hi *= 4
        if hi > 1e300: return np.inf
    for _ in range(100):
        lam = (lo + hi) / 2
        if g(y_of_lam(x, lam, cost, rule)).sum() >= need: hi = lam
        else: lo = lam
    y = y_of_lam(x, hi, cost, rule); c = CP[cost](x, y).sum(); return float(c) if np.isfinite(c) else np.inf

def min_cost(x, T, cost):
    if T > CAPV: return np.inf
    y = np.maximum(x, T); c = CP[cost](x, y).sum(); return float(c) if np.isfinite(c) else np.inf

def cost_linear_check(x, T, rule):      # the L1 of scorerules (cap 100)
    return sr.RULES[rule][1](x, T - EPS, np.full(len(x), CAPV), EPS)

if __name__ == "__main__":
    rows = []
    for ds in ("helm", "ollb"):
        X, names, tasks, meta = dt.load(ds); M, n = X.shape; rk = rankdata(-X.mean(axis=1), method="min")
        tg = np.where((rk >= 2) & (rk <= (TOP if ds == "ollb" else M)))[0]
        vals = {r: sr.RULES[r][0](X) for r in ("mean", "geomean", "harmonic", "min")}
        for i in tg:
            x = X[i]
            for rule in ("mean", "geomean", "harmonic", "min"):
                v = vals[rule]; T = np.delete(v, i).max() + EPS
                for cost in ("linear", "quadratic", "loghead"):
                    if cost == "linear": c = min_cost(x, T, "linear") if rule == "min" else cost_linear_check(x, T, rule)      # closed forms of scorerules
                    else: c = min_cost(x, T, cost) if rule == "min" else mean_like_cost(x, T, cost, rule)
                    rows.append(dict(dataset=ds, target=names[i], rank_mean=int(rk[i]), rule=rule, cost=cost, value=c, cv=float(x.std() / x.mean())))
        print(ds, len(tg), "targets done", flush=True)
    d = pd.DataFrame(rows); d.to_csv(R / "convex_cost.csv", index=False)
    # validation: the linear column against the main grids
    chk = []
    for ds, f in (("helm", "helm_main.csv"), ("ollb", "ollb_score.csv")):
        m = pd.read_csv(R / f); m = m[(m.cap == "ceil")].set_index(["target", "rule"]).L1
        s = d[(d.dataset == ds) & (d.cost == "linear")].copy(); s["ref"] = [m.get((t, r), np.nan) for t, r in zip(s.target, s.rule)]
        s = s[np.isfinite(s.value) & np.isfinite(s.ref)]; chk.append(dict(dataset=ds, n=len(s), max_abs_diff=float((s.value - s.ref).abs().max())))
    print("linear vs main grids:", chk)

    # summary: min vs each score rule, per cost
    from scipy.stats import spearmanr
    out = []
    for ds in ("helm", "ollb"):
        for other in ("mean", "geomean", "harmonic"):
            w = d[d.dataset == ds].pivot_table(index=["target", "rank_mean", "cv"], columns=["cost", "rule"], values="value").reset_index()
            for cost in ("linear", "quadratic", "loghead"):
                s = pd.DataFrame(dict(target=w.target, rank_mean=w.rank_mean, cv=w.cv, a=w[(cost, "min")].values, b=w[(cost, other)].values))
                s = s[np.isfinite(s.a) & np.isfinite(s.b) & (s.b > 0)].copy(); s["ratio"] = s.a / s.b
                terc = pd.qcut(s.cv.rank(method="first"), 3, labels=["low", "mid", "high"]); rho, p = spearmanr(s.cv, s.ratio)
                for tl, g in [("all", s)] + [(t, s[terc == t]) for t in ("low", "mid", "high")]:
                    out.append(dict(dataset=ds, comparison=f"min / {other}", cost=cost, cv_tercile=tl, n=len(g), n_min_inf_or_other_inf=int(((~np.isfinite(w[(cost, "min")])) | (~np.isfinite(w[(cost, other)]))).sum()) if tl == "all" else np.nan,
                                    ratio_median=float(g.ratio.median()), ratio_q25=float(g.ratio.quantile(.25)), ratio_q75=float(g.ratio.quantile(.75)), share_min_cheaper=float((g.ratio < 1).mean()),
                                    spearman_ratio_cv=rho if tl == "all" else np.nan, spearman_p=p if tl == "all" else np.nan))
    o = pd.DataFrame(out); o.to_csv(R / "summary" / "convex_cost.csv", index=False); print(o[o.cv_tercile == "all"].round(3).to_string()); print(o[o.comparison == "min / mean"].round(3).to_string())
