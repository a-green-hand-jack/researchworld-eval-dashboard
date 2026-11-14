cd "$(dirname "$0")/.."
jobs/_run.sh ollb_noise src/run_robust.py noise ollb mean,geomean,median,min,plurality gain10 results/ollb_noise_gain10.csv --R 100
jobs/_run.sh ollb_taskboot src/run_robust.py taskboot ollb mean,geomean,median,min,plurality gain10 results/ollb_taskboot_gain10.csv --R 100
