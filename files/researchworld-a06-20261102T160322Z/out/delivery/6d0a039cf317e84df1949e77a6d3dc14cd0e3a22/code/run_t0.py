"""T0 grid runner.  usage: run_t0.py SHARD NSHARDS [--reps R] [--only PATTERN]  -> results/t0/shard{S}.{runs,methods}.parquet
Cells are defined in grid(); seeds derive from (SEED, crc32(cell_id), rep)."""
import sys, os, time, itertools, argparse, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import t0
SEED = 20261102

def cid(**k): return "|".join(f"{a}={b}" for a, b in k.items())

def grid():
    cells = []
    def add(n, K, tau, rho=0.6, acc=0.3, proc="exhaustive", m3=False, reps=1000, leak=0):
        cells.append(dict(cell_id=cid(n=n, K=K, tau=tau, rho=rho, acc=acc, proc=proc) + ("|leak=1" if leak else ""), leak=leak, n=n, K=K, tau=tau, rho=rho, base_acc=acc,
                          procedure=proc, m3_B=100 if m3 else 0, reps=300 if m3 else reps))
    for n in (50, 100, 200, 500, 1000, 2000):          # main grid, exhaustive search
        for K in (2, 5, 20, 50, 200):
            for tau in (0.0, 0.05, 0.1, 0.2): add(n, K, tau)
    for rho in (0.2, 0.9):
        for tau in (0.0, 0.1): add(200, 50, tau, rho=rho)
    for acc in (0.15, 0.5):
        for tau in (0.0, 0.1): add(200, 50, tau, acc=acc)
    for proc in ("halving", "greedy"):                  # adaptive procedures
        for n in (100, 200, 500):
            for K in (20, 50, 200):
                for tau in (0.0, 0.1, 0.2): add(n, K, tau, proc=proc)
    for n in (50, 200, 1000):                           # bootstrap optimism (expensive): subset, fewer reps
        for K in (5, 50, 200):
            for tau in (0.0, 0.1): add(n, K, tau, m3=True, reps=300)
    for n in (50, 100, 200, 500):                        # leakage of few-shot demos from D (appended last: existing shard indices unchanged)
        for tau in (0.0, 0.1): add(n, 24, tau, leak=1); add(n, 24, tau)   # with / without leakage
    for c in cells:
        if c["m3_B"]: c["cell_id"] += "|m3"
    seen = set(); out = []
    for c in cells:
        if c["cell_id"] not in seen: seen.add(c["cell_id"]); out.append(c)
    return out

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("shard", type=int); ap.add_argument("nshards", type=int)
    ap.add_argument("--reps", type=int, default=None); ap.add_argument("--only", default=None); ap.add_argument("--out", default="/hutian/repo/results/t0")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    cells = [c for i, c in enumerate(grid()) if i % a.nshards == a.shard and (a.only is None or a.only in c["cell_id"])]
    runs, meths = [], []; t00 = time.time(); cost = []
    for c in cells:
        t = time.time(); R, M = t0.run_cell(c, a.reps or c["reps"], SEED, opts=dict(m3_B=c["m3_B"]))
        runs += R; meths += M; cost.append(dict(cell_id=c["cell_id"], seconds=time.time() - t, reps=a.reps or c["reps"]))
        print(f"HUTIAN_PROGRESS {len(cost)}/{len(cells)} {c['cell_id']} {time.time()-t:.0f}s", flush=True)
        if len(cost) % 10 == 0 or len(cost) == len(cells):
            pd.DataFrame(runs).to_parquet(f"{a.out}/shard{a.shard}.runs.parquet"); pd.DataFrame(meths).to_parquet(f"{a.out}/shard{a.shard}.methods.parquet")
            pd.DataFrame(cost).to_csv(f"{a.out}/shard{a.shard}.cost.csv", index=False)
