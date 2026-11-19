cd "$(dirname "$0")/.."
jobs/_run.sh ollb_eps0.1 src/run_core.py ollb gain10 borda,plurality sample results/ollb_eps0.1.csv --nsample 150 --eps 0.1
jobs/_run.sh ollb_notie src/run_core.py ollb gain10 borda,plurality sample results/ollb_notie.csv --nsample 150 --no-tie-levels
