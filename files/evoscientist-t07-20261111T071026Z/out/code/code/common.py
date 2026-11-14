"""Data loading, model splits and metrics for benchmark-prediction experiments."""
import os
import numpy as np
import joblib
from scipy.stats import spearmanr, kendalltau

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCORES_DIR = os.path.join(ROOT, "data", "repo", "data", "scores")

OPENLLM = ["ifeval", "openllm_math", "mmlu_pro", "arc_challenge", "bbh", "gpqa", "musr"]
HELM = ["commonsense", "gsm", "legalbench", "math", "med_qa", "mmlu"]
ALL = OPENLLM + HELM


def load_scores(name):
    S = joblib.load(os.path.join(SCORES_DIR, f"{name}.jbl")).astype(np.float64)
    assert set(np.unique(S)) <= {0.0, 1.0}
    return S


def load_models(name):
    p = os.path.join(SCORES_DIR, f"{name}_models.jbl")
    return joblib.load(p) if os.path.exists(p) else None


def make_split(name, S, kind, seed):
    """Return (source_idx, target_idx).

    interp : random 25% of models are targets, rest sources (repo's 'interpolation').
    extrap : sources = lowest-accuracy 50% of models, targets = highest-accuracy 30%
             (repo's 'extrapolation'); deterministic, only the coreset varies with seed.
    org    : (Open LLM only) whole organisations (prefix before '/') are held out until
             >=25% of models are targets -> "unseen developer" shift.
    """
    m = S.shape[0]
    rng = np.random.default_rng(10_000 + seed)
    if kind == "interp":
        perm = rng.permutation(m)
        nt = int(0.25 * m)
        tgt = np.sort(perm[:nt]); src = np.sort(perm[nt:])
    elif kind == "extrap":
        order = np.argsort(S.mean(1), kind="stable")
        src = np.sort(order[: int(0.5 * m)]); tgt = np.sort(order[-int(0.3 * m):])
    elif kind == "org":
        models = load_models(name)
        assert models is not None and len(models) == m
        orgs = np.array([x.split("/")[0] for x in models])
        uorgs = rng.permutation(np.unique(orgs))
        tmask = np.zeros(m, bool)
        for o in uorgs:
            tmask |= orgs == o
            if tmask.sum() >= 0.25 * m:
                break
        tgt = np.where(tmask)[0]; src = np.where(~tmask)[0]
    else:
        raise ValueError(kind)
    return src, tgt


def metrics(pred, true):
    err = pred - true
    out = dict(mae=float(np.abs(err).mean()), rmse=float(np.sqrt((err ** 2).mean())),
               bias=float(err.mean()))
    if np.std(pred) < 1e-12 or len(pred) < 3:
        out["spearman"] = np.nan; out["kendall"] = np.nan
    else:
        out["spearman"] = float(spearmanr(pred, true)[0])
        out["kendall"] = float(kendalltau(pred, true)[0])
    return out
