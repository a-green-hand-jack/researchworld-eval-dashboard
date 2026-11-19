"""Synthetic study following story-repo/PLAN.md section 3: one-factor-at-a-time (OFAT) around a reference cell, an n x K x tau interaction
grid, and stress cells. usage: run_synth3.py SHARD NSHARDS OUTDIR"""
import sys, os, numpy as np, pandas as pd, time, warnings; warnings.filterwarnings("ignore")
from synth import make_pool; from run_grid import run
shard, nsh, outdir = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]; os.makedirs(outdir, exist_ok=True)
REF = dict(n=200, K=16, tau=0.01, rho=0.5, m=0.3, proc="argmax", eps=0.0, leak=0, outlier=0.0)
cells = []
def add(kind, **ch):
    c = dict(REF); c.update(ch); c["kind"] = kind; c["M"] = 2000 if kind in ("ofat", "stress") else 500; cells.append(c)
add("ofat")
for n in (50, 100, 500, 1000, 2000): add("ofat", n=n)
for K in (2, 4, 8, 32, 64, 128): add("ofat", K=K)
for t in (0.0, 0.005, 0.03): add("ofat", tau=t)
for r in (0.0, 0.3, 0.6, 0.9): add("ofat", rho=r)
for m in (0.1, 0.5, 0.8): add("ofat", m=m)
for p in ("sh", "sr"): add("ofat", proc=p)
add("ofat", proc="greedy", K=128)
for e in (0.1, 0.2): add("ofat", eps=e)
for l in (3, 8): add("ofat", leak=l)
for o in (0.03, 0.05):
    for K in (16, 128): add("stress", outlier=o, tau=0.0, K=K)
add("stress", n=50, K=128, tau=0.0, m=0.1)          # K >> sqrt(n), near chance
for n in (100, 200, 500, 1000):
    for K in (4, 16, 64):
        for t in (0.0, 0.01, 0.03):
            for p in ("argmax", "sh"): add("inter", n=n, K=K, tau=t, proc=p)
mine = [c for i, c in enumerate(cells) if i % nsh == shard]; t0 = time.time()
for ci, c in enumerate(mine):
    name = "_".join(f"{k}{v}" for k, v in c.items() if k not in ("M",))
    f = f"{outdir}/{name}.parquet"
    if os.path.exists(f): continue
    Y = make_pool(128, 20000, m=c["m"], tau=c["tau"], rho=c["rho"], seed=7, outlier=c["outlier"])
    ests = ["naive", "split", "crossfit", "boot_opt", "simul"] + (["cond"] if c["proc"] == "argmax" else [])
    K = c["K"]
    d = run(Y, 0, [c["proc"]], [c["n"]], [K], ests, c["M"], seed=100 + cells.index(c), grid=(8, 4, 4),
            est_kw=dict(boot_opt=dict(B=100), simul=dict(B=200)), tag=name, eps=c["eps"], leak_m=c["leak"])
    for k, v in c.items(): d["f_" + k] = v
    d.to_parquet(f); print(ci + 1, "/", len(mine), name, round(time.time() - t0), flush=True)
