# Full scoring run (resumable: finished configs are skipped). ~5h (0.5B) + ~6h (1.5B) on a contended ~4-effective-core CPU.
./venv/bin/python code/score.py --model Qwen2.5-0.5B-Instruct --quant fp32 --K 32 --N 1500 --maxtok 220 --threads 4 >> results/score_0.5B.log 2>&1
./venv/bin/python code/score.py --model Qwen2.5-1.5B-Instruct --quant fp32 --K 16 --N 1000 --maxtok 220 --threads 4 >> results/score_1.5B.log 2>&1
