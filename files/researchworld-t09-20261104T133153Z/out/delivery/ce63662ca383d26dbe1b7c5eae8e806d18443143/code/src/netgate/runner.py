"""Run one simulation cell: (graph, outcome model, design) x worlds x assignments x estimators.
cfg options added after the freeze (all default to the earlier behaviour): hac, dense_k2, boot, no_acl, kappas, extra."""
import time
import numpy as np
import pandas as pd

from . import designs, estimators, graphs
from .outcomes import Outcome

_GRAPH_CACHE = {}


def get_graph(spec, seed):
    key = (spec, seed if spec.split(":")[0] not in ("stanford3", "ego") else 0)
    if key not in _GRAPH_CACHE:
        if len(_GRAPH_CACHE) > 3:
            _GRAPH_CACHE.clear()
        _GRAPH_CACHE[key] = graphs.make(spec, seed=key[1])
    return _GRAPH_CACHE[key]


def make_design(spec, g, rng):
    """'bern:p' | 'louv:res,p' (graph clusters) | 'rand:res,p' (random clusters, same sizes) | 'block:p'."""
    kind, _, args = spec.partition(":")
    a = [float(x) for x in args.split(",")]
    if kind == "bern":
        return designs.Bernoulli(a[0])
    if kind == "louv":
        return designs.Cluster(g.clusters(a[0]), a[1], name=f"louv{a[0]}")
    if kind == "rand":
        lab = designs.random_clusters(g, g.clusters(a[0]), rng)
        return designs.Cluster(lab, a[1], name=f"rand{a[0]}")
    if kind == "block":
        return designs.Cluster(g.blocks, a[0], name="block")
    raise ValueError(spec)


def run_cell(cfg):
    """cfg keys: graph, design, outcome (dict of Outcome kwargs), worlds, reps, seed, specs, gbm, hajek, tag."""
    t0 = time.time()
    rows = []
    out_kw = cfg.get("outcome", {})
    outcome = Outcome(**out_kw)
    for w in range(cfg["worlds"]):
        seed = cfg["seed"] * 1000 + w
        rng = np.random.default_rng(seed)
        g = get_graph(cfg["graph"], seed)
        design = make_design(cfg["design"], g, rng)
        if cfg.get("no_acl"):   # grids that only need point estimates skip the analysis clusters (and the Louvain run)
            acl = None
        else:
            acl = design.labels if design.kind == "cluster" else g.clusters(cfg.get("acl_res", 1.0))
        world = outcome.world(g, rng)
        gate = outcome.gate(g, world)
        ctx = estimators.make_ctx(g, outcome, acl, hac=cfg.get("hac", True), dense_k2=cfg.get("dense_k2", False),
                                  boot=cfg.get("boot", 0), boot_rng=np.random.default_rng(seed + 7),
                                  design=design, kappas=tuple(cfg.get("kappas", ())))
        for r in range(cfg["reps"]):
            z = design.draw(g, rng)
            if z.min() == z.max():
                continue
            y = outcome.Y(g, world, z)
            res = estimators.run_all(g, z, y, design, ctx, cfg.get("specs", estimators.OLS_SPECS),
                                     use_gbm=cfg.get("gbm", False), use_hajek=cfg.get("hajek", True), seed=r,
                                     extra=tuple(cfg.get("extra", ())))
            f1 = g.W @ z
            diag = {"f1_mean_t": float(f1[z == 1].mean()), "f1_mean_c": float(f1[z == 0].mean()),
                    "f1_sd": float(f1.std()), "z_mean": float(z.mean()),
                    "supp_hi": float((f1 >= 0.9).mean()), "supp_lo": float((f1 <= 0.1).mean())}
            for name, v in res.items():
                rows.append({"world": w, "rep": r, "est_name": name, "gate": gate, **v, **diag})
    df = pd.DataFrame(rows)
    df["n"] = g.n
    df["mean_deg"] = g.mean_deg
    for k in ("graph", "design", "tag"):
        df[k] = cfg.get(k, "")
    for k, v in out_kw.items():
        df["o_" + k] = v
    df["o_mech"] = outcome.mech
    df["o_kind"] = outcome.kind
    df["secs"] = time.time() - t0
    return df
