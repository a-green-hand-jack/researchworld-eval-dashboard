cd "$(dirname "$0")/.."
jobs/_run.sh helm_main src/run_core.py helm ceil,front0,front2,gain5,gain10,gain20 mean,geomean,harmonic,pow-5,median,min,borda,condorcet,plurality all results/helm_main.csv
# eps / tie sensitivity (ties as loss = target may only pass a rival by eps)
jobs/_run.sh helm_eps0.1 src/run_core.py helm ceil,gain10 mean,median,borda,condorcet,plurality all results/helm_eps0.1.csv --eps 0.1
jobs/_run.sh helm_notie src/run_core.py helm ceil,gain10 borda,condorcet,plurality all results/helm_notie.csv --no-tie-levels
