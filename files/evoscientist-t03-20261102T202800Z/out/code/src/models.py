"""Model zoo: logistic regression, random forest, XGBoost, MLP. All expose predict(X)->P(y=1) on the raw
(ordinal-coded) d-column feature matrix, so Shapley values are always over the d raw features."""
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import roc_auc_score, accuracy_score
import xgboost as xgb


class Encoder:
    """Standardise numeric columns; one-hot categorical columns (most frequent `max_levels` levels, rest -> 'other')."""

    def __init__(self, cat, max_levels=15):
        self.cat, self.max_levels = cat, max_levels

    def fit(self, X):
        self.mu = X.mean(0); self.sd = X.std(0) + 1e-9
        self.levels = {}
        for j in np.where(self.cat)[0]:
            v, c = np.unique(X[:, j], return_counts=True)
            self.levels[j] = v[np.argsort(-c)][: self.max_levels]
        return self

    def transform(self, X):
        cols = []
        for j in range(X.shape[1]):
            if self.cat[j]:
                cols.append((X[:, j:j + 1] == self.levels[j][None, :]).astype(np.float32))
            else:
                cols.append(((X[:, j:j + 1] - self.mu[j]) / self.sd[j]).astype(np.float32))
        return np.hstack(cols)


class Model:
    def __init__(self, kind, cat, seed=0):
        self.kind, self.cat, self.seed = kind, cat, seed

    def fit(self, X, y):
        k, s = self.kind, self.seed
        if k in ("lr", "mlp"):
            self.enc = Encoder(self.cat).fit(X)
            Z = self.enc.transform(X)
            if k == "lr":
                self.m = LogisticRegression(C=1.0, max_iter=2000)
            else:
                self.m = MLPClassifier((64, 64), alpha=1e-3, early_stopping=True, max_iter=200, random_state=s)
            self.m.fit(Z, y)
        elif k == "rf":
            self.m = RandomForestClassifier(100, min_samples_leaf=5, n_jobs=1, random_state=s).fit(X, y)
        elif k == "xgb":
            self.m = xgb.XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.1, subsample=0.8,
                                       colsample_bytree=0.8, n_jobs=1, random_state=s, tree_method="hist")
            self.m.fit(X, y)
        return self

    def predict(self, X):
        X = np.atleast_2d(X)
        if self.kind in ("lr", "mlp"):
            X = self.enc.transform(X)
        return self.m.predict_proba(X)[:, 1]

    def score(self, X, y):
        p = self.predict(X)
        return dict(auc=float(roc_auc_score(y, p)), acc=float(accuracy_score(y, p > 0.5)))


def train(kind, D, seed=0, subsample=None):
    """Train model; `subsample` (float) trains on a random fraction of the training rows (used for retraining replicates)."""
    X, y = D["Xtr"], D["ytr"]
    if subsample:
        idx = np.random.RandomState(1000 + seed).choice(len(y), int(subsample * len(y)), replace=False)
        X, y = X[idx], y[idx]
    return Model(kind, D["cat"], seed).fit(X, y)
