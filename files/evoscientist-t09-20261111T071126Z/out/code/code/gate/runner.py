"""Run one simulation configuration: several populations x many random assignments x several estimators."""
from __future__ import annotations

import time

import numpy as np
import pandas as pd
import scipy.sparse as sp

from .core import (Ctx, Design, OutcomeSpec, Population, REGRESSION, dm_gate, gbm_gate, hajek_gate, ols_gate)
from .graphs import get_graph, graph_stats


def _drop_edges(A, q, rng):
    if q <= 0:
        return A
    U = sp.triu(A, k=1).tocoo()
    keep = rng.random(len(U.row)) >= q
    M = sp.coo_matrix((np.ones(keep.sum()), (U.row[keep], U.col[keep])), shape=A.shape).tocsr()
    return (M + M.T).tocsr()


def _two_hop(A):
    B = (A @ A).tocsr()
    B.setdiag(0)
    B.eliminate_zeros()
    B = B - B.multiply(A)
    B.data = (B.data > 0).astype(float)
    B.eliminate_zeros()
    return B


def run_config(cfg: dict) -> tuple[pd.DataFrame, list]:
    t0 = time.time()
    g = cfg["graph"]
    spec = OutcomeSpec(**cfg.get("spec", {}))
    des = Design(**cfg.get("design", {}))
    ests = cfg["ests"]
    n_pops, n_reps, seed = cfg.get("n_pops", 4), cfg.get("n_reps", 150), cfg["seed"]
    rb = cfg.get("batch", 50)
    rows, gstats = [], []
    for pi in range(n_pops):
        A, lab = get_graph(g["kind"], g.get("n", 0), g.get("d", 0), seed=cfg.get("gseed", seed) * 100 + pi, K=g.get("K", 100),
                           mix=g.get("mix", 0.2))
        rng_pop = np.random.default_rng([seed, pi, 1])
        rng_as = np.random.default_rng([seed, pi, 2])
        pop = Population(A, lab, spec, rng_pop)
        tau = pop.gate()
        # analyst's graph (possibly corrupted)
        q = cfg.get("edge_drop", 0.0)
        Aobs = _drop_edges(A, q, np.random.default_rng([seed, pi, 3]))
        degobs = np.maximum(np.asarray(Aobs.sum(1)).ravel(), 1.0)
        ld = np.log(degobs)
        ctx = Ctx(deg=degobs, dbar=degobs.mean(), dstd=(ld - ld.mean()) / ld.std(), s_oracle=spec.s)
        A2obs = _two_hop(Aobs) if "two_hop" in ests else None
        B = None
        if cfg.get("hac", False):
            I = sp.identity(A.shape[0], format="csr")
            B = ((Aobs + I) @ (Aobs + I)).tocsr()
            B.data[:] = 1.0
        lp1 = lp0 = None
        if "hajek" in ests:
            lp1, lp0 = des.log_pi(A, lab)
        st = graph_stats(A, lab)
        st.update(pop=pi, tau=tau, **{k: cfg["graph"].get(k) for k in ("kind",)})
        gstats.append(st)
        done = 0
        while done < n_reps:
            R = min(rb, n_reps - done)
            Z = des.draw(A.shape[0], lab, R, rng_as)
            Y = pop.outcome(Z)
            CNT = (Aobs @ Z)
            F = CNT / degobs[:, None]
            F2 = (A2obs @ Z) / np.maximum(np.asarray(A2obs.sum(1)).ravel(), 1)[:, None] if A2obs is not None else None
            if A2obs is not None:
                nod = np.asarray(A2obs.sum(1)).ravel() == 0
                F2[nod] = F[nod]
            for r in range(R):
                z, y, f = Z[:, r], Y[:, r], F[:, r]
                base = dict(pop=pi, rep=done + r, tau=tau,
                            cov_ext=float(np.mean((f <= .1) | (f >= .9))),
                            corr_zf=float(np.corrcoef(z, f)[0, 1]) if z.std() > 0 else np.nan,
                            sd_f=float(f.std()), mean_z=float(z.mean()))
                for e in ests:
                    out = dict(base, est=e, hat=np.nan, se_hc=np.nan, se_hac=np.nan, se_mb=np.nan, s2=np.nan)
                    if e == "dm":
                        out["hat"] = dm_gate(y, z)
                    elif e == "hajek":
                        h, n1, n0 = hajek_gate(y, z, CNT[:, r], degobs, lp1, lp0)
                        out.update(hat=h, n1=n1, n0=n0)
                    elif e == "gbm":
                        out["hat"] = gbm_gate(y, z, f, ctx)
                    else:
                        est, se_hc, se_hac, se_mb, s2 = ols_gate(e, y, z, f, ctx, f2=None if F2 is None else F2[:, r], B=B)
                        out.update(hat=est, se_hc=se_hc, se_hac=se_hac, se_mb=se_mb, s2=s2)
                    rows.append(out)
            done += R
    df = pd.DataFrame(rows)
    df["exp"] = cfg.get("exp")
    df["cid"] = cfg.get("cid")
    df["sec"] = time.time() - t0
    for st in gstats:
        st["cid"] = cfg.get("cid")
    return df, gstats
