"""Experiment definitions.  Usage: python experiments.py E1 [E2 ...] [--quick]
Each experiment writes /work/results/<name>.csv (one row per world x setting x estimator)."""
import os, sys, time, itertools, json
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import numpy as np
import pandas as pd
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(__file__))
from sim import run_config

OUT = "/work/results"
NS = 6          # independent worlds (graph / outcome-parameter draws) per setting
R_DEFAULT = 300
REAL = {"stanford3", "egofb"}

ER = lambda n, d: dict(name="er", n=n, d=d)
REG = lambda n, d: dict(name="regular", n=n, d=d)
SBM = lambda n, d, K=40, ratio=30: dict(name="sbm", n=n, d=d, K=K, ratio=ratio)
BA = lambda n, m: dict(name="ba", n=n, m=m)
WS = lambda n, d, beta: dict(name="ws", n=n, d=d, beta=beta)
STAN = dict(name="stanford3")
EGO = dict(name="egofb")
BERN = lambda p=0.5: dict(type="bern", p=p)
CLU = lambda K=40, p=0.5: dict(type="cluster", K=K, p=p)
LIN = dict(kind="frac", shape="pow", k=1.0, gamma=1.0)
POW = lambda k, gamma=1.0, **kw: dict(kind="frac", shape="pow", k=k, gamma=gamma, **kw)
SIG = dict(kind="frac", shape="sigmoid", c=0.5, w=0.08, gamma=1.0)
MH = lambda lam: dict(kind="multihop", lam=lam)


def stable_seed(*objs):
    import hashlib
    h = hashlib.sha256(json.dumps(objs, sort_keys=True).encode()).hexdigest()
    return int(h[:8], 16) % (2 ** 31)


def gname(g):
    return g["name"]


def make(graph, mech, design, models, extras=(), tag=None, R=R_DEFAULT, ns=NS, infer=(), sigma=0.0, **kw):
    cfgs = []
    for i in range(ns):
        real = graph["name"] in REAL
        gseed = 0 if real else 100 + i
        wseed = 1000 + i
        cfgs.append(dict(graph=graph, gseed=gseed, mech=mech, wseed=wseed, design=design,
                         R=R, seed=stable_seed(graph, mech, design, i),
                         models=list(models), extras=list(extras), infer=list(infer), sigma=sigma,
                         tag=tag, world_i=i, **kw))
    return cfgs


def flat(d):
    out = {}
    for k, v in d.items():
        if isinstance(v, dict):
            for k2, v2 in v.items():
                out[f"{k}_{k2}"] = v2
        else:
            out[k] = v
    return out


def _worker(group):
    out = []
    for cfg in group:
        t = time.time()
        try:
            rows = run_config(cfg)
        except Exception as e:  # keep going, record failure
            import traceback
            sys.stderr.write(f"FAILED {cfg['graph']} {cfg['mech']} {cfg['design']}: {e}\n{traceback.format_exc()}\n")
            continue
        info = {k: v for k, v in cfg.items() if k in ("graph", "mech", "design", "tag", "world_i", "sigma", "obs_noise", "gseed", "wseed")}
        info = flat(info)
        for r in rows:
            r.update(info)
            r["secs"] = time.time() - t
            out.append(r)
    return out


def group_cfgs(cfgs, chunk=None):
    """group configs sharing a graph (so the graph is built once per process); chunk for balance"""
    g = {}
    for c in cfgs:
        g.setdefault((json.dumps(c["graph"], sort_keys=True), c["gseed"]), []).append(c)
    out = []
    for grp in g.values():
        ch = chunk or (4 if grp[0]["graph"]["name"] in REAL else 12)
        out += [grp[i:i + ch] for i in range(0, len(grp), ch)]
    return out


def run(name, cfgs, procs=4):
    groups = group_cfgs(cfgs)
    # biggest first for load balancing
    groups.sort(key=lambda g: -len(g) * (3 if g[0]["graph"]["name"] in REAL else 1))
    t0 = time.time()
    rows = []
    with Pool(procs) as pool:
        for i, out in enumerate(pool.imap_unordered(_worker, groups)):
            rows.extend(out)
            if i % 5 == 0:
                sys.stderr.write(f"[{name}] {i+1}/{len(groups)} groups {time.time()-t0:.0f}s\n")
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUT}/{name}.csv", index=False)
    sys.stderr.write(f"[{name}] done {len(df)} rows in {time.time()-t0:.0f}s\n")
    return df


# ----------------------------------------------------------------------------------
def E1(quick=False):
    """Variance scaling in degree d, size n, noise level, graph; correctly specified linear model."""
    M = ["ols_s", "ols_s_int", "ols_s_deg", "ols_s2"]
    X = ["dm", "hajek"]
    c = []
    for d in [4, 8, 16, 32, 64, 128, 256]:
        c += make(ER(4000, d), LIN, BERN(), M, X, tag="er_d")
    for n in [1000, 2000, 4000, 8000, 16000]:
        c += make(ER(n, 16), LIN, BERN(), M, X, tag="er_n")
    for s in [0.25, 0.5, 1.0, 2.0, 4.0]:
        c += make(ER(4000, 16), dict(LIN, sig_a=s), BERN(), M, X, tag="er_siga")
    for d in [8, 16, 32, 64, 128]:
        c += make(SBM(4000, d), LIN, BERN(), M, X, tag="sbm_d")
        c += make(SBM(4000, d), LIN, CLU(40), M, X, tag="sbm_d")
    for d in [6, 10, 20, 40]:
        c += make(WS(4000, d, 0.05), LIN, BERN(), M, X, tag="ws_d")
        c += make(WS(4000, d, 0.05), LIN, CLU(40), M, X, tag="ws_d")
    for m in [3, 6, 12, 24]:
        c += make(BA(4000, m), LIN, BERN(), M, X, tag="ba_m")
        c += make(BA(4000, m), LIN, CLU(40), M, X, tag="ba_m")
    for g in [STAN, EGO]:
        c += make(g, LIN, BERN(), M, X, tag="real")
        for K in [10, 30, 100, 300]:
            c += make(g, LIN, CLU(K), M, X, tag="real")
    return c


def E2(quick=False):
    """Nonlinear exposure response: extrapolation bias."""
    M = ["ols_s", "ols_s_quad", "ols_s_cub", "ols_s_int", "ols_s2"]
    X = ["dm", "hajek"]
    shapes = [POW(0.25), POW(0.5), POW(1.0), POW(2.0), POW(4.0), SIG]
    c = []
    graphs = [ER(4000, 30), REG(4000, 30), BA(4000, 10), SBM(4000, 30), STAN, EGO]
    for g in graphs:
        for sh in shapes:
            c += make(g, sh, BERN(), M, X, tag="shape")
            c += make(g, sh, CLU(40 if g["name"] not in REAL else 30), M, X, tag="shape")
    # degree sweep, Bernoulli, regular graphs (compare with closed-form projection bias)
    for d in [4, 8, 16, 32, 64, 128, 256]:
        for sh in [POW(0.5), POW(4.0), SIG]:
            c += make(REG(4000, d), sh, BERN(), ["ols_s", "ols_s_quad"], ["dm"], tag="reg_d")
    # n sweep: bias does not vanish
    for n in [1000, 4000, 16000]:
        for sh in [POW(4.0), SIG]:
            c += make(ER(n, 30), sh, BERN(), ["ols_s", "ols_s_quad"], ["dm"], tag="n_sweep")
    return c


def E2g(quick=False):
    """Flexible learner (gradient boosting on exposure features) under nonlinear response; expensive -> few reps."""
    c = []
    for g in [ER(4000, 30), EGO, STAN]:
        for sh in [LIN, POW(0.5), POW(4.0), SIG]:
            for d in [BERN(), CLU(40 if g["name"] not in REAL else 30)]:
                c += make(g, sh, d, ["ols_s"], ["dm", "gbm"], tag="gbm", R=40, ns=3)
    return c


def E3(quick=False):
    """Misspecified neighbourhood / exposure definition / heterogeneity."""
    c = []
    M1 = ["ols_s", "ols_s2", "ols_s_cnt"]
    X = ["dm", "hajek"]
    graphs = [(ER(4000, 30), BERN()), (SBM(4000, 30), BERN()), (SBM(4000, 30), CLU(40)),
              (EGO, BERN()), (EGO, CLU(30)), (STAN, BERN()), (STAN, CLU(30))]
    for lam in [0.0, 0.2, 0.4, 0.6, 0.8]:
        for g, d in graphs:
            c += make(g, MH(lam), d, M1, X, tag="multihop")
    M2 = ["ols_s", "ols_cnt", "ols_s_cnt", "ols_s_deg", "ols_s_deg_z"]
    gr2 = [(BA(4000, 5), BERN()), (BA(4000, 20), BERN()), (STAN, BERN()), (EGO, BERN()),
           (STAN, CLU(30)), (EGO, CLU(30))]
    for gh in ["none", "inv", "pos"]:
        for g, d in gr2:
            c += make(g, dict(LIN, gam_het=gh), d, M2, ["dm", "wls_s", "strat_s"], tag="gamhet")
    for g, d in gr2:
        c += make(g, dict(kind="count", gamma=1.0), d, M2, ["dm", "wls_s", "strat_s"], tag="count")
    return c


def E4(quick=False):
    """Crossover: regression vs. difference-in-means as spillover strength varies."""
    c = []
    for d in [8, 32, 128]:
        for n in [1000, 4000, 16000]:
            for gm in [0.0, 0.05, 0.1, 0.2, 0.35, 0.5, 0.75, 1.0, 2.0]:
                c += make(ER(n, d), POW(1.0, gm), BERN(), ["ols_s"], ["dm"], tag="cross")
    for g, K in [(EGO, 30), (STAN, 30)]:
        for gm in [0.0, 0.05, 0.1, 0.2, 0.35, 0.5, 0.75, 1.0, 2.0]:
            c += make(g, POW(1.0, gm), BERN(), ["ols_s"], ["dm"], tag="cross_real")
            c += make(g, POW(1.0, gm), CLU(K), ["ols_s"], ["dm"], tag="cross_real")
    return c


def E5(quick=False):
    """Design: treatment probability p and cluster granularity K."""
    c = []
    M = ["ols_s", "ols_s_quad", "ols_s2"]
    X = ["dm", "hajek"]
    for g in [SBM(4000, 30), EGO, STAN]:
        for p in [0.05, 0.1, 0.2, 0.3, 0.5]:
            for mech, nm in [(LIN, "lin"), (POW(4.0), "pow4"), (POW(0.5), "pow05")]:
                c += make(g, mech, BERN(p), M, X, tag=f"p_{nm}")
                c += make(g, mech, CLU(30 if g["name"] in REAL else 40, p), M, X, tag=f"p_{nm}")
        for K in [5, 10, 20, 40, 80, 160, 320, 640]:
            for mech, nm in [(LIN, "lin"), (POW(4.0), "pow4"), (MH(0.6), "mh06")]:
                c += make(g, mech, CLU(K), M, X, tag=f"K_{nm}")
    return c


def E6(quick=False):
    """Inference: coverage of 95% CIs (HC sandwich, community-clustered sandwich, 2-hop HAC)."""
    c = []
    inf = ["hc", "cr", "hac"]
    graphs = [(ER(3000, 10), BERN()), (ER(3000, 30), BERN()), (SBM(3000, 20), BERN()), (SBM(3000, 20), CLU(40)),
              (EGO, BERN()), (EGO, CLU(30)), (STAN, BERN()), (STAN, CLU(30))]
    for g, d in graphs:
        for mech, nm in [(LIN, "lin"), (POW(0.5), "pow05"), (MH(0.4), "mh04")]:
            c += make(g, mech, d, ["ols_s"], ["dm"], tag=f"inf_{nm}", R=400, infer=inf)
    return c


def E7(quick=False):
    """Mis-measured network: observed graph has a fraction of edges replaced by random ones."""
    c = []
    for g, d in [(ER(4000, 30), BERN()), (SBM(4000, 30), CLU(40)), (EGO, BERN()), (EGO, CLU(30)), (STAN, BERN()), (STAN, CLU(30))]:
        for f in [0.0, 0.05, 0.1, 0.2, 0.4]:
            for cf in make(g, LIN, d, ["ols_s", "ols_s2"], ["dm"], tag="obsnoise"):
                cf["obs_noise"] = dict(drop=f)
                c.append(cf)
    return c


EXPS = dict(E1=E1, E2=E2, E2g=E2g, E3=E3, E4=E4, E5=E5, E6=E6, E7=E7)

if __name__ == "__main__":
    names = [a for a in sys.argv[1:] if not a.startswith("--")]
    for nm in names:
        cfgs = EXPS[nm]()
        sys.stderr.write(f"{nm}: {len(cfgs)} configs\n")
        run(nm, cfgs)
