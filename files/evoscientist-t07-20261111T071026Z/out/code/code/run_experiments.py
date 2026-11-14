"""Main experiment grid.  One task = (dataset, split kind, seed).

Usage:  python code/run_experiments.py --seeds 30 --out results/main.csv [--datasets a,b] [--procs 36]

Per task: split models, fit source-side objects once, then for every budget n and method
draw a coreset, let the target models "answer" only those items and predict their full
accuracy.  Common random numbers: all methods built on the same design kind (e.g. uniform)
see the identical coreset within a (task, n).
"""
import os, sys, time, argparse, zlib, traceback
os.environ.setdefault("OMP_NUM_THREADS", "1"); os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
import numpy as np, pandas as pd
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from methods import *
from sklearn.linear_model import RidgeCV

BUDGETS = [10, 25, 50, 100]


def rng_for(seed, n, tag):
    return np.random.default_rng([seed, n, zlib.crc32(tag.encode()) & 0xFFFFFF])


def run_task(args):
    name, kind, seed, budgets, ablate_k = args
    t0 = time.time()
    try:
        S = load_scores(name)
        src, tgt = make_split(name, S, kind, seed)
        Ssrc, Stgt = S[src], S[tgt]
        true = Stgt.mean(1)
        N = S.shape[1]
        R = Runner(Ssrc, seed, k=2, extra_ks=(1, 4, 8) if ablate_k else (8,))
        m2 = R.mirt[2]
        rows = []

        def rec(method, n, pred, extra=None):
            d = dict(dataset=name, split=kind, seed=seed, n=n, method=method,
                     n_src=len(src), n_tgt=len(tgt), N=N, **metrics(pred, true))
            if extra: d.update(extra)
            rows.append(d)

        for n in budgets:
            if n >= N: continue
            # ---------------- designs (shared across estimators) -----------------
            designs = {}
            def get_design(kind_, gamma=0.3, k=2):
                key = (kind_, gamma, k)
                if key not in designs:
                    designs[key] = R.design(kind_, n, rng_for(seed, n, f"{kind_}-{gamma}-{k}"), gamma=gamma, k=k)
                return designs[key]

            # ---------------- plain estimators ----------------------------------
            for dname, mname in [("uniform", "random"), ("strat", "strat_mean"), ("pps_resid", "pps_resid_mean")]:
                idx, pi = get_design(dname)
                rec(mname, n, hajek_mean(Stgt[:, idx], pi[idx]))

            # ---------------- prior work ----------------------------------------
            idx, pi = get_design("uniform"); Y = Stgt[:, idx]
            # random sampling + ridge from coreset scores to source accuracy ("rs_learn")
            rg = RidgeCV().fit(Ssrc[:, idx], Ssrc.mean(1)); rec("rs_learn", n, rg.predict(Y))
            # AIPW as in the reference implementation (ridge alpha=10; residual shrink 1/(1+n/N))
            rest = np.setdiff1d(np.arange(N), idx)
            F_all = ridge_predictor(Ssrc, idx, Y)
            F_s = F_all[:, idx]
            rec("aipw_ref", n, F_all[:, rest].mean(1) + (Y - F_s).mean(1) / (1 + n / (N - n)))
            # anchor points (k-medoids on item correlation), weighted by cluster size
            med, w = R.anchors_kmedoids(n, seed)
            rec("anchor_w", n, Stgt[:, med] @ w)
            # pIRT (k-means on IRT item params, lambda = n/N mix of data and IRT)
            for kk in (2, 8):
                idxa, wa = R.anchors_irt(n, seed, kk)
                Ya = Stgt[:, idxa]; th = R.mirt[kk].fit_theta(Ya, idxa)
                Fa = R.mirt[kk].predict_all(th)
                unseen = np.setdiff1d(np.arange(N), idxa); lam = len(idxa) / N
                rec(f"pirt_k{kk}", n, lam * Ya.mean(1) + (1 - lam) * Fa[:, unseen].mean(1))
            # latent plug-in on a random coreset (no residual correction)
            th = m2.fit_theta(Y, idx); rec("irt_plugin", n, m2.predict_all(th).mean(1))

            # ---------------- design x predictor x (in-sample | cross-fit) grid ---
            for dname in ["uniform", "strat", "pps_resid"]:
                idx, pi = get_design(dname); Y = Stgt[:, idx]; pis = pi[idx]
                for pk in ["ridge", "lat", "knn"]:
                    rec(f"{dname}+{pk}_is", n, dr_insample(pk, Ssrc, m2, idx, pis, Y))
                    rec(f"{dname}+{pk}_cf", n, dr_crossfit(pk, Ssrc, m2, idx, pis, Y, rng_for(seed, n, "cf")))

            # ---------------- ablations of the proposed design (latent, cross-fit) --
            for g in (0.0, 0.6, 1.0):
                idx, pi = get_design("pps_resid", gamma=g); Y = Stgt[:, idx]
                rec(f"pps_resid_g{g}+lat_cf", n, dr_crossfit("lat", Ssrc, m2, idx, pi[idx], Y, rng_for(seed, n, "cf")))
            ks = (1, 4, 8) if ablate_k else (8,)
            for kk in ks:
                for dname in ("uniform", "pps_resid"):
                    idx, pi = get_design(dname, k=kk); Y = Stgt[:, idx]
                    rec(f"{dname}+lat_cf_k{kk}", n, dr_crossfit("lat", Ssrc, R.mirt[kk], idx, pi[idx], Y, rng_for(seed, n, "cf")))
        df = pd.DataFrame(rows); df["secs_task"] = time.time() - t0
        return df
    except Exception:
        traceback.print_exc()
        return pd.DataFrame()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--seed0", type=int, default=0)
    ap.add_argument("--out", default="results/main.csv")
    ap.add_argument("--datasets", default=",".join(ALL))
    ap.add_argument("--splits", default="interp,extrap,org")
    ap.add_argument("--procs", type=int, default=36)
    ap.add_argument("--budgets", default=",".join(map(str, BUDGETS)))
    ap.add_argument("--ablate_k_seeds", type=int, default=10, help="seeds < this also fit k=1,4 MIRT")
    a = ap.parse_args()
    budgets = [int(x) for x in a.budgets.split(",")]
    tasks = []
    for name in a.datasets.split(","):
        for kind in a.splits.split(","):
            if kind == "org" and name not in OPENLLM: continue
            for s in range(a.seed0, a.seed0 + a.seeds):
                tasks.append((name, kind, s, budgets, s < a.ablate_k_seeds))
    # big datasets first for load balancing
    size = {n: load_scores(n).size for n in a.datasets.split(",")}
    # seed-major order (so any prefix has every dataset with the same seeds), big datasets first within a seed
    tasks.sort(key=lambda t: (t[2], -size[t[0]]))
    print(f"{len(tasks)} tasks", flush=True)
    t0 = time.time(); parts = []
    with Pool(a.procs, maxtasksperchild=1) as pool:
        for i, df in enumerate(pool.imap_unordered(run_task, tasks)):
            parts.append(df)
            if (i + 1) % 20 == 0:
                print(f"{i+1}/{len(tasks)} done, {time.time()-t0:.0f}s", flush=True)
                pd.concat(parts).to_csv(a.out, index=False)
    out = pd.concat(parts, ignore_index=True)
    out.to_csv(a.out, index=False)
    print("done", len(out), "rows", time.time() - t0, "s")
