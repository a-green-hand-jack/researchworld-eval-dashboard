"""Models on the encoded features. All are scikit-learn-compatible; `predict_pos` returns P(y=1)."""
import warnings
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import HistGradientBoostingClassifier

MODELS = ["lr", "rf", "gbm", "mlp"]


def make_model(name, seed):
    if name == "lr":
        return make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=2000))
    if name == "rf":
        return RandomForestClassifier(n_estimators=50, min_samples_leaf=5, n_jobs=1, random_state=seed)
    if name == "gbm":
        return HistGradientBoostingClassifier(max_iter=150, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=20,
                                              random_state=seed)
    if name == "mlp":
        return make_pipeline(StandardScaler(), MLPClassifier((64, 64), alpha=1e-3, max_iter=300, early_stopping=True,
                                                             random_state=seed))
    raise ValueError(name)


def fit(name, Xtr, ytr, seed):
    m = make_model(name, seed)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        m.fit(Xtr, ytr)
    return m


def predict_pos(m, X):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return m.predict_proba(X)[:, 1]
