cd /hutian/repo
R=mean,geomean,harmonic,median,min
python3 src/run_core.py ollb ceil,front2,gain10 $R all results/ollb_margin1_score.csv --eps 0.96 > logs/ollb_margin1_score.log 2>&1 &
python3 src/run_core.py ollb ceil,front2,gain10 $R all results/ollb_margin_score.csv --eps 1.92 > logs/ollb_margin2_score.log 2>&1 &
python3 src/run_core.py ollb emp99 borda,condorcet,plurality top20 results/ollb_ordinal_emp99_top20.csv > logs/ollb_ordinal_emp99_top20.log 2>&1 &
wait
