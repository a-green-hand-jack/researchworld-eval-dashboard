cd "$(dirname "$0")/.."
R=mean,geomean,median,min,borda,condorcet,plurality
jobs/_run.sh helm_noise src/run_robust.py noise helm $R gain10 results/helm_noise_gain10.csv --R 100
jobs/_run.sh helm_taskboot src/run_robust.py taskboot helm $R gain10 results/helm_taskboot_gain10.csv --R 100
jobs/_run.sh helm_tasksub src/run_robust.py tasksub helm mean,geomean,median,min,borda,plurality ceil results/helm_tasksub_ceil.csv --R 50
