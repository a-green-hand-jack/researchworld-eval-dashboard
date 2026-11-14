"""Dataset loading. Every dataset is returned in a *raw attribute space*: an (n, d) float array whose
columns are the d original attributes ("players" of the Shapley game). Categorical attributes are
integer-coded (code = frequency rank in the training split; rare levels collapsed to one 'other' code).
"""
import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
MAX_TRAIN = 30000
RESULTS = os.path.abspath(os.path.join(ROOT, "..", "results"))
os.makedirs(RESULTS, exist_ok=True)
DATASETS = ["pima", "gmsc", "acsincome", "german"]


def _encode_cat(col_train, col_all, max_levels=30):
    vc = pd.Series(col_train).value_counts()
    levels = list(vc.index[:max_levels])
    mp = {v: i for i, v in enumerate(levels)}
    other = len(levels) if len(vc) > max_levels else None
    out = np.array([mp.get(v, other if other is not None else 0) for v in col_all], dtype=float)
    ncat = len(levels) + (1 if other is not None else 0)
    return out, ncat


def load(name, seed=0):
    """Return dict(X, y, names, ncat (0 for numeric), train_idx, test_idx). y=1 is the 'adverse' class."""
    if name == "pima":
        import openml
        d = openml.datasets.get_dataset(37)
        X, y, _, _ = d.get_data(target=d.default_target_attribute)
        y = (y == "tested_positive").astype(int).values
        names = list(X.columns)
        Xr = X.values.astype(float)
        ncat = [0] * Xr.shape[1]
    elif name == "gmsc":
        import openml
        d = openml.datasets.get_dataset(46929)
        X, y, _, _ = d.get_data(target=d.default_target_attribute)
        y = (y == "Yes").astype(int).values
        short = ["RevolvUtil", "age", "N30-59late", "DebtRatio", "MonthlyInc", "NOpenCredit",
                 "N90late", "NRealEstate", "N60-89late", "NDependents"]
        names = short
        Xr = X.values.astype(float)
        ncat = [0] * Xr.shape[1]
    elif name == "acsincome":
        from folktables import ACSDataSource, ACSIncome
        ds = ACSDataSource(survey_year="2018", horizon="1-Year", survey="person",
                           root_dir=os.path.join(ROOT, "acs"))
        raw = ds.get_data(states=["CO"], download=True)
        X, y, _ = ACSIncome.df_to_pandas(raw)
        y = y.values.ravel().astype(int)
        names = list(X.columns)
        Xr = X.values.astype(float)
        cats = ["COW", "MAR", "OCCP", "POBP", "RELP", "SEX", "RAC1P"]
        ncat = [1 if n in cats else 0 for n in names]
    elif name == "german":
        cols = ["status", "duration", "credit_hist", "purpose", "amount", "savings", "employment",
                "install_rate", "pers_status", "debtors", "residence", "property", "age",
                "other_plans", "housing", "n_credits", "job", "n_liable", "telephone", "foreign"]
        df = pd.read_csv(os.path.join(ROOT, "german.data"), sep=" ", header=None, names=cols + ["y"])
        y = (df.pop("y") == 2).astype(int).values  # 2 = bad credit = adverse
        names = cols
        num = {"duration", "amount", "install_rate", "residence", "age", "n_credits", "n_liable"}
        Xr = df.values  # object
        ncat = [0 if n in num else 1 for n in names]
    else:
        raise ValueError(name)

    n = len(y)
    idx = np.arange(n)
    tr, te = train_test_split(idx, test_size=0.3, random_state=seed, stratify=y)
    if len(tr) > MAX_TRAIN:
        tr = np.random.RandomState(seed).choice(tr, MAX_TRAIN, replace=False)
    Xo = np.zeros((n, len(names)))
    nc = np.zeros(len(names), dtype=int)
    for j in range(len(names)):
        col = Xr[:, j]
        if ncat[j]:
            Xo[:, j], nc[j] = _encode_cat(col[tr], col)
        else:
            Xo[:, j] = col.astype(float)
    # median impute numeric NaNs (fit on train)
    for j in range(len(names)):
        m = np.isnan(Xo[:, j])
        if m.any():
            Xo[m, j] = np.nanmedian(Xo[tr, j])
    return dict(name=name, X=Xo, y=y, names=names, ncat=nc, train=tr, test=te)


if __name__ == "__main__":
    for n in DATASETS:
        D = load(n)
        print(n, D["X"].shape, "pos rate %.3f" % D["y"].mean(), "train", len(D["train"]), "test", len(D["test"]),
              "ncat", D["ncat"].tolist())
