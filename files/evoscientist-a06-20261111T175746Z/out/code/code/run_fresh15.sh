./venv/bin/python code/score.py --model Qwen2.5-1.5B-Instruct --quant fp32 --K 16 --N 600 --skip 1500 --suffix _fresh --maxtok 220 --threads 4 >> results/score_1.5B_fresh.log 2>&1
