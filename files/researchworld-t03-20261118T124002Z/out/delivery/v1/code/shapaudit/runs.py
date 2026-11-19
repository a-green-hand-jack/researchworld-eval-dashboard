"""Stage B: run every explainer arm x budget x R reruns on the exact tables of a cell and store the attributions."""
import json, os, time, zlib
import numpy as np
from . import estimators as E, cells

MULTS = [0.25, 0.5, 1, 2, 4, 16]          # x the shipped KernelSHAP budget 2d + 2048 coalitions
ARMS = ["kshap_default", "kshap_l1off", "perm", "covert_lee"]


def seed_of(*key):
    return zlib.crc32("|".join(map(str, key)).encode())


def _oracle(meta, cdir, t, ds, enc, mod, bg_idx, inst_idx, var, d):
    if meta.get("live"):
        vf = cells.LiveVF(mod, enc(ds.X[inst_idx[t]])[0], enc(ds.X[bg_idx]), enc.col_attr(), d)
        return E.Oracle(live=vf, var_idx=var, d=d)
    return E.Oracle(table=np.load(os.path.join(cdir, f"tab_{t:03d}.npy")), var_idx=var, d=d)


def run_arm(arm, orc, N, rng):
    if arm == "kshap_default": return E.kshap(orc, N, rng, l1="num_features(10)")
    if arm == "kshap_l1off": return E.kshap(orc, N, rng, l1=False)
    if arm == "perm": return E.perm(orc, N, rng)
    if arm == "covert_lee": return E.covert_lee(orc, N, rng)
    if arm == "leverage": return E.leverage_shap(orc, N, rng)
    raise ValueError(arm)


def budgets(d, mults=MULTS):
    N0 = 2 * d + 2048
    return {f"x{m:g}": int(round(N0 * m)) for m in mults}


def run_cell(cid, R=20, inst=None, arms=ARMS, mults=MULTS, tag="R20", extra_budgets=None, work=cells.WORK, verbose=True):
    cdir = os.path.join(work, "cells", cid)
    meta = json.load(open(os.path.join(cdir, "meta.json")))
    mz = np.load(os.path.join(cdir, "meta.npz"))
    d, m = len(meta["names"]), meta["m"]
    ds, enc, mod, bg_idx, inst_idx, _ = cells.setup(meta["dataset"], meta["d_sub"], meta["model"], meta["seed"], m, meta["n_inst"], out=meta.get("output", "prob"))
    bud = budgets(d, mults)
    if extra_budgets: bud.update(extra_budgets)
    inst = list(range(meta["n_inst"])) if inst is None else list(inst)
    out = {a: {b: np.zeros((len(inst), R, d), np.float32) for b in bud} for a in arms}
    se = {b: np.zeros((len(inst), R, d), np.float32) for b in bud} if "covert_lee" in arms else {}
    cost = {a: {b: np.zeros((len(inst), R)) for b in bud} for a in arms}   # coalition evaluations actually used
    secs = {a: {b: np.zeros((len(inst), R)) for b in bud} for a in arms}
    nvar = np.zeros(len(inst), int)
    for ti, t in enumerate(inst):
        var = cells.varying(ds, ds.X[inst_idx[t]], bg_idx)
        nvar[ti] = len(var)
        orc = _oracle(meta, cdir, t, ds, enc, mod, bg_idx, inst_idx, var, d)
        for a in arms:
            for b, N in bud.items():
                if a != "perm" and b == "perm500": continue
                for r in range(R):
                    rng = np.random.default_rng(seed_of(cid, t, a, b, r))
                    t0 = time.perf_counter()
                    phi, info = run_arm(a, orc, N, rng)
                    secs[a][b][ti, r] = time.perf_counter() - t0
                    out[a][b][ti, r, var] = phi
                    cost[a][b][ti, r] = info.get("n_coal", N)
                    if a == "covert_lee" and "se" in info:
                        se[b][ti, r, var] = info["se"]
        if verbose and ti % 10 == 0:
            print(cid, tag, "inst", ti, flush=True)
    arrs = {}
    for a in arms:
        for b in bud:
            arrs[f"phi/{a}/{b}"] = out[a][b]; arrs[f"cost/{a}/{b}"] = cost[a][b]; arrs[f"sec/{a}/{b}"] = secs[a][b]
    for b in se: arrs[f"se/covert_lee/{b}"] = se[b]
    np.savez_compressed(os.path.join(cdir, f"runs_{tag}.npz"), inst=np.array(inst), nvar=nvar, **arrs)
    json.dump(dict(R=R, budgets=bud, arms=arms, m=m), open(os.path.join(cdir, f"runs_{tag}.json"), "w"))


def run_certs(cid, R=20, inst=None, tag="certs", work=cells.WORK, verbose=True):
    from . import certs
    cdir = os.path.join(work, "cells", cid)
    meta = json.load(open(os.path.join(cdir, "meta.json"))); mz = np.load(os.path.join(cdir, "meta.npz"))
    d = len(meta["names"])
    ds, enc, mod, bg_idx, inst_idx, _ = cells.setup(meta["dataset"], meta["d_sub"], meta["model"], meta["seed"], meta["m"], meta["n_inst"], out=meta.get("output", "prob"))
    inst = list(range(meta["n_inst"])) if inst is None else list(inst)
    res = {}
    for ti, t in enumerate(inst):
        tab = np.load(os.path.join(cdir, f"tab_{t:03d}.npy"))
        var = cells.varying(ds, ds.X[inst_idx[t]], bg_idx)
        orc = E.Oracle(table=tab, var_idx=var, d=d)
        o = certs.audit_instance(orc, mz["phi_star"][t], R, seed_of(cid, t, "cert"))
        for k, v in o.items():
            res.setdefault(k, []).append(v)
        if verbose and ti % 10 == 0: print(cid, "certs inst", ti, flush=True)
    np.savez_compressed(os.path.join(cdir, f"{tag}.npz"), inst=np.array(inst), **{k: np.stack(v) for k, v in res.items()})
