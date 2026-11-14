#!/bin/bash
# Regenerate every summary CSV in results/ from the raw per-replicate rows (RAW, default /hutian/scratch/raw). Cells not yet run are simply absent.
RAW=${RAW:-/hutian/scratch/raw}
cd "$(dirname "$0")"
python3 -W ignore summarize.py $RAW/mean_real ../results/summary_mean_real.csv
python3 -W ignore summarize.py $RAW/rho_real ../results/summary_rho_real.csv
ls $RAW/ols_real/*.csv >/dev/null 2>&1 && python3 -W ignore summarize.py $RAW/ols_real ../results/summary_ols_real.csv
python3 -W ignore summarize.py $RAW/synth ../results/summary_synth.csv
python3 -W ignore summarize.py $RAW/valid_real ../results/summary_validity_real.csv
mkdir -p /tmp/sp_$$; for c in plankton_noshift plankton_shift ballots_sub ballots_width; do mkdir -p /tmp/sp_$$/$c; cp $RAW/special/${c}_n*.csv /tmp/sp_$$/$c/ 2>/dev/null; done
python3 -W ignore summarize.py /tmp/sp_$$/plankton_noshift ../results/summary_plankton_noshift.csv
python3 -W ignore summarize.py /tmp/sp_$$/plankton_shift ../results/summary_plankton_shift.csv
python3 -W ignore summarize.py /tmp/sp_$$/ballots_sub ../results/summary_ballots_sub.csv
WIDTH_ONLY=1 python3 -W ignore summarize.py /tmp/sp_$$/ballots_width ../results/summary_ballots_width.csv
rm -rf /tmp/sp_$$
python3 -W ignore derived.py ../results/summary_synth.csv ../results/theory_synth.csv ../results/theory_vs_measured.csv
python3 -W ignore derived.py --breakeven ../results/summary_synth.csv ../results/breakeven_synth.csv scenario
python3 -W ignore derived.py --breakeven ../results/summary_mean_real.csv ../results/breakeven_real.csv dataset
# which cells each summary contains (grids are delivered while still running; this file says what is in)
python3 -W ignore - <<'PY'
import glob, pandas as pd
rows = []
for f in sorted(glob.glob("../results/summary_*.csv")):
    d = pd.read_csv(f)
    k = [c for c in ["dataset", "scenario", "n", "N", "rho", "coord"] if c in d]
    g = d.groupby(k, dropna=False).agg(reps=("reps", "first"), methods=("method", "nunique")).reset_index()
    g.insert(0, "file", f.split("/")[-1]); rows.append(g)
pd.concat(rows).to_csv("../results/cells_done.csv", index=False)
PY
python3 -W ignore headline.py ../results
