"""F3 - Global annual and cumulative glacier mass change 2000-2023.

Claims supported: mean loss -275.6 +- 11.2 Gt/yr, accelerating from 2000-2011
to 2012-2023, cumulative -6615 +- 270 Gt (18.2 +- 0.7 mm SLE); our series is
consistent with the published GlaMBIE global series.
Inputs: outputs/reconciliation/global_calendar_years.csv,
outputs/reconciliation/summary_global.json,
data/glambie/results/calendar_years/0_global.csv (reference).  1 sigma.
Cumulative uncertainty: sqrt of the sum of annual variances (as GlaMBIE).
"""
import json

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np
import pandas as pd

from style import (DATA, GT_PER_MM_SLE, RECON, RECONCILED_COLOR,
                   REFERENCE_COLOR, apply_style, num, save)


def cumulative(gt, err):
    """Cumulative change from 1 Jan 2000 with quadrature-accumulated 1 sigma."""
    return (np.r_[0, np.cumsum(gt)], np.r_[0, np.sqrt(np.cumsum(np.square(err)))])


def main():
    apply_style()
    g = pd.read_csv(RECON / "global_calendar_years.csv")
    ref = pd.read_csv(DATA / "results" / "calendar_years" / "0_global.csv")
    ref["year"] = ref.start_dates.round().astype(int)
    ref = ref[(ref.year >= 2000) & (ref.year <= 2023)]
    summ = json.load(open(RECON / "summary_global.json"))["ours"]

    fig, (a, b) = plt.subplots(2, 1, figsize=(8, 8.2), sharex=True,
                               gridspec_kw={"height_ratios": [1, 1], "hspace": 0.12})

    # (a) Annual mass change, bars centred on the calendar year.
    x = g.year + 0.5
    a.bar(x - 0.2, g["gt"], width=0.38, color="#4d4d4d", label="This study", zorder=2)
    a.errorbar(x - 0.2, g["gt"], yerr=g.gt_err, fmt="none", ecolor="black",
               elinewidth=0.8, capsize=1.8, zorder=3)
    a.bar(ref.year + 0.5 + 0.2, ref.combined_gt, width=0.38, color="#c7c7c7",
          label="GlaMBIE (2024) published", zorder=2)
    a.errorbar(ref.year + 0.5 + 0.2, ref.combined_gt, yerr=ref.combined_gt_errors,
               fmt="none", ecolor=REFERENCE_COLOR, elinewidth=0.8, capsize=1.8, zorder=3)
    for (p0, p1), key in (((2000, 2012), "2000_2011"), ((2012, 2024), "2012_2023"),):
        r = summ[key]["gt"]
        a.hlines(r["rate"], p0, p1, color="#B2182B", lw=1.6, zorder=4)
        a.fill_between([p0, p1], r["rate"] - r["rate_err"], r["rate"] + r["rate_err"],
                       color="#B2182B", alpha=0.15, lw=0, zorder=1)
        a.text(p0 + 0.3, 55, f"{p0}–{p1 - 1}: {num(r['rate'], '.0f')} ± {r['rate_err']:.0f} Gt yr⁻¹",
               fontsize=8, color="#B2182B", va="bottom")
    r = summ["2000_2023"]["gt"]
    a.set_ylabel("Annual mass change (Gt yr⁻¹)")
    a.axhline(0, color="#444444", lw=0.7)
    a.set_ylim(-720, 130)
    handles, labels = a.get_legend_handles_labels()
    handles.append(Line2D([], [], color="#B2182B", lw=1.6))
    labels.append("Period mean ±1σ (this study)")
    a.legend(handles, labels, loc="lower left", ncol=3, fontsize=7.5)
    a.set_title(f"(a) Global annual mass change; 2000–2023 mean "
                f"{num(r['rate'])} ± {r['rate_err']:.1f} Gt yr⁻¹", loc="left")

    # (b) Cumulative change since 1 January 2000.
    xe = np.r_[g.year.iloc[0], g.year + 1]
    c, ce = cumulative(g["gt"].to_numpy(), g.gt_err.to_numpy())
    cr, cre = cumulative(ref.combined_gt.to_numpy(), ref.combined_gt_errors.to_numpy())
    b.fill_between(xe, cr - cre, cr + cre, color=REFERENCE_COLOR, alpha=0.18, lw=0)
    b.plot(xe, cr, color=REFERENCE_COLOR, lw=1.4, ls="--")
    b.fill_between(xe, c - ce, c + ce, color=RECONCILED_COLOR, alpha=0.22, lw=0)
    b.plot(xe, c, color=RECONCILED_COLOR, lw=1.8)
    b.set_ylabel("Cumulative mass change (Gt)")
    b.set_xlabel("Year (calendar; cumulative values at 1 January)")
    b.set_xlim(1999.6, 2024.4)
    t = summ["2000_2023"]
    b.annotate(f"{num(t['gt']['total'], '.0f')} ± {t['gt']['total_err']:.0f} Gt\n"
               f"{t['sle_mm']['total']:.1f} ± {t['sle_mm']['total_err']:.1f} mm SLE",
               xy=(2024, c[-1]), xytext=(2017.2, c[-1] + 250), fontsize=8.5,
               ha="left", va="bottom")
    sec = b.secondary_yaxis("right", functions=(lambda v: -v / GT_PER_MM_SLE,
                                                lambda v: -v * GT_PER_MM_SLE))
    sec.set_ylabel("Sea-level contribution (mm SLE)")
    b.legend(handles=[
        Line2D([], [], color=RECONCILED_COLOR, lw=1.8, label="This study ±1σ"),
        Line2D([], [], color=REFERENCE_COLOR, lw=1.4, ls="--",
               label="GlaMBIE (2024) published ±1σ")], loc="lower left")
    b.set_title("(b) Cumulative global mass change since 2000", loc="left")
    return save(fig, "fig03_global_series")


if __name__ == "__main__":
    print(main())
