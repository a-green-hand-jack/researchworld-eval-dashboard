"""Datasets, preprocessing, models and value-table construction."""
import os, numpy as np, pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import QuantileTransformer
from sklearn.metrics import roc_auc_score

RAW = os.environ.get("SHAP_RAW", "/work/data/raw")

# dataset spec: name -> (loader, column types, background size R used for tables)
#   types: num (numeric), bin (binary/ordinal numeric), cat (one-hot for linear/MLP, ordinal for trees),
#          te (high-cardinality categorical -> smoothed target mean learnt on the training split)

GERMAN_COLS = ["checking_status", "duration", "credit_history", "purpose", "credit_amount", "savings",
               "employment_since", "installment_rate", "personal_status_sex", "other_debtors", "residence_since",
               "property", "age", "other_installment_plans", "housing", "n_existing_credits", "job",
               "n_liable", "telephone", "foreign_worker"]
GERMAN_CAT = {"checking_status", "credit_history", "purpose", "savings", "employment_since", "personal_status_sex",
              "other_debtors", "property", "other_installment_plans", "housing", "job", "telephone", "foreign_worker"}


def load_dataset(name, seed=0):
    """Returns X (DataFrame, raw players as columns), y (0/1 numpy), spec (dict col->type)."""
    if name == "german":
        g = pd.read_csv(f"{RAW}/german/german.data", sep=" ", header=None)
        X = g.iloc[:, :20].copy(); X.columns = GERMAN_COLS
        y = (g.iloc[:, 20].values == 2).astype(int)  # 1 = bad credit risk
        spec = {c: ("cat" if c in GERMAN_CAT else "num") for c in GERMAN_COLS}
        return X, y, spec
    if name == "pima":
        d = pd.read_parquet(f"{RAW}/pima.parquet")
        y = (d["__target__"].astype(str) == "tested_positive").astype(int).values
        X = d.drop(columns="__target__").astype(float)
        return X.reset_index(drop=True), y, {c: "num" for c in X.columns}
    if name == "gmsc":
        d = pd.read_parquet(f"{RAW}/gmsc.parquet")
        d = d.sample(n=40000, random_state=seed).reset_index(drop=True)  # subsample for tractable training
        y = (d["__target__"].astype(str) == "Yes").astype(int).values
        X = d.drop(columns="__target__").astype(float)
        return X, y, {c: "num" for c in X.columns}
    if name in ("acsincome", "acsemployment"):
        from folktables import ACSDataSource, ACSIncome, ACSEmployment
        src = ACSDataSource(survey_year="2018", horizon="1-Year", survey="person", root_dir=f"{RAW}/acs")
        df = src.get_data(states=["CA"], download=False)
        prob = ACSIncome if name == "acsincome" else ACSEmployment
        Xa, ya, _ = prob.df_to_pandas(df)
        X = Xa.copy().reset_index(drop=True); y = np.asarray(ya).ravel().astype(int)
        rng = np.random.RandomState(seed)
        idx = rng.choice(len(X), 40000, replace=False)
        X = X.iloc[idx].reset_index(drop=True); y = y[idx]
        X = X.fillna(0).astype(float)
        if name == "acsincome":
            spec = {"AGEP": "num", "COW": "cat", "SCHL": "num", "MAR": "cat", "OCCP": "te", "POBP": "te",
                    "RELP": "cat", "WKHP": "num", "SEX": "bin", "RAC1P": "cat"}
        else:
            spec = {"AGEP": "num", "SCHL": "num", "MAR": "cat", "RELP": "cat", "DIS": "bin", "ESP": "cat",
                    "CIT": "cat", "MIG": "cat", "MIL": "cat", "ANC": "cat", "NATIVITY": "bin", "DEAR": "bin",
                    "DEYE": "bin", "DREM": "bin", "SEX": "bin", "RAC1P": "cat"}
        return X, y, spec
    raise ValueError(name)


# table settings: reference-background size R (rows used to define the value function) and #instances
TABLE_CFG = {
    "pima": dict(R=500, n_inst=100),
    "gmsc": dict(R=1000, n_inst=100),
    "acsincome": dict(R=1000, n_inst=100),
    "acsemployment": dict(R=100, n_inst=60),
    "german": dict(R=100, n_inst=24),
}
DATASETS = ["pima", "gmsc", "acsincome", "acsemployment", "german"]
MODELS = ["lr", "mlp", "rf", "xgb"]


class Prep:
    """Maps the d raw player columns to model inputs.  `groups[j]` = encoded column indices of player j."""

    def __init__(self, spec, mode):
        self.spec, self.mode = spec, mode
        self.cols = list(spec.keys())

    def _imp(self, X):
        X = X.copy()
        for c, m in self.med.items():
            if X[c].isna().any():
                X[c] = X[c].fillna(m)
        return X

    def fit(self, X, y):
        self.cat_levels, self.te, self.qt = {}, {}, None
        self.gmean = float(np.mean(y))
        self.med = {c: float(np.nanmedian(X[c].values)) for c in self.cols if self.spec[c] in ('num', 'bin')}
        for c in self.cols:
            t = self.spec[c]
            if t == "cat":
                self.cat_levels[c] = sorted(pd.unique(X[c]).tolist())
            elif t == "te":
                df = pd.DataFrame({"k": X[c].values, "y": y})
                g = df.groupby("k")["y"].agg(["sum", "count"])
                self.te[c] = ((g["sum"] + 20 * self.gmean) / (g["count"] + 20)).to_dict()
        X = self._imp(X)
        if self.mode == "lin":
            numc = [c for c in self.cols if self.spec[c] == "num"]
            self.numc = numc
            if numc:
                self.qt = QuantileTransformer(n_quantiles=min(200, len(X)), output_distribution="normal",
                                              random_state=0).fit(X[numc].values)
            # standardisation stats for bin / te columns
            tmp = self._raw_other(X)
            self.mu = {c: tmp[c].mean() for c in tmp}; self.sd = {c: tmp[c].std() + 1e-9 for c in tmp}
        self._build_groups()
        return self

    def _raw_other(self, X):
        out = {}
        for c in self.cols:
            t = self.spec[c]
            if t == "bin":
                out[c] = X[c].values.astype(float)
            elif t == "te":
                out[c] = X[c].map(self.te[c]).fillna(self.gmean).values.astype(float)
        return out

    def _build_groups(self):
        self.groups, k = [], 0
        for c in self.cols:
            if self.mode == "lin" and self.spec[c] == "cat":
                n = len(self.cat_levels[c])
            else:
                n = 1
            self.groups.append(np.arange(k, k + n)); k += n
        self.p = k

    def encode(self, X):
        X = self._imp(X)
        n = len(X)
        out = np.zeros((n, self.p), dtype=np.float32)
        if self.mode == "lin" and self.qt is not None:
            q = self.qt.transform(X[self.numc].values)
        other = self._raw_other(X)
        for j, c in enumerate(self.cols):
            t, gi = self.spec[c], self.groups[j]
            if t == "num":
                out[:, gi[0]] = q[:, self.numc.index(c)] if self.mode == "lin" else X[c].values
            elif t in ("bin", "te"):
                v = other[c]
                out[:, gi[0]] = (v - self.mu[c]) / self.sd[c] if self.mode == "lin" else v
            else:  # cat
                lv = self.cat_levels[c]
                if self.mode == "lin":
                    codes = pd.Categorical(X[c].values, categories=lv).codes
                    ok = codes >= 0
                    out[np.where(ok)[0], gi[codes[ok]]] = 1.0
                else:
                    out[:, gi[0]] = pd.Categorical(X[c].values, categories=lv).codes
        return out


def make_model(kind, n_train, seed):
    if kind == "lr":
        from sklearn.linear_model import LogisticRegression
        return LogisticRegression(C=1.0, max_iter=2000)
    if kind == "mlp":
        from sklearn.neural_network import MLPClassifier
        if n_train < 5000:  # small data: strong L2 + few epochs (early stopping on a 10% split is unstable here)
            return MLPClassifier(hidden_layer_sizes=(64, 64), alpha=1.0, early_stopping=False, max_iter=50,
                                 random_state=seed)
        return MLPClassifier(hidden_layer_sizes=(64, 64), alpha=1e-3, early_stopping=True, max_iter=300,
                             random_state=seed)
    if kind == "rf":
        from sklearn.ensemble import RandomForestClassifier
        return RandomForestClassifier(n_estimators=50 if n_train < 1000 else 100, min_samples_leaf=5 if n_train < 5000 else 20,
                                      max_features="sqrt", n_jobs=1, random_state=seed)
    if kind == "xgb":
        import xgboost as xgb
        return xgb.XGBClassifier(n_estimators=150, max_depth=4, learning_rate=0.1, subsample=0.8,
                                 colsample_bytree=0.8, tree_method="hist", n_jobs=1, random_state=seed,
                                 verbosity=0)
    raise ValueError(kind)


def mode_of(kind):
    return "lin" if kind in ("lr", "mlp") else "tree"


class Fitted:
    """A trained model + its preprocessing; predict() takes encoded float32 matrices -> P(y=1)."""

    def __init__(self, kind, prep, model, auc=None):
        self.kind, self.prep, self.model, self.auc = kind, prep, model, auc

    def predict(self, E):
        if self.kind == "mlp":  # float32 forward pass (faster than sklearn's float64 path)
            h = E
            for W, b in zip(self.model.coefs_[:-1], self.model.intercepts_[:-1]):
                h = np.maximum(h @ W.astype(np.float32) + b.astype(np.float32), 0)
            z = h @ self.model.coefs_[-1].astype(np.float32) + self.model.intercepts_[-1].astype(np.float32)
            return (1.0 / (1.0 + np.exp(-z.ravel().astype(np.float64)))).astype(np.float32)
        return self.model.predict_proba(E)[:, 1].astype(np.float32)


def split_and_fit(ds, kind, split_seed=0, model_seed=0, bootstrap=False):
    X, y, spec = load_dataset(ds)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, random_state=split_seed, stratify=y)
    Xtr, Xte = Xtr.reset_index(drop=True), Xte.reset_index(drop=True)
    if bootstrap:  # resample the training set with replacement (used for the retraining baseline)
        rng = np.random.RandomState(1000 + model_seed)
        bi = rng.choice(len(Xtr), len(Xtr), replace=True)
        Xfit, yfit = Xtr.iloc[bi].reset_index(drop=True), ytr[bi]
    else:
        Xfit, yfit = Xtr, ytr
    prep = Prep(spec, mode_of(kind)).fit(Xfit, yfit)
    m = make_model(kind, len(Xfit), model_seed)
    m.fit(prep.encode(Xfit), yfit)
    f = Fitted(kind, prep, m)
    f.auc = float(roc_auc_score(yte, f.predict(prep.encode(Xte))))
    return f, Xtr, ytr, Xte, yte


def build_table(f, x_row, bg, chunk_rows=400_000, keep_full=True):
    """Value table of the interventional (marginal) game:  v(S) = mean_r f(x_S, b_r,~S).
    x_row: one-row DataFrame, bg: DataFrame of R background rows.  Returns (vbar[2^d], V[2^d,R] or None)."""
    prep = f.prep
    d = len(prep.cols)
    xe = prep.encode(x_row)[0]
    be = prep.encode(bg)
    R = len(be)
    col2pl = np.zeros(prep.p, dtype=np.int64)
    for j, g in enumerate(prep.groups):
        col2pl[g] = j
    nS = 1 << d
    per = max(1, chunk_rows // R)
    vbar = np.zeros(nS, dtype=np.float64)
    V = np.zeros((nS, R), dtype=np.float32) if keep_full else None
    shifts = col2pl
    for s0 in range(0, nS, per):
        ids = np.arange(s0, min(nS, s0 + per))
        sel = ((ids[:, None] >> shifts[None, :]) & 1).astype(bool)  # (c, p): column taken from x
        H = np.where(sel[:, None, :], xe[None, None, :], be[None, :, :]).reshape(-1, prep.p)
        pr = f.predict(H).reshape(len(ids), R)
        vbar[ids] = pr.mean(1)
        if keep_full:
            V[ids] = pr
    return vbar, V
