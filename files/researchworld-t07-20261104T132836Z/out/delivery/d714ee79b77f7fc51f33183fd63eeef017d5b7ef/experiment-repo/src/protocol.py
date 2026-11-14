"""Source/target model splits and metrics."""
import numpy as np
from scipy.stats import spearmanr, kendalltau


def dedup(X, models=None):
    """Drop exact duplicate model rows (identical response vectors), keeping the first."""
    _, first = np.unique(X.astype(np.uint8), axis=0, return_index=True)
    keep = np.sort(first)
    return X[keep], ([models[i] for i in keep] if models is not None else None)


def split(protocol, acc, rep, frac=0.2, names=None):
    """Return (source_idx, target_idx) over models.
    random : uniformly random `frac` of models are targets (new draw per rep)
    extrap : the top-`frac` models by full accuracy are targets (all stronger than every source model)
    """
    M = len(acc)
    nt = max(5, int(round(frac * M)))
    if protocol == "random":
        perm = np.random.default_rng(1000 + rep).permutation(M)
        return np.sort(perm[nt:]), np.sort(perm[:nt])
    if protocol == "family":  # whole organisations held out: random orgs are added to the target set until >= frac of models
        orgs = np.array([n.split("/")[0] for n in names])
        rng = np.random.default_rng(2000 + rep)
        tg = np.zeros(M, bool)
        for o in rng.permutation(np.unique(orgs)):
            if tg.sum() >= nt:
                break
            tg |= orgs == o
        return np.where(~tg)[0], np.where(tg)[0]
    if protocol.startswith("extrap"):
        order = np.argsort(acc)
        return np.sort(order[:M - nt]), np.sort(order[M - nt:])
    raise ValueError(protocol)


def metrics(true, pred):
    e = pred - true
    out = dict(mae=np.abs(e).mean(), rmse=np.sqrt((e ** 2).mean()), bias=e.mean())
    out["spearman"] = spearmanr(true, pred)[0] if np.std(pred) > 0 else 0.0
    out["kendall"] = kendalltau(true, pred)[0] if np.std(pred) > 0 else 0.0
    return out
