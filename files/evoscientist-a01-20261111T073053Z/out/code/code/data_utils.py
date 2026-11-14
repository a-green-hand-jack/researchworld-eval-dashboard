"""Benchmark loaders -> dict(S, models, tasks, pool_top) ; all scores on a 0-100 scale."""
import os, json, glob
import numpy as np, pandas as pd
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
P = os.path.join(ROOT, 'data', 'processed')
OLLB6 = ['IFEval', 'BBH', 'MATH Lvl 5', 'GPQA', 'MUSR', 'MMLU-PRO']

def _dedupe(df):
    """drop models whose complete score vector is identical to an already-kept model (keeps the first)."""
    return df[~df.round(9).duplicated(keep='first')]

def load_helm():
    H = pd.read_csv(os.path.join(P, 'helm_mmlu.csv'), index_col=0)
    NE = pd.read_csv(os.path.join(P, 'helm_mmlu_neval.csv'), index_col=0).loc[H.index, H.columns]
    return dict(name='HELM-MMLU', S=H.values.astype(float), models=H.index.tolist(), tasks=H.columns.tolist(),
                neval=NE.values.astype(float), pool_top=None)

def load_ollb6():
    df = pd.read_csv(os.path.join(P, 'ollb_contents_full.csv'))
    df = df[df['Flagged'] == False].drop_duplicates('fullname').set_index('fullname')
    X = _dedupe(df[OLLB6])
    return dict(name='OLLB-6', S=X.values.astype(float), models=X.index.tolist(), tasks=OLLB6, neval=None, pool_top=100)

def load_bbh():
    f = os.path.join(P, 'ollb_bbh24.csv')
    X = pd.read_csv(f, index_col=0)
    X = _dedupe(X)
    return dict(name='OLLB-BBH24', S=X.values.astype(float), models=X.index.tolist(), tasks=X.columns.tolist(), neval=None, pool_top=100)

LOADERS = {'helm': load_helm, 'ollb6': load_ollb6, 'bbh24': load_bbh}

def pool_for_ordinal(B, rule_scores_mean):
    """Return indices of the model pool used for ordinal rules (top-N by arithmetic mean if pool_top set)."""
    M = len(B['models'])
    if B['pool_top'] is None or M <= B['pool_top']: return np.arange(M)
    return np.argsort(-rule_scores_mean, kind='stable')[:B['pool_top']]
