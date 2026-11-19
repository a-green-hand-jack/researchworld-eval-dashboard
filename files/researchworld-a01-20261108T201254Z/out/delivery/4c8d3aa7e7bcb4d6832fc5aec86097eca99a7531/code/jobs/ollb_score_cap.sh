# usage: jobs/ollb_score_cap.sh CAP  -- all score rules, all 4496 targets, one cap (trimmed mean MILP ~45 min per cap)
cd "$(dirname "$0")/.."
jobs/_run.sh ollb_score_$1 src/run_core.py ollb $1 trimmed1,mean,geomean,harmonic,median,min all results/ollb_score_$1.csv
