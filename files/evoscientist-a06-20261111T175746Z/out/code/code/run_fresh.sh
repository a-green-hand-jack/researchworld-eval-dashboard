# Disjoint 'fresh' question sets scored with the SAME configs (used only to validate the pool-as-population simulation).
./venv/bin/python code/score.py --model Qwen2.5-0.5B-Instruct --quant fp32 --K 32 --N 1000 --skip 1500 --suffix _fresh --maxtok 220 --threads 4 >> results/score_0.5B_fresh.log 2>&1
