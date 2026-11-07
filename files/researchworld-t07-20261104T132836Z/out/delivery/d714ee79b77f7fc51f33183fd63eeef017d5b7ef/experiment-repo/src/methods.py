"""Benchmark-prediction methods. Each method: fit(Xs, n, seed, ctx) -> item indices; predict(Y) -> (T,) scores.

Xs: (S, N) binary source matrix. Y: (T, n) target responses on the selected items.
ctx: dict shared between methods for one source set (caches the latent model fits).
"""
import numpy as np
import torch
from sklearn.cluster import KMeans
from sklearn.linear_model import RidgeCV
from latent import Latent


def get_latent(Xs, ctx, k):
    key = ("latent", k)
    if key not in ctx:
        ctx[key] = Latent(k=k, seed=0).fit(Xs)
    return ctx[key]


class Random:
    """Uniform random subset, subset mean."""
    name = "random"

    def fit(self, Xs, n, seed, ctx):
        self.idx = np.sort(np.random.default_rng(seed).choice(Xs.shape[1], n, replace=False))
        return self.idx

    def predict(self, Y):
        return Y.mean(1)


class StratRandom:
    """Strata = equal-size bins of source-mean item difficulty; proportional allocation; mean."""
    name = "strat_random"

    def fit(self, Xs, n, seed, ctx):
        rng = np.random.default_rng(seed)
        N = Xs.shape[1]
        order = np.argsort(Xs.mean(0) + 1e-6 * rng.standard_normal(N))
        strata = np.array_split(order, n)  # n equal-size strata, one random draw from each
        self.idx = np.array([rng.choice(st) for st in strata])
        self.w = np.array([len(st) / N for st in strata])
        return self.idx

    def predict(self, Y):
        return Y @ self.w


class Anchor:
    """Anchor points: cluster items by their source-model response vectors; medoid-like anchor per cluster;
    score = cluster-size weighted mean of the anchor responses."""
    name = "anchor"

    def fit(self, Xs, n, seed, ctx):
        N = Xs.shape[1]
        F = Xs.T
        km = KMeans(n_clusters=n, n_init=1, random_state=seed).fit(F)
        idx, w = [], []
        for c in range(n):
            mem = np.where(km.labels_ == c)[0]
            if len(mem) == 0:  # empty cluster (duplicate item vectors): fewer anchors
                continue
            d = ((F[mem] - km.cluster_centers_[c]) ** 2).sum(1)
            idx.append(mem[np.argmin(d)])
            w.append(len(mem) / N)
        self.idx, self.w = np.array(idx), np.array(w)
        return self.idx

    def predict(self, Y):
        return Y @ self.w


class CalibRandom:
    """Random subset; full score = a + b * subset mean, with (a, b) fitted on the source models."""
    name = "calib"

    def fit(self, Xs, n, seed, ctx):
        self.idx = np.sort(np.random.default_rng(seed).choice(Xs.shape[1], n, replace=False))
        s = Xs[:, self.idx].mean(1)
        f = Xs.mean(1)
        A = np.stack([np.ones_like(s), s], 1)
        self.coef = np.linalg.lstsq(A, f, rcond=None)[0]
        return self.idx

    def predict(self, Y):
        return self.coef[0] + self.coef[1] * Y.mean(1)


class RidgeSub:
    """Random subset; ridge regression (CV penalty) from the subset responses to the full score,
    trained on source models (PCA/Lasso-style regressor of the benchmark-prediction literature)."""
    name = "ridge"

    def fit(self, Xs, n, seed, ctx):
        self.idx = np.sort(np.random.default_rng(seed).choice(Xs.shape[1], n, replace=False))
        self.m = RidgeCV(alphas=np.logspace(-2, 3, 12)).fit(Xs[:, self.idx], Xs.mean(1))
        return self.idx

    def predict(self, Y):
        return self.m.predict(Y)


class LatentBase:
    k = 2
    correct = False

    def _select(self, Xs, n, seed, ctx):
        return np.sort(np.random.default_rng(seed).choice(Xs.shape[1], n, replace=False))

    def fit(self, Xs, n, seed, ctx):
        self.lat = get_latent(Xs, ctx, self.k)
        self.idx = self._select(Xs, n, seed, ctx)
        self.N = Xs.shape[1]
        return self.idx

    def predict(self, Y):
        th = self.lat.infer(self.idx, Y)
        P = self.lat.prob_all(th)
        pred = P.mean(1)
        if self.correct:
            pred = pred + self._correction(Y, P)
        return pred

    def _correction(self, Y, P):
        return (Y - P[:, self.idx]).mean(1)


class IRTRand(LatentBase):
    name = "irt_rand"


class AIPWRand(LatentBase):
    """Latent-model prediction of all items + difference (control-variate) correction on a uniform random
    subset: unbiased for the full score whatever the model; the model only reduces variance."""
    name = "aipw_rand"
    correct = True


class IRTInfo(LatentBase):
    """Greedy D-optimal item selection under the latent model (information-based, metabench-style)."""
    name = "irt_info"

    def _select(self, Xs, n, seed, ctx):
        key = ("dopt", self.k, n)
        if key in ctx:
            return ctx[key]
        Phi = self.lat.features().numpy().astype(np.float64)
        p = self.lat.prob_all(torch.cat([self.lat.r_s[:, None], self.lat.U_s], 1))   # (S, N) source probs
        W = (p * (1 - p)).mean(0)
        d = Phi.shape[1]
        A = np.eye(d)
        chosen = []
        avail = np.ones(len(W), bool)
        for _ in range(n):
            Ai = np.linalg.inv(A)
            gain = W * np.einsum("nd,de,ne->n", Phi, Ai, Phi)
            gain[~avail] = -1
            j = int(np.argmax(gain))
            chosen.append(j)
            avail[j] = False
            A += W[j] * np.outer(Phi[j], Phi[j])
        ctx[key] = np.sort(np.array(chosen))
        return ctx[key]


class AnchorIRT(LatentBase):
    """Anchor points chosen by clustering items in the latent item space; latent-model prediction
    for the benchmark, optionally corrected with cluster-weighted anchor residuals."""
    name = "anchor_irt"
    correct = False

    def _select(self, Xs, n, seed, ctx):
        F = np.concatenate([self.lat.V.numpy(), self.lat.c.numpy()[:, None]], 1)
        km = KMeans(n_clusters=n, n_init=1, random_state=seed).fit(F)
        idx, w = [], []
        for c in range(n):
            mem = np.where(km.labels_ == c)[0]
            if len(mem) == 0:  # empty cluster (duplicate item vectors): fewer anchors
                continue
            idx.append(mem[np.argmin(((F[mem] - km.cluster_centers_[c]) ** 2).sum(1))])
            w.append(len(mem) / len(F))
        self.w = np.array(w)
        return np.array(idx)

    def _correction(self, Y, P):
        return (Y - P[:, self.idx]) @ self.w


class AnchorAIPW(AnchorIRT):
    name = "anchor_aipw"
    correct = True


ALL = {m.name: m for m in [Random, StratRandom, Anchor, CalibRandom, RidgeSub, IRTRand, AIPWRand, IRTInfo, AnchorIRT, AnchorAIPW]}
