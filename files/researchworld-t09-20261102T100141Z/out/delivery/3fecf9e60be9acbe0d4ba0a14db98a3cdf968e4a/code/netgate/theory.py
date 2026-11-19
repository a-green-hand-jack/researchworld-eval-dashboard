"""Closed-form predictions for the regression estimator OLS(1, z, f) under Bernoulli(p).

pop_bias_ols_f: asymptotic (n -> infinity, noise-free) bias from fitting a line in the neighbour fraction f when the
true exposure response is g(f):  slope = Cov(g(f), f)/Var(f) pooled over units, with f_i = Bin(d_i, p)/d_i;
GATE_hat -> tau + slope, GATE = tau + g(1) - g(0).
theory_sd (in sim.py): finite-n design-based SD for the correctly specified (linear g) case.
"""
import numpy as np
from scipy.stats import binom


def pop_bias_ols_f(deg, g, p):
    deg = np.asarray(deg).astype(int)
    ud, cnt = np.unique(deg, return_counts=True)
    w = cnt / cnt.sum()
    Eg = Egf = Vf = 0.0
    for d, wi in zip(ud, w):
        k = np.arange(d + 1)
        pk = binom.pmf(k, d, p)
        f = k / d
        gv = g(f)
        Eg += wi * (pk * gv).sum()
        Egf += wi * (pk * gv * f).sum()
        Vf += wi * (pk * (f - p) ** 2).sum()
    slope = (Egf - p * Eg) / Vf
    return slope - (g(np.array(1.0)) - g(np.array(0.0))), slope


def _row_block_sum(W, M, blk=400):
    """sum_ij W_ij * M_ij for sparse W, M (M may be a product computed blockwise by the caller)."""
    return float(W.multiply(M).sum())


def pop_plim_linear(net, out):
    """Population limit of GATE-hat from OLS(1, z, f) when the signal is *linear in z*: m_i(z) = tau z_i + sum_j M_ij z_j.
    Under Bernoulli(p) (p cancels): slope_z = tau + mean_i M_ii ;  slope_f = sum_ij W_ij M_ij / sum_ij W_ij^2.
    Covers lin_frac (+heterogeneous gamma_i -> weights proportional to 1/d_i), lin_2hop (omitted 2-hop term), lin_count.
    Returns (plim, gate)."""
    import scipy.sparse as sp
    W = net.W
    k = out.kind
    gam = out.gamma * (1 + out.het * out.zdeg)
    if k == "lin_frac":
        M = sp.diags(gam) @ W
        num = float(((sp.diags(gam) @ W.multiply(W)).sum()))        # sum_i gam_i sum_j W_ij^2
        diag = 0.0
    elif k == "lin_2hop":
        n = net.n
        num, diag = 0.0, 0.0
        for a in range(0, n, 400):
            Wb = W[a:a + 400]
            W2b = Wb @ W
            num += float(Wb.multiply(sp.diags(gam[a:a + 400]) @ Wb).sum()) + out.gamma2 * float(Wb.multiply(W2b).sum())
            diag += out.gamma2 * float(W2b.multiply(sp.csr_matrix((np.ones(Wb.shape[0]), (np.arange(Wb.shape[0]), np.arange(a, a + Wb.shape[0]))), shape=Wb.shape)).sum())
        diag /= n
    elif k == "lin_count":
        dbar = net.deg.mean()
        num = out.gamma / dbar * float(W.multiply(net.A).sum())
        diag = 0.0
    else:
        raise ValueError(k)
    den = float(W.multiply(W).sum())
    return out.tau + diag + num / den, out.gate()
