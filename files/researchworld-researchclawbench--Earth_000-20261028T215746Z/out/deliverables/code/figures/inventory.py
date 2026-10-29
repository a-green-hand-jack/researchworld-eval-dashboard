"""Inventory of the GlaMBIE input estimates (one CSV = one submitted estimate)."""
import re

import pandas as pd

from style import DATA, METHODS, REGIONS

_SRC = re.compile(r"_(" + "|".join(METHODS) + r")_")


def load_inventory():
    rows = []
    for region in REGIONS:
        prefix = region.split("_", 1)[1] + "_"
        for f in sorted((DATA / "input" / region).glob("*.csv")):
            method = _SRC.search("_" + f.name[len(prefix):]).group(1)
            d = pd.read_csv(f)
            period = (d.end_dates - d.start_dates)
            rows.append({
                "region": region,
                "method": method,
                "file": f.name,
                "author": d.author.iloc[0],
                "unit": d.unit.iloc[0].lower(),
                "start": d.start_dates.min(),
                "end": d.end_dates.max(),
                "n_periods": len(d),
                "median_period_yr": float(period.median()),
            })
    return pd.DataFrame(rows)
