"""E1/E3 on HELM MMLU (79 models x 57 subjects). usage: run_e1_helm.py OUT.csv [shard n_shards] [unit]"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, pandas as pd
from lbprice.e1 import run_board
out = sys.argv[1]; shard, ns = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (0, 1)
unit = sys.argv[4] if len(sys.argv) > 4 else "points"
df = pd.read_csv("data_proc/helm_mmlu_em.csv", index_col=0)
board = dict(S=df.values * 100.0, ceil=100.0, names=list(df.index))
targets = [t for t in range(len(df)) if t % ns == shard]
t0 = time.time()
res = run_board(board, targets, unit=unit, tl=30.0, log=lambda s: print(s, round(time.time() - t0), flush=True))
res["board"] = "helm"; res["model"] = [df.index[t] for t in res.target]
res.to_csv(out, index=False); print("done", len(res), round(time.time() - t0))
