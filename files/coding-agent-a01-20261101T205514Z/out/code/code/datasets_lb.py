"""Loaders for the leaderboard score matrices used in the paper. Each returns (S, models, tasks, n_items)."""
import json, os
import numpy as np, pandas as pd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OLLB_COLS = ['IFEval', 'BBH', 'MATH Lvl 5', 'GPQA', 'MUSR', 'MMLU-PRO']
# test-set sizes of the six Open LLM Leaderboard v2 tasks (sums of the per-subtask n-samples of the results repo)
OLLB_N = {'IFEval': 541, 'BBH': 5761, 'MATH Lvl 5': 1324, 'GPQA': 1192, 'MUSR': 756, 'MMLU-PRO': 12032}


def load_helm():
    df = pd.read_csv(os.path.join(ROOT, 'data/processed/helm_mmlu_v1.13.0.csv'), index_col=0)
    n = json.load(open(os.path.join(ROOT, 'data/processed/helm_n_instances.json')))
    n_items = np.array([max(n[c]) for c in df.columns])
    return df.values.astype(float), list(df.index), list(df.columns), n_items


def load_ollb6(drop_flagged=True):
    d = pd.read_parquet(os.path.join(ROOT, 'data/olmb/contents.parquet'))
    if drop_flagged:
        d = d[~d['Flagged']]
    d = d.reset_index(drop=True)
    S = d[OLLB_COLS].values.astype(float) / 100.0   # normalised score in [0,1] (official normalisation)
    models = (d['fullname'] + '|' + d['Precision']).tolist()
    return S, models, OLLB_COLS, np.array([OLLB_N[c] for c in OLLB_COLS]), d


def load_ollb_fine():
    df = pd.read_csv(os.path.join(ROOT, 'data/processed/ollb_fine.csv'), index_col=0)
    n = json.load(open(os.path.join(ROOT, 'data/processed/ollb_fine_n.json')))
    n_items = np.array([n[c] for c in df.columns])
    return df.values.astype(float), list(df.index), list(df.columns), n_items


def load(name):
    return {'helm': load_helm, 'ollb6': load_ollb6, 'ollbfine': load_ollb_fine}[name]()[:4]
