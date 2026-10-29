"""Report tables T1-T4 as CSV and Markdown in outputs/tables/.

T1 regional summary 2000-2023 (summary_regional.csv + inputs_inventory.csv),
T2 global annual series (global_calendar_years.csv),
T3 comparison with earlier global estimates (prior_estimates.csv),
T4 sensitivity of the global result (sensitivity_global.csv).
All uncertainties are 1 sigma, as delivered by the reconciliation.
"""
import pandas as pd

from fig07_sensitivity import LABEL
from style import GT_PER_MM_SLE, RECON, REGIONS, TABLES, VALID, region_label


def pm(v, e, fmt):
    return f"{format(v, fmt)} ± {format(e, fmt)}".replace("-", "−")


def to_markdown(df):
    """Pipe table; first column left-aligned, the others right-aligned."""
    head = "| " + " | ".join(df.columns) + " |"
    rule = "|" + "|".join([":---"] + ["---:"] * (len(df.columns) - 1)) + "|"
    rows = ["| " + " | ".join(str(v) for v in r) + " |" for r in df.itertuples(index=False)]
    return "\n".join([head, rule] + rows)


def write(df, name, md):
    TABLES.mkdir(parents=True, exist_ok=True)
    df.to_csv(TABLES / f"{name}.csv", index=False)
    (TABLES / f"{name}.md").write_text(to_markdown(md) + "\n")


def t1():
    s = pd.read_csv(RECON / "summary_regional.csv")
    inv = pd.read_csv(RECON / "inputs_inventory.csv")
    n = inv.groupby("region").agg(n_submitted=("file", "count"),
                                  n_used=("used_in_consensus", "sum")).reset_index()
    s = s.merge(n, on="region")
    s["ri"] = s.region.map(REGIONS.index)
    s = s.sort_values("ri").drop(columns="ri")
    md = pd.DataFrame({
        "Region": [region_label(r) for r in s.region],
        "Area 2000 (km²)": s.glacier_area_2000.map(lambda v: f"{v:,.0f}"),
        "Estimates used / submitted": [f"{u}/{t}" for u, t in zip(s.n_used, s.n_submitted)],
        "Rate 2000–2023 (m w.e. yr⁻¹)": [pm(v, e, ".2f") for v, e in zip(s.rate_mwe_2000_2023, s.rate_mwe_err_2000_2023)],
        "Rate 2000–2023 (Gt yr⁻¹)": [pm(v, e, ".1f") for v, e in zip(s.rate_gt_2000_2023, s.rate_gt_err_2000_2023)],
        "Rate 2000–2011 (m w.e. yr⁻¹)": [pm(v, e, ".2f") for v, e in zip(s.rate_mwe_2000_2011, s.rate_mwe_err_2000_2011)],
        "Rate 2012–2023 (m w.e. yr⁻¹)": [pm(v, e, ".2f") for v, e in zip(s.rate_mwe_2012_2023, s.rate_mwe_err_2012_2023)],
        "Cumulative 2000–2023 (Gt)": [pm(v, e, ".0f") for v, e in zip(s.cumulative_gt, s.cumulative_gt_err)],
        "Share of global loss (%)": s.share_of_global_loss_pct.map(lambda v: f"{v:.1f}"),
    })
    write(s, "t1_regional_summary", md)


def t2():
    g = pd.read_csv(RECON / "global_calendar_years.csv")
    g["cumulative_gt"] = g["gt"].cumsum()
    g["cumulative_gt_err"] = (g.gt_err ** 2).cumsum() ** 0.5
    g["cumulative_sle_mm"] = -g.cumulative_gt / GT_PER_MM_SLE
    md = pd.DataFrame({
        "Year": g.year,
        "Mass change (Gt)": [pm(v, e, ".0f") for v, e in zip(g["gt"], g.gt_err)],
        "Specific (m w.e.)": [pm(v, e, ".2f") for v, e in zip(g.mwe, g.mwe_err)],
        "Sea level (mm)": [pm(v, e, ".2f") for v, e in zip(g.sle_mm, g.sle_mm_err)],
        "Cumulative since 2000 (Gt)": [pm(v, e, ".0f") for v, e in zip(g.cumulative_gt, g.cumulative_gt_err)],
        "Glacier area (km²)": g.glacier_area.map(lambda v: f"{v:,.0f}"),
    })
    write(g, "t2_global_annual", md)


def t3():
    p = pd.read_csv(VALID / "prior_estimates.csv")
    md = pd.DataFrame({
        "Study": p.source,
        "Period": [f"{a}–{b}" for a, b in zip(p.first_year, p.last_year)],
        "Published (Gt yr⁻¹)": [pm(v, e, ".0f") for v, e in zip(p.prior_rate_gt, p.prior_rate_gt_err)],
        "This study (Gt yr⁻¹)": [pm(v, e, ".0f") for v, e in zip(p.ours_rate_gt, p.ours_rate_gt_err)],
        "GlaMBIE 2024 (Gt yr⁻¹)": [pm(v, e, ".0f") for v, e in zip(p.glambie_rate_gt, p.glambie_rate_gt_err)],
        "This study − published, z": [f"{d:+.0f}, {z:+.1f}".replace("-", "−") for d, z in zip(p.diff_ours_minus_prior, p.z)],
        "Source of published value": p["where"],
    })
    write(p, "t3_prior_estimates", md)


def t4():
    s = pd.read_csv(VALID / "sensitivity_global.csv")
    md = pd.DataFrame({
        "Variant": [LABEL.get(v, v) for v in s.variant],
        "Rate 2000–2023 (Gt yr⁻¹)": [pm(v, e, ".1f") for v, e in zip(s.rate_gt_2000_2023, s.rate_gt_err_2000_2023)],
        "Rate 2000–2011 (Gt yr⁻¹)": s.rate_gt_2000_2011.map(lambda v: f"{v:.1f}".replace("-", "−")),
        "Rate 2012–2023 (Gt yr⁻¹)": s.rate_gt_2012_2023.map(lambda v: f"{v:.1f}".replace("-", "−")),
        "Cumulative (Gt)": [pm(v, e, ".0f") for v, e in zip(s.cumulative_gt, s.cumulative_gt_err)],
        "Rate (m w.e. yr⁻¹)": s.rate_mwe_2000_2023.map(lambda v: f"{v:.3f}".replace("-", "−")),
    })
    write(s, "t4_sensitivity_global", md)


def main():
    for f in (t1, t2, t3, t4):
        f()
    return TABLES


if __name__ == "__main__":
    print(main())
