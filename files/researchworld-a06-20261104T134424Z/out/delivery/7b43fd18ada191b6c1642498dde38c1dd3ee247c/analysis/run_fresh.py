"""Reporting protocols at equal item budgets: tune on n items, report on m FRESH items (fresh-evaluation set), vs reporting on the tuning items
(naive, bootstrap-OOB, simultaneous, hybrid, 5-fold crossfit, 50/50 split). Items consumed: n (in-sample, split) or n + m (fresh).
usage: run_fresh.py cells SHARD NSHARDS OUTDIR           synthetic reference cell + interaction grid (tau x K x rho)
       run_fresh.py rank OUT.csv                          ranking of tuned systems with each protocol at equal budgets (synthetic)
       run_fresh.py real MATRIX OUT.parquet [M]           real replay at K = all cached configs (disjoint arm: truth = accuracy on the pool items not used)
Every row's truth is the TRUE accuracy of the config that protocol shipped (synthetic: exact pool mean; real: items of the pool not used by the protocol)."""
import sys, os, numpy as np, pandas as pd, time, itertools, warnings; warnings.filterwarnings("ignore")
from synth import make_pool; from lib import ESTIMATORS, PROCS, wilson; from run_grid import derive
INS = ["naive", "boot_opt", "simul", "hybrid", "crossfit", "split"]
N_IN = [100, 200, 300, 400, 600, 800]
FRESH = [(50, 150), (67, 133), (100, 100), (133, 67), (150, 50), (100, 300), (133, 267), (200, 200), (267, 133), (300, 100), (100, 50), (200, 100), (400, 200), (400, 400)]

def run_fresh(Y, Ks, ns_in, fresh, ests, M, seed, disjoint=False, tag="", est_kw=None):
    Kp, N = Y.shape; mu_pool = Y.mean(1); est_kw = est_kw or dict(boot_opt=dict(B=100), simul=dict(B=200)); rows = []
    def truth(used):
        return (Y.sum(1) - Y[:, used].sum(1)) / (N - len(used)) if disjoint else mu_pool
    for K in Ks:
        for n in ns_in:
            rng = np.random.default_rng([seed, n, K, 1])
            for rep in range(M):
                T = rng.choice(N, n, replace=False) if disjoint else rng.integers(0, N, n); mu = truth(T)
                cand = np.arange(Kp) if K == Kp else rng.choice(Kp, K, replace=False); S = Y[cand][:, T]
                for en in ests:
                    if en in ("hybrid",) and K == 1: continue
                    r = ESTIMATORS[en]("argmax", S, rng, **est_kw.get(en, {})); kk = cand[r["k"]]
                    rows.append(dict(tag=tag, K=K, protocol="insample", est_name=en, n_tune=n, m_fresh=0, items=n, rep=rep, k=kk, est=r["est"], lo=r["lo"], hi=r["hi"], mu=mu[kk], mu_best=mu[cand].max(),
                                     oob=r.get("oob", np.nan), est632=r.get("est632", np.nan)))
        for (nt, mf) in fresh:
            rng = np.random.default_rng([seed, nt, mf, K, 2])
            for rep in range(M):
                idx = rng.permutation(N)[:nt + mf] if disjoint else None
                T = idx[:nt] if disjoint else rng.integers(0, N, nt); F = idx[nt:] if disjoint else rng.integers(0, N, mf)
                mu = truth(idx if disjoint else T)
                cand = np.arange(Kp) if K == Kp else rng.choice(Kp, K, replace=False); S = Y[cand][:, T]
                k, _ = PROCS["argmax"](S, rng); kk = cand[k]; a = Y[kk][F].mean(); lo, hi = wilson(a, mf)
                rows.append(dict(tag=tag, K=K, protocol="fresh", est_name="fresh", n_tune=nt, m_fresh=mf, items=nt + mf, rep=rep, k=kk, est=a, lo=lo, hi=hi, mu=mu[kk], mu_best=mu[cand].max(), oob=np.nan, est632=np.nan))
    return pd.DataFrame(rows)

def summarize_fresh(df, extra=()):
    d = derive(df.assign(n=df.n_tune)) if (df.est_name == "boot_opt").any() else df; d = d.copy()
    d["err"] = d.est - d.mu; d["cover"] = (d.lo <= d.mu) & (d.mu <= d.hi); d["width"] = d.hi - d.lo; d["regret"] = d.mu_best - d.mu
    g = d.groupby(list(extra) + ["K", "protocol", "est_name", "n_tune", "m_fresh", "items"])
    out = g.agg(mu_ship=("mu", "mean"), mean_est=("est", "mean"), bias=("err", "mean"), bias_se=("err", lambda x: x.std() / np.sqrt(len(x))), rmse=("err", lambda x: np.sqrt((x ** 2).mean())), medae=("err", lambda x: np.median(np.abs(x))),
                cover=("cover", "mean"), width=("width", "mean"), regret=("regret", "mean"), reps=("err", "size")).reset_index()
    out["cover_se"] = np.sqrt(out.cover * (1 - out.cover) / out.reps); return out

def run_rank_eq(Y, Ks, designs, M, seed, tag):
    """designs: list of (label, kind, n_tune, m_fresh) with kind in naive/boot_oob/split/simul/fresh. All systems share T (and F)."""
    from scipy.stats import kendalltau
    N = Y.shape[1]; mu = Y.mean(1); S_ = len(Ks); big = int(np.argmax(Ks)); rows = []
    for (label, kind, nt, mf) in designs:
        rng = np.random.default_rng([seed, nt, mf, zlib_crc(kind)])
        for rep in range(M):
            T = rng.integers(0, N, nt); F = rng.integers(0, N, mf) if mf else None; cs = [rng.choice(Y.shape[0], K, replace=False) for K in Ks]
            rep_v = np.empty(S_); tru = np.empty(S_)
            for s in range(S_):
                S = Y[cs[s]][:, T]
                if kind == "fresh": k, _ = PROCS["argmax"](S, rng); v = Y[cs[s][k]][F].mean()
                elif kind == "boot_oob": r = ESTIMATORS["boot_opt"]("argmax", S, rng, B=100); k = r["k"]; v = r["oob"]
                else: r = ESTIMATORS[kind]("argmax", S, rng); k = r["k"]; v = r["est"]
                rep_v[s] = v; tru[s] = mu[cs[s][k]]
            d_rep = rep_v[:, None] - rep_v[None, :]; d_tru = tru[:, None] - tru[None, :]; iu = np.triu_indices(S_, 1); msk = np.abs(d_tru[iu]) >= 0.01
            tb = kendalltau(rep_v, tru, variant="b")[0]
            rows.append(dict(tag=tag, label=label, kind=kind, n_tune=nt, m_fresh=mf, items=nt + mf if kind == "fresh" else nt, rep=rep, tau_b=tb if tb == tb else 0.0,
                             top1=float(np.argmax(rep_v) == np.argmax(tru)), wrong_order_1pp=float((np.sign(d_rep[iu]) != np.sign(d_tru[iu]))[msk].mean()) if msk.any() else np.nan,
                             big_reported_best=float(np.argmax(rep_v) == big), big_truly_best=float(np.argmax(tru) == big), range_true=tru.max() - tru.min()))
    return pd.DataFrame(rows)
import zlib
def zlib_crc(s): return zlib.crc32(s.encode()) % 1000

if __name__ == "__main__":
    mode = sys.argv[1]; t0 = time.time()
    if mode == "cells":
        shard, nsh, outd = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]; os.makedirs(outd, exist_ok=True); M = 600
        cells = [(t, K, r) for r in (0.5, 0.9) for t in (0.01, 0.0, 0.03) for K in (16, 4, 64)]
        for ci, (tau, K, rho) in enumerate(cells):
            if ci % nsh != shard: continue
            f = f"{outd}/fresh_tau{tau}_K{K}_rho{rho}.parquet"
            if os.path.exists(f): continue
            Y = make_pool(128, 20000, m=0.3, tau=tau, rho=rho, seed=7)
            d = run_fresh(Y, [K], N_IN, FRESH, INS, M, seed=60 + ci, tag=f"tau{tau}_K{K}_rho{rho}"); d["tau"] = tau; d["rho"] = rho; d["m"] = 0.3
            d.to_parquet(f); print(ci, tau, K, rho, round(time.time() - t0), flush=True)
    elif mode == "rank":
        rows = []
        for tau in (0.0, 0.01, 0.03):
            Y = make_pool(128, 20000, m=0.3, tau=tau, rho=0.5, seed=400 + int(tau * 1000))
            for name, Ks in (("equal_K16", [16] * 5), ("unequal_K4_64", [4, 8, 16, 32, 64])):
                des = []
                for tot in (200, 400):
                    des += [(f"insample_{tot}", k, tot, 0) for k in ("naive", "boot_oob", "simul", "split")]
                    des += [(f"fresh_half_{tot}", "fresh", tot // 2, tot // 2), (f"fresh_3to1_{tot}", "fresh", 3 * tot // 4, tot // 4)]
                df = run_rank_eq(Y, Ks, des, 500, 21, f"rankeq_{name}_tau{tau}")
                g = df.groupby(["label", "kind", "n_tune", "m_fresh", "items"]).agg(tau_b_mean=("tau_b", "mean"), tau_b_sd=("tau_b", "std"), top1=("top1", "mean"), wrong_order_1pp=("wrong_order_1pp", "mean"),
                      big_reported_best=("big_reported_best", "mean"), big_truly_best=("big_truly_best", "mean"), range_true=("range_true", "mean"), reps=("tau_b", "size")).reset_index()
                g["tau_gen"] = tau; g["design"] = name; g["Ks"] = str(Ks); rows.append(g); print(name, tau, round(time.time() - t0), flush=True)
        pd.concat(rows).to_csv(sys.argv[2], index=False)
    elif mode == "real":
        Y = np.load(sys.argv[2], allow_pickle=True)["Y"]; M = int(sys.argv[4]) if len(sys.argv) > 4 else 500; Kp = Y.shape[0]
        fr = [f for f in FRESH if f[0] + f[1] <= 800]; ni = [n for n in N_IN if n <= 800]
        d = run_fresh(Y, sorted({1, 2, 4, Kp} & set(range(1, Kp + 1))), ni, fr, INS, M, seed=70, disjoint=True, tag="real"); d.to_parquet(sys.argv[3])
    print("done", round(time.time() - t0))
