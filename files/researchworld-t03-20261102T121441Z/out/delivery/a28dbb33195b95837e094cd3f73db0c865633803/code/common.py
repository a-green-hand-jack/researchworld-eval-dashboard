"""Datasets, models, SHAP runners and exact references for the SHAP-reliability study."""
import os, itertools, time
import numpy as np, pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
import xgboost as xgb
import shap

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
os.environ.setdefault("OPENML_CACHE_DIR", os.path.join(DATA, "raw", "openml"))


# ---------------------------------------------------------------- data
def _german():
    p = os.path.join(DATA, "raw", "german.data")
    df = pd.read_csv(p, sep=" ", header=None)
    y = (df.iloc[:, 20] == 2).astype(int).values  # 1 = bad credit
    X = df.iloc[:, :20].copy()
    cat = [i for i in range(20) if not pd.api.types.is_numeric_dtype(X[i])]
    for i in cat:
        X[i] = X[i].astype("category").cat.codes
    names = ["status", "duration", "history", "purpose", "amount", "savings", "employment", "rate", "personal",
             "debtors", "residence", "property", "age", "other_plans", "housing", "n_credits", "job", "n_liable",
             "telephone", "foreign"]
    X.columns = names
    return X, y, [names[i] for i in cat]


def _openml(i):
    import openml
    d = openml.datasets.get_dataset(i, download_data=True, download_qualities=False, download_features_meta_data=False)
    X, y, _, _ = d.get_data(target=d.default_target_attribute)
    return X, y


def _pima():
    X, y = _openml(37)
    return X.astype(float), (y == "tested_positive").astype(int).values, []


def _gmsc(nmax=30000):
    X, y = _openml(46929)
    y = (y == "Yes").astype(int).values
    X = X.astype(float)
    rng = np.random.RandomState(0)
    idx = rng.permutation(len(X))[:nmax]
    X = X.iloc[idx].reset_index(drop=True)
    X = X.fillna(X.median())  # MonthlyIncome / NumberOfDependents missing: median imputation (documented)
    return X, y[idx], []


def _acs(task="income", nmax=40000):
    from folktables import ACSDataSource, ACSIncome, ACSEmployment
    T = {"income": ACSIncome, "employment": ACSEmployment}[task]
    ds = ACSDataSource(survey_year="2018", horizon="1-Year", survey="person", root_dir=os.path.join(DATA, "acs"))
    d = ds.get_data(states=["CA"], download=True)
    X, y, _ = T.df_to_numpy(d)
    X = pd.DataFrame(X, columns=T.features).astype(float)
    y = y.astype(int)
    rng = np.random.RandomState(0)
    idx = rng.permutation(len(X))[:nmax]
    numeric = {"AGEP", "WKHP"}  # all other ACS attributes are coded categories (one-hot for LR/MLP, ordinal for trees)
    return X.iloc[idx].reset_index(drop=True), y[idx], [c for c in X.columns if c not in numeric]


def load_dataset(name):
    """Return (X DataFrame, y, categorical column names); cached as data/raw/<name>.pkl after the first download."""
    import pickle
    p = os.path.join(DATA, "raw", name + ".pkl")
    if os.path.exists(p):
        return pickle.load(open(p, "rb"))
    out = _load_dataset(name)
    pickle.dump(out, open(p, "wb"))
    return out


def _load_dataset(name):
    if name == "german": return _german()
    if name == "pima": return _pima()
    if name == "gmsc": return _gmsc()
    if name == "acs_income": return _acs("income")
    if name == "acs_employment": return _acs("employment")
    raise ValueError(name)


# ---------------------------------------------------------------- models
def make_model(kind, cols, cat, seed, n_train=0):
    num = [c for c in cols if c not in cat]
    if kind in ("lr", "mlp"):
        tf = ColumnTransformer([
            ("n", StandardScaler(), num),
            ("c", OneHotEncoder(handle_unknown="ignore", min_frequency=20, sparse_output=False), cat)])
        clf = (LogisticRegression(max_iter=2000, C=1.0) if kind == "lr" else
               MLPClassifier((64, 64), alpha=1e-2, early_stopping=n_train > 5000, max_iter=300,
                         random_state=seed))
        return Pipeline([("t", tf), ("m", clf)])
    if kind == "rf":
        return RandomForestClassifier(100, max_depth=8, min_samples_leaf=3, n_jobs=1, random_state=seed)
    if kind == "xgb":
        return xgb.XGBClassifier(n_estimators=200, max_depth=4, learning_rate=0.1, subsample=0.8, n_jobs=1,
                                 random_state=seed, tree_method="hist")
    raise ValueError(kind)


VALUE_FN = {"lr": "log-odds", "xgb": "log-odds", "mlp": "log-odds", "rf": "probability"}
KINDS = ["lr", "xgb", "rf", "mlp"]


def _logit(p):
    p = np.clip(p, 1e-12, 1 - 1e-12)
    return np.log(p / (1 - p))


class Task:
    """A dataset with a fixed split and one trained model.

    The explained function f is the model's log-odds (LR, XGBoost, MLP) or its probability (RF; the exact TreeSHAP
    target is only available there in probability space). The Shapley players are the original attributes: LR/MLP
    one-hot encode categoricals inside the pipeline, so masking an attribute masks its whole one-hot group.
    Instances are chosen once per dataset (select_instances) and shared by all models.
    """

    def __init__(self, ds, kind, model_seed=0, split_seed=0, K=50, bg_seed=0, data=None):
        X, y, cat = data if data is not None else load_dataset(ds)
        self.ds, self.kind, self.cols, self.cat = ds, kind, list(X.columns), cat
        Xtr, Xte, ytr, yte = train_test_split(X.values, y, test_size=0.3, random_state=split_seed, stratify=y)
        self.Xtr, self.Xte, self.ytr, self.yte = Xtr, Xte, ytr, yte
        mk = lambda a: pd.DataFrame(a, columns=self.cols)
        self.model = make_model(kind, self.cols, cat, model_seed, len(Xtr))
        if kind == "lr":
            self.model.fit(mk(Xtr), ytr)
            self.f = lambda a: self.model.decision_function(mk(np.asarray(a)))
        elif kind == "mlp":
            self.model.fit(mk(Xtr), ytr)
            self.f = lambda a: _logit(self.model.predict_proba(mk(np.asarray(a)))[:, 1])
        elif kind == "xgb":
            self.model.fit(Xtr, ytr)
            self.f = lambda a: self.model.get_booster().predict(xgb.DMatrix(np.asarray(a)), output_margin=True)
        else:
            self.model.fit(Xtr, ytr)
            self.f = lambda a: self.model.predict_proba(np.asarray(a))[:, 1]
        self.proba = (lambda a: 1 / (1 + np.exp(-self.f(a)))) if kind != "rf" else self.f
        self.auc = roc_auc_score(yte, self.proba(Xte))
        self.acc = float(((self.proba(Xte) > 0.5) == yte).mean())
        self.d = X.shape[1]
        rng = np.random.RandomState(1000 + bg_seed)
        self.bg = Xtr[rng.permutation(len(Xtr))[:K]]


def select_instances(tasks, n_random=25, n_near=25, pool=300, seed=7):
    """Instances shared by all models of a dataset: n_random random test rows plus n_near rows closest to
    the decision boundary (smallest |mean probability - 0.5| across models) from a random pool."""
    T0 = next(iter(tasks.values()))
    rng = np.random.RandomState(seed)
    perm = rng.permutation(len(T0.Xte))
    pool = min(pool, len(perm) // 2)
    pidx = perm[:pool]
    pm = np.mean([t.proba(t.Xte[pidx]) for t in tasks.values()], 0)
    near = pidx[np.argsort(np.abs(pm - 0.5))[:n_near]]
    rest = [i for i in perm[pool:]][:n_random]
    idx = np.concatenate([rest, near]).astype(int)
    stratum = np.array(["random"] * len(rest) + ["near_boundary"] * len(near))
    return idx, stratum


# ---------------------------------------------------------------- explainers
def run_kernel(f, bg, X, nsamples, seed, l1_reg=False):
    """KernelSHAP (shap.KernelExplainer, paired sampling as implemented) with `nsamples` coalitions per instance.
    Budget in model evaluations = nsamples * len(bg). l1_reg=False is the primary arm; the shap 0.51 default
    is 'num_features(10)'."""
    ex = shap.KernelExplainer(f, bg)
    np.random.seed(seed)
    return np.asarray(ex.shap_values(X, nsamples=int(nsamples), l1_reg=l1_reg, silent=True))


def run_perm(f, bg, X, nsamples, seed):
    """shap.PermutationExplainer (antithetic permutations); max_evals=nsamples coalition evaluations per instance."""
    ex = shap.PermutationExplainer(f, shap.maskers.Independent(bg, max_samples=len(bg)), seed=seed)
    return np.asarray(ex(X, max_evals=int(nsamples), silent=True).values)


def exact_enum(f, bg, x, chunk=2 ** 12):
    """Exact interventional Shapley values of v(S)=mean_b f(x_S, b_notS) by enumerating all 2^d coalitions.
    Returns (phi, v(full), v(empty))."""
    from math import factorial
    d, K = len(x), len(bg)
    n = 2 ** d
    v = np.empty(n)
    shifts = np.arange(d)
    for a in range(0, n, chunk):
        m = np.arange(a, min(a + chunk, n))
        masks = ((m[:, None] >> shifts[None, :]) & 1).astype(bool)  # bit j <-> feature j
        Z = np.where(masks[:, None, :], x[None, None, :], bg[None, :, :]).reshape(-1, d)
        v[m] = f(Z).reshape(len(m), K).mean(1)
    pop = np.array([bin(i).count("1") for i in range(n)]) if d <= 16 else np.unpackbits(
        np.arange(n, dtype=">u4").view(np.uint8).reshape(-1, 4), axis=1).sum(1)
    w = np.array([factorial(k) * factorial(d - k - 1) / factorial(d) for k in range(d)])
    allm = np.arange(n)
    phi = np.zeros(d)
    for j in range(d):
        S = allm[((allm >> j) & 1) == 0]
        phi[j] = np.sum(w[pop[S]] * (v[S | (1 << j)] - v[S]))
    return phi, v[n - 1], v[0]


def target_exact(task, X):
    """Exact target in the task's value function and background, by structure:
    LR closed form (log-odds, grouped by original attribute), interventional TreeSHAP (XGB raw margin = log-odds;
    RF probability). None for the MLP (enumeration only)."""
    if task.kind == "lr":
        t = task.model.named_steps["t"]
        w = task.model.named_steps["m"].coef_[0]
        mk = lambda a: pd.DataFrame(np.asarray(a), columns=task.cols)
        Zx, Zb = t.transform(mk(X)), t.transform(mk(task.bg))
        # map each transformed column back to its original attribute
        owner = []
        for name, tr, cols in t.transformers_:
            if name == "n":
                owner += [task.cols.index(c) for c in cols]
            elif len(cols):
                for nm in tr.get_feature_names_out(cols):  # "<col>_<level>"; longest column-name prefix wins
                    owner.append(task.cols.index(max((c for c in cols if nm.startswith(c + "_")), key=len)))
        owner = np.array(owner)
        contrib = w[None, :] * (Zx - Zb.mean(0)[None, :])
        phi = np.zeros((len(X), task.d))
        for j in range(task.d):
            phi[:, j] = contrib[:, owner == j].sum(1)
        return phi
    if task.kind in ("xgb", "rf"):
        ex = shap.TreeExplainer(task.model, task.bg, feature_perturbation="interventional", model_output="raw")
        out = np.asarray(ex.shap_values(X, check_additivity=False))
        return out[..., 1] if out.ndim == 3 else out  # RF: positive-class slice
    return None
