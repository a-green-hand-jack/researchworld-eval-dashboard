"""Model-assisted sampling designs (the proposed family) and ablations. Imports methods.py unchanged.

MASS = latent-model prediction of all items + weighted difference correction on a sample drawn by
systematic probability-proportional-to-size (PPS) sampling along the item-difficulty order:
  * stratification (systematic sampling over items sorted by source difficulty) removes between-difficulty variance;
  * PPS with pi_j ~ sqrt(mean source p_j(1-p_j)) allocates more of the sample to items whose residual is
    uncertain (Neyman allocation for the residual y_j - p_j);
  * estimator  mean_j p_j + sum_S w_j (y_j - p_j) / sum_S w_j,  w_j = 1/pi_j  (Hajek form; 'ht' uses /N instead).
"""
import numpy as np
import torch
from methods import LatentBase, ALL, get_latent


def pps_probs(s, n):
    """Inclusion probabilities pi_j = n s_j / sum s, capped at 1 (iterated), summing to n."""
    N = len(s)
    pi = np.zeros(N)
    free = np.ones(N, bool)
    m = n
    for _ in range(50):
        pi[free] = m * s[free] / s[free].sum()
        over = free & (pi >= 1)
        if not over.any():
            break
        pi[over] = 1.0
        free &= ~over
        m = n - (~free).sum()
    return pi


def systematic(pi, order, rng):
    """Systematic sampling with inclusion probs pi over items in `order`; returns item indices (size round(sum pi))."""
    cs = np.cumsum(pi[order])
    u = rng.uniform()
    pts = u + np.arange(int(round(cs[-1])))
    pos = np.searchsorted(cs, pts, side="right")
    return order[np.minimum(pos, len(order) - 1)]


class MASS(LatentBase):
    name = "mass"
    correct = True
    hajek = True
    pps = True
    sort = "difficulty"

    def _select(self, Xs, n, seed, ctx):
        rng = np.random.default_rng(seed)
        key = ("pbar", self.k)
        if key not in ctx:
            lat = self.lat
            p = lat.prob_all(torch.cat([lat.r_s[:, None], lat.U_s], 1))
            ctx[key] = (p.mean(0), (p * (1 - p)).mean(0))
        pbar, v = ctx[key]
        s = np.sqrt(v) if self.pps else np.ones_like(v)
        pi = pps_probs(s + 1e-6, n)
        order = np.argsort(pbar + 1e-9 * rng.standard_normal(len(pbar))) if self.sort == "difficulty" else rng.permutation(len(pbar))
        idx = systematic(pi, order, rng)
        # systematic sampling can draw duplicates only if pi>1 (excluded by the cap); guard anyway
        idx = np.unique(idx)
        self.pi = pi[idx]
        return idx

    def _correction(self, Y, P):
        R = Y - P[:, self.idx]
        w = 1.0 / self.pi
        if self.hajek:
            return (R * w).sum(1) / w.sum()
        return (R * w).sum(1) / self.N


class MASSht(MASS):
    name = "mass_ht"
    hajek = False


class StratAIPW(MASS):
    """Ablation: systematic equal-probability sampling along difficulty (stratification only, no PPS)."""
    name = "aipw_strat"
    pps = False


class PPSAIPW(MASS):
    """Ablation: PPS inclusion probabilities but unordered (random-order systematic = no stratification)."""
    name = "aipw_pps"
    sort = "random"


class MASSk1(MASS):
    name = "mass_k1"
    k = 1


class MASSk4(MASS):
    name = "mass_k4"
    k = 4


class AIPWk1(LatentBase):
    name = "aipw_k1"
    k = 1
    correct = True


class AIPWk4(LatentBase):
    name = "aipw_k4"
    k = 4
    correct = True


for m in [MASS, MASSht, StratAIPW, PPSAIPW, MASSk1, MASSk4, AIPWk1, AIPWk4]:
    ALL[m.name] = m


class PPI(LatentBase):
    """Prediction-powered inference with tuned weight: mean_sub(y) + lam (mean_all p - mean_sub p), lam in [0,1]
    chosen per target to minimise the plug-in variance, lam = cov_sub(y,p)/var_sub(p)."""
    name = "ppi"

    def predict(self, Y):
        th = self.lat.infer(self.idx, Y)
        P = self.lat.prob_all(th)
        Ps = P[:, self.idx]
        yc, pc = Y - Y.mean(1, keepdims=True), Ps - Ps.mean(1, keepdims=True)
        lam = np.clip((yc * pc).sum(1) / ((pc ** 2).sum(1) + 1e-12), 0, 1)
        return Y.mean(1) + lam * (P.mean(1) - Ps.mean(1))


class KNNBase(LatentBase):
    """Per-item prediction by kernel-weighted average of source models that agree with the target on the
    subset (weights exp(-hamming/tau)); optional blending with the latent-model probabilities."""
    name = "aipw_knn"
    correct = True
    blend = 0.0
    tau = 0.05

    def fit(self, Xs, n, seed, ctx):
        idx = super().fit(Xs, n, seed, ctx)
        self.Xs = Xs
        return idx

    def predict(self, Y):
        th = self.lat.infer(self.idx, Y)
        Pl = self.lat.prob_all(th)
        Xsub = self.Xs[:, self.idx]
        d = (Y[:, None, :] != Xsub[None, :, :]).mean(2)            # T x S
        w = np.exp(-(d - d.min(1, keepdims=True)) / self.tau)
        w /= w.sum(1, keepdims=True)
        Pk = w @ self.Xs                                           # T x N
        P = self.blend * Pl + (1 - self.blend) * Pk
        return P.mean(1) + (Y - P[:, self.idx]).mean(1)


class KNNEns(KNNBase):
    name = "aipw_ens"
    blend = 0.5


ALL.update({m.name: m for m in [PPI, KNNBase, KNNEns]})
