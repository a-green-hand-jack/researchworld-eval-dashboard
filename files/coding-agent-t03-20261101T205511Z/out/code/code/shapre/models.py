"""Models: LR / MLP (own table-lookup forward pass, so that d original features -> additive first layer),
XGBoost / RandomForest (ordinal codes). All expose f(X)->P(y=1) on the raw d-column matrix."""
import warnings
import numpy as np
import scipy.sparse as sp
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, accuracy_score

warnings.filterwarnings('ignore')


class Encoder:
    """numeric -> standardised; categorical -> one-hot over levels seen >= min_count times (others: all-zero)."""

    def __init__(self, is_cat, min_count=5):
        self.is_cat, self.min_count = np.asarray(is_cat), min_count

    def fit(self, X):
        d = X.shape[1]
        self.mean = np.zeros(d); self.std = np.ones(d); self.levels = [None] * d
        self.slices = []; pos = 0
        for j in range(d):
            if self.is_cat[j]:
                v, c = np.unique(X[:, j], return_counts=True)
                self.levels[j] = v[c >= self.min_count]
                w = len(self.levels[j])
            else:
                self.mean[j] = X[:, j].mean(); s = X[:, j].std(); self.std[j] = s if s > 0 else 1.0
                w = 1
            self.slices.append((pos, pos + w)); pos += w
        self.n_out = pos
        return self

    def level_index(self, j, v):
        """index of the level of categorical feature j (len(levels) = 'other')."""
        lv = self.levels[j]
        i = np.searchsorted(lv, v)
        i = np.clip(i, 0, max(len(lv) - 1, 0))
        ok = (len(lv) > 0) & (lv[i] == v) if len(lv) else np.zeros(len(v), bool)
        return np.where(ok, i, len(lv))

    def transform(self, X):  # sparse design matrix (training only)
        n, d = X.shape
        rows, cols, vals = [], [], []
        ar = np.arange(n)
        for j in range(d):
            s, e = self.slices[j]
            if self.is_cat[j]:
                i = self.level_index(j, X[:, j]); m = i < (e - s)
                rows.append(ar[m]); cols.append(s + i[m]); vals.append(np.ones(m.sum()))
            else:
                rows.append(ar); cols.append(np.full(n, s)); vals.append((X[:, j] - self.mean[j]) / self.std[j])
        return sp.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(n, self.n_out))


class NetModel:
    """LR (no hidden layer) or MLP with a first layer that is additive over the d original features:
    pre(x) = sum_j A_j(x_j) + b1. Forward pass via per-feature tables (no one-hot materialisation)."""

    def __init__(self, kind, is_cat, seed=0):
        self.kind, self.is_cat, self.seed = kind, np.asarray(is_cat), seed

    def fit(self, X, y):
        self.enc = Encoder(self.is_cat).fit(X)
        Xe = self.enc.transform(X)
        if self.kind == "lr":
            m = LogisticRegression(C=1.0, max_iter=5000).fit(Xe, y)
            self.W = m.coef_.T.copy(); self.b1 = m.intercept_.copy(); self.rest_layers = []
            self.out_b = np.zeros(1)
        else:
            small = X.shape[0] < 5000  # strong L2 + fixed epochs on small data, early stopping on large data
            m = MLPClassifier(hidden_layer_sizes=(32, 16), alpha=1.0 if small else 1e-2,
                              early_stopping=not small, max_iter=300 if small else 100,
                              random_state=self.seed).fit(Xe, y)
            self.W = m.coefs_[0]; self.b1 = m.intercepts_[0]
            self.rest_layers = list(zip(m.coefs_[1:], m.intercepts_[1:]))
        self.sk = m
        self.H = self.W.shape[1]
        self._tables()
        return self

    def _tables(self):
        self.tab = []
        for j, (s, e) in enumerate(self.enc.slices):
            if self.is_cat[j]:
                self.tab.append(np.vstack([self.W[s:e], np.zeros((1, self.H))]))  # last row = 'other'
            else:
                self.tab.append(self.W[s] / self.enc.std[j])

    def A(self, j, v):
        """first-layer contribution of feature j taking values v -> (len(v), H)."""
        if self.is_cat[j]:
            return self.tab[j][self.enc.level_index(j, v)]
        return np.outer(v - self.enc.mean[j], self.tab[j])

    def rest(self, pre):
        """pre: (..., H) first-layer pre-activation WITHOUT b1 -> P(y=1)."""
        h = pre + self.b1
        if self.kind == "lr":
            z = h[..., 0]
        else:
            h = np.maximum(h, 0)
            for k, (W, b) in enumerate(self.rest_layers):
                h = h @ W + b
                if k < len(self.rest_layers) - 1:
                    h = np.maximum(h, 0)
            z = h[..., 0]
        return 1.0 / (1.0 + np.exp(-z))

    def pre(self, X):
        out = np.zeros((X.shape[0], self.H))
        for j in range(X.shape[1]):
            out += self.A(j, X[:, j])
        return out

    def predict(self, X, block=4096):
        X = np.atleast_2d(X)
        return np.concatenate([self.rest(self.pre(X[i:i + block])) for i in range(0, len(X), block)])


class TreeModel:
    def __init__(self, kind, seed=0):
        self.kind, self.seed = kind, seed

    def fit(self, X, y):
        if self.kind == "xgb":
            from xgboost import XGBClassifier
            self.sk = XGBClassifier(n_estimators=200, max_depth=4, learning_rate=0.1, subsample=0.8,
                                    colsample_bytree=0.8, tree_method="hist", n_jobs=1,
                                    random_state=self.seed, verbosity=0).fit(X, y)
        else:
            self.sk = RandomForestClassifier(n_estimators=100, max_depth=10, min_samples_leaf=5,
                                             max_features="sqrt", n_jobs=1, random_state=self.seed).fit(X, y)
        return self

    def predict(self, X):
        return self.sk.predict_proba(np.atleast_2d(X))[:, 1]


MODELS = ["lr", "mlp", "xgb", "rf"]


def train(kind, is_cat, Xtr, ytr, seed=0, bootstrap=False):
    if bootstrap:
        idx = np.random.RandomState(1000 + seed).choice(len(Xtr), len(Xtr), replace=True)
        Xtr, ytr = Xtr[idx], ytr[idx]
    m = NetModel(kind, is_cat, seed) if kind in ("lr", "mlp") else TreeModel(kind, seed)
    return m.fit(Xtr, ytr)


def evaluate(model, Xte, yte):
    p = model.predict(Xte)
    return dict(auc=roc_auc_score(yte, p), acc=accuracy_score(yte, p > 0.5))
