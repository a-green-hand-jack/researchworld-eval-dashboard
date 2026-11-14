"""Studentized-bootstrap (bootstrap-t) intervals for classical / PPI++ / cross-fitted linear AIPW on the real populations.
usage: python run_boot.py --reps 500 --B 399 --out ../results/boot.csv.gz
"""
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
import argparse, zlib, time
import numpy as np, pandas as pd
from multiprocessing import Pool
from datasets import REAL, get_pop
import fast
from run_experiments import BASE_SEED

NS = [25, 50, 100, 200, 500]; N_UNL = 5000
FNS = {"classical": fast.classical, "ppi++": fast.ppi_pp, "aipw-lin": fast.aipw_lin}
_P = {}


def one(args):
    name, n, rep, B = args
    if name not in _P: _P[name] = get_pop(name)
    pop = _P[name]
    rng = np.random.default_rng(np.random.SeedSequence([BASE_SEED, 4242, zlib.crc32(name.encode()), n, rep]))
    Y, F, _ = pop.draw(rng, n); _, Fu, _ = pop.draw(rng, N_UNL)
    rows = []
    for m, fn in FNS.items():
        lo, hi, th, se = fast.boot_t_interval(fn, Y, F, Fu, rng, B=B)
        z = 1.959964
        rows.append(dict(dataset=name, n=n, N=N_UNL, rep=rep, method=m, est=th, se=se, truth=pop.truth,
                         lo_bt=lo, hi_bt=hi, lo_z=th - z * se, hi_z=th + z * se))
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--reps", type=int, default=500); ap.add_argument("--B", type=int, default=399)
    ap.add_argument("--out", required=True); ap.add_argument("--procs", type=int, default=38)
    a = ap.parse_args()
    tasks = [(d, n, r, a.B) for d in REAL for n in NS for r in range(a.reps)]
    t0 = time.time()
    with Pool(a.procs) as p:
        rows = [x for rr in p.imap_unordered(one, tasks, chunksize=10) for x in rr]
    pd.DataFrame(rows).to_csv(a.out, index=False); print("done %.0fs" % (time.time() - t0))
