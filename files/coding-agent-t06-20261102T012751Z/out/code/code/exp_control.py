"""Controlled comparisons.
 A) 'matched six': the six MT-Bench models also present in Arena-55k (gpt-4-0314,
    claude-1, gpt-3.5-turbo-0314, vicuna-13b, alpaca-13b, llama-13b); crowd votes (n=1367, all
    available), expert votes and GPT-4 judge votes, the latter two subsampled to the same n.
 B) size scaling: random vote subsamples of Arena-55k, MT-Bench human/GPT-4 and NBA seasons.
Writes results/control.csv"""
import numpy as np, pandas as pd, zlib
from multiprocessing import Pool
from bt import *
import datasets as ds

BOARDS = {}
SIX = ['gpt-4-0314', 'claude-1', 'gpt-3.5-turbo-0314', 'vicuna-13b', 'alpaca-13b', 'llama-13b']

def make_tasks():
    T = []
    # A: matched six
    T.append(("A", "arena6", "arena6", None, 0))
    for r in range(30):
        T.append(("A", "mt_human", "mt_human_n1367", 1367, r))
        T.append(("A", "mt_gpt4", "mt_gpt4_n1367", 1367, r))
    T.append(("A", "mt_human", "mt_human_full", None, 0))
    T.append(("A", "mt_gpt4", "mt_gpt4_full", None, 0))
    for r in range(30):   # arena-6 bootstrap-free replicates: resample votes
        T.append(("A", "arena6", "arena6_boot", "boot", r))
    # B: size scaling
    for n in (3000, 6000, 12000, 24000):
        for r in range(8):
            T.append(("B", "arena", f"arena_n{n}", n, r))
    T.append(("B", "arena", "arena_full", None, 0))
    for n in (500, 1000, 2000):
        for r in range(20):
            T.append(("B", "mt_human", f"mt_human_n{n}", n, r))
            T.append(("B", "mt_gpt4", f"mt_gpt4_n{n}", n, r))
    for yr in range(1990, 2016):
        for frac in (0.25, 0.5, 1.0):
            for r in range(3 if frac < 1 else 1):
                T.append(("B", f"nba{yr}", f"nba_frac{frac}", frac, r))
    return T

def run(t):
    part, key, label, size, rep = t
    rng = np.random.default_rng(zlib.crc32(f"{label}{rep}".encode()))
    b = BOARDS[key]
    if size == "boot":
        b = b.with_counts(rng.multinomial(b.n, (b.N / b.n).ravel()).reshape(b.N.shape))
    elif size is not None:
        n = int(size * b.n) if isinstance(size, float) and size <= 1 else int(size)
        b = b.subsample(n, rng)
    th = b.fit(); s = th[: b.m]; o = np.argsort(-s)
    pairs = {(o[r], o[r + 1]) for r in range(b.m - 1)}
    allp = [(o[a], o[c]) for a in range(b.m) for c in range(a + 1, b.m)]
    if len(allp) > 150:
        idx = rng.choice(len(allp), 150, replace=False); pairs |= {allp[x] for x in idx}
    else:
        pairs |= set(allp)
    rows = []
    for (i, j) in pairs:
        rows += pair_records(b, th, int(i), int(j), modes=("flip",), extra=dict(part=part, label=label, rep=rep, board=key))
    return rows

if __name__ == "__main__":
    a = ds.arena55k(); BOARDS["arena"] = a
    BOARDS["arena6"] = a.restrict([a.names.index(x) for x in SIX], "arena6")
    BOARDS["mt_human"] = ds.mtbench_human(); BOARDS["mt_gpt4"] = ds.mtbench_gpt4()
    for yr, b in ds.nba_seasons().items(): BOARDS[f"nba{yr}"] = b
    T = make_tasks(); print(len(T), "tasks", flush=True)
    with Pool(30) as p:
        out = sum(p.map(run, T, chunksize=1), [])
    pd.DataFrame(out).to_csv("/work/results/control.csv", index=False)
    print("done")
