"""E1: stability of the leaderboard under *random* perturbations (bootstrap, random drops, random label noise)."""
import sys, time, numpy as np, pandas as pd
from multiprocessing import Pool
import boards, bt
from run_attack import seed_for

B_BOOT = 200
R = 100
EPS = [0.01, 0.02, 0.05, 0.1, 0.2, 0.5]


def summarize(P, th, ths):
    """ths: (R, p) perturbed scores -> per-run metrics vs. th"""
    p = P.p
    order = np.argsort(-th[:p]); rk = bt.ranks_from_theta(th, p)
    tau = np.array([bt.kendall(th[:p], t[:p]) for t in ths])
    top1 = np.array([np.argmax(t[:p]) == order[0] for t in ths], float)
    # fraction of adjacent pairs (in full ranking) whose order is reversed
    adj_flip = np.array([np.mean([t[order[r]] < t[order[r + 1]] for r in range(p - 1)]) for t in ths])
    rkp = np.array([bt.ranks_from_theta(t, p) for t in ths])
    disp = np.abs(rkp - rk[None]).mean(1)
    return tau, top1, adj_flip, disp


def run_board(name):
    t0 = time.time()
    spec = boards.get_all()[name]
    P = bt.Problem(spec["load"]()); rng = np.random.default_rng(seed_for(name) + 1)
    th = P.fit(); p = P.p
    rows = []
    boot = np.array([P.fit(P.resample_counts(rng), th)[:P.p] for _ in range(B_BOOT)])
    cases = [("bootstrap", 1.0, boot)]
    for mode in ("drop", "relabel"):
        for e in EPS:
            k = int(round(e * P.Ntot))
            ths = []
            for _ in range(R):
                N = P.drop_random(k, rng) if mode == "drop" else P.relabel_random(k, rng)
                ths.append(P.fit(N, th)[:p])
            cases.append((mode, e, np.array(ths)))
    for mode, e, ths in cases:
        tau, top1, af, disp = summarize(P, th, ths)
        rk = np.array([bt.ranks_from_theta(t, p) for t in ths])
        lo, hi = np.percentile(rk, 2.5, axis=0), np.percentile(rk, 97.5, axis=0)
        rows.append(dict(board=name, design=spec["design"], mode=mode, eps=e, N=P.Ntot, p=p,
                         tau_mean=tau.mean(), tau_sd=tau.std(ddof=1), top1_same=top1.mean(),
                         adj_flip_mean=af.mean(), adj_flip_sd=af.std(ddof=1), disp_mean=disp.mean(),
                         rank_ci_width=(hi - lo).mean(), rank_ci_width_top5=(hi - lo)[np.argsort(-th[:p])[:5]].mean()))
    print(f"{name}: {time.time()-t0:.1f}s", flush=True)
    return rows


if __name__ == "__main__":
    out = sys.argv[1]; filt = sys.argv[2:]
    names = [n for n in boards.get_all() if (any(f in n for f in filt) if filt else ("noties" not in n and n != "arena140k"))]
    names.sort(key=lambda n: (0 if "arena" in n else 1, n))
    with Pool(10) as pool:
        res = pool.map(run_board, names, chunksize=1)
    pd.DataFrame([r for rs in res for r in rs]).to_csv(out, index=False)
