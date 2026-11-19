"""Models explained on the probability scale, P(y=1|x). Every model exposes
`predict(Z)` (Z = encoded inputs, float32) and `value_table(zx, Zb, col_attr, d)` = v(S) = mean_k f(x_S, b_k,~S)
for all 2^d coalitions S (bit j of the index = attribute j present)."""
import numpy as np, torch
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier
import lightgbm as lgb

torch.set_num_threads(2)


def coalition_masks(start, stop, d):
    s = np.arange(start, stop, dtype=np.int64)
    return ((s[:, None] >> np.arange(d)) & 1).astype(np.float32)  # (C, d)


class Model:
    kind = "generic"
    def predict(self, Z): raise NotImplementedError

    def value_table(self, zx, Zb, col_attr, d, chunk_rows=2_000_000):
        m, p = Zb.shape
        n = 1 << d
        out = np.empty(n, np.float32)
        C = max(1, chunk_rows // m)
        for a in range(0, n, C):
            b = min(n, a + C)
            cm = coalition_masks(a, b, d)[:, col_attr].astype(bool)        # (c, p)
            Z = np.where(cm[:, None, :], zx[None, None, :], Zb[None]).reshape(-1, p)
            out[a:b] = self.predict(Z).reshape(b - a, m).mean(1)
        return out

    def value_masks(self, masks, zx, Zb, col_attr, chunk_rows=1_000_000):
        """live evaluation for arbitrary coalition masks (c, d) -> v (c,)"""
        m, p = Zb.shape
        c = masks.shape[0]
        out = np.empty(c, np.float64)
        C = max(1, chunk_rows // m)
        for a in range(0, c, C):
            cm = masks[a:a + C][:, col_attr].astype(bool)
            Z = np.where(cm[:, None, :], zx[None, None, :], Zb[None]).reshape(-1, p)
            out[a:a + C] = self.predict(Z).reshape(cm.shape[0], m).mean(1)
        return out


class LR(Model):
    kind = "lr"
    def __init__(self, seed=0, C=1.0):
        self.m = LogisticRegression(C=C, max_iter=2000)
    def fit(self, Z, y):
        self.m.fit(Z, y); self.w = self.m.coef_[0].astype(np.float32); self.b = np.float32(self.m.intercept_[0]); return self
    def predict(self, Z):
        return 1.0 / (1.0 + np.exp(-(Z @ self.w + self.b)))
    def value_table(self, zx, Zb, col_attr, d, **kw):
        # margin is additive over attributes: margin(S,k) = base_k + sum_{j in S} delta_kj ; exact, same value as brute force
        m = Zb.shape[0]
        diff = (zx[None, :] - Zb) * self.w[None, :]                          # (m, p)
        delta = np.zeros((m, d), np.float32)
        for j in range(d):
            delta[:, j] = diff[:, col_attr == j].sum(1)
        base = Zb @ self.w + self.b
        out = np.empty(1 << d, np.float32)
        C = max(1, 2_000_000 // m)
        for a in range(0, 1 << d, C):
            b = min(1 << d, a + C)
            M = coalition_masks(a, b, d) @ delta.T + base[None, :]
            out[a:b] = (1.0 / (1.0 + np.exp(-M))).mean(1)
        return out


class MLP(Model):
    kind = "mlp"
    def __init__(self, seed=0, hidden=(64, 32)):
        self.m = MLPClassifier(hidden, early_stopping=True, alpha=1e-3, max_iter=300, random_state=seed)
    def fit(self, Z, y):
        self.m.fit(Z, y)
        self.W = [torch.tensor(w, dtype=torch.float32) for w in self.m.coefs_]
        self.bb = [torch.tensor(b, dtype=torch.float32) for b in self.m.intercepts_]
        return self
    def _fwd(self, h):
        for W, b in zip(self.W[:-1], self.bb[:-1]):
            h = torch.relu(h @ W + b)
        return torch.sigmoid(h @ self.W[-1] + self.bb[-1])[..., 0]
    def predict(self, Z):
        with torch.no_grad():
            return self._fwd(torch.from_numpy(np.ascontiguousarray(Z, dtype=np.float32))).numpy()
    def value_table(self, zx, Zb, col_attr, d, chunk_rows=400_000):
        # first layer is additive over attributes: pre1(S,k) = Zb_k W1 + b1 + sum_{j in S} (zx-Zb_k)_j W1_j
        m = Zb.shape[0]
        W1 = self.W[0]; H = W1.shape[1]
        zxt = torch.from_numpy(zx.astype(np.float32)); Zt = torch.from_numpy(Zb.astype(np.float32))
        diff = zxt[None, :] - Zt                                           # (m, p)
        D = torch.zeros(d, m, H)
        for j in range(d):
            cols = torch.from_numpy(np.where(col_attr == j)[0])
            D[j] = diff[:, cols] @ W1[cols]
        base = Zt @ W1 + self.bb[0]                                        # (m, H)
        D2 = D.reshape(d, m * H); base2 = base.reshape(1, m * H)
        out = np.empty(1 << d, np.float32)
        C = max(1, chunk_rows // m)
        with torch.no_grad():
            for a in range(0, 1 << d, C):
                b = min(1 << d, a + C)
                S = torch.from_numpy(coalition_masks(a, b, d))
                h = torch.relu(S @ D2 + base2).reshape(-1, H)
                for W, bias in zip(self.W[1:-1], self.bb[1:-1]):
                    h = torch.relu(h @ W + bias)
                out[a:b] = torch.sigmoid(h @ self.W[-1] + self.bb[-1])[:, 0].reshape(b - a, m).mean(1).numpy()
        return out


class GBDT(Model):
    kind = "gbdt"
    out = "prob"        # "logit": explain the raw margin (what TreeSHAP does by default; exact reference at any d)
    def __init__(self, seed=0, n_estimators=100, num_leaves=8):
        self.m = lgb.LGBMClassifier(n_estimators=n_estimators, num_leaves=num_leaves, learning_rate=0.1, subsample=0.8,
                                    subsample_freq=1, colsample_bytree=0.8, min_child_samples=10, random_state=seed,
                                    n_jobs=2, verbose=-1)
    def fit(self, Z, y):
        self.m.fit(Z, y); return self
    def predict(self, Z):
        Z = np.ascontiguousarray(Z, dtype=np.float32)
        if self.out == "logit":
            return self.m.predict(Z, raw_score=True)
        return self.m.predict_proba(Z)[:, 1]


class RF(Model):
    kind = "rf"
    def __init__(self, seed=0, n_estimators=100, max_depth=8):
        self.m = RandomForestClassifier(n_estimators=n_estimators, max_depth=max_depth, min_samples_leaf=3, n_jobs=2, random_state=seed)
    def fit(self, Z, y):
        self.m.fit(Z, y); return self
    def predict(self, Z):
        return self.m.predict_proba(Z)[:, 1]


MODELS = dict(lr=LR, mlp=MLP, gbdt=GBDT, rf=RF)
