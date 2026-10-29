"""F5 - Agreement between data groups within each region.

Claim supported: the mean rates of the data groups agree within uncertainty in
most region/group pairs over their common years; pairs with |z| >= 2 are the
exceptions and are highlighted.
Input: outputs/validation/group_agreement.csv (1 sigma; z = diff / err).
"""
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd

from style import GROUP_LABEL, REGIONS, VALID, apply_style, region_label, save

SHORT = {"demdiff_and_glaciological": "DEM+glac.", "altimetry": "Alt.",
         "gravimetry": "Grav."}
OK, BAD = "#4d4d4d", "#B2182B"


def main():
    apply_style()
    a = pd.read_csv(VALID / "group_agreement.csv")
    a["ri"] = a.region.map(REGIONS.index)
    a = a.sort_values(["ri", "group_a", "group_b"]).reset_index(drop=True)
    n = len(a)
    fig, ax = plt.subplots(figsize=(7.6, 0.27 * n + 1.6))
    y = np.arange(n)
    bad = a.z.abs() >= 2
    col = np.where(bad, BAD, OK)
    for yy, r, c in zip(y, a.itertuples(), col):
        ax.plot([r.mean_rate_diff_mwe - 2 * r.mean_rate_diff_err,
                 r.mean_rate_diff_mwe + 2 * r.mean_rate_diff_err], [yy, yy],
                color=c, lw=0.8, alpha=0.6)
        ax.plot([r.mean_rate_diff_mwe - r.mean_rate_diff_err,
                 r.mean_rate_diff_mwe + r.mean_rate_diff_err], [yy, yy], color=c, lw=2.4)
    ax.scatter(a.mean_rate_diff_mwe, y, c=col, s=26, zorder=3,
               edgecolors="white", linewidths=0.8)
    labels = [f"{region_label(r.region)}: {SHORT[r.group_a]} − {SHORT[r.group_b]}"
              f"  ({r.first}–{r.last})" for r in a.itertuples()]
    ax.set_yticks(y, labels, fontsize=7.5)
    for t, b in zip(ax.get_yticklabels(), bad):
        if b:
            t.set_color(BAD)
            t.set_fontweight("bold")
    # Separate regions.
    for i in range(1, n):
        if a.ri[i] != a.ri[i - 1]:
            ax.axhline(i - 0.5, color="#dddddd", lw=0.7)
    for yy, r in zip(y, a.itertuples()):
        ax.text(1.02, yy, f"z = {r.z:+.2f}".replace("-", "−"), transform=ax.get_yaxis_transform(),
                va="center", fontsize=7, color=BAD if abs(r.z) >= 2 else "#555555")
    ax.axvline(0, color="black", lw=0.8)
    ax.set_ylim(n - 0.5, -0.5)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Difference of mean specific rate over common years (m w.e. yr⁻¹)")
    ax.legend(handles=[
        Line2D([], [], color=OK, lw=2.4, label="±1σ"),
        Line2D([], [], color=OK, lw=0.8, alpha=0.6, label="±2σ"),
        Line2D([], [], color=BAD, marker="o", lw=0, label="|z| ≥ 2")],
        loc="lower left", fontsize=7.5, ncol=3, bbox_to_anchor=(0, 1.0))
    ax.set_title(f"{int((~bad).sum())} of {n} pairs agree within 2σ", loc="right", fontsize=8.5)
    return save(fig, "fig05_group_agreement")


if __name__ == "__main__":
    print(main())
