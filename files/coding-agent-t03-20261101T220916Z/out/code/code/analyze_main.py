"""Aggregate results/main/*/inst_*.pkl into instance-level tables (results/summary/*.parquet)."""
import os, glob, pickle, sys
import numpy as np, pandas as pd
import multiprocessing as mp
from metrics import vs_truth, pair_metrics, nogueira, rank_pos, self_agreement

SRC = os.environ.get("SHAP_SRC", "/work/results/main")
DST = os.environ.get("SHAP_DST", "/work/results/summary")
K = 3


def zstats(Phi, SE, k):
    """single-run certificate: gap between the k-th and (k+1)-th largest |phi_hat| in units of its own SE."""
    a = np.abs(Phi.astype(np.float64))
    o = np.argsort(-a, axis=1)
    r = np.arange(len(a))[:, None]
    A = a[r, o]; S = SE.astype(np.float64)[r, o]
    num = A[:, k - 1] - A[:, k]
    den = np.sqrt(S[:, k - 1] ** 2 + S[:, k] ** 2)
    z = np.where(den > 0, num / np.maximum(den, 1e-300), np.inf)
    z = np.where(np.isnan(den), 0.0, z)
    return z


def process(path):
    r = pickle.load(open(path, "rb"))
    phi, d = r["phi"], r["d"]
    a = np.sort(np.abs(phi))[::-1]
    nrm = np.linalg.norm(phi)
    top_true = rank_pos(phi[None])[0] < K
    ptrue = rank_pos(phi[None])[0]
    base = dict(ds=r["ds"], kind=r["kind"], inst=r["inst"], d=d, fx=r["fx"], f0=r["f0"], y=r["y"], rho=r["rho"],
                gap1=(a[0] - a[1]) / nrm, gap3=(a[K - 1] - a[K]) / nrm, norm=nrm)
    rows, runrows = [], []
    rng = np.random.default_rng(0)
    for (est, m), (Phi, SE) in r["runs"].items():
        Phi = Phi.astype(np.float64)
        v = vs_truth(Phi, phi, K)
        sa = self_agreement(Phi, K, 200, rng)
        pos = rank_pos(Phi)
        sd = Phi.std(0, ddof=1)
        # oracle noise-to-gap: empirical SD of the features at exact ranks K and K+1
        o = np.argsort(-np.abs(phi))
        sdk = np.sqrt(sd[o[K - 1]] ** 2 + sd[o[K]] ** 2)
        sd1 = np.sqrt(sd[o[0]] ** 2 + sd[o[1]] ** 2)
        row = dict(base, est=est, m=m, sd_rel=np.sqrt((sd ** 2).sum()) / nrm,
                   oz3=(a[K - 1] - a[K]) / max(sdk, 1e-12), oz1=(a[0] - a[1]) / max(sd1, 1e-12),
                   stab3=nogueira(pos < K), se_over_sd=float(np.nanmean(SE.mean(0) / np.maximum(sd, 1e-12))),
                   **{f"t_{k}": float(x.mean()) for k, x in v.items()},
                   **{f"r2r_{k}": float(x.mean()) for k, x in sa.items()},
                   # probability that a run's top-3 contains each exact top-3 feature etc. kept implicit
                   )
        rows.append(row)
        z1, z3 = zstats(Phi, SE, 1), zstats(Phi, SE, K)
        runrows.append(pd.DataFrame(dict(ds=r["ds"], kind=r["kind"], inst=r["inst"], est=est, m=m, run=np.arange(len(Phi)),
                                         z1=z1.astype(np.float32), z3=z3.astype(np.float32),
                                         ok1=v["top1"], ok3=v["topk"], rel=v["rel"])))
    # cost-matched two-run check: two independent runs at m/2 (pooled = their mean) vs one run at m
    two = []
    for (est, m), (Phi, SE) in r["runs"].items():
        if est != "kernel" or (est, m // 2) not in r["runs"]:
            continue
        P2 = r["runs"][(est, m // 2)][0].astype(np.float64)
        A, B = P2[:50], P2[50:100]
        ag = pair_metrics(A, B, K)["topk"]
        pooled = vs_truth(0.5 * (A + B), phi, K)["topk"]
        two.append(pd.DataFrame(dict(ds=r["ds"], kind=r["kind"], inst=r["inst"], m=m, agree=ag, ok3_pooled=pooled)))
    return (pd.DataFrame(rows), pd.concat(runrows) if runrows else None, pd.concat(two) if two else None)


if __name__ == "__main__":
    os.makedirs(DST, exist_ok=True)
    files = sorted(glob.glob(f"{SRC}/*/inst_*.pkl"))
    print(len(files), "instance files")
    with mp.get_context("fork").Pool(int(sys.argv[1]) if len(sys.argv) > 1 else 4) as pool:
        outs = pool.map(process, files, chunksize=4)
    pd.concat([o[0] for o in outs]).to_parquet(f"{DST}/inst_level.parquet")
    pd.concat([o[1] for o in outs if o[1] is not None]).to_parquet(f"{DST}/run_level.parquet")
    pd.concat([o[2] for o in outs if o[2] is not None]).to_parquet(f"{DST}/tworun.parquet")
    print("done")
