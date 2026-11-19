"""Run one cell (graph x outcome mechanism x design) for R independent replicates.

Replicate unit: synthetic graphs redraw graph, frozen heterogeneity, noise and assignment; fixed graphs
(Stanford3, ego-Facebook) redraw heterogeneity, noise and assignment.
"""
import hashlib
import json
import time

import numpy as np

from . import estimators as E
from . import theory
from .ctx import Ctx
from .designs import Design, louvain_clusters
from .graphs import is_fixed, make_graph, perturb_edges
from .outcomes import OutSpec, freeze, potential, truth

REG_DEFAULT = ["REG-L", "REG-O"]


def stag_estimates(ctx, spec, fz, T, p, rng):
    """Staggered rollout with T+1 measurements (coverage t/T, t=0..T, random adoption order, fresh idiosyncratic
    noise per measurement; assumes no carry-over / temporal drift) against T+1 repeated Bernoulli(p) experiments
    (independent assignments, pooled regression): same number of unit-measurements. Labelled 'design with extra cost'."""
    n = ctx.n
    order = rng.permutation(n)
    rank = np.empty(n, int); rank[order] = np.arange(n)
    f = E.FEATURES["REG-L"]
    c1, c0 = ctx.corner(1), ctx.corner(0)
    D = (f(c1, ctx, spec) - f(c0, ctx, spec)).mean(0)
    out = {}

    def pooled(zs):
        Phis, ys = [], []
        for z in zs:
            st = ctx.state(z)
            Phis.append(f(st, ctx, spec))
            ys.append(potential(spec, fz, ctx, st) + spec.sigma * rng.standard_normal(n))
        Phi, y = np.vstack(Phis), np.concatenate(ys)
        return float(D @ np.linalg.lstsq(Phi, y, rcond=None)[0]), ys

    zs = [(rank < round(n * t / T)).astype(float) for t in range(T + 1)]
    est, ys = pooled(zs)
    out["STAG-REG"] = est
    out["STAG-direct"] = float(ys[-1].mean() - ys[0].mean())
    out["REPEAT-REG"] = pooled([(rng.random(n) < p).astype(float) for _ in range(T + 1)])[0]
    return out


def cell_seed(base, cfg):
    h = hashlib.sha256(json.dumps(cfg, sort_keys=True, default=str).encode()).digest()
    return int.from_bytes(h[:8], "little") ^ base


def run_cell(cfg, base_seed=0):
    """cfg keys: graph(kind,n,d,kw), out(OutSpec kwargs), design(kind,p,res), regs, ht(bool), n_rep, theory_M, sandwich, ml."""
    t0 = time.time()
    g, o, dz = cfg["graph"], cfg["out"], cfg["design"]
    regs = cfg.get("regs", REG_DEFAULT)
    spec = OutSpec(**o)
    # `seed_cfg` (optional) names the configuration whose hash seeds the cell, so an extension grid can replay the draws of an earlier one
    ss = np.random.SeedSequence(cell_seed(base_seed, cfg.get("seed_cfg", cfg)))
    rows = []
    fixed_ctx = None
    world = None
    louvain_cache = {}
    for rep, child in enumerate(ss.spawn(cfg["n_rep"])):
        rng = np.random.default_rng(child)
        rng_th = np.random.default_rng(child.spawn(1)[0])
        if cfg.get("assign_only") and world is not None:
            ctx, fz, tau, design, eps = world        # graph, heterogeneity and noise frozen: only the assignment varies
        else:
            wrng = np.random.default_rng(np.random.SeedSequence([cell_seed(base_seed, cfg.get("seed_cfg", cfg)) % 2**63, 7])) \
                if cfg.get("assign_only") else rng
            if is_fixed(g["kind"]):
                if fixed_ctx is None:
                    A, blocks = make_graph(g["kind"], q=g.get("q", 1.0))
                    fixed_ctx = Ctx(A, blocks)
                ctx = fixed_ctx
            else:
                A, blocks = make_graph(g["kind"], g.get("n", 2000), g.get("d", 20), wrng, **g.get("kw", {}))
                ctx = Ctx(A, blocks)
            fz = freeze(spec, ctx, wrng)
            tau = truth(spec, fz, ctx)
            if dz["kind"] == "gcr":
                if dz.get("labels") == "blocks" and ctx.blocks is not None:
                    lab = ctx.blocks
                else:
                    lab = louvain_clusters(ctx.A, dz.get("res", 1.0), wrng)
                design = Design("gcr", dz["p"], lab)
            else:
                design = Design("bern", dz["p"])
            eps = wrng.standard_normal(ctx.n) if cfg.get("assign_only") else None
            if cfg.get("assign_only"):
                world = (ctx, fz, tau, design, eps)
        cstats, _ = design.cluster_stats(ctx)
        z = design.draw(ctx.n, rng)
        st = ctx.state(z)
        octx = None
        if cfg.get("obs"):      # regressions see a perturbed graph; outcomes, truth and the design follow the true one
            octx = Ctx(perturb_edges(ctx.A, cfg["obs"]["q"], np.random.default_rng(child.spawn(2)[1])))
        y = potential(spec, fz, ctx, st) + spec.sigma * (eps if eps is not None else rng.standard_normal(ctx.n))
        row = dict(rep=rep, tau=tau, **ctx.graph_stats(), **cstats, p_obs=float(z.mean()))
        row["DM"] = E.dm(st, y)
        S = ctx.S_pattern() if cfg.get("sandwich") and ctx.n * (ctx.dbar + 1) ** 2 <= 3e7 else None
        if S is not None:
            row["ball2"] = float(S.nnz / ctx.n)      # mean closed 2-hop neighbourhood size (effective independent units = n / ball2)
        for nm in regs:
            est, Phi, beta, D = E.reg_estimate(nm, octx or ctx, spec, octx.state(z) if octx else st, y)
            row[nm] = est
            if S is not None:
                row[nm + "_se"] = np.sqrt(max(E.sandwich_var(Phi, y, beta, D, S), 0.0))
                e = y - Phi @ beta
                row[nm + "_se_iid"] = float(np.sqrt(max(e.var() * (D @ np.linalg.pinv(Phi.T @ Phi) @ D), 0.0)))
        if cfg.get("intervals"):
            from . import intervals as Iv
            if ctx.blocks is not None:
                lab = ctx.blocks
            elif cfg.get("assign_only"):
                if "lab" not in louvain_cache:
                    louvain_cache["lab"] = louvain_clusters(ctx.A, 1.0, wrng)
                lab = louvain_cache["lab"]
            else:
                lab = louvain_clusters(ctx.A, 1.0, rng)
            for k, v in Iv.all_se(ctx, spec, st, y, S, lab, rng, B=cfg["intervals"].get("B", 100)).items():
                row["se_" + k] = v
        if cfg.get("stag"):
            row.update(stag_estimates(ctx, spec, fz, cfg["stag"]["T"], dz["p"], rng))
        if cfg.get("diag"):
            from . import diagnostics as Dg
            S2 = S if S is not None else None
            row.update({k: v for k, v in Dg.d1(ctx, spec, st, y, "REG-L").items()})
            row["d1q"] = Dg.d1(ctx, spec, st, y, "REG-Q")["d1"]
            row.update(Dg.spread(ctx, spec, st, y))
            row.update(Dg.d3(ctx, spec, st, y, S2))
            if cfg["diag"] != "no-boot":
                lab = ctx.blocks if ctx.blocks is not None else louvain_clusters(ctx.A, 1.0, rng)
                row["boot_lo"], row["boot_hi"] = Dg.boot_pairs(ctx, spec, st, y, rng=rng)
                row["bboot_lo"], row["bboot_hi"] = Dg.boot_blocks(ctx, spec, st, y, lab, rng=rng)
            if cfg.get("d4"):
                row.update(Dg.d4(ctx, spec, st, y, row["REG-L"]))
            row["sd_y"] = float(y.std())
            row["gscale"] = abs(spec.beta) + abs(spec.gamma)
        if cfg.get("ht", False):
            h = E.HT(ctx, dz["p"], design, deltas=tuple(cfg.get("ht_deltas", (0.25,))))
            row.update(h.estimate(st, y))
            if cfg.get("ht_exact", True):
                Y1 = potential(spec, fz, ctx, ctx.corner(1)); Y0 = potential(spec, fz, ctx, ctx.corner(0))
                row["HT_var_exact"] = E.ht_exact_var(ctx, Y1, Y0, dz["p"], spec.sigma, design)
        if cfg.get("ml"):
            from .ml import ml_estimates
            row.update(ml_estimates(ctx, spec, st, y, cfg["ml"]))
        if cfg.get("theory_M", 0):
            th = theory.projection(regs, ctx, spec, fz, design, rng_th, M=cfg["theory_M"], fctx=octx)
            for nm, v in th.items():
                row[nm + "_biaspred"] = v["bias_pred"]
                row[nm + "_L"] = v["L"]
        rows.append(row)
    for r in rows:
        r["secs"] = (time.time() - t0) / len(rows)
    return rows
