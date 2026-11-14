"""Shared configuration, data loading and model construction.

All experiment scripts import from here so that the datasets, splits,
background samples, instances, models and seeds are identical everywhere.
"""
import os
import pickle

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from lightgbm import LGBMClassifier

ROOT = "/work"
RAW = f"{ROOT}/data/raw"
PROC = f"{ROOT}/data/processed"
MODEL_DIR = f"{ROOT}/models"
RES_DIR = f"{ROOT}/results"

DATASETS = ["german", "acs", "pima"]
MODELS = ["LR", "LGBM", "RF", "MLP"]
BUDGETS = [100, 250, 500, 1000, 2000, 4000]  # KernelSHAP nsamples (coalitions), German grid
# ACS (d=10) and Pima (d=8): shap caps nsamples at 2^d-2 and then enumerates exactly, so budgets
# above the cap return the exact value. We keep one saturated budget per dataset as a check.
BUDGETS_BY_DS = {"german": BUDGETS, "acs": [100, 250, 500, 1000, 2000], "pima": [100, 250, 500]}
N_INST = 150  # explained test instances per dataset
R_RUNS = 20  # independent explainer runs per (instance, budget)
K_BG = 100  # background size of the main experiment
N_BG_MAX = 400  # largest background used in the background-size ablation
N_REF_GERMAN = 30  # German (d=20, no exact truth): instances with approximate reference
REF_BUDGET = 10000  # German reference: high-budget KernelSHAP
REF_RUNS = 4  # German reference: number of high-budget runs
RETRAIN_SEEDS = [0, 1, 2, 3, 4]  # model seeds for the retraining comparison
SEED = 0  # data split / instance / background seed

for _d in [PROC, MODEL_DIR, RES_DIR]:
    os.makedirs(_d, exist_ok=True)


def load_processed(name):
    """Return dict with X (all rows), y, names, train_idx, test_idx."""
    z = np.load(f"{PROC}/{name}.npz", allow_pickle=True)
    return {k: z[k] for k in z.files}


def split(name):
    """Train/test arrays plus the fixed background and explained instances."""
    d = load_processed(name)
    Xtr, ytr = d["X"][d["train_idx"]], d["y"][d["train_idx"]]
    Xte, yte = d["X"][d["test_idx"]], d["y"][d["test_idx"]]
    rng = np.random.RandomState(SEED)
    # fixed random permutation of the training rows: the background of size K
    # is the first K rows, so smaller backgrounds are nested in larger ones
    bg_perm = rng.permutation(len(Xtr))[:N_BG_MAX]
    inst_idx = rng.choice(len(Xte), size=min(N_INST, len(Xte)), replace=False)
    return dict(
        Xtr=Xtr,
        ytr=ytr,
        Xte=Xte,
        yte=yte,
        background=Xtr[bg_perm],
        X_inst=Xte[inst_idx],
        y_inst=yte[inst_idx],
        names=list(d["names"]),
    )


def build_model(model_name, seed):
    """Untrained estimator with fixed hyper-parameters and random_state=seed."""
    if model_name == "LR":
        return make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))
    if model_name == "LGBM":
        return LGBMClassifier(
            n_estimators=200, learning_rate=0.05, num_leaves=15, min_child_samples=20,
            subsample=0.8, subsample_freq=1, colsample_bytree=0.8,
            random_state=seed, n_jobs=1, verbose=-1,
        )
    if model_name == "RF":
        return RandomForestClassifier(
            n_estimators=100, min_samples_leaf=5, max_features="sqrt",
            random_state=seed, n_jobs=1,
        )
    if model_name == "MLP":
        return make_pipeline(
            StandardScaler(),
            MLPClassifier(hidden_layer_sizes=(64, 32), alpha=1e-3, max_iter=300,
                          early_stopping=True, random_state=seed),
        )
    raise ValueError(model_name)


def get_model(ds_name, model_name, seed):
    """Train (or load cached) model.

    seed 0 is trained on the full training split. For seed s > 0 the training
    split is resampled with replacement (bootstrap, seeded by s) and the
    algorithm's own random_state is s, which gives a retrained model of the
    same class used to measure between-model variability.
    """
    path = f"{MODEL_DIR}/{ds_name}_{model_name}_s{seed}.pkl"
    if os.path.exists(path):
        with open(path, "rb") as fh:
            return pickle.load(fh)
    s = split(ds_name)
    X, y = s["Xtr"], s["ytr"]
    if seed > 0:
        idx = np.random.RandomState(1000 + seed).choice(len(X), size=len(X), replace=True)
        X, y = X[idx], y[idx]
    m = build_model(model_name, seed)
    m.fit(X, y)
    with open(path, "wb") as fh:
        pickle.dump(m, fh)
    return m


def output_fn(model, model_name, output="prob"):
    """Value function handed to the explainer.

    output="prob"   : P(y=1 | x)            (main experiments)
    output="margin" : log-odds / raw score  (ablation)
    """
    if output == "prob":
        return lambda Z: model.predict_proba(np.asarray(Z))[:, 1]
    if output == "margin":
        if model_name == "LR":
            return lambda Z: model.decision_function(np.asarray(Z))
        if model_name == "LGBM":
            return lambda Z: model.predict(np.asarray(Z), raw_score=True)
        raise ValueError("margin output only defined for LR and LGBM")
    raise ValueError(output)
