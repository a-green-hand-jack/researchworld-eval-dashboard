"""Shared helpers for figure/table generators (GlaMBIE presentation)."""
import os
import pandas as pd

DATA = os.environ.get("GLAMBIE_DATA", "/initial-state/inputs/2/glambie")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
IMG = os.path.join(ROOT, "report", "images")
TAB = os.path.join(ROOT, "code", "figures", "tables")

REGIONS = {1: "Alaska", 2: "Western Canada & US", 3: "Arctic Canada N", 4: "Arctic Canada S",
           5: "Greenland periphery", 6: "Iceland", 7: "Svalbard", 8: "Scandinavia",
           9: "Russian Arctic", 10: "North Asia", 11: "Central Europe", 12: "Caucasus & Middle East",
           13: "Central Asia", 14: "South Asia West", 15: "South Asia East", 16: "Low latitudes",
           17: "Southern Andes", 18: "New Zealand", 19: "Antarctic & Subantarctic"}
METHODS = ["glaciological", "demdiff", "altimetry", "gravimetry", "combined"]
METHOD_LABEL = {"glaciological": "Glaciological", "demdiff": "DEM differencing",
                "altimetry": "Altimetry", "gravimetry": "Gravimetry", "combined": "Hybrid / combined"}
# Okabe-Ito colour-blind-safe palette, fixed per method in every figure
METHOD_COLOR = {"glaciological": "#009E73", "demdiff": "#E69F00", "altimetry": "#0072B2",
                "gravimetry": "#CC79A7", "combined": "#666666"}


def inventory():
    """One row per submitted input file: region number, method, group, citation, coverage, unit."""
    rows = []
    base = os.path.join(DATA, "input")
    for d in sorted(os.listdir(base)):
        p = os.path.join(base, d)
        if not os.path.isdir(p):
            continue
        rid = int(d.split("_")[0])
        rname = d.split("_", 1)[1]
        for f in sorted(os.listdir(p)):
            if not f.endswith(".csv"):
                continue
            df = pd.read_csv(os.path.join(p, f))
            stem = f[:-4]
            method = stem[len(rname) + 1:].split("_")[0]
            rows.append(dict(region_id=rid, region=REGIONS[rid], method=method, file=f"{d}/{f}",
                             author=df["author"].iloc[0], unit=df["unit"].iloc[0],
                             start=df["start_dates"].min(), end=df["end_dates"].max(),
                             n_periods=len(df),
                             median_step_yr=float((df["end_dates"] - df["start_dates"]).median())))
    return pd.DataFrame(rows)


SLE_GT_PER_MM = 362.5  # Gt of ice-water per mm global mean sea-level equivalent


def load_published(kind="calendar_years"):
    """Published GlaMBIE results as long table: region_id (0 = global), year (= start of annual period), values.
    For hydrological years the per-data-group columns are also kept."""
    base = os.path.join(DATA, "results", kind)
    out = []
    for f in sorted(os.listdir(base)):
        if not f.endswith(".csv"):
            continue
        rid = int(f.split("_")[0])
        df = pd.read_csv(os.path.join(base, f))
        df["region_id"] = rid
        out.append(df)
    df = pd.concat(out, ignore_index=True)
    df["year"] = df["start_dates"]
    return df


# Reconstruction products of experiment-repo (delivered in outputs/ of the paper repository)
OUT = os.environ.get("RECON_OUTPUTS", os.path.join(ROOT, "outputs"))
C_RECON = "#0072B2"   # reconstruction (this study)
C_PUB = "#D55E00"     # published GlaMBIE benchmark


def recon(name):
    return pd.read_csv(os.path.join(OUT, name))
