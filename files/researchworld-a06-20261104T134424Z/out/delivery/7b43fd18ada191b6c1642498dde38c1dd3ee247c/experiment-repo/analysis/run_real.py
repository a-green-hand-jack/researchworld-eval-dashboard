"""Real-LLM replication study on the cached correctness matrix. usage: run_real.py POOLNAME OUT [M]"""
import os, sys, json, numpy as np, pandas as pd, time
from run_grid import run
pool = sys.argv[1]; out = sys.argv[2]; M = int(sys.argv[3]) if len(sys.argv) > 3 else 1000
HERE = os.path.dirname(os.path.abspath(__file__)); d = np.load(os.environ.get("MATRIX", os.path.join(HERE, "..", "results", "matrix.npz"))); Yall = d["Y"]; cfg_idx = d["cfg_idx"]; allcfgs = json.load(open(os.path.join(HERE, "..", "code", "config_pool.json"))); cfgs = [allcfgs[i] for i in cfg_idx]
DISJ = len(sys.argv) > 4 and sys.argv[4] == "disjoint"
sel = {"full60": lambda c: True,
       "shot3": lambda c: c["demo_id"] > 0,
       "shot3_plain": lambda c: c["demo_id"] > 0 and c["layout"] == "plain",
       "instr_only": lambda c: c["demo_id"] == 1 and c["layout"] == "plain"}[pool]
idx = [i for i, c in enumerate(cfgs) if sel(c)]; Y = Yall[idx]
base = [i for i, c in enumerate(cfgs) if c['instr'] == 0 and c['demo_id'] == 1 and c['layout'] == 'plain']
base = idx.index(base[0]) if base and base[0] in idx else 0   # baseline: instr 0, 3-shot demo set 1, plain layout ("hand-written default")
Kp = len(Y); Ks = [k for k in (1, 2, 4, 8, 16, 32, 60) if k <= Kp]
if Kp not in Ks: Ks.append(Kp)
ests = ["naive", "split", "crossfit", "boot_opt", "simul", "cond", "hybrid"]
grid = (6, 5, 2) if (pool == "full60" and len(cfg_idx) == 60) else None
procs = ["argmax", "sh", "sr"] + (["greedy"] if grid else [])
NS = [50, 100, 200, 400] if DISJ else [50, 100, 200, 400, 800]   # disjoint arm: n <= N/4 (truth = pool minus T)
df = run(Y, base, procs, NS, Ks, ests, M, seed=5, grid=grid,
         est_kw=dict(boot_opt=dict(B=100), simul=dict(B=200)), tag=pool + ("_disjoint" if DISJ else ""), disjoint=DISJ)
df["pool"] = pool; df.to_parquet(out); print("done", len(df))
