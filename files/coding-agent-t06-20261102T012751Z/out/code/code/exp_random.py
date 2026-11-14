"""Random (non-adversarial) perturbation baseline: random vote deletion and random
relabelling (replace label by a uniformly random label) at fraction alpha.
Metrics vs the full-data ranking: Kendall tau, P(adjacent pair reversed),
P(top-1 changes).  Writes results/random.csv"""
import zlib
import numpy as np, pandas as pd
from multiprocessing import Pool
from bt import *
import datasets as ds

ALPHAS = [0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5]
R = 40
BOARDS = {}

def kendall(a, b):
    m = len(a)
    da = np.sign(a[:, None] - a[None, :]); db = np.sign(b[:, None] - b[None, :])
    iu = np.triu_indices(m, 1)
    return float(np.mean(da[iu] * db[iu]))

def run(key):
    b = BOARDS[key]; rng = np.random.default_rng(zlib.crc32(key.encode()))
    th = b.fit(); s = th[: b.m]; order = np.argsort(-s)
    flat = b.N.ravel(); n = b.n
    rows = []
    for mode in ("drop", "relabel"):
        for a in ALPHAS:
            for r in range(R):
                k = int(round(a * n))
                if mode == "drop":
                    N2 = b.N - rng.multivariate_hypergeometric(flat, k).reshape(b.N.shape)
                else:
                    sel = rng.multivariate_hypergeometric(flat, k).reshape(b.N.shape)
                    # distribute new labels over the selected configs uniformly at random
                    N2 = b.N - sel
                    cfgs = np.repeat(np.arange(len(sel)), sel.sum(1))
                    labs = rng.integers(0, 3, size=k)
                    np.add.at(N2, (cfgs, labs), 1)
                s2 = b.fit(N2, th)[: b.m]
                adj = [(order[q], order[q + 1]) for q in range(b.m - 1)]
                rev = [s2[i] < s2[j] for i, j in adj]
                rows.append(dict(board=key, mode=mode, alpha=a, rep=r, tau=kendall(s, s2),
                                 rev_frac=float(np.mean(rev)), top1=int(np.argmax(s2) != order[0]),
                                 n_rev=int(np.sum(rev)), n_adj=len(adj)))
    return rows

if __name__ == "__main__":
    BOARDS["arena"] = ds.arena55k(); BOARDS["mt_human"] = ds.mtbench_human(); BOARDS["mt_gpt4"] = ds.mtbench_gpt4()
    for yr, b in ds.nba_seasons().items(): BOARDS[f"nba{yr}"] = b
    with Pool(30) as p:
        out = sum(p.map(run, list(BOARDS)), [])
    pd.DataFrame(out).to_csv("/work/results/random.csv", index=False)
