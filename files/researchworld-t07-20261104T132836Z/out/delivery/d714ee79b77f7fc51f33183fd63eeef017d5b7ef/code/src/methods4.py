"""Reference rows, ridge-based AIPW variants, MASS ablations (selection only / predictor only) and interval widths."""
import numpy as np
from sklearn.linear_model import Ridge
from methods import ALL, Random
from methods3 import MASSEns


class Null:
    """Sources only: every target gets the mean source-model accuracy (no target items used)."""
    name = "sources_only"

    def fit(self, Xs, n, seed, ctx):
        self.m = Xs.mean()
        return np.array([], dtype=int)

    def predict(self, Y):
        return np.full(Y.shape[0], self.m)


class AIPWRidgeRepo:
    """Variant of AIPW as implemented in the data repository (own re-implementation): per target, ridge(alpha=10) regression of the
    target's sampled responses on the source models' responses to the same items; mean prediction over the unsampled items plus the
    in-sample residual mean divided by (1 + n/N_rest).  Differs from textbook AIPW (see aipw_ridge_cf)."""
    name = "aipw_ridge_repo"

    def fit(self, Xs, n, seed, ctx):
        self.Xs = Xs
        N = Xs.shape[1]
        self.idx = np.random.default_rng(seed).permutation(N)[:n]
        self.rest = np.setdiff1d(np.arange(N), self.idx)
        return self.idx

    def predict(self, Y):
        A, R = self.Xs[:, self.idx].T, self.Xs[:, self.rest].T
        out = []
        for y in Y:
            r = Ridge(alpha=10).fit(A, y)
            res = (y - r.predict(A)).mean()
            out.append(r.predict(R).mean() + res / (1 + len(self.idx) / len(self.rest)))
        return np.array(out)


class AIPWRidgeCF(AIPWRidgeRepo):
    """Textbook AIPW with the same predictor: mean prediction over ALL items + mean 5-fold cross-fitted residual on the sample."""
    name = "aipw_ridge_cf"

    def predict(self, Y):
        A, R = self.Xs[:, self.idx].T, self.Xs.T
        n = len(self.idx)
        folds = np.arange(n) % 5
        out = []
        for y in Y:
            full = Ridge(alpha=10).fit(A, y).predict(R).mean()
            res = np.empty(n)
            for f in range(5):
                m = Ridge(alpha=10).fit(A[folds != f], y[folds != f])
                res[folds == f] = y[folds == f] - m.predict(A[folds == f])
            out.append(full + res.mean())
        return np.array(out)


def _predict_with_se(self, Y):
    th = self.lat.infer(self.idx, Y)
    Pl = self.lat.prob_all(th)
    d = (Y[:, None, :] != self.Xs[None][:, :, self.idx]).mean(2)
    w = np.exp(-(d - d.min(1, keepdims=True)) / self.tau)
    w /= w.sum(1, keepdims=True)
    P = self.blend * Pl + (1 - self.blend) * (w @ self.Xs)
    Rr = Y - P[:, self.idx]
    ww = 1.0 / self.pi
    z = (Rr * ww).sum(1) / ww.sum()
    n = len(self.idx)
    self.se = np.sqrt((((Rr - z[:, None]) * ww) ** 2).sum(1) * n / max(n - 1, 1)) / ww.sum()
    return P.mean(1) + z


MASSEns.predict = _predict_with_se


class MASSSel(MASSEns):
    """Ablation: MASS sampling design only (stratified PPS sample), Hajek-weighted sample mean, no predictor."""
    name = "mass_sel"

    def predict(self, Y):
        w = 1.0 / self.pi
        return (Y * w).sum(1) / w.sum()


class MASSEnsNoCorr(MASSEns):
    """Ablation: MASS design + ensemble predictor, no difference correction (pure model prediction)."""
    name = "mass_ens_nocorr"

    def _correction(self, Y, P):
        return 0.0

    def predict(self, Y):
        th = self.lat.infer(self.idx, Y)
        Pl = self.lat.prob_all(th)
        d = (Y[:, None, :] != self.Xs[None][:, :, self.idx]).mean(2)
        w = np.exp(-(d - d.min(1, keepdims=True)) / self.tau)
        w /= w.sum(1, keepdims=True)
        return (self.blend * Pl + (1 - self.blend) * (w @ self.Xs)).mean(1)


class RandEnsNoCorr(MASSEnsNoCorr):
    """Ablation: random items + ensemble predictor, no correction (predictor only)."""
    name = "ens_rand_nocorr"

    def _select(self, Xs, n, seed, ctx):
        return np.sort(np.random.default_rng(seed).choice(Xs.shape[1], n, replace=False))


ALL.update({m.name: m for m in [Null, AIPWRidgeRepo, AIPWRidgeCF, MASSSel, MASSEnsNoCorr, RandEnsNoCorr]})
