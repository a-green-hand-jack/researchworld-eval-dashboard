import numpy as np, sys, time
from multiprocessing import Pool
import leaver, sr
LMAX = {1: 0.60, 2: 1.15, 3: 1.65, 4: 2.15, 5: 2.65, 6: 3.15}
LMIN = {1: 0.10, 2: 0.20, 3: 0.35, 4: 0.50, 5: 0.65, 6: 0.80}
AGRID = np.concatenate([np.linspace(0.30, 0.95, 40), 1 - np.logspace(np.log10(0.05), -4, 30)[1:]])
AGRID = np.unique(np.round(AGRID, 6))
hyd = lambda al, n: al*(1 - al**2/(2*n**2))
def row(args):
    l, a = args
    n = l + 1
    als = np.linspace(LMIN[l], LMAX[l], 56)
    out = np.full((len(als), 2), np.nan)
    wprev = None
    for i, al in enumerate(als):
        if wprev is None:
            guess = hyd(al, n) + 1j*float(sr.gamma(al, a, l))
        else:
            guess = wprev + (hyd(al, n) - hyd(als[i-1], n))
        try:
            w = leaver.solve(a, al, l, N=1500, w0=guess)
            if np.isfinite(w) and abs(w.real - hyd(al, n)) < 0.25*al and abs(w.imag) < 1e-3:
                out[i] = (w.real, w.imag); wprev = w
            else:
                wprev = None
        except Exception as e:
            wprev = None
    return l, a, als, out
if __name__ == '__main__':
    t = time.time()
    jobs = [(l, a) for l in (1, 2, 3, 4, 5, 6) for a in AGRID]
    with Pool() as p: res = p.map(row, jobs, chunksize=2)
    tab = {}
    for l, a, als, out in res:
        tab.setdefault(l, {'a': [], 'al': als, 'w': []})
        tab[l]['a'].append(a); tab[l]['w'].append(out)
    np.savez('/work/outputs/leaver_table.npz', **{f'l{l}_a': np.array(tab[l]['a']) for l in tab},
             **{f'l{l}_al': tab[l]['al'] for l in tab}, **{f'l{l}_w': np.array(tab[l]['w']) for l in tab})
    print('done', time.time()-t)
