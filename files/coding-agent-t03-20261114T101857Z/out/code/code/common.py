import numpy as np, pandas as pd, openml, warnings
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
import xgboost as xgb
warnings.filterwarnings("ignore")
DATASETS = ["german", "pima", "gmsc", "acs", "acspc", "arr"]
MODELS = ["lr", "rf", "xgb", "mlp"]
TREE_ONLY = {"arr"}  # d=279: no trustworthy reference for lr/mlp, so only exact-TreeSHAP models
NSUB = 20000  # row cap for big datasets

def load(name):
    """Return X (float DataFrame, original features, categoricals ordinal-coded), y (0/1)."""
    if name in ("german", "pima", "gmsc", "arr"):
        did = {"german": 31, "pima": 37, "gmsc": 46929, "arr": 5}[name]
        ds = openml.datasets.get_dataset(did, download_data=True, download_qualities=False, download_features_meta_data=False)
        X, y, cat, names = ds.get_data(target=ds.default_target_attribute, dataset_format="dataframe")
        if name == "gmsc":
            X = X.copy()
        for c in X.columns:
            if str(X[c].dtype) in ("category", "object"):
                X[c] = X[c].astype("category").cat.codes
        X = X.astype(float)
        y = pd.Series(y).astype(str)
        y = (y == sorted(y.unique())[-1]).astype(int).values if name != "pima" else (y == "tested_positive").astype(int).values
        if name == "arr": y = (pd.Series(ds.get_data(target=ds.default_target_attribute, dataset_format="dataframe")[1]).astype(str) != "1").astype(int).values  # abnormal vs normal
        if name == "german": y = (pd.Series(ds.get_data(target=ds.default_target_attribute, dataset_format="dataframe")[1]).astype(str)=="bad").astype(int).values
    elif name in ("acs", "acspc"):
        from folktables import ACSDataSource, ACSIncome, ACSPublicCoverage
        ACSIncome = ACSIncome if name == "acs" else ACSPublicCoverage
        src = ACSDataSource(survey_year="2018", horizon="1-Year", survey="person", root_dir="/work/data/acs")
        df = src.get_data(states=["CA"], download=True)
        X, y, _ = ACSIncome.df_to_pandas(df)
        y = y.iloc[:, 0].astype(int).values
        X = X.astype(float)
    if len(X) > NSUB:
        idx = np.random.RandomState(0).choice(len(X), NSUB, replace=False)
        X, y = X.iloc[idx], y[idx]
    X = X.reset_index(drop=True)
    if X.isna().any().any():
        X = X.fillna(X.median())
    return X, y

def split(name, seed=0):
    X, y = load(name)
    return train_test_split(X, y, test_size=0.3, random_state=seed, stratify=y)

def make_model(kind, seed):
    if kind == "lr": return make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))
    if kind == "rf": return RandomForestClassifier(100, min_samples_leaf=3, n_jobs=1, random_state=seed)
    if kind == "xgb": return xgb.XGBClassifier(n_estimators=150, max_depth=4, learning_rate=0.1, n_jobs=1, random_state=seed)
    if kind == "mlp": return make_pipeline(StandardScaler(), MLPClassifier((64, 64), max_iter=500, early_stopping=True, random_state=seed))
