"""E1/E3 on the Open LLM Leaderboard boards. usage: run_e1_ollb.py BOARD(m6|m6raw|m39) OUT.csv [shard n_shards] [unit]
Targets: top-30 under the official mean among the main slice (non-merged, non-flagged, on-hub), plus (optionally) a rank-stratified sample."""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, pandas as pd
from lbprice.e1 import run_board
from lbprice.boards import load_ollb
name, out = sys.argv[1], sys.argv[2]
shard, ns = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (0, 1)
unit = sys.argv[5] if len(sys.argv) > 5 else "points"
b = load_ollb(name, slice_="main")
S = b["S"]; order = np.argsort(-S.mean(axis=1) if name != "m39" else -b["official"])
top = list(order[:30]); targets = [t for k, t in enumerate(top) if k % ns == shard]
t0 = time.time()
res = run_board(b, targets, unit=unit, tl=60.0, log=lambda s: print(s, round(time.time() - t0), flush=True))
res["board"] = name; res["model"] = [b["names"][t] for t in res.target]
res.to_csv(out, index=False); print("done", len(res), round(time.time() - t0), flush=True)
