cd "$(dirname "$0")/.."
jobs/_run.sh ollb_plurality_sample src/run_core.py ollb ceil,front0,front2,gain5,gain10,gain20,emp95,emp99 plurality sample results/ollb_plurality_sample.csv --nsample 150
jobs/_run.sh ollb_plurality_top500 src/run_core.py ollb ceil,front2,gain10,emp95 plurality top500 results/ollb_plurality_top500.csv
