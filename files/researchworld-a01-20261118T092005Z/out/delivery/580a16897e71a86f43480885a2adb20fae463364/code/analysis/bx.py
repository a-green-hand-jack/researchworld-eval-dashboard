"""Crossing budget B_x (Brief rev 4, request 2): the budget at which the median-type vs mean-type ordering of the price swaps, per board.
usage: bx.py TABLES_DIR RAWDIR   reads RAWDIR/r1_*.csv + r1x_*.csv (sigma-unit runs at b = c * median B* of the mean family, c in 0.5..8) and TABLES_DIR/price.csv (points unit, B = 2..100 points per task);
writes TABLES_DIR/bx_curve.csv (the statistic at each budget) and bx_crossing.csv (the crossing, with CI).
Statistic s(b) = mean over targets of  k_frac(rule) - k_frac(reference)  for rule in the median-type rules (median, plurality, copeland) and the reference mean-type rule of R1 ('mean', 'meanh' on OLLB sub-tasks),
k_frac = k/m, an infeasible plan counted as 1 (lower bound; as in R1), targets with a non-positive gap for the pair dropped.  'breadth_feasible' variant: only targets feasible for both rules at that budget (no infeasible-as-1 convention). 'depth' variant: the same with the minimum total cost (sigma units): mean of log(cost_rule/cost_ref)
over targets feasible for both.  s > 0: the median-type rule needs more breadth (the Brief's R1 direction); s < 0: less.
B_x is the first budget on the grid where s changes sign, located by linear interpolation of s in ln b between the two grid points; 'direction' says from-to; a target-family cluster bootstrap (2000 draws) gives
the share of draws with a crossing in the grid and the percentile interval of B_x among those draws.  If s keeps one sign on the whole grid there is no B_x in the range (reported with the sign)."""
import sys, os, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import warnings; warnings.filterwarnings("ignore", category=RuntimeWarning)
import numpy as np, pandas as pd
from families import fam_map
T, RAW = sys.argv[1], sys.argv[2]; NB = int(os.environ.get("NBOOT", 2000))
MEDT = ["median", "plurality", "copeland"]; BOARD = {"helm": "helm_mmlu", "m6raw": "ollb_bench_raw", "m39": "ollb_sub"}


def crossing(bs, s):
    """first sign change of s over the increasing grid bs: (B_x, direction) or (nan, '')"""
    sg = np.sign(np.where(np.abs(s) < 1e-9, 0.0, s)); last = 0.0; lb = None
    for i in range(len(s)):
        if sg[i] == 0: continue
        if last != 0 and sg[i] != last:
            a = s[lb] if lb is not None else s[i - 1]; x0 = np.log(bs[lb]) if lb is not None else np.log(bs[i - 1])
            return float(np.exp(x0 + (0 - a) * (np.log(bs[i]) - x0) / (s[i] - a))), ("median-type needs more -> less" if last > 0 else "median-type needs less -> more")
        last = sg[i]; lb = i
    return np.nan, ""


def boot(cell, bgrid, stat, fam, seed):
    """cell: array targets x grid of per-target differences (nan = dropped); fam: family label per target"""
    lab = pd.factorize(fam)[0]; k = lab.max() + 1; groups = [np.flatnonzero(lab == c) for c in range(k)]; rng = np.random.default_rng(seed); xs = []
    for _ in range(NB):
        ix = np.concatenate([groups[c] for c in rng.integers(0, k, k)]); xs.append(crossing(bgrid, np.nanmean(cell[ix], axis=0))[0])
    xs = np.array(xs); ok = np.isfinite(xs)
    return float(ok.mean()), (np.percentile(xs[ok], 2.5) if ok.sum() > 20 else np.nan), (np.percentile(xs[ok], 97.5) if ok.sum() > 20 else np.nan), k


curve, cross = [], []
# ---- sigma units
files = sorted(glob.glob(f"{RAW}/r1_*.csv") + glob.glob(f"{RAW}/r1x_*.csv"))
r = pd.concat([pd.read_csv(f) for f in files]).drop_duplicates(["board", "target", "rule", "c", "objective"])
for name, g0 in r.groupby("board"):
    b, fam = fam_map(name); ref = "meanh" if name == "m39" else "mean"
    for obj in ("breadth", "breadth_feasible", "depth"):
        g = g0[g0.objective == obj.split("_")[0]].copy(); cs = np.array(sorted(g.c.unique()))
        g["v"] = np.where(g.feasible, g.k / g.m, 1.0 if obj == "breadth" else np.nan) if obj.startswith("breadth") else np.where(g.feasible, g.cost, np.nan)
        V = g.pivot_table(index=["target", "model"], columns=["rule", "c"], values="v"); G = g.pivot_table(index=["target", "model"], columns="rule", values="gap0")
        medB = float(g.med_Bstar_meanfam.iloc[0]); fams = np.array([fam[i[1]] for i in V.index])
        for rule in MEDT:
            use = (G[[ref, rule]] > 0).all(axis=1).values
            A = V[rule].reindex(columns=cs).values; R_ = V[ref].reindex(columns=cs).values
            with np.errstate(all="ignore"): d = (A - R_) if obj.startswith("breadth") else np.log(np.where((A > 0) & (R_ > 0), A, np.nan) / np.where(R_ > 0, R_, np.nan))
            d[~use] = np.nan; d[~np.isfinite(d)] = np.nan
            s = np.nanmean(d, axis=0)
            for c, sv, n in zip(cs, s, np.isfinite(d).sum(0)):
                curve.append(dict(unit="sigma", board=BOARD[name], objective=obj, rule=rule, reference=ref, b=c * medB, c=c, stat=sv, n_targets=int(n)))
            c_ = cs * medB; bx, dr = crossing(c_, s); share, lo, hi, k = boot(d, c_, None, fams, 7)
            cross.append(dict(unit="sigma", board=BOARD[name], objective=obj, rule=rule, reference=ref, B_x=bx, direction=dr, B_x_ci_lo=lo, B_x_ci_hi=hi, share_boot_with_crossing=share,
                              sign_lowest_b=float(np.sign(s[0])), sign_highest_b=float(np.sign(s[-1])), grid_lo=c_[0], grid_hi=c_[-1], n_grid=len(cs), n_clusters=k, med_Bstar_meanfam=medB))
# ---- points unit (E1 price table, own incumbent): breadth k*/m
p = pd.read_csv(f"{T}/price.csv"); p = p[p.incumbent == "own"]
for (board, obj), g in [((b_, o_), gg) for b_, gg in p.groupby("board") for o_ in ("breadth", "breadth_feasible")]:
    if board == "ollb_bench_raw": continue
    ref = "meanh" if board == "ollb_sub" and "meanh" in set(g.rule) else "mean"; bs = np.array(sorted(g.B.unique()))
    g = g.copy(); g["v"] = np.where(g.feasible, g.k_star / g.m, 1.0 if obj == "breadth" else np.nan)
    V = g.pivot_table(index=["target"], columns=["rule", "B"], values="v"); G = g.pivot_table(index="target", columns="rule", values="gap", aggfunc="first")
    fm = g.drop_duplicates("target").set_index("target").family
    for rule in MEDT:
        use = (G[[ref, rule]] > 0).all(axis=1).values
        d = V[rule].reindex(columns=bs).values - V[ref].reindex(columns=bs).values; d[~use] = np.nan
        s = np.nanmean(d, axis=0)
        for B, sv, n in zip(bs, s, np.isfinite(d).sum(0)): curve.append(dict(unit="points", board=board, objective=obj, rule=rule, reference=ref, b=B, c=np.nan, stat=sv, n_targets=int(n)))
        bx, dr = crossing(bs, s); share, lo, hi, k = boot(d, bs, None, fm.loc[V.index].values, 7)
        cross.append(dict(unit="points", board=board, objective=obj, rule=rule, reference=ref, B_x=bx, direction=dr, B_x_ci_lo=lo, B_x_ci_hi=hi, share_boot_with_crossing=share,
                          sign_lowest_b=float(np.sign(s[0])), sign_highest_b=float(np.sign(s[-1])), grid_lo=bs[0], grid_hi=bs[-1], n_grid=len(bs), n_clusters=k, med_Bstar_meanfam=np.nan))
pd.DataFrame(curve).to_csv(f"{T}/bx_curve.csv", index=False); c = pd.DataFrame(cross); c.to_csv(f"{T}/bx_crossing.csv", index=False)
print(c.round(3).to_string())
