"""Main experiment: winner's-curse gap and reporting-method evaluation on real cached LLM scores.

Population = the first Q questions of the universe (fixed finite pool, Q ~ 1500). A "search set" is n questions drawn
i.i.d. (with replacement) from the pool, so the true accuracy mu_c of config c on fresh questions = pool mean of M[:, c]
exactly. For each rep and each search algorithm we: run the search on S (n x 72), select config `sel`, and compute reports.

Usage: python code/exp_main.py MODEL PARSER REPS OUT_CSV [nlist]
"""
import sys, time, os
import numpy as np, pandas as pd
import multiprocessing as mp
sys.path.insert(0, "code")
from data_io import load
from selinf import *
from search_algs import *

model, parser, REPS, OUT = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
NS = [int(x) for x in sys.argv[5].split(",")] if len(sys.argv) > 5 else [50, 100, 200, 400, 800]
ALPHA = 0.1
M, info = load(model, parser=parser)
Q = M.shape[0]; GMU = M.mean(0)
DISJOINT = os.environ.get('DISJOINT', '0') == '1'
ALGLIST = [("grid", 72), ("random", 4), ("random", 12), ("random", 36), ("coord", 72), ("sh", 72)]


def one_rep(args):
    n, rep = args
    rng = np.random.RandomState(1000003 * n + rep)
    if DISJOINT:  # search set without replacement; target = accuracy on the disjoint remaining questions
        perm = rng.permutation(Q); ix = perm[:n]; MU = M[perm[n:]].mean(0)
    else:
        ix = rng.randint(0, Q, n); MU = GMU
    S = M[ix]
    rows = []
    for aname, K in ALGLIST:
        alg = ALGS[aname]
        r2 = np.random.RandomState(rng.randint(1 << 30))
        sel, cols, adaptive = alg(S, r2, K)
        base = dict(n=n, rep=rep, alg=aname, K=K, sel=sel, mu_sel=MU[sel], mu_best=MU.max(), mu_med=np.median(MU))
        def add(meth, est, lo, hi, s=sel):
            rows.append(dict(base, method=meth, est=est, lo=lo, hi=hi, mu_sel=MU[s]))
        add("naive", S[:, sel].mean(), *wilson(S[:, sel].sum(), n, ALPHA))
        # --- holdout: rerun the algorithm on the first part; report on the remaining part
        for frac, nm in [(0.5, "holdout50"), (0.75, "holdout75")]:
            ns = int(round(n * frac)); A, B = S[:ns], S[ns:]
            s_h, _, _ = alg(A, np.random.RandomState(rng.randint(1 << 30)), K)
            # NB: for 'random' the candidate set is redrawn; fine (a different draw of K configs)
            lo, hi = wilson(B[:, s_h].sum(), len(B), ALPHA)
            add(nm, B[:, s_h].mean(), lo, hi, s_h)
        # --- selection-aware reports on the visited columns
        if aname in ("grid", "random"):
            Sc = S[:, cols]; ci = int(np.where(cols == sel)[0][0])
            for nm, f in [("boot_opt", boot_optimism), ("maxT", maxT), ("cond", conditional)]:
                e, lo, hi, _ = f(Sc, r2, ALPHA, c=ci)
                add(nm, e, lo, hi)
        else:  # adaptive: selection-aware reports valid for any rule use all 72 columns
            e, lo, hi, _ = maxT(S, r2, ALPHA, c=sel); add("maxT", e, lo, hi)
        e, lo, hi, _ = replay_boot(alg, K, S, r2, ALPHA, B=100); add("replay", e, lo, hi)
        if aname == "grid":
            e, _, _, s_l = ladder(S, r2, ALPHA); add("ladder_n13", e, np.nan, np.nan, s_l)
            e, _, _, s_l = ladder(S, r2, ALPHA, 0.5 / np.sqrt(n)); add("ladder_n12", e, np.nan, np.nan, s_l)
    return rows


if __name__ == "__main__":
    t0 = time.time()
    jobs = [(n, r) for n in NS for r in range(REPS)]
    out = []
    with mp.Pool(min(24, os.cpu_count())) as pool:
        for i, rows in enumerate(pool.imap_unordered(one_rep, jobs, chunksize=4)):
            out.extend(rows)
            if i % 500 == 0: print(i, len(jobs), round(time.time() - t0), flush=True)
    df = pd.DataFrame(out); df.insert(0, "parser", parser); df.insert(0, "model", model)
    df.to_csv(OUT, index=False); print("saved", OUT, df.shape, "Q", Q, round(time.time() - t0))
