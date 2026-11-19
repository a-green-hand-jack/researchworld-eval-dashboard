"""Dataset loading. Every loader returns a dict with
X (n,d float64; categorical features are non-negative integer codes), y (0/1), names, is_cat.
Raw files live in /work/data/<name>/ (see README for the download commands)."""
import os
import numpy as np
import pandas as pd

DATA = os.environ.get("SHAPRE_DATA", "/work/data")


def _codes(s):
    return pd.factorize(s, sort=True)[0].astype(float)


def load_german():
    cols = [f"A{i}" for i in range(1, 21)] + ["cls"]
    df = pd.read_csv(f"{DATA}/german/german.data", sep=" ", header=None, names=cols)
    y = (df.pop("cls").values == 2).astype(int)  # 1 = bad credit risk
    is_cat = np.array([not pd.api.types.is_numeric_dtype(df[c]) for c in df.columns])
    X = np.column_stack([_codes(df[c]) if cat else df[c].astype(float).values
                         for c, cat in zip(df.columns, is_cat)])
    return dict(X=X, y=y, names=list(df.columns), is_cat=is_cat)


def _from_csv(name, pos_label, target="target"):
    df = pd.read_csv(f"{DATA}/{name}/{name}.csv")
    y = (df.pop(target).astype(str).values == pos_label).astype(int)
    X = df.astype(float)
    X = X.fillna(X.median())  # median imputation (only GMSC has missing values)
    return dict(X=X.values, y=y, names=list(df.columns), is_cat=np.zeros(X.shape[1], bool))


def load_pima():
    return _from_csv("pima", "tested_positive")


def load_gmsc():
    return _from_csv("gmsc", "Yes")


def load_spambase():
    return _from_csv("spambase", "1")


def load_wdbc():
    from sklearn.datasets import load_breast_cancer  # UCI WDBC, bundled with scikit-learn
    b = load_breast_cancer()
    return dict(X=b.data.astype(float), y=(b.target == 0).astype(int),  # 1 = malignant
                names=list(b.feature_names), is_cat=np.zeros(b.data.shape[1], bool))


def load_arrhythmia():
    df = pd.read_csv(f"{DATA}/arrhythmia/arrhythmia.data", header=None, na_values="?")
    y = (df.iloc[:, -1].values != 1).astype(int)  # 1 = any arrhythmia class, 0 = normal (class 1)
    X = df.iloc[:, :-1].astype(float)
    X = X.loc[:, X.nunique() > 1]  # drop constant columns
    X = X.fillna(X.median())
    return dict(X=X.values, y=y, names=[f"c{c}" for c in X.columns], is_cat=np.zeros(X.shape[1], bool))


def load_acs(n_sub=40000, seed=0):
    from folktables import ACSDataSource, ACSIncome
    ds = ACSDataSource(survey_year="2018", horizon="1-Year", survey="person", root_dir=f"{DATA}/acs")
    df = ds.get_data(states=["CA"], download=False)
    X, y, _ = ACSIncome.df_to_numpy(df)
    idx = np.random.RandomState(seed).choice(len(X), n_sub, replace=False)
    names = list(ACSIncome.features)
    cat = {"COW", "SCHL", "MAR", "OCCP", "POBP", "RELP", "SEX", "RAC1P"}
    return dict(X=X[idx].astype(float), y=y[idx].astype(int), names=names,
                is_cat=np.array([n in cat for n in names]))


LOADERS = dict(pima=load_pima, gmsc=load_gmsc, acs=load_acs, german=load_german,
               wdbc=load_wdbc, spambase=load_spambase, arrhythmia=load_arrhythmia)


def load(name, test_frac=0.3, seed=0, n_sub=None):
    d = LOADERS[name]()
    X, y = d["X"], d["y"]
    if n_sub is not None and len(X) > n_sub:
        idx = np.random.RandomState(seed).choice(len(X), n_sub, replace=False)
        X, y = X[idx], y[idx]
    from sklearn.model_selection import train_test_split
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=test_frac, stratify=y, random_state=seed)
    d.update(Xtr=Xtr, Xte=Xte, ytr=ytr, yte=yte, d=X.shape[1])
    return d
