"""Dataset loaders. Every loader returns a dict with
   X (n x d float array, categoricals ordinal-coded), y (0/1), names, cat (bool mask of categorical cols).
Data are cached under data/ (see README for download steps)."""
import os, io, json, urllib.request
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")


def _openml_csv(data_id):
    """Download an OpenML dataset as a DataFrame via the OpenML API (cached as parquet-less csv)."""
    path = os.path.join(DATA, f"openml_{data_id}.csv")
    if not os.path.exists(path):
        from sklearn.datasets import fetch_openml
        b = fetch_openml(data_id=data_id, as_frame=True, parser="auto", data_home=os.path.join(DATA, "sk_openml"))
        df = b.frame
        df.to_csv(path, index=False)
        with open(os.path.join(DATA, f"openml_{data_id}_target.txt"), "w") as f:
            f.write(b.target.name if hasattr(b.target, "name") else "class")
    return pd.read_csv(path)


def load_german():
    p = os.path.join(DATA, "german", "german.data")
    if not os.path.exists(p):
        import zipfile
        url = "https://archive.ics.uci.edu/static/public/144/statlog+german+credit+data.zip"
        os.makedirs(DATA, exist_ok=True)
        zp = os.path.join(DATA, "german.zip")
        urllib.request.urlretrieve(url, zp)
        zipfile.ZipFile(zp).extractall(os.path.join(DATA, "german"))
    df = pd.read_csv(p, sep=" ", header=None)
    names = ["status", "duration", "history", "purpose", "amount", "savings", "employment", "installment_rate",
             "personal_status", "debtors", "residence_since", "property", "age", "other_installments", "housing",
             "existing_credits", "job", "liable_people", "telephone", "foreign_worker"]
    cat = np.array([n in ("status", "history", "purpose", "savings", "employment", "personal_status", "debtors",
                          "property", "other_installments", "housing", "job", "telephone", "foreign_worker")
                    for n in names])
    X = np.zeros((len(df), 20))
    for j in range(20):
        X[:, j] = df[j].astype("category").cat.codes if cat[j] else df[j].astype(float)
    y = (df[20].values == 2).astype(int)  # 1 = bad credit risk
    return dict(X=X, y=y, names=names, cat=cat, name="german")


def load_pima():
    df = _openml_csv(37)
    tgt = df.columns[-1]
    y = (df[tgt].astype(str) == "tested_positive").astype(int).values
    Xdf = df.drop(columns=[tgt])
    return dict(X=Xdf.values.astype(float), y=y, names=list(Xdf.columns), cat=np.zeros(Xdf.shape[1], bool), name="pima")


def load_gmsc():
    df = _openml_csv(46929)
    tgt = "FinancialDistressNextTwoYears"
    y = (df[tgt].astype(str) == "Yes").astype(int).values
    Xdf = df.drop(columns=[tgt]).astype(float)
    Xdf = Xdf.fillna(Xdf.median())  # median imputation (MonthlyIncome, NumberOfDependents)
    return dict(X=Xdf.values, y=y, names=list(Xdf.columns), cat=np.zeros(Xdf.shape[1], bool), name="gmsc")


def load_acs():
    from folktables import ACSDataSource, ACSIncome
    ds = ACSDataSource(survey_year="2018", horizon="1-Year", survey="person", root_dir=os.path.join(DATA, "acs"))
    d = ds.get_data(states=["CA"], download=True)
    X, y, _ = ACSIncome.df_to_numpy(d)
    names = list(ACSIncome.features)
    cat_names = {"COW", "MAR", "SCHL", "OCCP", "POBP", "RELP", "RAC1P", "SEX"}
    cat = np.array([n in cat_names for n in names])
    return dict(X=X.astype(float), y=y.astype(int), names=names, cat=cat, name="acs")


def load_arrhythmia():
    import zipfile
    p = os.path.join(DATA, "arrhythmia", "arrhythmia.data")
    if not os.path.exists(p):
        zp = os.path.join(DATA, "arrhythmia.zip")
        urllib.request.urlretrieve("https://archive.ics.uci.edu/static/public/5/arrhythmia.zip", zp)
        zipfile.ZipFile(zp).extractall(os.path.join(DATA, "arrhythmia"))
    df = pd.read_csv(p, header=None, na_values="?")
    y = (df.iloc[:, -1].values != 1).astype(int)  # class 1 = normal; others = arrhythmia
    Xdf = df.iloc[:, :-1]
    Xdf = Xdf.loc[:, Xdf.nunique() > 1]  # drop constant columns
    Xdf = Xdf.fillna(Xdf.median())
    return dict(X=Xdf.values.astype(float), y=y, names=[f"f{c}" for c in Xdf.columns],
                cat=np.zeros(Xdf.shape[1], bool), name="arrhythmia")


LOADERS = dict(german=load_german, pima=load_pima, gmsc=load_gmsc, acs=load_acs, arrhythmia=load_arrhythmia)


def load(name, seed=0, max_train=50000):
    """Returns dict with train/test split (stratified 70/30, fixed seed). Training set capped at max_train rows."""
    from sklearn.model_selection import train_test_split
    D = LOADERS[name]()
    idx = np.arange(len(D["y"]))
    tr, te = train_test_split(idx, test_size=0.3, random_state=seed, stratify=D["y"])
    if len(tr) > max_train:
        tr = np.random.RandomState(seed).choice(tr, max_train, replace=False)
    D.update(Xtr=D["X"][tr], ytr=D["y"][tr], Xte=D["X"][te], yte=D["y"][te])
    return D
