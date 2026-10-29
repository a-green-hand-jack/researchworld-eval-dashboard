#!/bin/sh
# Reproduce every file in outputs/ from the supplied GlaMBIE dataset (read-only inputs).
# Env: GLAMBIE_DATA (default /initial-state/inputs/2/glambie). Runtime ~4-6 min on 1 CPU.
set -e
cd "$(dirname "$0")"
python3 run_all.py --ndraw 1000 --out ../outputs
# Analyses requested in review (acceleration significance variants, Zemp-matched years, DEM vs Hugonnet, drop-DEM/glac, group validation summary)
python3 review_analyses.py --ndraw 1000 --out ../outputs
