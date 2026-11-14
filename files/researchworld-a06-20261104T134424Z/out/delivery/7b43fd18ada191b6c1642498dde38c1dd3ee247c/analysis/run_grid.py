"""Replicated experiments: for each (procedure, n, K, estimator) draw M tuning sets, run search + reporting estimator,
and record estimate, CI, the TRUE score mu of the selected config (exact: pool mean) and decision-level quantities."""
import numpy as np, pandas as pd, argparse, time, itertools, json, sys, zlib
from lib import PROCS, ESTIMATORS

def run(Y, base_idx, procs, ns, Ks, ests, M, seed, grid=None, est_kw=None, tag="", eps=0.0, leak_m=0, leak_p=0.9, disjoint=False):
    """Y: (Kpool, N) bool. For 'greedy' the candidate set is the whole grid (K ignored)."""
    Kp, N = Y.shape; mu = Y.mean(1); mu = mu + eps * (1 - 2 * mu); rows = []; est_kw = est_kw or {}
    for proc, n, K in itertools.product(procs, ns, Ks):
        if proc == "greedy" and K != Kp: continue
        rng = np.random.default_rng([seed, n, K, zlib.crc32(proc.encode()) % 1000])
        for m in range(M):
            T = rng.choice(N, n, replace=False) if disjoint else rng.integers(0, N, n)
            if disjoint: mu = (Y.sum(1) - Y[:, T].sum(1)) / (N - n)   # truth = accuracy on the pool items NOT in T
            cand = np.arange(Kp) if (K == Kp) else rng.choice(Kp, K, replace=False)
            S = Y[cand][:, T]; Sb = Y[base_idx][T]
            if eps > 0:   # generation noise: each (config,item) evaluation is a fresh noisy call; correctness flipped w.p. eps
                S = S ^ (rng.random(S.shape) < eps); Sb = Sb ^ (rng.random(Sb.shape) < eps)
            S_clean = S
            if leak_m > 0:  # demo leakage: each candidate config shows leak_m tuning items (answers included) in its prompt
                S = S.copy()
                for c in range(len(cand)):
                    ix = rng.choice(n, min(leak_m, n), replace=False); S[c, ix] |= rng.random(len(ix)) < leak_p
            kw = dict(grid=grid) if proc == "greedy" else {}
            for en in ests:
                if en in ("cond", "hybrid", "ladder") and proc != "argmax": continue
                ekw = dict(S_clean=S_clean) if (en == "split" and leak_m > 0) else {}
                r = ESTIMATORS[en](proc, S, rng, Sb=Sb, **kw, **ekw, **est_kw.get(en, {}))
                kk = cand[r["k"]]
                rows.append(dict(tag=tag, proc=proc, n=n, K=K, est_name=en, rep=m, k=kk, est=r["est"], lo=r["lo"], hi=r["hi"],
                                 mu=mu[kk], mu_best=mu[cand].max(), mu_base=mu[base_idx], mu_mean=mu[cand].mean(), eps=eps, leak_m=leak_m,
                                 naive=r.get("naive", np.nan), oob=r.get("oob", np.nan), est632=r.get("est632", np.nan),
                                 base=r.get("base", np.nan), dse=r.get("dse", np.nan), z=r.get("z", np.nan)))
    return pd.DataFrame(rows)

def derive(df):
    """Add the bootstrap-OOB and .632 variants (stored with every boot_opt row) as their own reporting methods, with a normal
    interval est +- 1.96 sqrt(p(1-p)/n) around their point estimate."""
    b = df[df.est_name == "boot_opt"]
    out = [df]
    for name, col in (("boot_oob", "oob"), ("boot_632", "est632")):
        d = b.copy(); d["est_name"] = name; d["est"] = d[col]
        se = np.sqrt(np.clip(d.est * (1 - d.est), 1e-6, None) / d.n); d["lo"] = d.est - 1.96 * se; d["hi"] = d.est + 1.96 * se
        out.append(d)
    return pd.concat(out, ignore_index=True)

SHIP_MARGINS = (0.01, 0.02, 0.03)
def summarize(df, groupcols=("tag", "proc", "n", "K", "est_name")):
    d = derive(df); d["err"] = d.est - d.mu; d["cover"] = (d.lo <= d.mu) & (d.mu <= d.hi); d["width"] = d.hi - d.lo
    d["claim"] = ((d.est - d.base) / d.dse) > d.z; d["true_delta"] = d.mu - d.mu_base
    d["regret"] = d.mu_best - d.mu; d["lb_viol"] = d.lo > d.mu       # lower bound lo exceeds the truth
    for mg in SHIP_MARGINS:   # ship if reported score >= baseline's true score + margin; false-ship if the selected config truly is below that bar
        d[f"false_ship_{int(mg*100)}pp"] = (d.est >= d.mu_base + mg) & (d.mu < d.mu_base + mg)
        d[f"ship_{int(mg*100)}pp"] = d.est >= d.mu_base + mg
    g = d.groupby(list(groupcols))
    agg = dict(bias=("err", "mean"), rmse=("err", lambda x: np.sqrt((x ** 2).mean())), cover=("cover", "mean"),
               width=("width", "mean"), mu_sel=("mu", "mean"), regret=("regret", "mean"), claim=("claim", "mean"),
               lb_viol=("lb_viol", "mean"), reps=("err", "size"), bias_se=("err", lambda x: x.std() / np.sqrt(len(x))))
    for mg in SHIP_MARGINS:
        agg[f"ship_{int(mg*100)}pp"] = (f"ship_{int(mg*100)}pp", "mean"); agg[f"false_ship_{int(mg*100)}pp"] = (f"false_ship_{int(mg*100)}pp", "mean")
    out = g.agg(**agg)
    out["cover_se"] = np.sqrt(out.cover * (1 - out.cover) / out.reps)
    fp = d[d.true_delta <= 0].groupby(list(groupcols)).claim.agg(["mean", "size"]).rename(columns={"mean": "fp_rate", "size": "n_nonpos"})
    return out.join(fp)

def run_compare(Y, specA, specB, ns, M, seed, ests=("naive", "split", "boot_opt"), est_kw=None, tag="", poolB=None):
    """Compare two tuned systems on the SAME tuning set. spec = dict(proc=, K=, pool=array of pool row indices).
    Decision: one-sided paired z-test (alpha=.05) of 'A better than B' on the reported scores. true_delta = mu_A* - mu_B*."""
    from lib import _pair
    mu = Y.mean(1); N = Y.shape[1]; rows = []; est_kw = est_kw or {}
    for n in ns:
        rng = np.random.default_rng([seed, n, zlib.crc32(tag.encode()) % 1000])
        for m in range(M):
            T = rng.integers(0, N, n)
            cA = rng.choice(specA["pool"], specA["K"], replace=False) if specA["K"] < len(specA["pool"]) else np.asarray(specA["pool"])
            cB = rng.choice(specB["pool"], specB["K"], replace=False) if specB["K"] < len(specB["pool"]) else np.asarray(specB["pool"])
            SA, SB = Y[cA][:, T], Y[cB][:, T]
            for en in ests:
                kwa = est_kw.get(en, {})
                rA = ESTIMATORS[en](specA["proc"], SA, rng, Sb=None, **kwa); rB = ESTIMATORS[en](specB["proc"], SB, rng, Sb=None, **kwa)
                kA, kB = cA[rA["k"]], cB[rB["k"]]
                cols = np.arange(n // 2, n) if en == "split" else None
                xa = Y[kA][T]; xb = Y[kB][T]
                if cols is not None: xa, xb = xa[cols], xb[cols]
                d = xa.astype(float) - xb; dse = d.std(ddof=1) / np.sqrt(len(d)) + 1e-12
                dhat = rA["est"] - rB["est"]
                rows.append(dict(tag=tag, n=n, rep=m, est_name=en, dhat=dhat, dse=dse, claim=dhat / dse > 1.645,
                                 true_delta=mu[kA] - mu[kB], muA=mu[kA], muB=mu[kB]))
    return pd.DataFrame(rows)

def run_rank(Y, Ks, procs, ns, M, seed, ests=("naive", "split", "boot_opt"), est_kw=None, tag="", pool=None):
    """Ranking of len(Ks) tuned systems on the SAME tuning set. System s searches Ks[s] configs drawn (without replacement) from the
    pool by procs[s]. Reported value = the method's estimate; the true value of a system is the true score of the config it selected.
    Per replication: Kendall tau between reported and true ranking, top-1 hit (reported best is truly best), share of discordant pairs
    among pairs with true difference >= 1pp (wrong_order_1pp), and whether the system with the largest budget is reported best / truly best."""
    from scipy.stats import kendalltau
    mu = Y.mean(1); N = Y.shape[1]; pool = np.arange(Y.shape[0]) if pool is None else np.asarray(pool); est_kw = est_kw or {}; rows = []; S_ = len(Ks)
    big = int(np.argmax(Ks))
    for n in ns:
        rng = np.random.default_rng([seed, n, zlib.crc32(tag.encode()) % 1000])
        for m in range(M):
            T = rng.integers(0, N, n); cs = [rng.choice(pool, K, replace=False) for K in Ks]
            for en in ests:
                kw = est_kw.get(en, {}); rep = np.empty(S_); tru = np.empty(S_); oob = np.empty(S_)
                for s in range(S_):
                    r = ESTIMATORS[en](procs[s], Y[cs[s]][:, T], rng, Sb=None, **kw); rep[s] = r["est"]; tru[s] = mu[cs[s][r["k"]]]; oob[s] = r.get("oob", np.nan)
                for name, v in ((en, rep),) + ((("boot_oob", oob),) if en == "boot_opt" else ()):
                    d_rep = v[:, None] - v[None, :]; d_tru = tru[:, None] - tru[None, :]; iu = np.triu_indices(S_, 1)
                    msk = np.abs(d_tru[iu]) >= 0.01
                    tau = kendalltau(v, tru)[0]
                    rows.append(dict(tag=tag, n=n, rep=m, est_name=name, tau=tau if tau == tau else 0.0, top1=float(np.argmax(v) == np.argmax(tru)),
                                     wrong_order_1pp=float((np.sign(d_rep[iu]) != np.sign(d_tru[iu]))[msk].mean()) if msk.any() else np.nan,
                                     big_reported_best=float(np.argmax(v) == big), big_truly_best=float(np.argmax(tru) == big),
                                     range_true=tru.max() - tru.min()))
    return pd.DataFrame(rows)
