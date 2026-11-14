"""Shared helpers: load experiment outputs, compute metrics with Monte-Carlo CIs, theory predictions."""
import ast
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gate.core import OutcomeSpec, bern_frac_pseudotrue, harmonic_degree  # noqa: E402
from gate.graphs import get_graph, load_egofb, load_stanford3  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
FIG = os.path.join(ROOT, "figures")
TAB = os.path.join(ROOT, "tables")
os.makedirs(FIG, exist_ok=True)
os.makedirs(TAB, exist_ok=True)


def load(ex):
    reps = pd.read_csv(os.path.join(RES, f"{ex}_reps.csv.gz"))
    gr = pd.read_csv(os.path.join(RES, f"{ex}_graphs.csv"))
    cf = pd.read_csv(os.path.join(RES, f"{ex}_configs.csv"))
    rows = []
    for _, r in cf.iterrows():
        g, sp_, d = ast.literal_eval(r.graph), ast.literal_eval(r.spec), ast.literal_eval(r.design)
        rows.append(dict(cid=r.cid, tag=r.tag, seed=r.seed, gkind=g["kind"], n_spec=g.get("n", np.nan), d_spec=g.get("d", np.nan),
                         mix=g.get("mix", np.nan), K=g.get("K", np.nan), s=sp_.get("s", 0.0), sigma=sp_.get("sigma", 1.0),
                         comm_sd=sp_.get("comm_sd", 1.0), deg_coef=sp_.get("deg_coef", 0.5), channel=sp_.get("channel", "frac"), omega=sp_.get("omega", 0.0),
                         dkind=d.get("kind"), p=d.get("p"), edge_drop=r.edge_drop))
    cf2 = pd.DataFrame(rows)
    return reps, gr, cf2


def _boot(x, f, B=300, seed=0):
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(x), size=(B, len(x)))
    vals = np.array([f(x[i]) for i in idx])
    return np.percentile(vals, [2.5, 97.5])


def metrics(reps, cf, boot=True):
    """Per (config, estimator): bias, sd, rmse, relative errors, coverage; MC CIs by replicate bootstrap."""
    out = []
    reps = reps.copy()
    reps["err"] = reps.hat - reps.tau
    for (cid, est), g in reps.groupby(["cid", "est"]):
        ok = g[np.isfinite(g.hat)]
        tau = g.tau.mean()
        e = ok.err.values
        r = dict(cid=cid, est=est, n=len(g), fail=1 - len(ok) / len(g), tau=tau, bias=e.mean() if len(e) else np.nan,
                 sd=ok.hat.std() if len(e) > 1 else np.nan, rmse=np.sqrt(np.mean(e ** 2)) if len(e) else np.nan)
        r["sd_pop"] = np.sqrt(ok.groupby("pop").hat.var().mean()) if len(e) > 1 else np.nan   # within-population SD
        r["rel_rmse"] = r["rmse"] / abs(tau)
        r["rel_bias"] = r["bias"] / abs(tau)
        if boot and len(e) > 20:
            lo, hi = _boot(e, lambda x: np.sqrt(np.mean(x ** 2)), B=200)
            r["rmse_lo"], r["rmse_hi"] = lo, hi
            lo, hi = _boot(e, np.mean, B=200)
            r["bias_lo"], r["bias_hi"] = lo, hi
        if ok.se_hc.notna().any():
            ctr = ok.groupby("pop").hat.transform("mean")      # pseudo-true proxy (pop-level mean estimate)
            for nm in ("hc", "hac", "mb"):
                se = ok["se_" + nm]
                if se.notna().any():
                    r["cov_" + nm] = float(np.mean(np.abs(ok.err) <= 1.96 * se))
                    r["covps_" + nm] = float(np.mean(np.abs(ok.hat - ctr) <= 1.96 * se))
                    r["se_" + nm] = float(se.mean())
            r["s2"] = float(ok.s2.mean())
        for c in ("cov_ext", "corr_zf", "sd_f"):
            r[c] = float(g[c].mean())
        out.append(r)
    m = pd.DataFrame(out).merge(cf, on="cid")
    return m


def pop_degrees(row, pop):
    """Degree sequence of population `pop` of config row (re-generated deterministically)."""
    if row.gkind == "stanford3":
        A = load_stanford3()
    elif row.gkind == "egofb":
        A = load_egofb()
    else:
        A, _ = get_graph(row.gkind, int(row.n_spec), int(row.d_spec), seed=int(row.seed) * 100 + pop, K=int(row.K) if row.K == row.K else 100,
                         mix=row.mix if row.mix == row.mix else 0.2, need_labels=(row.gkind == "sbm"))
    return np.asarray(A.sum(1)).ravel()
