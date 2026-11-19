"""T1 pair design (ranking flips): two systems A and B are each tuned (exhaustive search over their own disjoint K_A / K_B candidates drawn from the
300-candidate set) on the SAME search set D, then compared with a reporting method. Truth: the two selected configs' accuracy on the fresh set.
usage: t1_pairs.py MODEL N [--reps R] -> results/t1pairs/MODEL.n{N}.methods.parquet and .runs.parquet  (cell ids 'pair|n=|KA=|KB=|A' and '|B')"""
import sys, os, zlib, argparse, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import configs as C, lib, methods, t1
SEED = 20261104
PAIRS = ((5, 5), (75, 5), (75, 75), (24, 24))   # (K_A, K_B), disjoint candidate subsets of the 300

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("model"); ap.add_argument("n", type=int); ap.add_argument("--reps", type=int, default=1000)
    ap.add_argument("--n_pool", type=int, default=2000); ap.add_argument("--chunk", type=int, default=250); ap.add_argument("--out", default="/hutian/repo/results/t1pairs")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    L, pool = t1.load_matrix(a.model, a.n_pool, a.chunk); test = C.load_test(); Y, names = t1.correctness(L, test.answer_index.values[pool]); N = Y.shape[1]
    runs, meths = [], []
    for KA, KB in PAIRS:
        cid = f"pair|n={a.n}|KA={KA}|KB={KB}"
        for rep in range(a.reps):
            rng = np.random.default_rng([SEED, zlib.crc32(cid.encode()), rep])
            perm = rng.permutation(Y.shape[0]); selA, selB = perm[:KA], perm[KA:KA + KB]
            blk = rep % t1.G; avail = np.flatnonzero(np.arange(N) % t1.G != blk); D = rng.choice(avail, a.n, replace=False); F = np.setdiff1d(avail, D)
            for side, sel in (("A", selA), ("B", selB)):
                th = Y[np.ix_(sel, F)].mean(1)
                run, rows = methods.run_methods(Y[np.ix_(sel, D)], th, "exhaustive", (len(sel),), rng, opts=dict(m3_B=0))
                meta = dict(tier="T1pair", cell_id=f"{cid}|{side}", rep=rep, seed=SEED, n=a.n, K=len(sel), procedure="exhaustive", block=blk, n_fresh=len(F))
                runs.append({**meta, **run}); meths += [{**{k: meta[k] for k in ("tier", "cell_id", "rep", "n", "K", "procedure")}, **r} for r in rows]
        print(f"HUTIAN_PROGRESS {cid}", flush=True)
    tag = f"{a.out}/{a.model}.n{a.n}"; pd.DataFrame(runs).to_parquet(tag + ".runs.parquet"); pd.DataFrame(meths).to_parquet(tag + ".methods.parquet")
