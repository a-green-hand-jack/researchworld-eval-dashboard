"""results/headline.json: the headline numbers of the study with uncertainty, read by the paper text.
usage: headline.py TABLES_DIR OUT.json   reads the tables of make_results.py / run_analysis.py / verdicts.py / e5-e7 / spillover in TABLES_DIR (a missing table is skipped).
Price magnitudes are medians over the top-30 targets that are not already first (magnitude.py); other price summaries are over the top-30 targets of each board under the official rule (own incumbent, B = ceilings 100 points, unit = points); the CI of a mean is the union of the family and
incumbent cluster bootstraps (stats.cluster_mean_ci, 2000 draws).  Compute figures are taken from $CPU_NOTE (free text) when set."""
import sys, os, json, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from stats import cluster_mean_ci
T, OUT = sys.argv[1], sys.argv[2]
NB = int(os.environ.get("NBOOT", 2000))


def rd(name):
    f = f"{T}/{name}.csv"
    return pd.read_csv(f) if os.path.exists(f) else None


def clean(x):
    if isinstance(x, dict): return {str(k): clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)): return [clean(v) for v in x]
    if isinstance(x, (np.floating, float)): return None if not np.isfinite(x) else float(x)
    if isinstance(x, (np.integer,)): return int(x)
    if isinstance(x, (np.bool_,)): return bool(x)
    return x


H = dict(created=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), note="every number is produced by scripts in code/ (see code/README.md); CIs are cluster bootstraps by target family and incumbent")
b = rd("boards")
if b is not None: H["boards"] = b[["board", "snapshot", "m", "N", "n_targets"]].to_dict("records")

p = rd("price")
if p is not None:
    top = p[(p.init_rank <= 30) & (p.incumbent == "own") & (p.B == 100.0)]
    pm = rd("price_magnitude")
    rows = []
    for (board, rule), g in top.groupby(["board", "rule"]):
        first = (g.rank_rule == 1) | (g.gap <= 0); h = g[~first]   # targets already first under the rule have price zero and enter no statistic below
        kf = (h.k_star / h.m).where(h.feasible)
        r = dict(board=board, rule=rule, n_targets=len(g), n_not_first=len(h), share_feasible=float(h.feasible_depth.mean()) if len(h) else None, max_opt_gap=float(g.opt_gap.max()) if g.opt_gap.notna().any() else None,
                 median_breadth_frac=float(kf.median()), median_B_star=float(h.B_star.replace(np.inf, np.nan).median()), median_targeting_mult=float(h.targeting_mult.replace(np.inf, np.nan).median()))
        if pm is not None:
            x = pm[(pm.board == board) & (pm.rule == rule) & (pm.incumbent == "own") & (pm.B == 100.0)].iloc[0]
            r.update(share_already_first=float(x.share_already_first), median_depth_points=x.median_depth, depth_q25_points=x.q25_depth, depth_q75_points=x.q75_depth, median_depth_ci_lo=x.median_ci_lo, median_depth_ci_hi=x.median_ci_hi,
                     share_infeasible=x.share_infeasible)
        rows.append(r)
    H["price_magnitude_statistic"] = ("price magnitudes are the MEDIAN (with quartiles and a cluster-bootstrap CI of the median) of the depth in points over the top-30 targets that are NOT already first under the rule, own incumbent, "
                                      "per-task cap B = 100 points; the share of targets already first is reported separately; no geometric mean and no floor is used (price_magnitude.csv has all caps and both incumbents)")
    if pm is not None: H["price_magnitude_all_caps"] = pm.to_dict("records")
    H["price_top30_own_ceilings"] = rows
    milp = p[p.solver == "milp"]
    H["solver_gaps"] = [dict(board=bd, rule=r, n=len(g), max_opt_gap=float(g.opt_gap.max()), n_gap_gt_1e4=int((g.opt_gap > 1e-4).sum()), all_verified=bool(g.verified.all()))
                        for (bd, r), g in milp.groupby(["board", "rule"])]
s = rd("solver_check")
if s is not None: H["solver_check"] = s.to_dict("records")
v = rd("verdicts")
if v is not None: H["verdicts"] = v.to_dict("records")
for key, name in (("m_effect_fit", "m_effect_fit"), ("e6_confidence", "e6_confidence"), ("e6b_confidence", "e6b_confidence"), ("r3_norm", "predictors_norm"), ("e6_topnoise", "e6_topnoise"), ("e5_summary", "e5_summary"), ("e7_margin_slice", "e7_margin_slice"),
                  ("rule_order", "rule_order"), ("r3_within_board", "predictors_within"), ("flip_summary", "flip_summary"), ("flip_proxy", "flip_proxy"), ("units_tau", "units_tau"), ("predictors", "predictors"), ("calibration_summary", "calibration_summary"), ("spillover_matrix", "spillover_matrix")):
    d = rd(name)
    if d is not None: H[key] = d.to_dict("records")
sp = rd("spillover_price")
if sp is not None:
    w = sp.pivot_table(index=["board", "target", "B"], columns="variant", values="depth", aggfunc="first").reset_index()
    w = w[w.no_spillover > 0]
    H["spillover_depth_ratio"] = [dict(B=float(B), median_ratio=float((g.spillover / g.no_spillover).median()), n=len(g)) for B, g in w.groupby("B")]
hl = rd("predictors_hl")
if hl is not None:
    g = hl[hl.model == "gap+profile"]
    H["hl_exploratory"] = [dict(r2_variant=v, rule=r, n_cases=len(x), n_retained=int(x.retained.sum()), median_gain=float(x.gain.median())) for (v, r), x in g.groupby(["r2_variant", "rule"])]
fn = rd("flip_N")
if fn is not None: H["flip_N"] = fn.groupby(["board", "N"], as_index=False)[["median_marg_plur", "share_feasible_plur"]].mean().to_dict("records")
bx = rd("bx_crossing")
if bx is not None: H["bx_crossing"] = bx.to_dict("records")
if os.environ.get("CPU_NOTE"): H["compute"] = os.environ["CPU_NOTE"]
json.dump(clean(H), open(OUT, "w"), indent=1)
print("wrote", OUT, "keys:", ", ".join(H))
