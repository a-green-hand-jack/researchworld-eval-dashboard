"""Join the NBA and Arena / MT-Bench replicate files written by `run_units.py nba` and `run_units.py arena mt`
-> results/kstar_units.csv (pure concatenation)."""
import sys, os
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import provenance as pv

parts = [os.path.join(pv.RES, f) for f in ("kstar_units_nba.csv", "kstar_units_arena_mt.csv")]
pv.save(pd.concat([pd.read_csv(p) for p in parts], ignore_index=True), "kstar_units.csv", "merge_units.py", 0, parts)
