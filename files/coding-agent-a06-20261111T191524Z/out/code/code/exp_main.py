"""Main experiments on an outcome matrix.  Usage: python exp_main.py WORLD OUT EXP [R] [WORKERS]
WORLD: q15 | q05 | synth ;  EXP: gap | ksweep | conclusions
Writes parquet to OUT/{EXP}_{WORLD}.parquet"""
import sys, os, itertools, time, hashlib
sys.path.insert(0, "/work/code")
import numpy as np, pandas as pd
from multiprocessing import Pool
from episodes import episode
from sim_lib import *
from worlds import synth_world, load_real

def get_world(w):
    """returns Y[K,N] (from results/world_*.npy, built by build_worlds.py) and sets the factor structure used by structured optimizers"""
    from common_b import config_list_b
    SA = [[k % 8, k // 8, 0] for k in range(40)]; SB = [list(c) for c in config_list_b()]
    if w == 'synth': set_struct(SA); return synth_world()
    L = lambda n: np.load(f"/work/results/world_{n}.npy")
    if w == 'q15': set_struct(SA); return L('q15')
    if w in ('b05', 'b15', 's17'): set_struct(SB); return L(w)
    if w == 'mix':   # 1.5B prompt/demo grid + 0.5B format/demo grid: very different quality levels in one search space
        set_struct([[0, a[0], a[1], 0] for a in SA] + [[1] + b for b in SB]); return np.concatenate([L('q15'), L('b05')])
    raise ValueError(w)

def seed_of(*a):
    return int(hashlib.md5(repr(a).encode()).hexdigest()[:8], 16)

W = {}
def init(w):
    W['Y'] = get_world(w); W['theta'] = W['Y'].mean(1)

OPT_KW = dict(grid={}, random=dict(B=8), sh=dict(frac=0.5), minibatch=dict(T=30), greedy={})

# ---------------------------------------------------------------- experiment: gap (all optimizers, all protocols)
def job_gap(args):
    opt, n, R, rep = args
    rng = np.random.default_rng(seed_of('gap', opt, n, rep)); Y, th = W['Y'], W['theta']
    space = np.arange(Y.shape[0]); rows = []
    for _ in range(R):
        r = episode(Y, th, n, opt, space, rng, OPT_KW[opt], split_f=(0.3, 0.5, 0.7)); r.update(opt=opt, n=n); rows.append(r)
    return rows

def job_norepl(args):
    opt, n, R, rep = args
    rng = np.random.default_rng(seed_of('norepl', opt, n, rep)); Y, th = W['Y'], W['theta']; space = np.arange(Y.shape[0]); rows = []
    for _ in range(R):
        r = episode(Y, th, n, opt, space, rng, OPT_KW[opt], replace=False, do_boot=False, do_cv=False, do_maxt=False, do_cond=False, do_ladder=False, split_f=())
        r.update(opt=opt, n=n); rows.append(r)
    return rows

OPTSENS = [('random', dict(B=B)) for B in (1, 2, 4, 8, 16, 40)] + [('sh', dict(frac=f)) for f in (0.1, 0.25, 0.5, 1.0)] + \
          [('minibatch', dict(T=T, bfrac=b)) for T in (10, 30, 100, 300) for b in (0.1, 0.25, 0.5)] + [('greedy', dict(sweeps=s)) for s in (1, 3)]
def job_optsens(args):
    idx, n, R, rep = args; opt, kw = OPTSENS[idx]
    rng = np.random.default_rng(seed_of('optsens', idx, n, rep)); Y, th = W['Y'], W['theta']; space = np.arange(Y.shape[0]); rows = []
    for _ in range(R):
        r = episode(Y, th, n, opt, space, rng, kw, do_boot=False, do_cv=False, do_maxt=False, do_cond=False, do_ladder=False, split_f=())
        r.update(opt=opt, n=n, kw=str(kw), idx=idx); rows.append(r)
    return rows

# ---------------------------------------------------------------- experiment: K sweep (random subsets of the config grid, exhaustive search)
def job_ksweep(args):
    K, n, R, rep, opt = args
    rng = np.random.default_rng(seed_of('ks', K, n, rep, opt)); Y, th = W['Y'], W['theta']; rows = []
    for _ in range(R):
        space = np.sort(rng.choice(Y.shape[0], K, replace=False))
        kw = dict(B=max(1, K // 2)) if opt == 'random' else OPT_KW[opt]
        r = episode(Y, th, n, opt, space, rng, kw, split_f=(0.5,), do_boot=False, do_cv=False, do_maxt=(K > 1), do_cond=False, do_ladder=False)
        r.update(K=K, n=n, opt=opt); rows.append(r)
    return rows

# ---------------------------------------------------------------- experiment: conclusions
def paired_z(a, b):
    d = a.astype(float) - b.astype(float); s = d.std(ddof=1)
    return d.mean() / (s / np.sqrt(len(d)) + 1e-12)

def job_concl(args):
    """(a) 'optimizer beats the baseline prompt' claims; (b) 'system A (large search) beats system B (small search)' claims."""
    kind, n, R, rep, par = args
    rng = np.random.default_rng(seed_of('concl', kind, n, rep, par)); Y, th = W['Y'], W['theta']; N = Y.shape[1]; K = Y.shape[0]; rows = []
    for _ in range(R):
        D = rng.integers(N, size=n); Yd = Y[:, D]; ns = n // 2
        if kind == 'lift':   # par = baseline config id; optimizer = exhaustive grid
            b = par; space = np.arange(K)
            k = int(OPTS['grid'](Yd, space, rng)['k'])
            ks = int(OPTS['grid'](Yd[:, :ns], space, rng)['k'])
            rows.append(dict(kind=kind, n=n, base=b, true_lift=th[k] - th[b], naive_lift=Yd[k].mean() - Yd[b].mean(), naive_z=paired_z(Yd[k], Yd[b]),
                             split_k_true_lift=th[ks] - th[b], split_lift=Yd[ks, ns:].mean() - Yd[b, ns:].mean(), split_z=paired_z(Yd[ks, ns:], Yd[b, ns:])))
        else:   # 'budget': A searches KA random configs, B searches KB random configs (disjoint spaces)
            KA, KB = par; perm = rng.permutation(K); sA, sB = perm[:KA], perm[KA:KA + KB]
            kA = int(OPTS['grid'](Yd, sA, rng)['k']); kB = int(OPTS['grid'](Yd, sB, rng)['k'])
            kAs = int(OPTS['grid'](Yd[:, :ns], sA, rng)['k']); kBs = int(OPTS['grid'](Yd[:, :ns], sB, rng)['k'])
            rows.append(dict(kind=kind, n=n, KA=KA, KB=KB, true_diff=th[kA] - th[kB], naive_diff=Yd[kA].mean() - Yd[kB].mean(), naive_z=paired_z(Yd[kA], Yd[kB]),
                             split_true_diff=th[kAs] - th[kBs], split_diff=Yd[kAs, ns:].mean() - Yd[kBs, ns:].mean(), split_z=paired_z(Yd[kAs, ns:], Yd[kBs, ns:]),
                             best_true_diff=th[sA].max() - th[sB].max()))
    return rows

def main():
    w, out, exp = sys.argv[1:4]; R = int(sys.argv[4]) if len(sys.argv) > 4 else 1000; nw = int(sys.argv[5]) if len(sys.argv) > 5 else 2
    os.makedirs(out, exist_ok=True)
    NS = [25, 50, 100, 200, 400, 800]; per = 250   # episodes per job; R/per jobs per cell
    reps = list(range(max(1, R // per)))
    if exp == 'gap': jobs = [(o, n, min(per, R), r) for o in OPTS for n in NS for r in reps]; fn = job_gap
    elif exp == 'norepl': jobs = [(o, n, min(per, R), r) for o in ('grid', 'minibatch') for n in (50, 100, 200) for r in reps]; fn = job_norepl
    elif exp == 'optsens': jobs = [(i, n, min(per, R), r) for i in range(len(OPTSENS)) for n in (50, 100, 200) for r in reps]; fn = job_optsens
    elif exp == 'ksweep': jobs = [(K, n, min(per * 2, R), r, 'grid') for K in (1, 2, 4, 8, 16, 24, 32, 40) for n in (50, 100, 200, 400, 800) for r in reps[:max(1, len(reps) // 2)] ] ; fn = job_ksweep
    elif exp == 'conclusions':
        jobs = [('lift', n, min(per * 2, R), r, b) for n in (50, 100, 200, 400) for b in range(Wk(w)) for r in reps[:max(1, len(reps) // 2)]]
        jobs += [('budget', n, min(per * 2, R), r, (KA, KB)) for n in (50, 100, 200, 400) for (KA, KB) in ((32, 4), (16, 4), (8, 8), (32, 8)) for r in reps[:max(1, len(reps) // 2)]]
        fn = job_concl
    t0 = time.time()
    with Pool(nw, initializer=init, initargs=(w,)) as p:
        rows = [x for res in p.imap_unordered(fn, jobs) for x in res]
    df = pd.DataFrame(rows); df.to_parquet(f"{out}/{exp}_{w}.parquet"); print(exp, w, len(df), "rows", "%.0fs" % (time.time() - t0))

def Wk(w): return {'q15': 40, 'b05': 40, 'b15': 40, 's17': 40, 'mix': 80, 'synth': 40}[w]
if __name__ == "__main__": main()
