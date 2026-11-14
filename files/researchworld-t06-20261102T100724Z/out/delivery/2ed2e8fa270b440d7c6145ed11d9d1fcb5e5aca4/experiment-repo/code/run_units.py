"""Replicated k*: NBA seasons (unit = season), Arena battle bootstrap, MT-Bench question-cluster bootstrap
(h/g/matched share the same resampled questions).  -> results/kstar_units.csv
Usage: python3 -I run_units.py [nba|arena|mt]  (default all)."""
import sys, os, time
import numpy as np, pandas as pd
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datasets import *
from experiments import *
from btlib import Board
import provenance as pv

SEED = 20261103
R_ARENA, R_MT = 60, 200


def tag(rows, **kw):
    for r in rows:
        r.update(kw)
    return rows


def nba_unit(year):
    n = nba()
    B = nba_season_board(n, year, True)
    return tag(claim_rows(B, B.fit()), board="nba_season", design="sports", unit_type="nba_season", unit_id=year)


def arena_unit(rep):
    a, names = arena55k()
    B0 = arena_board(a, names)
    rng = np.random.default_rng([SEED, 1, rep])
    cnt = rng.multinomial(int(B0.N), np.concatenate([B0.W, B0.L, B0.T]) / B0.N)
    m = B0.n_cells
    B = Board(B0.P, B0.i, B0.j, cnt[:m], cnt[m:2 * m], cnt[2 * m:], names=names)
    return tag(claim_rows(B, B.fit(), claims=("C1", "C2", "C4")), board="arena55k", design="crowd",
               unit_type="boot", unit_id=rep)


def mt_tensor(df, P, qids):
    """counts[q, cell, type] on the 15 unordered pairs (i<j); type 0 = i wins, 1 = j wins, 2 = tie."""
    ii, jj = np.triu_indices(P, 1)
    cell = {(i, j): c for c, (i, j) in enumerate(zip(ii, jj))}
    qix = {q: k for k, q in enumerate(qids)}
    T = np.zeros((len(qids), len(ii), 3))
    for q, a, b, o in zip(df.question_id, df.a, df.b, df.o):
        if a < b:
            c, t = cell[(a, b)], (0 if o == 1 else 1 if o == 0 else 2)
        else:
            c, t = cell[(b, a)], (1 if o == 1 else 0 if o == 0 else 2)
        T[qix[q], c, t] += 1
    return T, ii, jj


def mt_unit(rep):
    mm, names = mt_matched()
    h, _ = mtbench("human")
    g, _ = mtbench("gpt4")
    sets = dict(mtbench_human=h, mtbench_gpt4=g, mtmatched_h=mm["h"], mtmatched_g=mm["g"], mtmatched_h1=mm["h1"])
    qids = sorted(h.question_id.unique())
    rng = np.random.default_rng([SEED, 2, rep])
    w = np.bincount(rng.integers(0, len(qids), len(qids)), minlength=len(qids))   # question multiplicities
    rows = []
    for label, df in sets.items():
        T, ii, jj = mt_tensor(df, len(names), qids)
        C = np.tensordot(w, T, axes=(0, 0))
        B = Board(len(names), ii, jj, C[:, 0], C[:, 1], C[:, 2], names=names)
        des = "model-judge" if label.endswith("gpt4") or label.endswith("_g") else "expert"
        rows += tag(claim_rows(B, B.fit()), board=label, design=des, unit_type="qboot", unit_id=rep)
    return rows


JOBS = {"nba": (nba_unit, list(range(1947, 2016))), "arena": (arena_unit, list(range(R_ARENA))),
        "mt": (mt_unit, list(range(R_MT)))}


def _run(args):
    name, u = args
    t = time.time()
    r = JOBS[name][0](u)
    print(f"HUTIAN_WAKE: {name} {u} {time.time()-t:.0f}s", flush=True) if u % 10 == 0 else None
    return r


if __name__ == "__main__":
    which = sys.argv[1:] or ["nba", "arena", "mt"]
    tasks = [(w, u) for w in which for u in JOBS[w][1]]
    with Pool(2) as p:
        res = p.map(_run, tasks, chunksize=1)
    src = [f"{DATA}/arena55k/train.csv", f"{DATA}/nba/nbaallelo.csv"] + sorted(
        f"{DATA}/mtbench/{f}" for f in os.listdir(f"{DATA}/mtbench"))
    sfx = "" if len(which) == 3 else "_" + "_".join(which)   # kstar_units_nba.csv, kstar_units_arena_mt.csv; merge_units.py joins
    pv.save(pd.DataFrame([r for x in res for r in x]), f"kstar_units{sfx}.csv", "run_units.py", SEED, src)
