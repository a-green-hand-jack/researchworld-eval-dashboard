"""Price magnitudes without a floor: share of targets already first, and the depth distribution among targets that are not yet first.
usage: magnitude.py TABLES_DIR   reads price.csv; writes price_magnitude.csv.
Per (board, rule, incumbent in {own, common}, per-task cap B in points) over the top-30 targets of the board under the official rule (the same set as headline.json):
  share_already_first : share of targets whose price is zero because they already rank first under the rule against the incumbent (rank_rule == 1 or gap <= 0); no depth is computed for them.
  n_not_first         : targets that are not yet first; every depth statistic below is over these only (no geometric mean, no floor).
  share_infeasible    : share of the not-yet-first targets that cannot reach first within the cap B (price infinite).
  median_depth, q25_depth, q75_depth : median and quartiles of the depth (total boost in points, depth-optimal plan) over the not-yet-first targets, infeasible plans counted as +inf (a NaN here means the statistic is infinite);
                        median_depth_feasible: median over the feasible ones only.
  median_ci_lo/hi     : cluster bootstrap CI of the median (target family and incumbent clusters, union; 2000 draws).
  median_B_star       : median over not-yet-first targets of the smallest per-task cap with which first place is feasible."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import warnings; warnings.filterwarnings("ignore", category=RuntimeWarning)
import numpy as np, pandas as pd
T = sys.argv[1]; NB = int(os.environ.get("NBOOT", 2000))
p = pd.read_csv(f"{T}/price.csv")
p = p[p.init_rank <= 30]


def boot_median(v, labs, seed):
    rng = np.random.default_rng(seed); lo, hi = [], []
    for lab in labs:
        lab = pd.factorize(np.asarray(lab))[0]; k = lab.max() + 1
        if k < 2: continue
        groups = [np.flatnonzero(lab == c) for c in range(k)]
        m = np.array([np.median(v[np.concatenate([groups[c] for c in rng.integers(0, k, k)])]) for _ in range(NB)])
        m = m[np.isfinite(m)] if np.isfinite(m).sum() > 0.5 * NB else m  # an infinite median in more than half of the draws stays infinite
        lo.append(np.percentile(m, 2.5)); hi.append(np.percentile(m, 97.5))
    return (min(lo), max(hi)) if lo else (np.nan, np.nan)


rows = []
for (board, rule, inc, B), g in p.groupby(["board", "rule", "incumbent", "B"]):
    first = (g.rank_rule == 1) | (g.gap <= 0)
    h = g[~first]
    v = np.where(h.feasible_depth, h.depth_star, np.inf)
    fin = v[np.isfinite(v)]
    ci = boot_median(v, [h.family.values, h.incumbent_id.values], 5) if len(h) >= 3 else (np.nan, np.nan)
    f = lambda x: float(x) if np.isfinite(x) else np.nan
    rows.append(dict(board=board, rule=rule, incumbent=inc, B=B, n_targets=len(g), share_already_first=float(first.mean()), n_not_first=len(h),
                     share_infeasible=float((~h.feasible_depth).mean()) if len(h) else np.nan,
                     median_depth=f(np.median(v)) if len(v) else np.nan, q25_depth=f(np.percentile(v, 25)) if len(v) else np.nan, q75_depth=f(np.percentile(v, 75)) if len(v) else np.nan,
                     median_depth_feasible=float(np.median(fin)) if len(fin) else np.nan, median_ci_lo=f(ci[0]), median_ci_hi=f(ci[1]),
                     median_B_star=float(h.B_star.replace(np.inf, np.nan).median()) if len(h) else np.nan, n_families=h.family.nunique(), n_incumbents=h.incumbent_id.nunique()))
r = pd.DataFrame(rows); r.to_csv(f"{T}/price_magnitude.csv", index=False)
print(r[(r.B == 100) & (r.incumbent == "own")].round(2).to_string())
