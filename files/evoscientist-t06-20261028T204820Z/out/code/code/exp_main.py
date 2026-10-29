"""Main experiment: for every leaderboard and a set of ranked pairs (i above j) compute
  * BT scores, sandwich SE, z = gap/SE, bootstrap flip probability (B resamples)
  * minimal #votes whose drop / flip / injection reverses the pair (verified by refit)
  * random-perturbation baselines at the same budget
Usage: python code/exp_main.py core|judges [nproc]
Outputs: results/pairs_<group>.csv, results/boards_<group>.csv
"""
import os, sys, time, zlib
os.environ["OMP_NUM_THREADS"] = "1"; os.environ["OPENBLAS_NUM_THREADS"] = "1"; os.environ["MKL_NUM_THREADS"] = "1"
import numpy as np, pandas as pd
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bt
from common import load, ROOT

BOOT_B = 300
RAND_R = 100
RAND_PAIRS = 30
DIST = (1, 2, 3, 5)

GROUPS = {
    "core": ["arena55k_human", "mtbench_human", "mtbench_gpt4", "nba_alltime"] + [f"nba_{y}" for y in range(1980, 2016)],
    "extras": ["arena55k_noties"] + [f"nba_{y}_nohome" for y in range(1980, 2016)],
    "judges": ["arenaST_human"] + [f"arenaST_judge_{j}" for j in
              ["Athene-70B", "Meta-Llama-3-70B-Instruct", "Qwen2-72B-Instruct", "Mistral-7B-Instruct-v0.2", "dolphin-2.1-mistral-7b"]],
}

_cache = {}


def get(name):
    if name not in _cache:
        D = load(name)
        th = bt.fit_data(D)
        _cache.clear()
        _cache[name] = (D, th)
    return _cache[name]


def seed_of(name, extra=0):
    return zlib.crc32(name.encode()) % (2**31) + extra


def pair_list(th, M):
    rank = np.argsort(-th[:M])
    pairs = set()
    for r in range(M):
        for d in DIST:
            if r + d < M:
                pairs.add((r, r + d))
    for j in range(1, min(M, 6)):
        pairs.add((0, j))
    return rank, sorted(pairs)


def boot_scores(name):
    D, th = get(name)
    rng = np.random.default_rng(seed_of(name, 1))
    out = np.empty((BOOT_B, D.P))
    for b in range(BOOT_B):
        w = rng.multinomial(D.N, np.ones(D.N) / D.N).astype(float)
        out[b] = bt.fit_data(D, w=w, th0=th)
    return out


def task_pair(args):
    name, ri, rj = args
    D, th = get(name)
    rank = np.argsort(-th[:D.M])
    i, j = rank[ri], rank[rj]
    gap = th[i] - th[j]
    rec = dict(board=name, rank_i=ri, rank_j=rj, i=D.names[i], j=D.names[j], gap=gap,
               se=bt.se_gap_sandwich(D, th, i, j), N=D.N, M=D.M)
    cnt = np.bincount(np.concatenate([D.a, D.b]), minlength=D.M)
    rec["n_i"], rec["n_j"] = int(cnt[i]), int(cnt[j])
    rec["n_ij"] = int(((D.a == i) & (D.b == j)).sum() + ((D.a == j) & (D.b == i)).sum())
    rec["n_inv"] = rec["n_i"] + rec["n_j"] - rec["n_ij"]
    t0 = time.time()
    for mode in ("drop", "flip", "add"):
        if gap < 1e-6:  # exact BT tie (identical sufficient statistics): zero perturbations needed
            r = dict(k=0.0, k_lin=0.0)
        else:
            r = bt.min_perturbation(D, th, i, j, mode)
        rec["k_" + mode] = r["k"]
        rec["klin_" + mode] = r["k_lin"]
    rec["secs"] = time.time() - t0
    return rec


def task_rand(args):
    name, ri, rj, kd, kf = args
    D, th = get(name)
    rank = np.argsort(-th[:D.M])
    i, j = rank[ri], rank[rj]
    rng = np.random.default_rng(seed_of(name, 1000 * ri + rj + 7))
    fd = ff = 0
    for _ in range(RAND_R):
        w = np.ones(D.N)
        w[rng.choice(D.N, int(kd), replace=False)] = 0
        t = bt.fit_data(D, w=w, th0=th)
        fd += (t[i] - t[j] <= 0)
        y = D.y.copy()
        cand = np.flatnonzero(D.y != 0.5)
        sel = rng.choice(cand, int(min(kf, len(cand))), replace=False)
        y[sel] = 1 - y[sel]
        t = bt.fit_data(D, y=y, th0=th)
        ff += (t[i] - t[j] <= 0)
    # semi-informed random baseline: drop random votes that favour i (i wins) or hurt j (j loses),
    # i.e. an adversary that knows the direction of each vote but not its influence weight
    ya = D.y
    fav = np.flatnonzero(((D.a == i) & (ya == 1)) | ((D.b == i) & (ya == 0)) | ((D.a == j) & (ya == 0)) | ((D.b == j) & (ya == 1)))
    ks = []
    for rep in range(3):
        perm = rng.permutation(fav)

        def flips(k):
            w = np.ones(D.N)
            w[perm[:k]] = 0
            t = bt.fit_data(D, w=w, th0=th)
            return t[i] - t[j] <= 0

        if not flips(len(perm)):
            ks.append(np.inf)
            continue
        lo, hi = 0, len(perm)
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if flips(mid):
                hi = mid
            else:
                lo = mid
        ks.append(hi)
    return dict(board=name, rank_i=ri, rank_j=rj, rand_drop_flip=fd / RAND_R, rand_flip_flip=ff / RAND_R,
                k_targ_rand=float(np.median(ks)))


def run(group, nproc):
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    names = GROUPS[group]
    t0 = time.time()
    # --- per-board: fit, bootstrap
    boards, boot = [], {}
    for nm in names:
        D, th = get(nm)
        bs = boot_scores(nm)
        boot[nm] = bs
        rank, pairs = pair_list(th, D.M)
        boards.append(dict(board=nm, N=D.N, M=D.M, tie_frac=float((D.y == 0.5).mean()),
                           gamma=float(th[D.M]) if D.q else np.nan))
        print(nm, "boot done", round(time.time() - t0), flush=True)
    # --- pairs (parallel; each worker caches one board at a time -> order tasks by board)
    tasks = []
    for nm in names:
        D, th = get(nm)
        rank, pairs = pair_list(th, D.M)
        tasks += [(nm, r, s) for r, s in pairs]
    with Pool(nproc) as p:
        recs = p.map(task_pair, tasks, chunksize=4)
    df = pd.DataFrame(recs)
    df["z"] = df.gap / df.se
    # bootstrap flip prob & sd
    fl, bsd = [], []
    for _, r in df.iterrows():
        D, th = get(r.board)
        rank = np.argsort(-th[:D.M])
        i, j = rank[int(r.rank_i)], rank[int(r.rank_j)]
        g = boot[r.board][:, i] - boot[r.board][:, j]
        fl.append(float((g <= 0).mean()))
        bsd.append(float(g.std(ddof=1)))
    df["boot_flip"] = fl
    df["boot_sd"] = bsd
    # --- random baselines on a sample of pairs
    rng = np.random.default_rng(12345)
    rt = []
    for nm, g in df.groupby("board"):
        g = g[np.isfinite(g.k_drop) & np.isfinite(g.k_flip)]
        sel = g.sample(min(RAND_PAIRS, len(g)), random_state=int(rng.integers(1 << 30)))
        rt += [(nm, int(r.rank_i), int(r.rank_j), r.k_drop, r.k_flip) for r in sel.itertuples()]
    with Pool(nproc) as p:
        rr = pd.DataFrame(p.map(task_rand, rt, chunksize=2))
    df = df.merge(rr, on=["board", "rank_i", "rank_j"], how="left")
    df.to_csv(os.path.join(ROOT, "results", f"pairs_{group}.csv"), index=False)
    pd.DataFrame(boards).to_csv(os.path.join(ROOT, "results", f"boards_{group}.csv"), index=False)
    print("done", group, len(df), "pairs", round(time.time() - t0), "s", flush=True)


if __name__ == "__main__":
    run(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 16)
