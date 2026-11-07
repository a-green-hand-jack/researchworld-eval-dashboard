"""s4 size/sparsity-matched Arena subsets and the Arena size curve. -> results/matched_arena.csv
unit_type: mt_dense (6 heavily-battled models, N=3355 votes, = MT-Bench-h), mt_random6 (6 random models, all their
mutual votes), nba_like (30 random models, N=1230 votes, = one NBA season), sizecurve (all 64 models, N subsampled)."""
import sys, os, time, itertools, functools
import numpy as np, pandas as pd
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datasets import *
from experiments import *
from btlib import Board
import provenance as pv

SEED = 20261104
_A = None


def arena():
    global _A
    if _A is None:
        a, names = arena55k()
        P = len(names)
        M = np.zeros((P, P))
        for x, y in zip(a.a.values, a.b.values):
            M[x, y] += 1; M[y, x] += 1
        _A = (a, names, M)
    return _A


def sub_board(a, names, models, idx):
    """Board on `models` from the rows `idx` of the arena frame (all rows must be among `models`)."""
    ix = {m: k for k, m in enumerate(models)}
    d = a.iloc[idx]
    return board_from_records(d.a.map(ix).values, d.b.map(ix).values, d.o.values, len(models),
                              [names[m] for m in models])


def induced(a, models):
    s = set(models)
    return np.where(a.a.isin(s).values & a.b.isin(s).values)[0]


@functools.lru_cache(None)
def valid_subsets():
    a, names, M = arena()
    top = np.argsort(-M.sum(1))[:14]
    out = []
    for S in itertools.combinations(top, 6):
        S = list(S)
        sub = M[np.ix_(S, S)]
        if sub.sum() / 2 >= 3355 and sub[np.triu_indices(6, 1)].min() >= 30:
            out.append(S)
    return out


def unit(args):
    kind, rep, param = args
    a, names, M = arena()
    rng = np.random.default_rng([SEED, ["mt_dense", "mt_random6", "nba_like", "sizecurve"].index(kind), rep, param])
    P = len(names)
    if kind == "mt_dense":
        S = valid_subsets()[rng.integers(len(valid_subsets()))]
        pool = induced(a, S)
        idx = rng.choice(pool, 3355, replace=False)
    elif kind == "mt_random6":
        while True:
            S = list(rng.choice(P, 6, replace=False))
            sub = M[np.ix_(S, S)]
            if sub[np.triu_indices(6, 1)].min() >= 3:
                break
        idx = induced(a, S)
    elif kind == "nba_like":
        S = list(rng.choice(P, 30, replace=False))
        idx = rng.choice(induced(a, S), 1230, replace=False)
    else:  # sizecurve
        S = list(range(P))
        idx = rng.choice(len(a), param, replace=False)
    B = sub_board(a, names, S, idx)
    deg = np.zeros(B.P)
    np.add.at(deg, B.i, B.W + B.L + B.T); np.add.at(deg, B.j, B.W + B.L + B.T)
    if deg.min() < 5:  # disconnected / near-empty participant: skip (counted in manifest note)
        return []
    beta = B.fit()
    rows = claim_rows(B, beta, claims=("C1", "C2", "C4"))
    for r in rows:
        r.update(board="arena55k_sub", design="crowd", unit_type=kind, unit_id=rep, n_sub=param,
                 score_sd=float(beta[:B.P].std()), cmp_per_participant=2 * B.N / B.P)
    return rows


if __name__ == "__main__":
    tasks = [("mt_dense", r, 0) for r in range(100)] + [("mt_random6", r, 0) for r in range(100)] + \
            [("nba_like", r, 0) for r in range(100)] + \
            [("sizecurve", r, n) for n in (1000, 2000, 5000, 10000, 20000, 40000) for r in range(30)]
    with Pool(2) as p:
        res = p.map(unit, tasks, chunksize=2)
    src = [f"{DATA}/arena55k/train.csv"]
    pv.save(pd.DataFrame([r for x in res for r in x]), "matched_arena.csv", "run_matched.py", SEED, src,
            note="hash-free seeds: kind index; subsets with a participant of <5 comparisons are skipped")
