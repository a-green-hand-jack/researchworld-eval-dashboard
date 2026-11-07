"""Dataset loading at *attribute level*.

Every loader returns a `Data` with
  A      (n, d) float matrix: one column per original attribute (categoricals as integer codes)
  names  list of d attribute names
  levels dict {col index: array of category codes} for categorical attributes (others numeric)
  y      binary labels
  encode(A) -> model input matrix (categoricals one-hot, numerics as is).
SHAP explanations are computed over the d attributes (a one-hot group is masked jointly), which is
how a practitioner reports an attribution per original attribute.
Raw files are cached in $SHAP_DATA (default /hutian/data/raw).
"""
import io, os, zipfile
import numpy as np, pandas as pd

RAW = os.environ.get("SHAP_DATA", "/hutian/data/raw")
os.makedirs(RAW, exist_ok=True)


class Data:
    def __init__(self, name, A, names, y, levels):
        self.name, self.A, self.names, self.y, self.levels = name, np.asarray(A, float), list(names), np.asarray(y), levels
        self.d = self.A.shape[1]

    def encode(self, A):
        A = np.asarray(A, float)
        parts = []
        for j in range(self.d):
            if j in self.levels:
                parts.append((A[:, [j]] == self.levels[j][None, :]).astype(float))
            else:
                parts.append(A[:, [j]])
        return np.concatenate(parts, axis=1)


def _cat_codes(df, cat_cols):
    levels, out = {}, df.copy()
    for c in cat_cols:
        codes, uniques = pd.factorize(df[c], sort=True)
        out[c] = codes.astype(float)
        levels[list(df.columns).index(c)] = np.arange(len(uniques), dtype=float)
    return out, levels


def german():
    path = f"{RAW}/german.zip"
    if not os.path.exists(path):
        import urllib.request
        urllib.request.urlretrieve("https://archive.ics.uci.edu/static/public/144/statlog+german+credit+data.zip", path)
    df = pd.read_csv(io.BytesIO(zipfile.ZipFile(path).read("german.data")), sep=" ", header=None)
    names = ["status", "duration", "history", "purpose", "amount", "savings", "employment", "rate", "personal",
             "debtors", "residence", "property", "age", "other_plans", "housing", "existing_credits", "job",
             "liable", "telephone", "foreign"]
    df.columns = names + ["y"]
    y = (df.pop("y") == 2).astype(int).values  # 1 = bad credit
    cat = [c for c in names if not pd.api.types.is_numeric_dtype(df[c])]
    df, levels = _cat_codes(df, cat)
    return Data("german", df.values, names, y, levels)


def pima():
    from sklearn.datasets import fetch_openml
    d = fetch_openml(data_id=37, as_frame=True, data_home=RAW)
    return Data("pima", d.data.astype(float).values, list(d.data.columns), (d.target == "tested_positive").astype(int).values, {})


def gmsc(n=20000, seed=0):
    from sklearn.datasets import fetch_openml
    d = fetch_openml(data_id=46929, as_frame=True, data_home=RAW)
    X = d.data.astype(float)
    y = d.target.astype(str).isin(["Yes", "1"]).astype(int).values
    X = X.fillna(X.median())
    idx = np.random.RandomState(seed).choice(len(X), size=min(n, len(X)), replace=False)
    return Data("gmsc", X.values[idx], list(X.columns), y[idx], {})


def acs(state="CA", year=2018, n=30000, seed=0):
    from folktables import ACSDataSource, ACSIncome
    src = ACSDataSource(survey_year=str(year), horizon="1-Year", survey="person", root_dir=RAW + "/acs")
    df = src.get_data(states=[state], download=True)
    feats, lab, _ = ACSIncome.df_to_pandas(df)
    y = lab.values.ravel().astype(int)
    idx = np.random.RandomState(seed).choice(len(feats), size=min(n, len(feats)), replace=False)
    feats, y = feats.iloc[idx].reset_index(drop=True), y[idx]
    feats, levels = _cat_codes(feats, ["COW", "MAR", "RELP", "RAC1P"])
    return Data("acs", feats.values, list(feats.columns), y, levels)


def acs_emp(state="CA", year=2018, n=30000, seed=0):
    """ACSEmployment task (16 features) from the same CA-2018 person file: a higher-dimensional ACS task."""
    from folktables import ACSDataSource, ACSEmployment
    src = ACSDataSource(survey_year=str(year), horizon="1-Year", survey="person", root_dir=RAW + "/acs")
    df = src.get_data(states=[state], download=True)
    feats, lab, _ = ACSEmployment.df_to_pandas(df)
    y = lab.values.ravel().astype(int)
    idx = np.random.RandomState(seed).choice(len(feats), size=min(n, len(feats)), replace=False)
    feats, y = feats.iloc[idx].reset_index(drop=True), y[idx]
    cat = [c for c in feats.columns if c not in ("AGEP", "SCHL")]
    feats, levels = _cat_codes(feats, cat)
    return Data("acs_emp", feats.values, list(feats.columns), y, levels)


LOADERS = {"german": german, "pima": pima, "gmsc": gmsc, "acs": acs, "acs_emp": acs_emp}

if __name__ == "__main__":
    import sys
    for k in sys.argv[1:] or LOADERS:
        D = LOADERS[k]()
        print(k, D.A.shape, "pos rate %.3f" % D.y.mean(), "d", D.d, "encoded", D.encode(D.A[:2]).shape)
