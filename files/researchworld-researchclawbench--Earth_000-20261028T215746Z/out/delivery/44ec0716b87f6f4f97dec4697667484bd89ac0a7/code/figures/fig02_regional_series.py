"""F2 - Regional annual specific mass change per data group and consensus.

Claim supported: within each region the data groups agree on the level and the
interannual variability, and the consensus follows them.
Inputs: outputs/reconciliation/group_series_hydrological_years.csv,
outputs/reconciliation/regional_hydrological_years.csv (hydrological years, 1 sigma).
"""
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import pandas as pd

from style import (GROUPS, GROUP_COLOR, GROUP_LABEL, GROUP_MARKER, RECON,
                   RECONCILED_COLOR, REGIONS, apply_style, region_label, save)


def main():
    apply_style()
    grp = pd.read_csv(RECON / "group_series_hydrological_years.csv")
    con = pd.read_csv(RECON / "regional_hydrological_years.csv")
    summ = pd.read_csv(RECON / "summary_regional.csv").set_index("region")
    for d in (grp, con):
        d["mid"] = 0.5 * (d.start_dates + d.end_dates)

    fig, axes = plt.subplots(5, 4, figsize=(11, 12.5), sharex=True, sharey=True)
    axes = axes.ravel()
    for ax, region in zip(axes, REGIONS):
        c = con[con.region == region].sort_values("mid")
        ax.fill_between(c.mid, c.mwe - c.mwe_err, c.mwe + c.mwe_err,
                        color="#bdbdbd", alpha=0.55, lw=0, zorder=1)
        for g in GROUPS:
            s = grp[(grp.region == region) & (grp.group == g)].sort_values("mid")
            if s.empty:
                continue
            ax.plot(s.mid, s.mwe, color=GROUP_COLOR[g], lw=1.0, zorder=2)
            own = s[~s.borrowed]
            ax.plot(own.mid, own.mwe, ls="none", marker=GROUP_MARKER[g], ms=2.8,
                    color=GROUP_COLOR[g], zorder=3)
        ax.plot(c.mid, c.mwe, color=RECONCILED_COLOR, lw=1.5, zorder=4)
        ax.axhline(0, color="#666666", lw=0.6, zorder=0)
        ax.set_title(region_label(region), loc="left", fontsize=8.5)
        r = summ.loc[region]
        ax.set_title(f"{r.rate_mwe_2000_2023:.2f} ± {r.rate_mwe_err_2000_2023:.2f}",
                     loc="right", fontsize=7.5, color="#333333")
    for ax in axes[len(REGIONS):]:
        ax.axis("off")
    for ax in axes[::4]:
        ax.set_ylabel("m w.e. yr⁻¹")
    for ax in axes[15:19]:
        ax.set_xlabel("Hydrological year")
        ax.xaxis.set_tick_params(labelbottom=True)
    axes[0].set_xlim(1999, 2025)
    axes[0].set_xticks([2000, 2010, 2020])
    axes[0].set_ylim(-3.8, 2.6)

    handles = [Line2D([], [], color=GROUP_COLOR[g], marker=GROUP_MARKER[g], ms=4,
                      lw=1.0, label=GROUP_LABEL[g]) for g in GROUPS]
    handles += [Line2D([], [], color=RECONCILED_COLOR, lw=1.5, label="Consensus"),
                Patch(color="#bdbdbd", alpha=0.55, label="Consensus ±1σ"),
                Line2D([], [], color="#555555", lw=1.0,
                       label="line without markers:\nvariability borrowed from\nDEM diff. + glaciological")]
    axes[19].legend(handles=handles, loc="center", fontsize=8, frameon=False)
    fig.tight_layout(h_pad=0.8, w_pad=0.4)
    return save(fig, "fig02_regional_series")


if __name__ == "__main__":
    print(main())
