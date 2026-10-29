"""F7 - Sensitivity of the global result to the combination choices.

Claim supported: the global 2000-2023 rate and the acceleration are robust to
weighting, gravimetry selection and hybrid data; ice density and the
DEM differencing + glaciological group dominate the spread.
Input: outputs/validation/sensitivity_global.csv (1 sigma).
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from style import RECONCILED_COLOR, VALID, apply_style, save

LABEL = {
    "main": "Main configuration",
    "equal_weights": "Equal weights of data groups",
    "independent_group_errors": "Group errors independent",
    "glaciological_UZH_with_trend": "Glaciological series keep own trend",
    "gravimetry_all_regions": "Gravimetry in all regions",
    "no_gravimetry": "Without gravimetry",
    "no_altimetry": "Without altimetry",
    "no_demdiff_glaciological": "Without DEM diff. + glaciological",
    "with_hybrid_group": "Hybrids as fourth group",
    "density_800": "Density 800 kg m⁻³",
    "density_900": "Density 900 kg m⁻³",
}


def main():
    apply_style()
    s = pd.read_csv(VALID / "sensitivity_global.csv")
    s["acc"] = s.rate_gt_2012_2023 - s.rate_gt_2000_2011
    y = np.arange(len(s))
    m = s[s.variant == "main"].iloc[0]
    fig, (a, b) = plt.subplots(1, 2, figsize=(10, 4.8), sharey=True,
                               gridspec_kw={"width_ratios": [1.3, 1], "wspace": 0.08})
    a.axvspan(m.rate_gt_2000_2023 - m.rate_gt_err_2000_2023,
              m.rate_gt_2000_2023 + m.rate_gt_err_2000_2023, color="#dddddd", lw=0)
    a.axvline(m.rate_gt_2000_2023, color=RECONCILED_COLOR, lw=0.8)
    isMain = s.variant == "main"
    a.errorbar(s.rate_gt_2000_2023, y, xerr=s.rate_gt_err_2000_2023, fmt="none",
               ecolor="#555555", elinewidth=0.9)
    a.scatter(s.rate_gt_2000_2023, y, s=np.where(isMain, 46, 26),
              c=np.where(isMain, "#B2182B", RECONCILED_COLOR), zorder=3)
    a.set_yticks(y, [LABEL.get(v, v) for v in s.variant])
    a.set_ylim(len(s) - 0.5, -0.5)
    a.grid(axis="y", visible=False)
    a.set_xlabel("Global mean rate 2000–2023 (Gt yr⁻¹)")
    a.set_title("(a) Mean rate ±1σ (band: main ±1σ)", loc="left")

    b.axvline(m.acc, color=RECONCILED_COLOR, lw=0.8)
    b.axvline(0, color="#444444", lw=0.6)
    b.scatter(s.acc, y, s=np.where(isMain, 46, 26),
              c=np.where(isMain, "#B2182B", RECONCILED_COLOR), zorder=3)
    b.grid(axis="y", visible=False)
    b.set_xlabel("Rate 2012–2023 minus rate 2000–2011 (Gt yr⁻¹)")
    b.set_title("(b) Change in global rate between periods", loc="left")
    return save(fig, "fig07_sensitivity")


if __name__ == "__main__":
    print(main())
