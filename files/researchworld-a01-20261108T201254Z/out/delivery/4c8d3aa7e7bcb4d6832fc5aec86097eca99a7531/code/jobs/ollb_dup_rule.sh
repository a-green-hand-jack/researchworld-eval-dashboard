# duplicate-name rule variants (#6.3a): headline cells under each rule. Usage: jobs/ollb_dup_rule.sh first|latest|worst
cd "$(dirname "$0")/.."
MTI_OLLB_CSV=data/processed/ollb6_dup_$1.csv.gz jobs/_run.sh ollb_dup_$1 src/run_core.py ollb ceil,emp95 mean,median,min all results/ollb_dup_$1.csv
