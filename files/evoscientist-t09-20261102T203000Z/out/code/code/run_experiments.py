import os
for _v in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS"):
    os.environ[_v]="1"
"""Run simulation experiments.  Usage: python code/run_experiments.py E1 [E2grid ...] [--procs 36] [--quick]

Each experiment writes results/<exp>_scen.csv (one row per scenario), results/<exp>_raw.csv.gz (one row per
scenario x replicate x estimator) and results/<exp>_pred.csv (population-OLS theory predictions).
"""
import os, sys, time, argparse, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
import multiprocessing as mp
from gate_lib import *

RES = os.path.join(ROOT, "results")
os.makedirs(RES, exist_ok=True)

SYN = ["er", "sbm", "ba", "ws", "rgg"]
REAL = ["egofb", "stanford3"]
N_SYN, D_SYN = 4000, 20
EST_MAIN = ["DM", "OLS-f", "OLS-s", "OLS-sx", "OLS-fx", "OLS-fs", "OLS-quad", "OLS-2hop", "OLS-full", "Oracle",
            "GBM", "Hajek-full", "Hajek-eps"]
EST_SWEEP = ["DM", "OLS-f", "OLS-fx", "OLS-quad", "Oracle", "GBM"]
PRED_MAIN = ["OLS-f", "OLS-s", "OLS-sx", "OLS-fx", "OLS-fs", "OLS-quad", "OLS-2hop", "OLS-full", "Oracle"]
PRED_SWEEP = ["OLS-f", "OLS-fx", "OLS-quad", "Oracle"]


def gspec(kind, gseed=0, n=N_SYN, d=D_SYN, **kw):
    if kind in ("egofb", "stanford3"):
        return dict(kind=kind, gseed=0)
    g = dict(kind=kind, n=n, d=d, gseed=gseed)
    if kind == "sbm":
        g.update(K=kw.get("K", 20), ratio=kw.get("ratio", 10.0))
    if kind == "ws":
        g.update(beta=kw.get("beta", 0.1))
    return g


def mk(exp, kind, mech, reps_total=200, chunks=5, n=N_SYN, d=D_SYN, kappa=2.0, p=0.5, dkind="bern", res=1.0,
       est=EST_MAIN, pred=PRED_MAIN, outcome_extra=None, obs_noise=0.0, gkw=None, tag=""):
    """One scenario per graph seed (synthetic) or per chunk (real graphs)."""
    out = []
    for c in range(chunks):
        gs = gspec(kind, gseed=c, n=n, d=d, **(gkw or {})) if kind not in REAL else gspec(kind)
        o = dict(kappa=kappa)
        o.update(outcome_extra or {})
        out.append(dict(exp=exp, tag=tag, graph=gs, mech=mech, outcome=o, design=dict(kind=dkind, p=p, res=res),
                        estimators=est, pred_for=pred, reps=reps_total // chunks, chunk=c, obs_noise=obs_noise))
    return out


def exp_E1():
    S = []
    mechs = [("lin-frac", 1), ("lin-sum", 1), ("pow", 2.0), ("pow", 4.0), ("thresh", 1), ("lin-2hop", 1),
             ("het-frac", 1)]
    for g in SYN + REAL:
        for m, k in mechs:
            S += mk("E1", g, m, kappa=k)
    return S


def exp_E2grid():
    S = []
    for kap in [0.5, 1, 2, 3, 4, 6]:
        for p in [0.1, 0.2, 0.3, 0.5, 0.7, 0.8, 0.9]:
            S += mk("E2grid", "er", "pow", kappa=kap, p=p, est=EST_SWEEP, pred=PRED_SWEEP)
    return S


def exp_E2deg():
    S = []
    for kind, ds in [("er", [2, 3, 5, 10, 20, 40, 80, 160]), ("ws", [2, 4, 6, 10, 20, 40, 80, 160])]:
        for d in ds:
            for kap, p in [(1, 0.5), (4, 0.5), (2, 0.8)]:
                S += mk("E2deg", kind, "pow", kappa=kap, p=p, d=d, est=EST_SWEEP, pred=PRED_SWEEP,
                        gkw=dict(beta=1.0) if kind == "ws" else None)
    return S


def exp_E2n():
    S = []
    for n in [500, 1000, 2000, 4000, 8000, 16000]:
        for kap in [1, 4]:
            S += mk("E2n", "er", "pow", kappa=kap, n=n, est=EST_SWEEP, pred=PRED_SWEEP)
    return S


def exp_E3():
    S = []
    est = ["DM", "OLS-f", "OLS-fx", "OLS-quad", "OLS-2hop", "OLS-full", "Oracle", "GBM", "Hajek-full", "Hajek-eps"]
    pred = ["OLS-f", "OLS-fx", "OLS-quad", "OLS-2hop", "OLS-full", "Oracle"]
    mechs = [("lin-frac", 1), ("pow", 4.0), ("thresh", 1), ("lin-sum", 1)]
    for g in ["sbm", "egofb", "stanford3"]:
        for m, k in mechs:
            S += mk("E3", g, m, kappa=k, dkind="bern", est=est, pred=pred, tag="bern")
            for res in [1.0, 3.0, 10.0]:
                S += mk("E3", g, m, kappa=k, dkind="cluster", res=res, est=est, pred=pred, tag=f"cl{res}")
    return S


def exp_E3c():
    """Cluster-level dose randomisation (q_c ~ U(0,1)) vs Bernoulli(0.5) vs cluster randomisation."""
    S = []
    est = ["DM", "OLS-f", "OLS-fx", "OLS-quad", "Oracle", "GBM"]
    pred = ["OLS-f", "OLS-fx", "OLS-quad", "Oracle"]
    mechs = [("lin-frac", 1), ("pow", 4.0), ("thresh", 1), ("lin-sum", 1)]
    for g in ["sbm", "egofb", "stanford3"]:
        for m, k in mechs:
            for res in [1.0, 3.0, 10.0]:
                S += mk("E3c", g, m, kappa=k, dkind="dose", res=res, est=est, pred=pred, tag=f"dose{res}")
    return S


def exp_E5gam():
    """Interference strength sweep: when does regression beat the plain difference in means?"""
    S = []
    est = ["DM", "OLS-f", "OLS-fx", "OLS-fs", "Oracle", "GBM"]
    pred = ["OLS-f", "OLS-fx", "OLS-fs", "Oracle"]
    for (n, d) in [(1000, 20), (4000, 20), (16000, 20), (4000, 5), (4000, 80)]:
        for gam in [0.0, 0.1, 0.25, 0.5, 1.0, 2.0]:
            for m, k in [("lin-frac", 1), ("pow", 4.0)]:
                S += mk("E5gam", "er", m, kappa=k, n=n, d=d, est=est, pred=pred, outcome_extra=dict(gam=gam))
    return S


def exp_E3b():
    S = []
    est = ["DM", "OLS-f", "OLS-fx", "OLS-quad", "Oracle", "GBM"]
    pred = ["OLS-f", "OLS-fx", "OLS-quad", "Oracle"]
    for csd in [0.0, 0.5, 1.0, 2.0]:
        for m, k in [("pow", 4.0), ("thresh", 1)]:
            S += mk("E3b", "sbm", m, kappa=k, dkind="bern", est=est, pred=pred, outcome_extra=dict(comm_sd=csd), tag="bern")
            for res in [1.0, 10.0]:
                S += mk("E3b", "sbm", m, kappa=k, dkind="cluster", res=res, est=est, pred=pred,
                        outcome_extra=dict(comm_sd=csd), tag=f"cl{res}")
    return S


def exp_E4a():
    S = []
    est = ["DM", "OLS-f", "OLS-fx", "OLS-quad", "Oracle", "GBM"]
    for g in ["er", "sbm"]:
        for q in [0.0, 0.05, 0.1, 0.2, 0.4, 0.6]:
            for m, k in [("lin-frac", 1), ("pow", 4.0), ("thresh", 1)]:
                S += mk("E4a", g, m, kappa=k, est=est, pred=PRED_SWEEP, obs_noise=q)
    return S


def exp_E4b():
    S = []
    est = ["DM", "OLS-f", "OLS-fx", "OLS-2hop", "OLS-full", "Oracle", "GBM"]
    pred = ["OLS-f", "OLS-fx", "OLS-2hop", "OLS-full", "Oracle"]
    for g in ["er", "sbm"]:
        for w2 in [0.0, 0.25, 0.5, 0.75, 1.0]:
            S += mk("E4b", g, "lin-2hop", est=est, pred=pred, outcome_extra=dict(w2=w2))
    return S


def exp_E4c():
    S = []
    est = ["DM", "OLS-f", "OLS-fx", "OLS-fs", "OLS-full", "Oracle", "GBM"]
    pred = ["OLS-f", "OLS-fx", "OLS-fs", "OLS-full", "Oracle"]
    for g in ["er", "ba", "sbm"]:
        for het in [0.0, 0.25, 0.5, 0.75, 1.0]:
            S += mk("E4c", g, "het-frac", est=est, pred=pred, outcome_extra=dict(het=het))
    return S


EXPS = dict(E1=exp_E1, E2grid=exp_E2grid, E2deg=exp_E2deg, E2n=exp_E2n, E3=exp_E3, E3b=exp_E3b, E3c=exp_E3c, E5gam=exp_E5gam,
            E4a=exp_E4a, E4b=exp_E4b, E4c=exp_E4c)


def work(args):
    sid, sc = args
    t0 = time.time()
    seed = int(hashlib.md5(f"{sc['exp']}-{sid}".encode()).hexdigest()[:8], 16)
    sc = dict(sc, seed=seed)
    ctx = Context(sc)
    rng = np.random.default_rng(np.random.SeedSequence([seed, 1]))
    rows = []
    for r in range(sc["reps"]):
        res = ctx.one_rep(rng)
        for nm, (est, se, secl) in res.items():
            rows.append((sid, r, nm, est, se, secl))
    pred = []
    for nm in sc.get("pred_for", []):
        # predictions are computed separately by compute_pred.py (set GATE_INRUN_PRED=1 to also compute them here)
        if os.environ.get("GATE_INRUN_PRED") == "1" and nm in ctx.X1:
            b, v, vt, dmd = predict_ols(ctx, nm, R=150, seed=seed)
            pred.append((sid, nm, b, v, vt, dmd))
    meta = dict(sid=sid, gate=ctx.out.gate, n=ctx.net.n, dbar=ctx.net.dbar,
                dharm=1.0 / np.mean(ctx.net.invdeg), sec=time.time() - t0)
    if ctx.des.kind == "cluster":
        meta.update(n_clusters=int(ctx.des.K), intra=ctx.net.intra_fraction(ctx.des.lab))
    return meta, rows, pred


def flat(sid, sc):
    d = dict(sid=sid, exp=sc["exp"], tag=sc["tag"], mech=sc["mech"], chunk=sc["chunk"], reps=sc["reps"],
             obs_noise=sc["obs_noise"], p=sc["design"]["p"], dkind=sc["design"]["kind"], res=sc["design"]["res"])
    d.update({f"g_{k}": v for k, v in sc["graph"].items()})
    d.update({f"o_{k}": v for k, v in sc["outcome"].items()})
    return d


def run(exp, procs, quick=False):
    S = EXPS[exp]()
    if quick:
        S = [dict(s, reps=2) for s in S[:: max(1, len(S) // 12)]]
    print(f"[{exp}] {len(S)} scenarios", flush=True)
    jobs = list(enumerate(S))
    # longest first: real graphs / large n
    jobs.sort(key=lambda j: -(j[1]["graph"].get("n", 12000) * (1 + j[1]["graph"].get("d", 100) / 20)))
    metas, rows, preds = [], [], []
    t0 = time.time()
    with mp.Pool(procs, maxtasksperchild=10) as pool:
        for i, (m, r, p) in enumerate(pool.imap_unordered(work, jobs)):
            metas.append(m); rows += r; preds += p
            if (i + 1) % 20 == 0 or i + 1 == len(jobs):
                print(f"  {i+1}/{len(jobs)} done, {time.time()-t0:.0f}s", flush=True)
    scen = pd.DataFrame([flat(i, s) for i, s in enumerate(S)]).merge(pd.DataFrame(metas), on="sid")
    raw = pd.DataFrame(rows, columns=["sid", "rep", "est", "estimate", "se_hc", "se_cl"])
    pred = pd.DataFrame(preds, columns=["sid", "est", "bias_pred", "var_pred_noise", "var_pred_total", "dMd"])
    sfx = "_quick" if quick else ""
    scen.to_csv(os.path.join(RES, f"{exp}{sfx}_scen.csv"), index=False)
    raw.to_csv(os.path.join(RES, f"{exp}{sfx}_raw.csv.gz"), index=False)
    pred.to_csv(os.path.join(RES, f"{exp}{sfx}_pred.csv"), index=False)
    print(f"[{exp}] finished in {time.time()-t0:.0f}s; total CPU-s in scenarios {scen['sec'].sum():.0f}", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("exps", nargs="+")
    ap.add_argument("--procs", type=int, default=36)
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    for e in a.exps:
        run(e, a.procs, a.quick)
