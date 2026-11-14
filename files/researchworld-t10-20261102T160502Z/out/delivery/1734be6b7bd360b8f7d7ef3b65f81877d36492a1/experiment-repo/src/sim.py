"""Monte-Carlo coverage/width study. One cell = (population, n, N); R replications; all methods share the same draws.

Population spec: a real dataset name (pool = population, iid draws with replacement) or
`syn:<kind>:<kappa>:<snr>[:<tail>]` (known truth).  Seed spaces: 'dev' and 'final' use disjoint SeedSequence entropy.
Output of a cell: summary rows + raw endpoints (npz, git-ignored).
"""
import numpy as np, sys, os, time, hashlib
sys.path.insert(0, os.path.dirname(__file__))
import estimators as E
import data as D
from ppi_py import ppi_mean_ci

# M-labels follow PLAN.md: M1 classical, M2 ppi, M3 ppipp_pkg (reference), M4 cal_* (calibrated, candidates),
# M5 small-n corrected (ppipp_t / ppipp_jk on M3; cal_*_t on M4).  Others are ablations/controls.
METHODS = ["classical", "classical_t", "ppi", "ppipp_pkg", "ppipp", "ppipp_t", "ppipp_jk", "ppipp_nc", "ppipp_nc_t",
           "cal_lin", "cal_iso", "cal_bin", "cal_spl", "cal_lin_t", "cal_iso_t", "cal_bin_t", "cal_spl_t"]
RAW = "results/raw"
SPACE = {"dev": 0, "final": 1}


def seed_for(space, *a):
    h = int(hashlib.sha256("|".join(map(str, a)).encode()).hexdigest()[:8], 16)
    return np.random.SeedSequence([SPACE[space], h])


def make_pop(name):
    if name.startswith("syn:"):
        parts = name.split(":")
        kind, kappa, snr = parts[1], float(parts[2]), float(parts[3])
        tail = int(parts[4]) if len(parts) > 4 else 0
        sampler, th, _ = D.synth_sampler(kind, kappa, snr, tail)
        return {"sampler": sampler, "theta": th}
    return D.population(name)


def draw(rng, pop, n, N, shift=False, wor=False):
    if "sampler" in pop:
        Yl, fl = pop["sampler"](rng, n)
        _, fu = pop["sampler"](rng, N)
        return Yl, fl, fu
    Y, f = pop["Y"], pop["f"]
    i = rng.choice(len(Y), n, replace=False) if wor else rng.integers(0, len(Y), n)
    fu = pop["f_shift"][rng.integers(0, len(pop["f_shift"]), N)] if shift else f[rng.integers(0, len(Y), N)]
    return Y[i], f[i], fu


def one_rep(rng, pop, n, N, shift=False, wor=False):
    Yl, fl, fu = draw(rng, pop, n, N, shift, wor)
    r = {}
    r["classical"], r["classical_t"] = E.classical(Yl), E.classical(Yl, use_t=True)
    r["ppi"] = E.ppi_scores(Yl, fl, fu, lam=1.0)
    lo, hi = ppi_mean_ci(Yl, fl, fu, alpha=0.05)
    r["ppipp_pkg"] = (float(lo[0]), float(hi[0]))
    r["ppipp"], r["ppipp_t"] = E.ppi_scores(Yl, fl, fu, clip=True, both=True)
    r["ppipp_jk"] = E.ppi_jackknife(Yl, fl, fu)
    r["ppipp_nc"], r["ppipp_nc_t"] = E.ppi_scores(Yl, fl, fu, both=True)
    for kind in ["lin", "iso", "bin", "spl"]:
        r["cal_" + kind], r["cal_%s_t" % kind] = E.cal_ppi(Yl, fl, fu, kind, rng=rng, both=True)
    return r


def run_cell(args):
    name, n, N, R, space, flags = args
    shift, wor = flags.get("shift", False), flags.get("wor", False)
    pop = make_pop(name)
    theta = pop["theta_shift"] if shift else pop["theta"]
    rng = np.random.default_rng(seed_for(space, name, n, N, shift, wor))
    lo = {m: np.empty(R) for m in METHODS}
    hi = {m: np.empty(R) for m in METHODS}
    t0 = time.time()
    for k in range(R):
        r = one_rep(rng, pop, n, N, shift, wor)
        for m in METHODS:
            lo[m][k], hi[m][k] = r[m]
    tag = flags.get("tag", "")
    os.makedirs(RAW, exist_ok=True)
    np.savez_compressed(f"{RAW}/{name.replace(':', '_')}__{n}__{N}__{tag}.npz", theta=theta, R=R,
                        **{f"lo_{m}": lo[m] for m in METHODS}, **{f"hi_{m}": hi[m] for m in METHODS})
    print(f"HUTIAN_PROGRESS {space} {tag} {name} n={n} N={N} {time.time()-t0:.0f}s", flush=True)
    return (name, n, N, tag)


if __name__ == "__main__":
    import argparse
    from multiprocessing import Pool
    import grids
    ap = argparse.ArgumentParser()
    ap.add_argument("--grid", required=True, help="name in src/grids.py")
    ap.add_argument("--space", choices=["dev", "final"], default="dev")
    ap.add_argument("--R", type=int, default=None, help="override replicates")
    ap.add_argument("--raw", default=None)
    ap.add_argument("--procs", type=int, default=2)
    a = ap.parse_args()
    RAW = a.raw or f"results/raw_{a.space}_{a.grid}"
    cells = grids.GRIDS[a.grid](a.R)
    cells = [(nm, n, N, R, a.space, fl) for (nm, n, N, R, fl) in cells]
    with Pool(a.procs) as p:
        p.map(run_cell, cells, chunksize=1)
