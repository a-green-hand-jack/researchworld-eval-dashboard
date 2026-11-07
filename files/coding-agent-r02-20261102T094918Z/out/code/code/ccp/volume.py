"""Reference-measure size of conformal regions  C = {y in simplex : s(y, yhat) <= q}.

size(C) = P_{Y ~ Dir(a * 1)}(Y in C)  (a=1: uniform / Lebesgue on the simplex; a=1/2: Jeffreys /
Fisher-Rao volume).  Estimated by multiple importance sampling (balance heuristic) with a mixture of
the reference measure and Dirichlet(kappa * yhat + 1) proposals at several kappa; the mixture density in
the denominator bounds all weights by the number of components.
"""
import numpy as np
from scipy.special import gammaln, logsumexp

KAPPAS = (5.0, 20.0, 100.0, 500.0, 2500.0, 12500.0)


def _dir_logpdf(Y, alpha):
    # Y: (N, D); alpha: (D,) or (N, D)
    return gammaln(alpha.sum(-1)) - gammaln(alpha).sum(-1) + ((alpha - 1) * np.log(np.maximum(Y, 1e-300))).sum(-1)


def sample_proposal(yhat, a, n_per, rng, kappas=KAPPAS):
    """Return samples (N, D), log mixture density (N,), log reference density (N,)."""
    D = yhat.shape[0]
    comps = [np.full(D, a)] + [kappa * yhat + 1.0 for kappa in kappas]
    comps = np.array(comps)
    S = []
    for al in comps:
        g = rng.gamma(np.maximum(al, 1e-8), size=(n_per, D))
        g = np.maximum(g, 1e-300)
        S.append(g / g.sum(-1, keepdims=True))
    Y = np.concatenate(S)
    logq = logsumexp(np.stack([_dir_logpdf(Y, al[None, :]) for al in comps]), axis=0) - np.log(len(comps))
    logu = _dir_logpdf(Y, np.full(D, a)[None, :])
    return Y, logq, logu


def region_mass(score_fns, yhat, qs, a=1.0, n_per=1500, rng=None):
    """For one centre yhat and, for each score name, an array of radii qs[name] (any shape),
    return the reference mass of each region and the ESS of the sample (diagnostic)."""
    rng = rng or np.random.default_rng(0)
    Y, logq, logu = sample_proposal(yhat, a, n_per, rng)
    w = np.exp(logu - logq)
    w = w / len(w)
    ess = (w.sum() ** 2) / (w ** 2).sum()
    out = {}
    for name, fn in score_fns.items():
        s = fn(Y, yhat[None, :])
        q = np.asarray(qs[name])
        out[name] = ((s[None, :] <= q.reshape(-1, 1)) * w[None, :]).sum(1).reshape(q.shape)
    return out, ess
