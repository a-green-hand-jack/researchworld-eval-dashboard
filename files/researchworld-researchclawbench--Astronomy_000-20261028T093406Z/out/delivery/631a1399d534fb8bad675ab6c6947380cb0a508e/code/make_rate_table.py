"""Tabulate numerical (Leaver) growth rates for l=m=1,2,3, n=0 on a (alpha, a*) grid and
store the ratio Gamma_num/Gamma_Detweiler. Parallel over a*. Output: outputs/rate_table.npz"""
import os, sys, numpy as np, multiprocessing as mp_
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sr, leaver

A_GRID = np.array([0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.93, 0.95, 0.97, 0.99])
XF = np.array([0.10, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.92])   # alpha / alpha_crit, alpha_crit = m Omega_H r_g
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outputs")


def one(args):
    l, a = args
    acrit = l * a / (2.0 * sr.horizon(a))            # alpha at which m Omega_H = mu
    res = np.full(len(XF), np.nan)
    for i, xf in enumerate(XF):
        al = xf * acrit
        try:
            w = leaver.growth_rate(al, a, l, l)
            g = float(w.imag)
            gd = float(sr.gamma_detweiler(al, a, l))
            if g > 0 and gd > 0 and 1e-3 < g / gd < 1e3:
                res[i] = g / gd
        except Exception as e:
            print("fail", l, a, xf, repr(e)[:80], flush=True)
    print("done", l, a, res, flush=True)
    return l, a, res


if __name__ == "__main__":
    jobs = [(l, a) for l in (1, 2, 3) for a in A_GRID]
    with mp_.Pool(2) as p:
        out = p.map(one, jobs, chunksize=1)
    ratio = {l: np.array([r for (ll, a, r) in out if ll == l]) for l in (1, 2, 3)}
    np.savez(os.path.join(OUT, "rate_table.npz"), a_grid=A_GRID, x_grid=XF,
             ratio_l1=ratio[1], ratio_l2=ratio[2], ratio_l3=ratio[3])
    print("HUTIAN_WAKE: rate table finished", flush=True)
