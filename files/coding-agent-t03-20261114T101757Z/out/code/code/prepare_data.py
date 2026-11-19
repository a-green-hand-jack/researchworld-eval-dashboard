"""Build processed datasets (German Credit, ACS income subsample, Pima).

Output: /work/data/processed/{german,acs,pima}.npz with keys
X, y, names, train_idx, test_idx.  Positive class y=1 is the "risk / target"
class: bad credit (German), income > 50k (ACS), tested positive (Pima).
"""
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from common import RAW, PROC, SEED


def save(name, X, y, names):
    tr, te = train_test_split(np.arange(len(y)), test_size=0.3, stratify=y, random_state=SEED)
    np.savez(f"{PROC}/{name}.npz", X=X.astype(np.float64), y=y.astype(int),
             names=np.array(names), train_idx=tr, test_idx=te)
    print(f"{name}: n={len(y)} d={X.shape[1]} pos_rate={y.mean():.3f} "
          f"train={len(tr)} test={len(te)}")


def load_german():
    cols = ["checking", "duration", "credit_history", "purpose", "amount", "savings",
            "employment", "installment_rate", "personal_status", "other_debtors",
            "residence_since", "property", "age", "other_installment", "housing",
            "n_existing_credits", "job", "n_liable", "telephone", "foreign_worker", "target"]
    df = pd.read_csv(f"{RAW}/german/german.data", sep=r"\s+", header=None, names=cols)
    y = (df.pop("target") == 2).astype(int).values  # 2 = bad credit risk
    for c in df.columns:
        if not pd.api.types.is_numeric_dtype(df[c]):  # categorical attribute -> integer code
            df[c] = pd.Categorical(df[c]).codes
    return df.values.astype(float), y, list(df.columns)


def load_acs():
    from folktables import ACSDataSource, ACSIncome
    ds = ACSDataSource(survey_year="2018", horizon="1-Year", survey="person",
                       root_dir=f"{RAW}/acs")
    data = ds.get_data(states=["CA"], download=False)
    X, y, _ = ACSIncome.df_to_pandas(data)
    y = np.ravel(y.values).astype(int)
    rng = np.random.RandomState(SEED)
    idx = rng.choice(len(X), size=50000, replace=False)  # subsample for tractable runs
    return X.values[idx].astype(float), y[idx], list(X.columns)


def load_pima():
    X = pd.read_csv(f"{RAW}/pima/X.csv")
    y = (pd.read_csv(f"{RAW}/pima/y.csv").iloc[:, 0] == "tested_positive").astype(int).values
    return X.values.astype(float), y, list(X.columns)


if __name__ == "__main__":
    save("german", *load_german())
    save("acs", *load_acs())
    save("pima", *load_pima())
