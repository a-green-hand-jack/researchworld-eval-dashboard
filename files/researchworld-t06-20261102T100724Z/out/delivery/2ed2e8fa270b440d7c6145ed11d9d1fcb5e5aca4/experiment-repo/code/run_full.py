"""Full-data boards: data summary, k* for C1-C4 x P1-P3, B1 random curves, B2 bootstrap/subsample flips.
Usage: python3 -I run_full.py [pilot]   -> results/data_summary.csv, kstar_full.csv, random_curve.csv, boot_flip.csv"""
import sys, os, time
import numpy as np, pandas as pd
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datasets import *
from experiments import *
import provenance as pv

SEED = 20261102
KGRID = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000]
BOOT = 300


def boards(pilot=False):
    out = []   # (label, design, board_builder)
    nbad = nba()
    out.append(("nba_2015", "sports", lambda: nba_season_board(nbad, 2015, True)))
    d, nm = mtbench("human")
    out.append(("mtbench_human", "expert", lambda: mt_board(d, nm)))
    if pilot:
        return out
    g, _ = mtbench("gpt4")
    out.append(("mtbench_gpt4", "model-judge", lambda: mt_board(g, nm)))
    mm, nm2 = mt_matched()
    for k, des in (("h", "expert"), ("g", "model-judge"), ("h1", "expert")):
        out.append((f"mtmatched_{k}", des, lambda k=k: mt_board(mm[k], nm2)))
    a, an = arena55k()
    out.append(("arena55k", "crowd", lambda: arena_board(a, an)))
    for y in (1950, 1970, 1990, 2005, 2010):
        out.append((f"nba_{y}", "sports", lambda y=y: nba_season_board(nbad, y, True)))
    return out


_B = None


def work(k):
    global _B
    if _B is None:
        _B = boards(PILOT)
    label, design, mk = _B[k]
    t0 = time.time()
    B = mk()
    beta = B.fit()
    rng = np.random.default_rng([SEED, k])
    rows = claim_rows(B, beta)
    for r in rows:
        r.update(board=label, design=design, unit_type="full", unit_id=0)
    big = B.N > 20000
    curves = []
    ks = [x for x in KGRID if x < 0.2 * B.N]
    nrep = 100 if big else 200
    for kind in ("remove", "flip"):
        for r in random_curve(B, beta, ks, nrep, kind, rng):
            r.update(board=label, design=design, N=B.N)
            curves.append(r)
    boots = []
    for frac in (1.0, 0.5):
        for r in resample_curve(B, beta, BOOT if not big else 200, rng, frac):
            r.update(board=label, design=design, N=B.N)
            boots.append(r)
    summ = dict(board=label, design=design, N=B.N, n_participants=B.P, n_cells=B.n_cells,
                cmp_per_participant=2 * B.N / B.P, tie_rate=float(B.T.sum() / B.N),
                score_range=float(beta[:B.P].max() - beta[:B.P].min()), score_sd=float(beta[:B.P].std()),
                top1=B.names[int(np.argmax(beta[:B.P]))])
    print(f"HUTIAN_WAKE: {label} done {time.time()-t0:.0f}s", flush=True)
    return rows, curves, boots, summ


PILOT = len(sys.argv) > 1 and sys.argv[1] == "pilot"

if __name__ == "__main__":
    n = len(boards(PILOT))
    with Pool(2) as p:
        res = p.map(work, range(n), chunksize=1)
    sfx = "_pilot" if PILOT else ""
    src = [f"{DATA}/arena55k/train.csv", f"{DATA}/nba/nbaallelo.csv"] + sorted(
        f"{DATA}/mtbench/{f}" for f in os.listdir(f"{DATA}/mtbench"))
    pv.save(pd.DataFrame([r for x in res for r in x[0]]), f"kstar_full{sfx}.csv", "run_full.py", SEED, src)
    pv.save(pd.DataFrame([r for x in res for r in x[1]]), f"random_curve{sfx}.csv", "run_full.py", SEED, src)
    pv.save(pd.DataFrame([r for x in res for r in x[2]]), f"boot_flip{sfx}.csv", "run_full.py", SEED, src)
    pv.save(pd.DataFrame([x[3] for x in res]), f"data_summary{sfx}.csv", "run_full.py", SEED, src)
