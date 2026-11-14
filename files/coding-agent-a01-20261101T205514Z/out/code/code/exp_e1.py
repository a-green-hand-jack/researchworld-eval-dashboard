"""E1: depth/breadth needed to climb from rank r to rank 1, per rule, with parametric-bootstrap CIs.
usage: exp_e1.py DATASET OUT.json B ranks(comma) rules(comma) [ordinal_B] [cap]"""
import sys, json, time, os
import numpy as np
from multiprocessing import Pool
import lbmanip as L
from lbexp import Dataset, order_by, cell

name, out, B, ranks, rules = sys.argv[1], sys.argv[2], int(sys.argv[3]), [int(x) for x in sys.argv[4].split(',')], sys.argv[5].split(',')
B_ord = int(sys.argv[6]) if len(sys.argv) > 6 else B
cap = sys.argv[7] if len(sys.argv) > 7 else 'frontier'
SEED = 20241101
ds = Dataset(name)


def one(args):
    """args = (rule, replicate index or -1 for observed). Returns list over ranks."""
    rule, b = args
    if b < 0:
        S = ds.S
    else:
        rng = np.random.default_rng([SEED, b])
        S = ds.noisy(rng)
    order, agg = order_by(rule, S)
    res = []
    for r in ranks:
        t = int(order[r - 1])
        t0 = time.time()
        c = cell(rule, S, t, cap)
        res.append(dict(rule=rule, rank=r, b=b, target=t, comp_rank=L.rank_of(agg, t), depth=c['depth'], breadth=c['breadth'],
                        already=bool(c['already']), optimal=bool(c.get('optimal', True)), sec=time.time() - t0))
    return res


if __name__ == '__main__':
    jobs = [(rule, -1) for rule in rules]
    for rule in rules:
        nb = B_ord if rule in L.ORDINAL else B
        jobs += [(rule, b) for b in range(nb)]
    t0 = time.time()
    with Pool(int(os.environ.get('NPROC', 36))) as p:
        out_rows = [r for res in p.imap_unordered(one, jobs, chunksize=1) for r in res]
    meta = dict(dataset=name, N=ds.N, m=ds.m, B=B, B_ord=B_ord, ranks=ranks, rules=rules, cap=cap, seed=SEED, wall_sec=time.time() - t0,
                models=ds.models, tasks=ds.tasks)
    json.dump(dict(meta=meta, rows=out_rows), open(out, 'w'))
    print('done', len(out_rows), 'rows in', round(time.time() - t0), 's')
