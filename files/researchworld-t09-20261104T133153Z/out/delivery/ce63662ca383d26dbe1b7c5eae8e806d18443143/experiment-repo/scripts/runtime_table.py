#!/usr/bin/env python3
"""Per-grid timing from the `secs` column of the raw files -> results/RUNTIME.csv (cells with secs >= 1e4 stalled on the shared host and are excluded from the CPU-hours)."""
import sys as _s, os as _o
_s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "..", "src"))
from netgate.paths import results_dir
import glob, os
import pandas as pd

R = results_dir(); rows = []
for e in [f"e{i}" for i in range(1, 22)]:
    s = pd.Series([pd.read_csv(f, usecols=["secs"]).secs.iloc[0] for f in glob.glob(os.path.join(R, "raw", e, "*.csv.gz"))]); ok = s[s < 1e4]
    rows.append(dict(exp=e, cells_run=len(s), median_cell_secs=round(s.median(), 1), cpu_hours_excl_stalled=round(ok.sum() / 3600, 2), cells_stalled_over_1e4s=int((s >= 1e4).sum())))
d = pd.DataFrame(rows); d.to_csv(os.path.join(R, "RUNTIME.csv"), index=False); print(d.to_string(index=False), "\ntotal CPU-h", d.cpu_hours_excl_stalled.sum())
