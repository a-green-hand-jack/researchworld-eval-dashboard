# cap-composition caps (#6.1): score rules on all targets, plurality on the rank sample. Usage: jobs/ollb_cap_composition.sh CAP
cd "$(dirname "$0")/.."
jobs/_run.sh ollb_capcomp_score_$1 src/run_core.py ollb $1 mean,median,min all results/ollb_capcomp_score_$1.csv
jobs/_run.sh ollb_capcomp_plurality_$1 src/run_core.py ollb $1 plurality sample results/ollb_capcomp_plurality_$1.csv --nsample 150
