"""Combination: MASS sampling design + kernel/latent ensemble predictor (the proposed method candidate)."""
import numpy as np
from methods import ALL
from methods2 import MASS


class MASSEns(MASS):
    """MASS design (stratified PPS sample) + prediction = 0.5 latent-model + 0.5 kernel-weighted source models,
    plus Hajek-weighted difference correction."""
    name = "mass_ens"
    k = 4
    blend = 0.5
    tau = 0.05

    def fit(self, Xs, n, seed, ctx):
        idx = super().fit(Xs, n, seed, ctx)
        self.Xs = Xs
        return idx

    def predict(self, Y):
        th = self.lat.infer(self.idx, Y)
        Pl = self.lat.prob_all(th)
        d = (Y[:, None, :] != self.Xs[None][:, :, self.idx]).mean(2)
        w = np.exp(-(d - d.min(1, keepdims=True)) / self.tau)
        w /= w.sum(1, keepdims=True)
        P = self.blend * Pl + (1 - self.blend) * (w @ self.Xs)
        return P.mean(1) + self._correction(Y, P)


class MASSEns2(MASSEns):
    name = "mass_ens_k2"
    k = 2


ALL.update({m.name: m for m in [MASSEns, MASSEns2]})
