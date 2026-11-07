"""Synthetic benchmark/config model with exact truth.

X_kq ~ Bernoulli(sigmoid(mu + b_k + d_q + e_kq)),  d_q ~ N(0, sd^2) shared question difficulty,
e_kq ~ N(0, se^2) config-specific question effect, b_k = tau * eta_k with eta_k from a chosen law.
True accuracy of config k on fresh questions: E[sigmoid(mu + b_k + N(0, sd^2+se^2))] (Gauss-Hermite).
"""
import numpy as np
import sel_lib as sl

_gh_x, _gh_w = np.polynomial.hermite_e.hermegauss(80)
_gh_w = _gh_w / _gh_w.sum()


def sig(x): return 1 / (1 + np.exp(-x))


class SynthModel:
    def __init__(self, mu=0.0, sd=1.5, se=0.7, tau=0.1, law="normal", **kw):
        self.mu, self.sd, self.se, self.tau, self.law = mu, sd, se, tau, law

    def draw_b(self, K, rng):
        if self.law == "normal": eta = rng.standard_normal(K)
        elif self.law == "t3": eta = rng.standard_t(3, K) / np.sqrt(3)
        elif self.law == "spike":  # most configs identical, a few differ (sparse)
            eta = np.where(rng.random(K) < 0.1, rng.standard_normal(K) * 3.0, 0.0) / np.sqrt(0.1 * 9)
        elif self.law == "one_good":  # a single genuinely better config
            eta = np.zeros(K); eta[0] = 3.0
        else: raise ValueError
        return self.tau * eta

    def truth(self, b):
        s = np.sqrt(self.sd ** 2 + self.se ** 2)
        return (sig(self.mu + b[:, None] + s * _gh_x[None, :]) * _gh_w[None, :]).sum(1)

    def sample(self, b, n, rng):
        K = len(b)
        d = rng.normal(0, self.sd, n)
        e = rng.normal(0, self.se, (K, n))
        p = sig(self.mu + b[:, None] + d[None, :] + e)
        return (rng.random((K, n)) < p).astype(np.float64)

    def replicate(self, n, Kc, rng, **kw):
        b = self.draw_b(Kc, rng)
        tr = self.truth(b)
        S = self.sample(b, n, rng)
        return sl.estimate(S, rng, tr, np.zeros(Kc), **kw)

    def describe(self, rng, K=200, n=20000):
        b = self.draw_b(K, rng); tr = self.truth(b); S = self.sample(b, n, rng)
        C = np.corrcoef(S); rho = (C.sum() - K) / (K * (K - 1))
        return dict(mean_acc=tr.mean(), sd_acc=tr.std(), mean_pair_corr=rho)


PRESETS = {
    "base_tau0": SynthModel(tau=0.0),
    "base_tau.05": SynthModel(tau=0.05),
    "base_tau.1": SynthModel(tau=0.1),
    "base_tau.25": SynthModel(tau=0.25),
    "t3_tau.1": SynthModel(tau=0.1, law="t3"),
    "spike_tau.25": SynthModel(tau=0.25, law="spike"),
    "lowcorr_tau.1": SynthModel(tau=0.1, sd=0.3, se=1.5),
}
