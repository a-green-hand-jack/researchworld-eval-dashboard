"""Monte-Carlo runner. Usage: python run_experiments.py <EXP> [--reps R] [--procs P]
Each replicate: draw n labeled + N unlabeled points i.i.d. from a DGP with known truth, compute 95% intervals for all methods.
Writes results/<EXP>.csv.gz with one row per (cell, rep) and lo_/hi_/est_ columns per method."""
import sys, os, zlib, time, argparse, itertools
for _v in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']: os.environ[_v]='1'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from multiprocessing import Pool
import ppi_py
from cppi import crossfit_mean, ci_from, ppi_pp_unclipped_ci, classical_ci
from dgps import PopDGP, SynthQuad, SynthLogit

ALPHA = 0.05
METHODS = ['classical', 'ppi', 'ppipp', 'ppipp_u', 'lin', 'iso', 'bin10', 'spl', 'auto']
BASE_SEED = 20261111

def make_dgp(spec):
    kind = spec[0]
    if kind == 'pop': return PopDGP(spec[1], spec[2])
    if kind == 'quad': return SynthQuad(**spec[1])
    if kind == 'slogit': return SynthLogit(**spec[1])
    if kind == 'plankton_noshift': 
        d = np.load('/work/data/plankton.npz'); return PopDGP('plankton2013', 'id', y=d['Y'].astype(float), f=d['Yhat'].astype(float))
    if kind == 'plankton_shift':
        d = np.load('/work/data/plankton.npz')
        return PopDGP('plankton2013->2014', 'id', y=d['Y'].astype(float), f=d['Yhat'].astype(float),
                      f_unl_pool=d['Yhat_unlabeled'].astype(float), truth=float(d['Y_unlabeled'].mean()))
    raise ValueError(spec)

def f1(x): return float(np.ravel(x)[0])

def one_rep(dgp, n, N, rng, methods):
    y, fl, fu = dgp.sample(rng, n, N)
    out = {}
    if 'classical' in methods:
        lo, hi = ppi_py.classical_mean_ci(y, alpha=ALPHA); out['classical'] = (f1(lo), f1(hi), y.mean())
    if N > 0:
        if 'ppi' in methods:
            lo, hi = ppi_py.ppi_mean_ci(y, fl, fu, alpha=ALPHA, lam=1.0); out['ppi'] = (f1(lo), f1(hi), np.nan)
        if 'ppipp' in methods:
            lo, hi = ppi_py.ppi_mean_ci(y, fl, fu, alpha=ALPHA); out['ppipp'] = (f1(lo), f1(hi), np.nan)
        if 'ppipp_u' in methods:
            lo, hi = ppi_pp_unclipped_ci(y, fl, fu, ALPHA); out['ppipp_u'] = (lo, hi, np.nan)
    for k in ['lin', 'iso', 'bin10', 'spl', 'auto']:
        if k in methods:
            th, se = crossfit_mean(y, fl, fu, k, K=5, rng=rng); lo, hi = ci_from(th, se, ALPHA); out[k] = (lo, hi, th)
    return out

def run_chunk(args):
    cell_id, spec, n, N, rep0, rep1, methods = args
    dgp = make_dgp(spec); rows = []
    for r in range(rep0, rep1):
        rng = np.random.default_rng(np.random.SeedSequence([BASE_SEED, zlib.crc32(cell_id.encode()), r]))
        o = one_rep(dgp, n, N, rng, methods)
        row = dict(cell=cell_id, dgp=dgp.name, n=n, N=N, rep=r, truth=dgp.truth)
        for k, (lo, hi, th) in o.items(): row[f'lo_{k}'] = lo; row[f'hi_{k}'] = hi; row[f'est_{k}'] = th
        rows.append(row)
    return rows

# ---------------- experiment definitions ----------------
REAL = ['galaxies', 'forest', 'alphafold', 'gene_expression', 'census_income', 'census_healthcare', 'census_education']
def cells(exp):
    C = []  # (spec, n, N)
    if exp == 'E1a':   # real data, original predictors, vary n at N=20000
        for ds in REAL:
            for n in [50, 100, 200, 500, 1000, 2000, 5000]: C.append((('pop', ds, 'id'), n, 20000))
    elif exp == 'E1b':  # real data, vary N at n=500
        for ds in REAL:
            for N in [50, 250, 1000, 5000, 50000]: C.append((('pop', ds, 'id'), 500, N))
    elif exp == 'E2':  # distorted (uncalibrated, monotone-transformed) predictor outputs
        for ds, tr in [('galaxies', 'logit'), ('galaxies', 'pow3'), ('alphafold', 'logit'), ('forest', 'logit'),
                       ('gene_expression', 'exp'), ('census_healthcare', 'logit'), ('census_income', 'sqrt')]:
            for n in [100, 300, 1000, 3000]: C.append((('pop', ds, tr), n, 20000))
    elif exp == 'E3a':  # synthetic quadratic: nonlinearity sweep, theory check
        for c in [0.0, 0.25, 0.5, 1.0, 2.0]:
            for N in [100, 500, 5000, 50000]: C.append((('quad', dict(a=1.0, c=c, sigma=1.0)), 500, N))
    elif exp == 'E3b':  # synthetic quadratic: n sweep (small-n cost of flexible recalibration), N = 20n capped
        for c in [0.0, 1.0]:
            for n in [25, 50, 100, 200, 500, 1000, 2000]: C.append((('quad', dict(a=1.0, c=c, sigma=1.0)), n, 20000))
    elif exp == 'E3c':  # synthetic logit-scale classifier
        for n in [50, 100, 200, 500, 1000, 3000]: C.append((('slogit', dict(mu=-1.0, s=2.0)), n, 20000))
        for N in [50, 500, 5000, 50000]: C.append((('slogit', dict(mu=-1.0, s=2.0)), 500, N))
    elif exp == 'E3d':  # synthetic logit-scale classifier with sharp (over-confident) logits
        for n in [50, 100, 200, 500, 1000, 3000]: C.append((('slogit', dict(mu=-1.0, s=4.0)), n, 20000))
        for N in [50, 500, 5000, 50000]: C.append((('slogit', dict(mu=-1.0, s=4.0)), 500, N))
    elif exp == 'E4':   # binary predictor (no gain expected) and distribution shift (all methods invalid)
        for n in [100, 500, 2000, 10000]:
            C.append((('plankton_noshift',), n, 20000)); C.append((('plankton_shift',), n, 20000))
    else: raise ValueError(exp)
    return C

def cell_id(spec, n, N): return f'{spec[0]}:{"|".join(str(s) for s in spec[1:])}:n{n}:N{N}'

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('exp'); ap.add_argument('--reps', type=int, default=2000)
    ap.add_argument('--procs', type=int, default=36); ap.add_argument('--chunk', type=int, default=50)
    a = ap.parse_args(); t0 = time.time()
    jobs = []
    for spec, n, N in cells(a.exp):
        cid = cell_id(spec, n, N)
        for r0 in range(0, a.reps, a.chunk): jobs.append((cid, spec, n, N, r0, min(a.reps, r0 + a.chunk), METHODS))
    rows = []
    with Pool(a.procs) as p:
        for i, rs in enumerate(p.imap_unordered(run_chunk, jobs)):
            rows += rs
            if i % 50 == 0: print(f'{a.exp}: {i+1}/{len(jobs)} chunks, {time.time()-t0:.0f}s', flush=True)
    df = pd.DataFrame(rows).sort_values(['cell', 'rep'])
    os.makedirs('/work/results', exist_ok=True); df.to_csv(f'/work/results/{a.exp}.csv.gz', index=False)
    print(f'done {a.exp}: {len(df)} rows in {time.time()-t0:.0f}s')
