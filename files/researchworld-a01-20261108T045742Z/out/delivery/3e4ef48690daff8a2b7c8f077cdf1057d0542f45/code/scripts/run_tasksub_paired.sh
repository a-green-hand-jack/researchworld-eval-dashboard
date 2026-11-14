cd /hutian/repo
for c in gain10 front2; do python3 src/run_robust.py tasksub helm mean,geomean,median,min,borda,plurality $c results/helm_tasksubpaired_$c.csv --R 200 --targets mean > logs/helm_tasksubpaired_$c.log 2>&1 & done; wait
