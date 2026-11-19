cd "$(dirname "$0")/.."
for d in ollb_raw ollb_nomerge ollb_top500; do
jobs/_run.sh ${d}_variants src/run_core.py $d ceil,gain10 trimmed1,mean,geomean,median,min,borda,plurality sample results/${d}_variants.csv --nsample 60
done
