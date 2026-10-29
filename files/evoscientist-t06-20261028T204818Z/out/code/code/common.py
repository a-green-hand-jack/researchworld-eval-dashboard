"""Shared helpers for experiment scripts."""
import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import numpy as np  # noqa: E402

import btlib as bt  # noqa: E402
import datasets as D  # noqa: E402

ROOT = D.ROOT
RES = os.path.join(ROOT, "artifacts", "results")
FIG = os.path.join(ROOT, "artifacts", "figures")
os.makedirs(RES, exist_ok=True)
os.makedirs(FIG, exist_ok=True)

N_WORKERS = int(os.environ.get("N_WORKERS", "8"))
LAM = 0.01

DESIGN_ORDER = ["crowd", "llm-judge", "expert", "sports"]


def table(d, all_pairs=False):
    return bt.build_table(d["a"], d["b"], d["y"], h=d["h"], use_home=d["use_home"], all_pairs=all_pairs)


def move_profile(tt, moves, i, j):
    """Describe a perturbation: share of moved comparisons that involve i or j, are head-to-head,
    are ties, and are 'favourable to i' (i won or j lost) before the move."""
    if not moves:
        return {}
    tot = inv_i = inv_j = h2h = ties = fav = 0.0
    for s, d, c in moves:
        t = s if s >= 0 else d
        a, b, y = tt.a[t], tt.b[t], tt.y[t]
        tot += c
        ii = (a == i) or (b == i)
        jj = (a == j) or (b == j)
        inv_i += c * ii
        inv_j += c * jj
        h2h += c * (ii and jj)
        ties += c * (y == 0.5)
        # outcome from i's / j's perspective
        if a == i:
            fav += c * (y == 1.0)
        elif b == i:
            fav += c * (y == 0.0)
        elif a == j:
            fav += c * (y == 0.0)
        elif b == j:
            fav += c * (y == 1.0)
    return dict(share_involve_i=inv_i / tot, share_involve_j=inv_j / tot, share_h2h=h2h / tot,
                share_ties=ties / tot, share_fav_i=fav / tot,
                share_involve_either=(inv_i + inv_j - h2h) / tot)


def pool_map(fn, items, workers=None):
    workers = workers or N_WORKERS
    if workers <= 1:
        return [fn(x) for x in items]
    import multiprocessing as mp
    import sys
    import time
    ctx = mp.get_context("fork")
    out = [None] * len(items)
    t0 = time.time()
    with ctx.Pool(workers) as p:
        for done, (k, r) in enumerate(p.imap_unordered(_indexed, [(fn, k, x) for k, x in enumerate(items)]), 1):
            out[k] = r
            if done % max(1, len(items) // 20) == 0 or done == len(items):
                print(f"  progress {done}/{len(items)} ({time.time() - t0:.0f}s)", file=sys.stderr, flush=True)
    return out


def _indexed(args):
    fn, k, x = args
    return k, fn(x)
