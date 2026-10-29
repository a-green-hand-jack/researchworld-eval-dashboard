"""F6 - Validation against the published GlaMBIE results and prior estimates.

Claims supported: the independent reconciliation reproduces GlaMBIE globally
(annual series) and regionally (2000-2023 mean rates); it agrees with
Hugonnet et al. (2021) and Zemp et al. (2019) where periods overlap; and,
the contradictory part, its acceleration (2012-2023 minus 2000-2011) is weaker
than GlaMBIE's, with the difference concentrated in a few regions.
Inputs: outputs/validation/vs_glambie_global_pairs.csv,
outputs/validation/vs_glambie_regional_pairs.csv (level = calendar),
outputs/validation/prior_estimates.csv, outputs/reconciliation/summary_global.json.
All errors 1 sigma; period errors combine annual errors in quadrature.
"""
import json

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd

from style import (RECON, RECONCILED_COLOR, REFERENCE_COLOR, REGIONS, VALID,
                   apply_style, num, region_label, save)

PRIOR_COLOR = "#E69F00"


def period_rate(d, col, ecol, y0, y1):
    s = d[(d.year >= y0) & (d.year <= y1)]
    return s[col].mean(), np.sqrt(np.square(s[ecol]).sum()) / len(s)


def main():
    apply_style()
    gp = pd.read_csv(VALID / "vs_glambie_global_pairs.csv")
    rp = pd.read_csv(VALID / "vs_glambie_regional_pairs.csv")
    rp = rp[rp.level == "calendar"]
    pri = pd.read_csv(VALID / "prior_estimates.csv")
    st = json.load(open(RECON / "summary_global.json"))["global_vs_glambie_annual"]

    fig = plt.figure(figsize=(11, 9.6))
    gs = fig.add_gridspec(2, 2, hspace=0.32, wspace=0.42)
    a, b = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])
    c, d = fig.add_subplot(gs[1, 0]), fig.add_subplot(gs[1, 1])

    # (a) Global annual: ours vs GlaMBIE.
    a.errorbar(gp.gt_ref, gp["gt"], xerr=gp.gt_err_ref, yerr=gp.gt_err, fmt="o", ms=4,
               color=RECONCILED_COLOR, ecolor="#9e9e9e", elinewidth=0.7, capsize=0)
    lim = [-650, 0]
    a.plot(lim, lim, color="#B2182B", lw=0.9, ls="--", label="1:1")
    for r in gp.itertuples():
        if r.year in (2000, 2014, 2022, 2023):
            a.annotate(str(r.year), (r.gt_ref, r[4]), xytext=(4, -9),
                       textcoords="offset points", fontsize=7, color="#444444")
    a.set_xlim(lim)
    a.set_ylim(lim)
    a.set_aspect("equal")
    a.set_xlabel("GlaMBIE (2024) published (Gt yr⁻¹)")
    a.set_ylabel("This study (Gt yr⁻¹)")
    a.set_title("(a) Global annual mass change, 2000–2023", loc="left")
    a.text(0.97, 0.04, f"r = {st['r_gt']:.2f}\nRMSE = {st['rmse_gt']:.0f} Gt yr⁻¹\n"
           f"bias = {num(st['bias_gt'])} Gt yr⁻¹\n"
           f"{st['frac_within_1sigma_gt'] * 100:.0f}% of years within combined 1σ",
           transform=a.transAxes, ha="right", va="bottom", fontsize=7.5)
    a.legend(loc="upper left")

    # (b) Regional 2000-2023 mean specific rate.
    rows = []
    for reg in REGIONS:
        s = rp[rp.region == reg]
        o, oe = period_rate(s, "mwe", "mwe_err", 2000, 2023)
        g, ge = period_rate(s, "mwe_ref", "mwe_err_ref", 2000, 2023)
        e0, e0e = period_rate(s, "gt", "gt_err", 2000, 2011)
        e1, e1e = period_rate(s, "gt", "gt_err", 2012, 2023)
        f0, f0e = period_rate(s, "gt_ref", "gt_err_ref", 2000, 2011)
        f1, f1e = period_rate(s, "gt_ref", "gt_err_ref", 2012, 2023)
        rows.append(dict(region=reg, ours=o, ours_err=oe, ref=g, ref_err=ge,
                         acc=e1 - e0, acc_err=np.hypot(e0e, e1e),
                         acc_ref=f1 - f0, acc_ref_err=np.hypot(f0e, f1e)))
    R = pd.DataFrame(rows)
    b.errorbar(R.ref, R.ours, xerr=R.ref_err, yerr=R.ours_err, fmt="o", ms=4,
               color=RECONCILED_COLOR, ecolor="#9e9e9e", elinewidth=0.7)
    lim = [-1.2, 0]
    b.plot(lim, lim, color="#B2182B", lw=0.9, ls="--")
    for r in R.itertuples():
        b.annotate(r.region.split("_")[0], (r.ref, r.ours), xytext=(3, 3),
                   textcoords="offset points", fontsize=6.5, color="#333333")
    rms = np.sqrt(np.mean((R.ours - R.ref) ** 2))
    b.text(0.97, 0.04, f"RMS difference = {rms:.2f} m w.e. yr⁻¹\n"
           f"labels: region number", transform=b.transAxes, ha="right",
           va="bottom", fontsize=7.5)
    b.set_xlim(lim)
    b.set_ylim(lim)
    b.set_aspect("equal")
    b.set_xlabel("GlaMBIE (2024) published (m w.e. yr⁻¹)")
    b.set_ylabel("This study (m w.e. yr⁻¹)")
    b.set_title("(b) Regional mean specific rate, 2000–2023", loc="left")

    # (c) Acceleration per region: change of the mean rate between periods.
    R["dacc"] = R.acc - R.acc_ref
    R = R.sort_values("dacc", key=np.abs, ascending=False).reset_index(drop=True)
    y = np.arange(len(R))
    c.errorbar(R.acc, y - 0.17, xerr=R.acc_err, fmt="o", ms=4, color=RECONCILED_COLOR,
               elinewidth=0.8, label="This study")
    c.errorbar(R.acc_ref, y + 0.17, xerr=R.acc_ref_err, fmt="s", ms=4,
               color=REFERENCE_COLOR, mfc="white", elinewidth=0.8, label="GlaMBIE (2024)")
    c.axvline(0, color="black", lw=0.7)
    c.set_yticks(y, [region_label(r) for r in R.region], fontsize=7)
    c.set_ylim(len(R) - 0.5, -0.5)
    c.grid(axis="y", visible=False)
    c.set_xlabel("Rate 2012–2023 minus rate 2000–2011 (Gt yr⁻¹)\nnegative = accelerating loss")
    tot, totr = R.acc.sum(), R.acc_ref.sum()
    c.set_title("(c) Change in regional loss rate between periods", loc="left")
    c.text(0.98, 0.42, f"Sum of regions:\n{num(tot, '.0f')} Gt yr⁻¹ (this study)\n"
           f"{num(totr, '.0f')} Gt yr⁻¹ (GlaMBIE)",
           transform=c.transAxes, ha="right", va="center", fontsize=7.5)
    c.legend(loc="lower left", fontsize=7)

    # (d) Prior global estimates over the same calendar years.
    pri = pri.reset_index(drop=True)
    y = np.arange(len(pri))
    d.errorbar(pri.prior_rate_gt, y - 0.22, xerr=pri.prior_rate_gt_err, fmt="D", ms=4,
               color=PRIOR_COLOR, elinewidth=0.9, label="Published estimate")
    d.errorbar(pri.ours_rate_gt, y, xerr=pri.ours_rate_gt_err, fmt="o", ms=4,
               color=RECONCILED_COLOR, elinewidth=0.9, label="This study")
    d.errorbar(pri.glambie_rate_gt, y + 0.22, xerr=pri.glambie_rate_gt_err, fmt="s", ms=4,
               color=REFERENCE_COLOR, mfc="white", elinewidth=0.9, label="GlaMBIE (2024)")
    lab = [f"{s.split(' et')[0]} {s.split()[-1]}\n{f}–{l}" for s, f, l in
           zip(pri.source, pri.first_year, pri.last_year)]
    d.set_yticks(y, lab, fontsize=7.5)
    d.set_ylim(len(pri) - 0.5, -0.5)
    d.grid(axis="y", visible=False)
    d.set_xlabel("Global mean mass change rate (Gt yr⁻¹)")
    d.set_title("(d) Comparison with earlier global estimates", loc="left")
    d.legend(loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=3, fontsize=7)
    return save(fig, "fig06_validation")


if __name__ == "__main__":
    print(main())
