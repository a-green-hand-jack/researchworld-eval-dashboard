"""Models operating on the raw attribute space (n, d) -> P(y=1). Single-threaded for process-level parallelism."""
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, accuracy_score
import xgboost as xgb

MODELS = ["lr", "xgb", "rf", "mlp"]


class Encoder:
    """standardise numeric attributes, one-hot categorical attributes (used by lr / mlp only)."""

    def __init__(self, Xtr, ncat):
        self.ncat = ncat
        # winsorise numeric attributes at the 1st/99th training percentile, then standardise
        self.lo = np.percentile(Xtr, 1, axis=0)
        self.hi = np.percentile(Xtr, 99, axis=0)
        Xc = np.clip(Xtr, self.lo, self.hi)
        self.mu = Xc.mean(0)
        self.sd = Xc.std(0) + 1e-9
        self.d = Xtr.shape[1]
        self.groups = []  # columns of the encoded space belonging to each attribute
        c = 0
        for j in range(self.d):
            w = int(ncat[j]) if ncat[j] > 0 else 1
            self.groups.append(list(range(c, c + w)))
            c += w
        self.p = c

    def __call__(self, X):
        out = np.zeros((X.shape[0], self.p), dtype=np.float32)
        for j in range(self.d):
            g = self.groups[j]
            if self.ncat[j] > 0:
                out[np.arange(X.shape[0]), g[0] + X[:, j].astype(int)] = 1.0
            else:
                out[:, g[0]] = (np.clip(X[:, j], self.lo[j], self.hi[j]) - self.mu[j]) / self.sd[j]
        return out


class Model:
    def __init__(self, kind, D, seed=0, train_idx=None):
        self.kind = kind
        X, y = D["X"], D["y"]
        tr = D["train"] if train_idx is None else train_idx
        Xtr, ytr = X[tr], y[tr]
        self.enc = Encoder(D["X"][D["train"]], D["ncat"]) if kind in ("lr", "mlp") else None
        if kind == "lr":
            self.m = LogisticRegression(C=1.0, max_iter=2000)
            self.m.fit(self.enc(Xtr), ytr)
        elif kind == "mlp":
            big = len(Xtr) > 5000
            self.m = MLPClassifier(hidden_layer_sizes=(64, 64), alpha=1e-3 if big else 1e-2, early_stopping=big,
                                   max_iter=200 if big else 500, random_state=seed)
            self.m.fit(self.enc(Xtr), ytr)
        elif kind == "xgb":
            self.m = xgb.XGBClassifier(n_estimators=200, max_depth=4, learning_rate=0.1, subsample=0.8,
                                       colsample_bytree=0.8, tree_method="hist", n_jobs=1, random_state=seed)
            self.m.fit(Xtr, ytr)
        elif kind == "rf":
            self.m = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, n_jobs=1, random_state=seed)
            self.m.fit(Xtr, ytr)
        else:
            raise ValueError(kind)
        self.D = D

    def proba(self, X):
        if self.kind in ("lr", "mlp"):
            return self.m.predict_proba(self.enc(X))[:, 1].astype(np.float64)
        return self.m.predict_proba(X)[:, 1].astype(np.float64)

    def score(self):
        te = self.D["test"]
        p = self.proba(self.D["X"][te])
        y = self.D["y"][te]
        return dict(auc=float(roc_auc_score(y, p)), acc=float(accuracy_score(y, p > 0.5)))
