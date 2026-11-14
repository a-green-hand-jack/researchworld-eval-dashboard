"""E1 (core): run-to-run variability of Kernel-SHAP-style and permutation SHAP estimates for a FIXED trained model,
FIXED background set and FIXED instance. Only the estimator's own randomness differs between runs.
Usage: python code/run_core.py [--quick]
Writes results/core/<dataset>_<model>.npz and results/core/cpu_time.csv
"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
import sys, time, json, argparse
import numpy as np, pandas as pd
from multiprocessing import Pool
from data import load, RESULTS, DATASETS
from models import Model, MODELS
from shapsim import *

OUT = os.path.join(RESULTS, "core")
os.makedirs(OUT, exist_ok=True)
MULTS_TABLE = [2, 4, 8, 16, 32, 64]
MULTS_LIVE = [2, 4, 8, 16, 32]
B = 100
SEED = 20261111


def setup(ds, N):
    D = load(ds, seed=0)
    rs = np.random.RandomState(1000 + DATASETS.index(ds))
    bg = D["X"][D["train"]][rs.choice(len(D["train"]), B, replace=False)]
    inst = rs.choice(D["test"], N, replace=False)
    return D, bg, inst


def z_stats(pair, phi):
    """in-run z statistics for separating (1) rank1 vs rank2, (2) rank3 vs rank4 by |phi| (needs >=2 pairs)."""
    n, d = pair.shape
    if n < 2:
        return np.nan, np.nan
    o = np.argsort(-np.abs(phi), kind="stable")
    s = np.sign(phi)
    out = []
    for r in (0, 2):
        a, b = o[r], o[r + 1]
        Dp = s[a] * pair[:, a] - s[b] * pair[:, b]
        sd = Dp.std(ddof=1)
        out.append(Dp.mean() / (sd / np.sqrt(n) + 1e-15))
    return out[0], out[1]


def work(args):
    ds, kind, pos_list, N, R, mults, scales = args
    t0 = time.process_time()
    D, bg, inst = setup(ds, N)
    dsi, ki = DATASETS.index(ds), MODELS.index(kind)
    M = Model(kind, D, seed=0)
    X = D["X"]
    d = X.shape[1]
    live = d > 12
    res = {}
    for pos in pos_list:
        x = X[inst[pos]]
        for si, scale in enumerate(scales):
            logit = scale == "logit"
            if live:
                V = LiveV(M.proba, x, bg, logit)
                v_null = float(eval_masks(M.proba, x, bg, np.zeros((1, d), bool), logit)[0])
                v_x = float(eval_masks(M.proba, x, bg, np.ones((1, d), bool), logit)[0])
                rg = np.random.default_rng([SEED, dsi, ki, pos, si, 999])
                refs = np.array([perm_shap(V, d, v_null, v_x, 64 * d, rg)[0] for _ in range(20)])
                ref, ref_se = refs.mean(0), refs.std(0, ddof=1) / np.sqrt(20)
                nonadd = np.nan
            else:
                tab = build_table(M.proba, x, bg, logit)
                V = TableV(tab)
                v_null, v_x = tab[0], tab[-1]
                ref = exact_shapley(tab)
                ref_se = np.zeros(d)
                nonadd = nonadditivity(tab, ref)
            res[(pos, scale, "ref")] = ref
            res[(pos, scale, "ref_se")] = ref_se
            res[(pos, scale, "meta")] = np.array([nonadd, v_null, v_x])
            for ei, est in enumerate(["kernel", "perm"]):
                for m_ in mults:
                    m = m_ * d
                    rg = np.random.default_rng([SEED, dsi, ki, pos, si, ei, m_])
                    phis = np.zeros((R, d))
                    zs = np.full((R, 2), np.nan)
                    nev = 0
                    for r in range(R):
                        if est == "kernel":
                            phis[r], nev = kernel_shap(V, d, v_null, v_x, m, rg)
                        else:
                            phis[r], nev, pair = perm_shap(V, d, v_null, v_x, m, rg, return_pairs=True)
                            zs[r] = z_stats(pair, phis[r])
                    res[(pos, scale, est, m_)] = (phis, zs, nev)
    return ds, kind, res, time.process_time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--procs", type=int, default=36)
    a = ap.parse_args()
    jobs = []
    plan = {}
    for ds in DATASETS:
        live = ds == "german"
        N = 100 if not live else 50
        R = 50 if not live else 30
        if a.quick:
            N, R = 6, 10
        plan[ds] = (N, R)
        chunks = np.array_split(np.arange(N), 5 if live else 2)
        scales = ["prob"] if live else ["prob", "logit"]
        mults = MULTS_LIVE if live else MULTS_TABLE
        for kind in MODELS:
            for ch in chunks:
                jobs.append((ds, kind, list(ch), N, R, mults, scales))
    jobs.sort(key=lambda j: -(j[0] == "german") * 10 - (j[1] in ("rf", "mlp")))
    t0 = time.time()
    store, cpu = {}, []
    with Pool(a.procs) as p:
        for ds, kind, res, cpu_t in p.imap_unordered(work, jobs):
            store.setdefault((ds, kind), {}).update(res)
            cpu.append(dict(dataset=ds, model=kind, cpu_s=cpu_t))
            print("done", ds, kind, "%.0fs cpu" % cpu_t, flush=True)
    wall = time.time() - t0
    scores = {}
    for (ds, kind), res in store.items():
        N, R = plan[ds]
        D, bg, inst = setup(ds, N)
        if (ds, kind) not in scores:
            scores[(ds, kind)] = Model(kind, D, seed=0).score()
        d = D["X"].shape[1]
        live = ds == "german"
        scales = ["prob"] if live else ["prob", "logit"]
        mults = MULTS_LIVE if live else MULTS_TABLE
        out = dict(inst=inst, d=d, B=B, R=R, y=D["y"][inst])
        for scale in scales:
            for key in ("ref", "ref_se", "meta"):
                out[f"{key}_{scale}"] = np.stack([res[(p_, scale, key)] for p_ in range(N)])
            for est in ("kernel", "perm"):
                for m_ in mults:
                    out[f"phi_{scale}_{est}_{m_}"] = np.stack([res[(p_, scale, est, m_)][0] for p_ in range(N)])
                    out[f"z_{scale}_{est}_{m_}"] = np.stack([res[(p_, scale, est, m_)][1] for p_ in range(N)])
                    out[f"nev_{scale}_{est}_{m_}"] = np.array(res[(0, scale, est, m_)][2])
        np.savez_compressed(os.path.join(OUT, f"{ds}_{kind}{'_quick' if a.quick else ''}.npz"), **out)
    cp = pd.DataFrame(cpu)
    cp.to_csv(os.path.join(OUT, "cpu_time%s.csv" % ("_quick" if a.quick else "")), index=False)
    pd.DataFrame([dict(dataset=k[0], model=k[1], **v) for k, v in scores.items()]).to_csv(
        os.path.join(OUT, "model_scores.csv"), index=False)
    print("total cpu hours %.3f, wall %.1f min" % (cp.cpu_s.sum() / 3600, wall / 60))


if __name__ == "__main__":
    main()
