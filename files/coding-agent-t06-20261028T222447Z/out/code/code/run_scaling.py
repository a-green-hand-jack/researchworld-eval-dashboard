"""E3: Arena subsampled to N comparisons (dependence of budgets/resolution on N); E4: bootstrap datasets
(sampling uncertainty of the budgets themselves).  Rows: one per adjacent pair / top-1 challenger.
usage: python run_scaling.py OUT.csv"""
import sys, zlib, numpy as np, pandas as pd
from multiprocessing import Pool
import boards, bt
from run_attack import seed_for

SIZES = [1000, 2000, 5000, 10000, 20000, 40000]
REPS = 20
BOOT_BOARDS = ["arena55k", "arena6", "mt_human", "mt_gpt4", "arenaST_human", "arenaST_Meta-Llama-3-70B-Instruct",
               "arenaST_Qwen2-72B-Instruct", "arenaST_Mistral-7B-Instruct-v0.2"]
B_BOOT = 100
_cache = {}


def get_problem(name):
    if name not in _cache:
        _cache[name] = bt.Problem(boards.get_all(False)[name]["load"]())
    return _cache[name]


def rows_for(P0, N, th_counts, tag):
    """attack all adjacent pairs and top-1 challengers on the counts matrix N (a perturbed/resampled dataset)"""
    P = P0
    th = P.fit(N)
    order = np.argsort(-th[:P.p])
    out = []
    Ntot = N.sum()
    def nloc(i, j):
        m = (P.ca == i) | (P.cb == i) | (P.ca == j) | (P.cb == j)
        return float(N[m].sum())
    pairs = [("adjacent", r + 1, order[r], order[r + 1]) for r in range(P.p - 1)]
    pairs += [("top1", 1, order[0], order[jr]) for jr in range(1, min(5, P.p - 1) + 1)]
    for kind, rank, i, j in pairs:
        if th[i] - th[j] <= 1e-9: continue
        # attacks on a resampled dataset: temporarily swap N0
        old = P.N0, P.Ntot
        P.N0, P.Ntot = N, Ntot
        try:
            u = P.contrast(i, j); se = float(np.sqrt(u @ np.linalg.solve(P.hessian(th, N), u)))
            kd, _ = P.attack(i, j, ("drop",), th_full=th)
            kr, _ = P.attack(i, j, ("relabel",), th_full=th)
        finally:
            P.N0, P.Ntot = old
        out.append(dict(tag=tag, kind=kind, rank=rank, gap=float(th[i] - th[j]), se=se, z=float((th[i] - th[j]) / se),
                        n_loc=nloc(i, j), N=Ntot, drop=np.nan if kd is None else kd, relabel=np.nan if kr is None else kr))
    return out


def task(args):
    kind, board, size, rep = args
    P = get_problem(board)
    rng = np.random.default_rng(seed_for(f"{kind}|{board}|{size}|{rep}"))
    if kind == "sub":
        k = P.Ntot - size
        N = P.drop_random(int(k), rng)       # random subsample without replacement
    else:
        N = P.resample_counts(rng)           # bootstrap resample (with replacement)
    rows = rows_for(P, N, None, f"{kind}|{board}|{size}|{rep}")
    for r in rows: r.update(exp=kind, board=board, size=size, rep=rep)
    return rows


if __name__ == "__main__":
    out = sys.argv[1]
    if len(sys.argv) > 2:      # extra boards: bootstrap datasets only
        tasks = [("boot", b, 0, r) for b in sys.argv[2:] for r in range(B_BOOT)]
    else:
        tasks = [("sub", "arena55k", s, r) for s in SIZES for r in range(REPS)]
        tasks += [("boot", b, 0, r) for b in BOOT_BOARDS for r in range(B_BOOT)]
    with Pool(12) as pool:
        res = pool.map(task, tasks, chunksize=4)
    pd.DataFrame([r for rs in res for r in rs]).to_csv(out, index=False)
