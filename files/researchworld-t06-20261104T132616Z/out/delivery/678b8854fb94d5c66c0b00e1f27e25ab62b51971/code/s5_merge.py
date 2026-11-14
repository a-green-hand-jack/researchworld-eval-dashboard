"""Merge the per-unit parts of s5_published.py and s5_restarts.py and summarise them per dataset (paper-repo requests #9a and #10a).
Writes results/s5_published.csv, s5_published_summary.csv, s5_restarts.csv, s5_restarts_summary.csv, s5_budget_intervals.csv (C1 and median-C2 budget with a dataset-bootstrap interval, request #10b).   Usage: python code/s5_merge.py"""
import glob
import os

import numpy as np
import pandas as pd

from btlib import prov

OUT = os.path.join(os.path.dirname(__file__), "..", "results")


def main():
    pub = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(f"{OUT}/parts/s5_published_*.csv"))], ignore_index=True)
    pub["dataset"] = np.where(pub.unit.str.match(r"nba\d{4}$"), "nba_seasons_sample", pub.unit)
    pub.to_csv(f"{OUT}/s5_published.csv", index=False, float_format="%.6g")
    rows = []
    for ds, g in pub.groupby("dataset"):
        c2 = g[g.claim.str.startswith("c2ci_")]
        c1 = g[g.claim == "c1p"]
        held = c2[c2.base_holds.astype(bool)]
        rows.append(dict(dataset=ds, units=g.unit.nunique(), adjacent_pairs=len(c2), ci_separated_at_base=int(c2.base_holds.sum()),
                         share_ci_separated=float(c2.base_holds.mean()), median_budget_ci_separated=held.budget.median() if len(held) else np.nan,
                         median_budget_point_same_pairs=held.budget_point.median() if len(held) else np.nan,
                         median_ratio_ci_to_point=float((held.budget / held.budget_point).median()) if len(held) else np.nan,
                         c1prime_holds_at_base=int(c1.base_holds.sum()), c1prime_units=len(c1),
                         median_p_rank1=c1.p_rank1.median(), median_c1prime_budget_holding=c1[c1.base_holds.astype(bool)].budget.median()
                         if c1.base_holds.astype(bool).any() else np.nan))
    pd.DataFrame(rows).to_csv(f"{OUT}/s5_published_summary.csv", index=False, float_format="%.4g")
    rs = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(f"{OUT}/parts/s5_restarts_*.csv"))], ignore_index=True)
    rs.to_csv(f"{OUT}/s5_restarts.csv", index=False, float_format="%.6g")
    srows = []
    for ds, g in rs.groupby("unit"):
        srows.append(dict(unit=ds, claims=len(g), restarts_per_claim=int(g.R.max()), claims_where_a_restart_beat_det=int((g.restart_min < g.budget_det).sum()),
                          claims_where_all_restarts_equal_det=int(((g.restart_min == g.budget_det) & (g.restart_max == g.budget_det)).sum()),
                          max_restart_over_det=float((g.restart_max / g.budget_det).max()), median_det_over_lin_est=float((g.budget_det / g.lin_est.clip(lower=1e-9)).median()),
                          c1_det=g[g.claim == "c1"].budget_det.iloc[0], c1_restart_min=g[g.claim == "c1"].restart_min.iloc[0],
                          c1_lin_est=g[g.claim == "c1"].lin_est.iloc[0]))
    pd.DataFrame(srows).to_csv(f"{OUT}/s5_restarts_summary.csv", index=False, float_format="%.4g")
    # dataset-level intervals of the C1 and median-C2 budgets over the dataset-bootstrap resamples of s3_uncert.csv (request #10b)
    un = pd.read_csv(f"{OUT}/s3_uncert.csv")
    un = un[un.flipped]
    base = pd.read_csv(f"{OUT}/budgets_remove.csv")
    irows = []
    for ds, g in un.groupby("unit_base"):
        c1 = g[g.claim == "c1"].set_index("resample").budget
        c2 = g[g.claim.str.startswith("c2_") & (g.gap > 1e-9)].groupby("resample").budget.median()
        b = base[base.unit == ds]
        b2 = b[b.claim.str.startswith("c2_")]
        for name, v, b0 in (("c1", c1, b[b.claim == "c1"].budget.iloc[0]), ("median_c2", c2, b2.budget.median())):
            irows.append(dict(dataset=ds, statistic=name, base_budget=b0, resamples=len(v), resample_median=v.median(), lo95=np.percentile(v, 2.5),
                              hi95=np.percentile(v, 97.5), min=v.min(), max=v.max(), N=float(b.N.iloc[0]), base_frac_N=b0 / float(b.N.iloc[0])))
    pd.DataFrame(irows).to_csv(f"{OUT}/s5_budget_intervals.csv", index=False, float_format="%.5g")
    print(pd.DataFrame(irows).round(4).to_string())
    prov.write_meta(f"{OUT}/s5_merge.meta.json", script="code/s5_merge.py")
    print(pd.DataFrame(rows).round(3).to_string()); print(pd.DataFrame(srows).round(3).to_string())


if __name__ == "__main__":
    main()
