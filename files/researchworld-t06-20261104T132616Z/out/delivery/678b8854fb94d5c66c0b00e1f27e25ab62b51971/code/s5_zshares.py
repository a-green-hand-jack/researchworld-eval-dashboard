"""Shares of adjacent-pair (C2) claims called resolved at z < 1 and z < 2 under the i.i.d. bootstrap and the cluster / block bootstrap (paper-repo request #7).
Reads results/budgets_remove.csv (z, iid) and results/s5_cluster_se.csv (z_cluster); NBA seasons are pooled over the 69 seasons.
Writes results/s5_z_shares.csv.   Usage: python code/s5_zshares.py"""
import os

import numpy as np
import pandas as pd

OUT = os.path.join(os.path.dirname(__file__), "..", "results")


def main():
    b = pd.read_csv(f"{OUT}/budgets_remove.csv")
    c = pd.read_csv(f"{OUT}/s5_cluster_se.csv")[["unit", "claim", "se_gap_cluster", "z_cluster", "cluster_type", "n_clusters"]]
    d = b.merge(c, on=["unit", "claim"])
    d = d[d.claim.str.startswith("c2_") & (d.gap > 1e-9)].copy()
    d["dataset"] = np.where(d.season.notna(), "nba_seasons", d.unit)
    rows = []
    for ds, s in d.groupby("dataset"):
        r = dict(dataset=ds, n_claims=len(s), cluster_type=s.cluster_type.iloc[0], median_se_ratio=float((s.se_gap_cluster / s.se_gap).median()))
        for lab, z in (("iid", s.z), ("cluster", s.z_cluster)):
            r[f"share_z_lt1_{lab}"] = float((z < 1).mean())
            r[f"share_z_lt2_{lab}"] = float((z < 2).mean())
            r[f"median_z_{lab}"] = float(z.median())
        rows.append(r)
    pd.DataFrame(rows).to_csv(f"{OUT}/s5_z_shares.csv", index=False, float_format="%.4g")
    print(pd.DataFrame(rows).round(3).to_string())


if __name__ == "__main__":
    main()
