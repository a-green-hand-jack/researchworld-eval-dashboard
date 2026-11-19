"""Data loading, model training and explainer wrappers (shared by all experiments)."""
import os, pickle
import numpy as np, pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, accuracy_score

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
RES = os.path.join(ROOT, "results")
os.makedirs(RES, exist_ok=True)

DATASETS = ["german", "pima", "acs", "gmsc", "arrhythmia"]
MODELS = ["lr", "rf", "xgb", "mlp"]
TREE_MODELS = ["rf", "xgb"]
# per-dataset coalition budgets B (KernelExplainer caps at 2^d-2 => exact; grids straddle that cap)
BUDGETS = {"pima": [30, 60, 120, 250], "acs": [50, 150, 400, 1000], "gmsc": [50, 150, 400, 1000],
           "german": [100, 300, 1000, 3000], "arrhythmia": [500, 1000, 2000, 4000]}
N_RUNS_DEFAULT = 10
EXPLAINERS = ["kernel", "kernel_l1", "perm"]
N_INST = 30
N_RUNS = 10
N_BG = 100
N_BOOT = 10


def load_dataset(name):
    """Return X (float array, categoricals ordinal-coded), y (0/1), names, cat_idx."""
    if name == "german":
        cols = ["status", "duration", "credit_history", "purpose", "amount", "savings", "employment",
                "installment_rate", "personal_status", "other_debtors", "residence_since", "property",
                "age", "other_plans", "housing", "n_credits", "job", "n_liable", "telephone", "foreign"]
        df = pd.read_csv(os.path.join(DATA, "german.data"), sep=" ", header=None)
        y = (df.iloc[:, 20].values == 2).astype(int)  # 1 = bad credit
        Xdf = df.iloc[:, :20].copy(); Xdf.columns = cols
        cat = [c for c in cols if not pd.api.types.is_numeric_dtype(Xdf[c])]
        for c in cat:
            Xdf[c] = Xdf[c].astype("category").cat.codes
        return Xdf.values.astype(float), y, cols, [cols.index(c) for c in cat]
    if name == "pima":
        import openml
        d = openml.datasets.get_dataset(37)
        X, y, _, names = d.get_data(target=d.default_target_attribute)
        y = (y.astype(str) == "tested_positive").astype(int).values
        return X.values.astype(float), y, list(names), []
    if name == "gmsc":
        import openml
        d = openml.datasets.get_dataset(46929)
        X, y, _, names = d.get_data(target=d.default_target_attribute)
        y = pd.Series(y).astype(str).map(lambda s: 1 if s in ("1", "Yes", "True", "yes") else 0).values
        rng = np.random.RandomState(0)
        idx = rng.choice(len(X), 30000, replace=False)  # CPU budget: 30k-row subsample
        Xv = X.values.astype(float)[idx]
        med = np.nanmedian(Xv, axis=0)  # median imputation (documented; same for all models)
        Xv = np.where(np.isnan(Xv), med, Xv)
        return Xv, y[idx], list(names), []
    if name == "arrhythmia":
        df = pd.read_csv(os.path.join(DATA, "arrhythmia.data"), header=None, na_values="?")
        y = (df.iloc[:, 279].values != 1).astype(int)  # 1 = any arrhythmia class vs normal (class 1)
        Xv = df.iloc[:, :279].values.astype(float)
        keep = np.nanstd(Xv, axis=0) > 0  # drop constant columns
        Xv = Xv[:, keep]
        med = np.nanmedian(Xv, axis=0)
        Xv = np.where(np.isnan(Xv), med, Xv)
        names = [f"f{i}" for i in np.arange(279)[keep]]
        return Xv, y, names, []
    if name == "acs":
        from folktables import ACSDataSource, ACSIncome
        ds = ACSDataSource(survey_year="2018", horizon="1-Year", survey="person",
                           root_dir=os.path.join(DATA, "acs"))
        d = ds.get_data(states=["AL"], download=True)
        X, y, _ = ACSIncome.df_to_numpy(d)
        names = list(ACSIncome.features)
        cat = [names.index(c) for c in ["COW", "MAR", "OCCP", "POBP", "RELP", "SEX", "RAC1P"]]
        return X.astype(float), y.astype(int), names, cat
    raise ValueError(name)


def make_model(kind, cat_idx, d, seed=0):
    def prep():
        num = [i for i in range(d) if i not in cat_idx]
        tr = []
        if num: tr.append(("num", StandardScaler(), num))
        if cat_idx:
            tr.append(("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=30, sparse_output=False), list(cat_idx)))
        return ColumnTransformer(tr)
    if kind == "lr":
        return make_pipeline(prep(), LogisticRegression(C=1.0, max_iter=2000))
    if kind == "mlp":
        return make_pipeline(prep(), MLPClassifier((64, 64), alpha=1e-1, max_iter=500, early_stopping=False,
                                                  random_state=seed))
    if kind == "rf":
        return RandomForestClassifier(n_estimators=50, min_samples_leaf=10, n_jobs=1, random_state=seed)
    if kind == "xgb":
        from xgboost import XGBClassifier
        return XGBClassifier(n_estimators=150, max_depth=4, learning_rate=0.1, subsample=0.8, n_jobs=1,
                             random_state=seed, tree_method="hist", enable_categorical=False)
    raise ValueError(kind)


def split(name):
    X, y, names, cat = load_dataset(name)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, random_state=0, stratify=y)
    return Xtr, Xte, ytr, yte, names, cat


class Fn:
    """Probability-of-positive-class function with chunking and row counting."""
    def __init__(self, model, chunk=20000):
        self.model, self.chunk, self.rows = model, chunk, 0
    def __call__(self, X):
        X = np.asarray(X, dtype=float)
        self.rows += len(X)
        out = np.empty(len(X))
        for s in range(0, len(X), self.chunk):
            out[s:s + self.chunk] = self.model.predict_proba(X[s:s + self.chunk])[:, 1]
        return out


def tree_exact(model, bg, X):
    import shap
    ex = shap.TreeExplainer(model, data=bg, feature_perturbation="interventional", model_output="probability")
    v = ex.shap_values(X, check_additivity=False)
    v = np.asarray(v)
    if v.ndim == 3:  # (n, d, 2) or (2, n, d)
        v = v[:, :, 1] if v.shape[0] == len(X) else v[1]
    return v


def explain_once(kind, fn, bg, x, B, seed):
    """One stochastic SHAP run for a single instance x with budget B coalitions."""
    import shap
    x = x.reshape(1, -1)
    if kind in ("kernel", "kernel_l1"):
        np.random.seed(seed)
        ex = shap.KernelExplainer(fn, bg)
        l1 = 0 if kind == "kernel" else f"num_features({min(10, x.shape[1] // 2)})"  # sparsified variant
        return np.asarray(ex.shap_values(x, nsamples=B, l1_reg=l1, silent=True)).reshape(-1)
    if kind == "perm":
        ex = shap.explainers.Permutation(fn, bg, seed=seed)
        return np.asarray(ex(x, max_evals=B, silent=True).values).reshape(-1)
    raise ValueError(kind)


def exact_enum(fn, bg, x):
    """Exact interventional Shapley values by full coalition enumeration (d <= ~12) via KernelExplainer."""
    import shap
    d = len(x)
    ex = shap.KernelExplainer(fn, bg)
    return np.asarray(ex.shap_values(x.reshape(1, -1), nsamples=2 ** d - 2, l1_reg=0, silent=True)).reshape(-1)
