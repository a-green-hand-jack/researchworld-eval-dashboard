"""F4 - Regional contributions to global glacier mass loss, 2000-2023.

Claims supported: which regions dominate the global loss in Gt (and their
share), which lose most per unit area (m w.e./yr), and in which regions the
specific loss rate increased from 2000-2011 to 2012-2023.
Input: outputs/reconciliation/summary_regional.csv (calendar years, 1 sigma).
"""
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd

from style import RECON, apply_style, num, region_label, save

EARLY, LATE = "#56B4E9", "#B2182B"


def main():
    apply_style()
    s = pd.read_csv(RECON / "summary_regional.csv")
    s = s.sort_values("cumulative_gt", ascending=True).reset_index(drop=True)
    y = np.arange(len(s))
    labels = [region_label(r) for r in s.region]

    fig, (a, b) = plt.subplots(1, 2, figsize=(10.5, 7.2), sharey=True,
                               gridspec_kw={"width_ratios": [1.15, 1], "wspace": 0.06})
    a.barh(y, s.cumulative_gt, height=0.65, color="#4d4d4d", zorder=2)
    a.errorbar(s.cumulative_gt, y, xerr=s.cumulative_gt_err, fmt="none",
               ecolor="black", elinewidth=0.8, capsize=2, zorder=3)
    for yy, v, e, sh in zip(y, s.cumulative_gt, s.cumulative_gt_err,
                            s.share_of_global_loss_pct):
        a.text(v - e - 25, yy, f"{sh:.1f}%", va="center", ha="right", fontsize=7.5,
               color="#333333")
    a.set_yticks(y, labels)
    a.invert_yaxis()
    a.set_xlim(-1900, 0)
    a.set_xlabel("Cumulative mass change 2000–2023 (Gt)")
    a.set_title("(a) Cumulative mass change ±1σ and share of global loss", loc="left")
    a.grid(axis="y", visible=False)

    # (b) Specific rates: 2000-2011 and 2012-2023 (dumbbell) and 2000-2023 mean.
    for yy, r in zip(y, s.itertuples()):
        b.plot([r.rate_mwe_2000_2011, r.rate_mwe_2012_2023], [yy, yy], color="#bbbbbb",
               lw=1.6, zorder=1)
    b.errorbar(s.rate_mwe_2000_2011, y - 0.15, xerr=s.rate_mwe_err_2000_2011, fmt="o",
               color=EARLY, ms=5, elinewidth=0.8, capsize=0, zorder=3)
    b.errorbar(s.rate_mwe_2012_2023, y + 0.15, xerr=s.rate_mwe_err_2012_2023, fmt="s",
               color=LATE, ms=5, elinewidth=0.8, capsize=0, zorder=3)
    b.plot(s.rate_mwe_2000_2023, y, ls="none", marker="|", ms=11, mew=1.8,
           color="black", zorder=4)
    b.axvline(0, color="#444444", lw=0.7)
    b.set_xlabel("Specific mass change rate (m w.e. yr⁻¹)")
    b.set_title("(b) Mean specific rate by period ±1σ", loc="left")
    b.grid(axis="y", visible=False)
    b.legend(handles=[
        Line2D([], [], ls="none", marker="o", color=EARLY, label="2000–2011"),
        Line2D([], [], ls="none", marker="s", color=LATE, label="2012–2023"),
        Line2D([], [], ls="none", marker="|", ms=10, mew=1.8, color="black",
               label="2000–2023")], loc="lower left", fontsize=8)
    return save(fig, "fig04_regional_contributions")


if __name__ == "__main__":
    print(main())
