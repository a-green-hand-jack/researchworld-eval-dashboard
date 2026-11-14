"""Shared experiment utilities: dataset registry with score-noise samplers, rank-conditional targets."""
import numpy as np
import lbmanip as L
import datasets_lb as D

OLLB_BASELINE = {'IFEval': 0.0, 'BBH': 0.2798, 'MATH Lvl 5': 0.0, 'GPQA': 0.25, 'MUSR': 0.3305, 'MMLU-PRO': 0.10}


class Dataset:
    def __init__(self, name):
        self.name = name
        if name == 'helm':
            S, models, tasks, n = D.load_helm()
            self.scale = np.ones(len(tasks))
        elif name == 'ollb6':
            S, models, tasks, n, _ = D.load_ollb6()
            self.scale = 1.0 / (1 - np.array([OLLB_BASELINE[t] for t in tasks]))
        elif name == 'ollbfine':
            S, models, tasks, n = D.load_ollb_fine()
            self.scale = np.ones(len(tasks))
        else:
            raise ValueError(name)
        self.S, self.models, self.tasks, self.n = S, models, tasks, np.asarray(n)
        if name == 'ollb6':   # raw accuracy implied by the normalised score (for the binomial noise model)
            b = np.array([OLLB_BASELINE[t] for t in tasks])
            self.raw = np.where(S > 0, b + S * (1 - b), np.nan)
        else:
            self.raw = S.copy()

    @property
    def N(self): return self.S.shape[0]
    @property
    def m(self): return self.S.shape[1]

    def noisy(self, rng):
        """Parametric bootstrap: each cell ~ Binomial(n_j, p)/n_j around the observed value (p = observed raw
        accuracy), mapped back to the leaderboard scale (normalisation for ollb6, clipped at 0)."""
        p = np.clip(np.nan_to_num(self.raw, nan=0.0), 0, 1)
        k = rng.binomial(self.n[None, :].astype(int), p) / self.n[None, :]
        if self.name == 'ollb6':
            out = np.maximum(0.0, self.S + (k - p) * self.scale[None, :])
            out = np.where(self.S > 0, out, np.maximum(0.0, (k - p) * self.scale[None, :]) * (self.S > 0))
            return np.clip(out, 0, 1)
        return np.clip(k, 0, 1)


def order_by(rule, S, w=None):
    a = L.aggregate(rule, S, w)
    return np.argsort(-a, kind='stable'), a


def cell(rule, S, t, cap='frontier', delta=None, ceiling=1.0, time_limit=120):
    u = L.make_caps(S, t, cap, delta=delta, ceiling=ceiling)
    return L.min_investment(rule, S, t, u, time_limit=time_limit)
