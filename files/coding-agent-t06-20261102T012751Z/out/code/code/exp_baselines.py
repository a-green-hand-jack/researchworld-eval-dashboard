"""Search-strategy baselines for the order-reversal budget (relabel / delete / insert):
  greedy  : all votes, ranked by first-order influence, refit between batches (our method)
  touch   : only votes involving i or j, ranked by influence
  direct  : only votes between i and j
  random  : random helpful edits among votes involving i or j (no influence ranking)
Writes results/baselines.csv"""
import numpy as np, pandas as pd, zlib
from multiprocessing import Pool
from bt import *
import datasets as ds

BOARDS = {}
def task(a):
    key, i, j = a
    b = BOARDS[key]; th = b.fit(); rng = np.random.default_rng(zlib.crc32(f"{key}{i}{j}".encode()))
    touch = (b.pairs[:, 0] == i) | (b.pairs[:, 1] == i) | (b.pairs[:, 0] == j) | (b.pairs[:, 1] == j)
    direct = ((b.pairs[:, 0] == i) & (b.pairs[:, 1] == j)) | ((b.pairs[:, 0] == j) & (b.pairs[:, 1] == i))
    se = b.ij_se(th, i, j); z = (th[i] - th[j]) / se
    rows = []
    for kind in ("relabel", "drop", "insert"):
        mk = int(0.3 * b.n)
        res = dict(greedy=min_edits(b, i, j, kind, mk, th0=th)["k"],
                   touch=min_edits(b, i, j, kind, mk, th0=th, allowed=touch)["k"],
                   direct=min_edits(b, i, j, kind, mk, th0=th, allowed=direct)["k"])
        rr = [min_edits(b, i, j, kind, mk, th0=th, allowed=touch, rng=np.random.default_rng(rng.integers(1 << 30)))["k"] for _ in range(3)]
        res["random"] = float(np.median(rr))
        for k, v in res.items():
            rows.append(dict(board=key, i=i, j=j, z=z, n=b.n, kind=kind, strategy=k, k=v))
    return rows

if __name__ == "__main__":
    rng = np.random.default_rng(5)
    BOARDS["arena"] = ds.arena55k(); BOARDS["mt_human"] = ds.mtbench_human(); BOARDS["mt_gpt4"] = ds.mtbench_gpt4()
    nb = ds.nba_seasons()
    for yr in (1960, 1975, 1990, 2005, 2015): BOARDS[f"nba{yr}"] = nb[yr]
    T = []
    for key, b in BOARDS.items():
        s = b.fit()[: b.m]
        allp = [(i, j) for i in range(b.m) for j in range(b.m) if s[i] > s[j]]
        sel = allp if len(allp) <= 150 else [allp[x] for x in rng.choice(len(allp), 150, replace=False)]
        T += [(key, i, j) for i, j in sel]
    with Pool(30) as p:
        out = sum(p.map(task, T, chunksize=2), [])
    pd.DataFrame(out).to_csv("/work/results/baselines.csv", index=False)
    print("done", len(out))
