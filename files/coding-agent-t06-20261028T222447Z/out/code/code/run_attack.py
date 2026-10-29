"""E2: minimal flip budgets for every adjacent pair (and top-1 / top-k boundary) on every leaderboard.
usage: python run_attack.py OUT.csv [board-name-filter-substring ...]"""
import sys, zlib, time, numpy as np, pandas as pd
from multiprocessing import Pool
import boards, bt

BASE_SEED = 20261028
B_BOOT = 200
R_RAND = 100


def seed_for(name):
    return BASE_SEED + zlib.crc32(name.encode()) % 100000


def pair_row(P, th, i, j, rank, boot, rng, N_full):
    gap = float(th[i] - th[j]); se = P.gap_se(th, i, j)
    row = dict(rank=rank, item_i=P.items[i], item_j=P.items[j], gap=gap, se_model=se, z_model=gap / se,
               n_loc=P.n_involving(i, j), N=P.Ntot, p=P.p)
    g = boot[:, i] - boot[:, j]
    row.update(boot_sd=float(g.std(ddof=1)), z_boot=gap / float(g.std(ddof=1)), p_flip_boot=float((g < 0).mean()))
    res = {}
    for name, kinds, mode, mask in [("drop", ("drop",), "greedy", None), ("relabel", ("relabel",), "greedy", None),
                                    ("inject", ("inject",), "greedy", None),
                                    ("inject_target", ("inject_t",), "greedy", None),
                                    ("drop_oneshot", ("drop",), "oneshot", None),
                                    ("relabel_oneshot", ("relabel",), "oneshot", None)]:
        k, info = P.attack(i, j, kinds, mode, th_full=th, cell_mask=mask)
        res[name] = np.nan if k is None else k
        if name == "drop" and k:
            # random removal of the same number of comparisons: how often does it flip the pair?
            fl = 0
            for _ in range(R_RAND):
                thr = P.fit(P.drop_random(k, rng), th)
                fl += thr[i] < thr[j]
            res["rand_drop_flip_at_k"] = fl / R_RAND
        if name == "relabel" and k:
            fl = 0
            for _ in range(R_RAND):
                thr = P.fit(P.relabel_random(k, rng), th)
                fl += thr[i] < thr[j]
            res["rand_relabel_flip_at_k"] = fl / R_RAND
    for a_, nm in ((0.2, "drop_a02"), (0.05, "drop_a005")):
        k, _ = P.attack(i, j, ("drop",), "greedy", alpha=a_, th_full=th)
        res[nm] = np.nan if k is None else k
    # direct-only baseline: edits restricted to comparisons between i and j themselves
    mask = ((P.ca == i) & (P.cb == j)) | ((P.ca == j) & (P.cb == i))
    for kn in ("drop", "relabel"):
        k, _ = P.attack(i, j, (kn,), "greedy", th_full=th, cell_mask=mask)
        res[kn + "_direct"] = np.nan if k is None else k
    row.update(res)
    return row


def run_board(name):
    t0 = time.time()
    spec = boards.get_all()[name]
    d = spec["load"](); P = bt.Problem(d)
    rng = np.random.default_rng(seed_for(name))
    th = P.fit()
    boot = np.array([P.fit(P.resample_counts(rng), th)[:P.p] for _ in range(B_BOOT)])
    order = np.argsort(-th[:P.p])
    rows = []
    for r in range(P.p - 1):
        row = pair_row(P, th, order[r], order[r + 1], r + 1, boot, rng, P.Ntot)
        row.update(board=name, design=spec["design"], kind="adjacent")
        rows.append(row)
    # top-1 challengers (ranks 2..5) and top-k boundary windows
    extra = []
    for jr in range(2, min(5, P.p - 1) + 1):
        extra.append(("top1", 1, order[0], order[jr - 1]))
    for k in (3, 5, 10):
        if P.p >= k + 3 and (P.p >= 20 or k <= 5):
            for ir in range(max(1, k - 2), k + 1):
                for jr in range(k + 1, k + 4):
                    extra.append((f"top{k}", ir, order[ir - 1], order[jr - 1]))
    for kind, ir, i, j in extra:
        if th[i] <= th[j]: continue
        row = {}
        gap = float(th[i] - th[j]); se = P.gap_se(th, i, j)
        row.update(rank=ir, item_i=P.items[i], item_j=P.items[j], gap=gap, se_model=se, z_model=gap / se,
                   n_loc=P.n_involving(i, j), N=P.Ntot, p=P.p, board=name, design=spec["design"], kind=kind)
        for nm, kinds in [("drop", ("drop",)), ("relabel", ("relabel",)), ("inject", ("inject",))]:
            k_, _ = P.attack(i, j, kinds, "greedy", th_full=th)
            row[nm] = np.nan if k_ is None else k_
        rows.append(row)
    print(f"{name}: {len(rows)} rows in {time.time()-t0:.1f}s", flush=True)
    return rows


if __name__ == "__main__":
    out = sys.argv[1]; filt = sys.argv[2:]
    names = [n for n in boards.get_all() if (any(f in n for f in filt) if filt else "noties" not in n)]
    # big boards first for load balance
    names.sort(key=lambda n: (0 if "arena" in n else 1, n))
    with Pool(12) as pool:
        res = pool.map(run_board, names, chunksize=1)
    pd.DataFrame([r for rs in res for r in rs]).to_csv(out, index=False)
