"""F1 - Data overview: temporal coverage and count of the input estimates.

Claim supported: the 2000-2023 study window is covered by several independent
methods in every region, while sub-annual/annual resolution comes mainly from
glaciological and gravimetric estimates and multi-annual DEM differencing
constrains long-term change.
Inputs: data/glambie/input/*/*.csv and outputs/reconciliation/inputs_inventory.csv
(which submissions enter the consensus).  Writes outputs/tables/input_inventory.csv
and outputs/tables/input_counts_region_method.csv.
"""
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

from inventory import load_inventory
import pandas as pd

from style import (RECON, METHODS, METHOD_COLOR, METHOD_LABEL, REGIONS, TABLES,
                   apply_style, region_label, save)


def main():
    apply_style()
    inv = load_inventory()
    used = pd.read_csv(RECON / "inputs_inventory.csv")
    used["file"] = used.file.str.split("/").str[-1]
    inv = inv.merge(used[["file", "used_in_consensus", "role"]], on="file", how="left")
    inv["used_in_consensus"] = inv.used_in_consensus.fillna(False).astype(bool)
    TABLES.mkdir(parents=True, exist_ok=True)
    inv.to_csv(TABLES / "input_inventory.csv", index=False)
    counts = (inv.pivot_table(index="region", columns="method", values="file",
                              aggfunc="count", fill_value=0)
              .reindex(index=REGIONS, columns=METHODS, fill_value=0))
    counts["total"] = counts.sum(axis=1)
    nused = (inv[inv.used_in_consensus]
             .pivot_table(index="region", columns="method", values="file",
                          aggfunc="count", fill_value=0)
             .reindex(index=REGIONS, columns=METHODS, fill_value=0))
    nused["total"] = nused.sum(axis=1)
    out = counts.join(nused, rsuffix="_used_in_consensus")
    out.loc["total"] = out.sum()
    out.to_csv(TABLES / "input_counts_region_method.csv")

    fig, (ax, axh) = plt.subplots(
        1, 2, figsize=(11, 10.5), sharey=True,
        gridspec_kw={"width_ratios": [3.1, 1.25], "wspace": 0.04})

    # Left: one horizontal line per estimate, grouped by region, ordered by method.
    y = 0.0
    yticks, ylabels, bands = [], [], []
    for region in REGIONS:
        sub = inv[inv.region == region].copy()
        sub["m"] = sub.method.map(METHODS.index)
        sub = sub.sort_values(["m", "start"])
        n = len(sub)
        step = 0.8 / max(n - 1, 1)
        ys = y - 0.4 + step * np.arange(n) if n > 1 else np.array([y])
        for yy, (_, r) in zip(ys, sub.iterrows()):
            annual = r.median_period_yr <= 1.01
            ax.plot([r.start, r.end], [yy, yy], color=METHOD_COLOR[r.method],
                    lw=1.6 if annual else 0.9, ls="-" if annual else (0, (2, 1.2)),
                    solid_capstyle="butt", alpha=1.0 if r.used_in_consensus else 0.3)
        bands.append(y)
        yticks.append(y)
        ylabels.append(region_label(region))
        y -= 1.0
    for i, b in enumerate(bands):
        if i % 2 == 0:
            ax.axhspan(b - 0.5, b + 0.5, color="#f4f4f4", zorder=-2, lw=0)
    ax.axvspan(2000, 2024, color="#fff3d6", zorder=-1, lw=0)
    ax.text(2012, bands[0] + 0.62, "study period 2000–2023", ha="center",
            va="bottom", fontsize=8, color="#7a5a00")
    ax.set_yticks(yticks, ylabels)
    ax.set_ylim(bands[-1] - 0.55, bands[0] + 1.0)
    ax.set_xlim(1970, 2025.5)
    ax.set_xlabel("Year (decimal)")
    ax.grid(axis="y", visible=False)
    ax.set_title(f"(a) Temporal coverage of the {len(inv)} input estimates "
                 f"({int(inv.used_in_consensus.sum())} used in the consensus)", loc="left")
    handles = [Line2D([], [], color=METHOD_COLOR[m], lw=2, label=METHOD_LABEL[m])
               for m in METHODS]
    handles += [Line2D([], [], color="#555555", lw=1.6, label="annual or finer resolution"),
                Line2D([], [], color="#555555", lw=0.9, ls=(0, (2, 1.2)),
                       label="multi-annual resolution"),
                Line2D([], [], color="#555555", lw=1.6, alpha=0.3,
                       label="not used in consensus (pale)")]
    ax.legend(handles=handles, loc="upper left", fontsize=7.5, ncol=4,
              bbox_to_anchor=(0.0, -0.045))

    # Right: count per region x method.
    mat = counts[METHODS].to_numpy()
    yb = np.array(bands)
    xedges = np.arange(len(METHODS) + 1) - 0.5
    yedges = np.r_[yb + 0.5, yb[-1] - 0.5]
    axh.pcolormesh(xedges, yedges, mat, cmap="Blues", vmin=0,
                   vmax=max(mat.max(), 1) * 1.3, edgecolors="white", linewidth=1.5)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            v = mat[i, j]
            u = nused[METHODS].to_numpy()[i, j]
            axh.text(j, yb[i], f"{u}/{v}" if v else "–", ha="center", va="center",
                     fontsize=7.5, color="white" if v > mat.max() * 0.65 else "#222222")
        axh.text(mat.shape[1] - 0.35, yb[i],
                 f"{nused['total'].iloc[i]}/{counts['total'].iloc[i]}", ha="left",
                 va="center", fontsize=8, fontweight="bold", color="#222222")
    axh.set_xticks(range(len(METHODS)),
                   ["Glac.", "DEM", "Alt.", "Grav.", "Hybrid"], rotation=0)
    axh.xaxis.tick_top()
    axh.tick_params(axis="x", length=0)
    axh.text(mat.shape[1] - 0.35, yb[0] + 0.75, "Total", ha="left", va="center", fontsize=8)
    axh.tick_params(axis="y", left=False)
    axh.grid(False)
    for s_ in axh.spines.values():
        s_.set_visible(False)
    axh.set_xlim(-0.5, mat.shape[1] + 0.4)
    axh.set_title("(b) Estimates used / submitted", loc="left", pad=16)
    tot = counts[METHODS].sum()
    axh.text(-0.5, yb[-1] - 0.75,
             "All regions (used/submitted): " + ", ".join(
                 f"{METHOD_LABEL[m].split()[0]} {nused[m].sum()}/{tot[m]}" for m in METHODS),
             fontsize=7, va="top", color="#444444")
    return save(fig, "fig01_data_overview")


if __name__ == "__main__":
    print(main())
