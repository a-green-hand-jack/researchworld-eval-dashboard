"""T0: synthetic latent-probit world with exact truth.
 L_ci = mu_c + sqrt(rho) z_i + sqrt(1-rho) e_ci ;  Y_ci = 1[L_ci > 0] ;  theta_c = Phi(mu_c) exactly.
 mu_c = a + tau*(sqrt(sf)*additive-over-factors + sqrt(1-sf)*idiosyncratic) with a = Phi^-1(base_acc), tau on the probit scale.
 Every replicate draws a new world (config effects) and a new item set."""
import zlib
import numpy as np
from scipy import stats
import lib, methods

def draw_world(levels, a, tau, sf, rng):
    K = int(np.prod(levels)); co = lib.coords(levels)
    add = np.zeros(K)
    for f, L in enumerate(levels):
        u = rng.standard_normal(L); add += u[co[:, f]]
    add = add / np.sqrt(len(levels)) if len(levels) else add
    idio = rng.standard_normal(K)
    d = np.sqrt(sf) * add + np.sqrt(1 - sf) * idio
    return a + tau * d

def draw_items(mu, n, rho, rng):
    K = len(mu); z = rng.standard_normal(n); e = rng.standard_normal((K, n))
    return ((mu[:, None] + np.sqrt(rho) * z[None] + np.sqrt(1 - rho) * e) > 0).astype(np.uint8)

def binary_corr(a, rho):
    """corr of the two binary outcomes with the same marginal Phi(a), latent corr rho"""
    p = stats.norm.cdf(a); p2 = stats.multivariate_normal.cdf([a, a], mean=[0, 0], cov=[[1, rho], [rho, 1]])
    return (p2 - p * p) / (p * (1 - p))

def run_cell(cell, nrep, seed, opts=None):
    """cell: dict(cell_id, n, K, tau, rho, base_acc, procedure, sf). Returns (runs, methods) lists of dict rows."""
    levels = lib.LEVELS[cell["K"]]; a = stats.norm.ppf(cell["base_acc"])
    runs, meths = [], []
    for rep in range(nrep):
        rng = np.random.default_rng([seed, zlib.crc32(cell["cell_id"].encode()), rep])
        mu = draw_world(levels, a, cell["tau"], cell.get("sf", 0.5), rng); th = stats.norm.cdf(mu)
        Yd = draw_items(mu, cell["n"], cell["rho"], rng)
        if cell.get("leak"):   # few-shot demos drawn from D: configs with demos (index % 3 != 0, as in the real 0-shot/3-shot/3-shot family)
            for c in range(len(mu)):                                         # answer the 3 demo items of D correctly (they are shown in the prompt)
                if c % 3 != 0: Yd[c, rng.choice(cell["n"], 3, replace=False)] = 1
        run, rows = methods.run_methods(Yd, th, cell["procedure"], levels, rng, opts=opts)
        meta = dict(tier="T0", cell_id=cell["cell_id"], rep=rep, seed=seed, n=cell["n"], K=cell["K"], tau=cell["tau"], rho=cell["rho"],
                    base_acc=cell["base_acc"], procedure=cell["procedure"], leakage=int(bool(cell.get("leak"))), subject="all", n_fresh=np.nan, theta_se=0.0)
        runs.append({**meta, **run})
        for r in rows: meths.append({**{k: meta[k] for k in ("tier", "cell_id", "rep", "n", "K", "tau", "rho", "base_acc", "procedure")}, **r})
    return runs, meths
