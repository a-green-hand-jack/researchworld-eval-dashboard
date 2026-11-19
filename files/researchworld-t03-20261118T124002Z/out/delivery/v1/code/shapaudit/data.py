"""Datasets in *attribute space*: X_attr (n, d) holds numeric values or integer category codes;
`Encoder` maps attribute rows to model inputs (standardised numerics, one-hot categoricals) and
records which model-input columns belong to which attribute (the Shapley players)."""
import io, os, zipfile, urllib.request
import numpy as np, pandas as pd

RAW = os.environ.get("SHAPAUDIT_RAW", os.path.join(os.path.dirname(__file__), "..", "data", "raw"))


def _get(url, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        urllib.request.urlretrieve(url, path)
    return path


class Dataset:
    def __init__(self, name, X, y, is_cat, names):
        self.name, self.X, self.y, self.is_cat, self.names = name, X.astype(np.float64), y.astype(int), np.asarray(is_cat), list(names)
        self.d = X.shape[1]


def german():
    p = _get("https://archive.ics.uci.edu/static/public/144/statlog+german+credit+data.zip", os.path.join(RAW, "german.zip"))
    df = pd.read_csv(io.BytesIO(zipfile.ZipFile(p).read("german.data")), sep=" ", header=None)
    num_cols = [1, 4, 7, 10, 12, 15, 17]  # duration, amount, rate, residence, age, n_credits, n_liable
    y = (df[20] == 2).astype(int).values  # 1 = bad credit
    cols, is_cat, names = [], [], []
    for j in range(20):
        if j in num_cols:
            cols.append(df[j].values.astype(float)); is_cat.append(False)
        else:
            cols.append(pd.factorize(df[j])[0].astype(float)); is_cat.append(True)
        names.append(f"A{j + 1}")
    return Dataset("german", np.stack(cols, 1), y, is_cat, names)


def arrhythmia():
    p = _get("https://archive.ics.uci.edu/static/public/5/arrhythmia.zip", os.path.join(RAW, "arrhythmia.zip"))
    df = pd.read_csv(io.BytesIO(zipfile.ZipFile(p).read("arrhythmia.data")), header=None, na_values="?")
    y = (df[279] != 1).astype(int).values  # 1 = any arrhythmia class (class 1 = normal)
    X = df.iloc[:, :279]
    X = X.fillna(X.median())
    X = X.loc[:, X.nunique() > 1]
    # keep binary (0/1) and low-cardinality columns numeric: no one-hot, every attribute is a single column
    return Dataset("arrhythmia", X.values, y, np.zeros(X.shape[1], bool), [f"c{j}" for j in X.columns])


def acs(task="ACSEmployment", state="AL", year="2018"):
    from folktables import ACSDataSource, ACSEmployment, ACSIncome, ACSPublicCoverage, ACSMobility, ACSTravelTime
    T = dict(ACSEmployment=ACSEmployment, ACSIncome=ACSIncome, ACSPublicCoverage=ACSPublicCoverage,
             ACSMobility=ACSMobility, ACSTravelTime=ACSTravelTime)[task]
    src = ACSDataSource(survey_year=year, horizon="1-Year", survey="person", root_dir=os.path.join(RAW, "acs"))
    data = src.get_data(states=[state], download=True)
    X, y, _ = T.df_to_numpy(data)
    feats = list(T.features)
    nunique = [len(np.unique(X[:, j])) for j in range(X.shape[1])]
    # nominal categoricals are one-hot encoded; AGEP, SCHL, WKHP, PINCP-like numerics and binaries stay ordinal/numeric
    ordinal = {"AGEP", "SCHL", "WKHP", "JWMNP", "POVPIP", "PWGTP", "PINCP", "FER"}
    is_cat = np.array([(f not in ordinal) and n > 2 for f, n in zip(feats, nunique)])
    X = X.astype(float)
    for j in np.where(is_cat)[0]:
        X[:, j] = pd.factorize(X[:, j])[0]
    return Dataset(f"{task}_{state}{year}", X, y.astype(int), is_cat, feats)


class Encoder:
    """attribute rows -> model inputs; `blocks[j]` = slice of model-input columns of attribute j."""
    def __init__(self, onehot=True):
        self.onehot = onehot

    def fit(self, ds, Xtr):
        self.is_cat = ds.is_cat & self.onehot
        self.d = ds.d
        self.mu = Xtr.mean(0); self.sd = Xtr.std(0) + 1e-9
        if not self.onehot:  # ordinal codes for tree models: raw values, no scaling
            self.mu = np.zeros(ds.d); self.sd = np.ones(ds.d)
        self.ncat = [int(Xtr[:, j].max()) + 1 if self.is_cat[j] else 0 for j in range(ds.d)]
        self.blocks, c = [], 0
        for j in range(ds.d):
            w = self.ncat[j] if self.is_cat[j] else 1
            self.blocks.append(slice(c, c + w)); c += w
        self.p = c
        return self

    def __call__(self, X):
        X = np.atleast_2d(X)
        Z = np.zeros((X.shape[0], self.p), np.float32)
        for j in range(self.d):
            b = self.blocks[j]
            if self.is_cat[j]:
                codes = np.clip(X[:, j].astype(int), 0, self.ncat[j] - 1)
                Z[np.arange(len(X)), b.start + codes] = 1.0
            else:
                Z[:, b.start] = (X[:, j] - self.mu[j]) / self.sd[j]
        return Z

    def col_attr(self):
        """attribute index of every model-input column"""
        a = np.zeros(self.p, int)
        for j, b in enumerate(self.blocks):
            a[b] = j
        return a
