"""Vote-level bootstrap replicates (Arena-55k, MT-Bench human, MT-Bench GPT-4) for
uncertainty of leaderboard-level fragility statistics.  In every replicate the board is
refit, and minimal edits are computed for: all rank-adjacent pairs, all pairs among
the top-10, and 300 uniformly random pairs ('rand' rows are a uniform sample of all pairs).  Writes results/boot.csv"""
import numpy as np, pandas as pd, sys
from multiprocessing import Pool
from bt import *
import datasets as ds

B = 30
BOARDS = {}

def one(args):
    key, rep = args
    b0 = BOARDS[key]
    rng = np.random.default_rng(1000 * rep + {"arena": 1, "mt_human": 2, "mt_gpt4": 3}[key])
    Nb = rng.multinomial(b0.n, (b0.N / b0.n).ravel()).reshape(b0.N.shape)
    b = b0.with_counts(Nb); th = b.fit(); s = th[: b.m]; o = np.argsort(-s)
    struct = {(o[r], o[r + 1]) for r in range(b.m - 1)}
    top = min(10, b.m)
    struct |= {(o[a], o[c]) for a in range(top) for c in range(a + 1, top)}
    allp = [(o[a], o[c]) for a in range(b.m) for c in range(a + 1, b.m)]
    nr = min(len(allp), 300)
    rnd_idx = rng.choice(len(allp), nr, replace=False)
    rand = {allp[x] for x in rnd_idx}
    rows = []
    for (i, j) in struct | rand:
        src = "rand" if (i, j) in rand else "struct"   # 'rand' = uniform sample of all pairs
        rows += pair_records(b, th, int(i), int(j), extra=dict(board=key, rep=rep, src=src))
    return rows

if __name__ == "__main__":
    BOARDS["arena"] = ds.arena55k(); BOARDS["mt_human"] = ds.mtbench_human(); BOARDS["mt_gpt4"] = ds.mtbench_gpt4()
    tasks = [(k, r) for r in range(B) for k in BOARDS]
    with Pool(30) as p:
        out = sum(p.map(one, tasks, chunksize=1), [])
    pd.DataFrame(out).to_csv("/work/results/boot.csv", index=False)
