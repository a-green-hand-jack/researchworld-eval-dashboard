"""Synthetic model x benchmark matrices from a rank-r factor model (known truth) -> data/matrices/syn_*.npz

usage: python synthetic.py <out matrices dir>
Each matrix: Y = a_j + b_j * (F W' + E),  F ~ N(0,I_r), E_ij ~ N(0, psi_j); raw scale lies roughly in [0,1].
Variants (M models x N benchmarks):
  syn_base   : r=3, N=60, M=150, iid Gaussian loadings, psi=0.3 (SNR ~ 2.7)        'incoherent'
  syn_r8     : r=8
  syn_noisy  : psi=1.0
  syn_hetero : loadings row-norm ~ lognormal(sigma=0.8) (some benchmarks barely load, some load strongly)
  syn_clust  : benchmarks in 4 clusters with near-identical loadings (high redundancy)
  syn_miss50 : base with 50% MCAR missing cells
  syn_M30    : base with only 30 models
Ground truth W, psi saved for theory checks as syn_*_truth.npz.
"""
import sys, os
import numpy as np

def gen(M, N, r, psi, seed, hetero=0.0, clusters=0, miss=0.0, psi_spread=0.0):
    rng = np.random.default_rng(seed)
    if clusters:
        C = rng.normal(size=(clusters, r))
        W = C[rng.integers(0, clusters, N)] * 0.9 + 0.15 * rng.normal(size=(N, r))
    else:
        W = rng.normal(size=(N, r)) * np.sqrt(1.0 / r) * 1.5
    if hetero:
        W = W * np.exp(hetero * rng.normal(size=(N, 1)) - hetero ** 2 / 2)
    ps = psi * np.exp(psi_spread * rng.normal(size=N))
    F = rng.normal(size=(M, r))
    Z = F @ W.T + rng.normal(size=(M, N)) * np.sqrt(ps)
    a = rng.uniform(0.3, 0.7, N); b = rng.uniform(0.03, 0.12, N)
    Y = a + b * Z
    if miss:
        Y[rng.random(Y.shape) < miss] = np.nan
    return Y, W, ps, a, b

VARIANTS = {
    'syn_base': dict(M=150, N=60, r=3, psi=0.3),
    'syn_r8': dict(M=150, N=60, r=8, psi=0.3),
    'syn_noisy': dict(M=150, N=60, r=3, psi=1.0),
    'syn_hetero': dict(M=150, N=60, r=3, psi=0.3, hetero=0.8),
    'syn_clust': dict(M=150, N=60, r=3, psi=0.3, clusters=4),
    'syn_miss50': dict(M=150, N=60, r=3, psi=0.3, miss=0.5),
    'syn_M30': dict(M=30, N=60, r=3, psi=0.3),
}

if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    for i, (n, kw) in enumerate(VARIANTS.items()):
        Y, W, ps, a, b = gen(seed=100 + i, **kw)
        np.savez_compressed(os.path.join(out, n + '.npz'), Y=Y, models=np.arange(Y.shape[0]).astype(str), benches=np.arange(Y.shape[1]).astype(str))
        np.savez_compressed(os.path.join(out, n + '_truth.npz'), W=W, psi=ps, b=b)
        print(n, Y.shape, np.isnan(Y).mean())
