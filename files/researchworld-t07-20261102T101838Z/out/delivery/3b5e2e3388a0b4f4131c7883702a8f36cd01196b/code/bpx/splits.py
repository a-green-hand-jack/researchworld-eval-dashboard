"""Source/target model splits. Targets are held out entirely: their rows are never seen by selectors or fitted models."""
import numpy as np
from .data import org_of


def make_split(kind, S, names, rng, frac=0.25, fold=0, nfolds=4):
    M = S.shape[0]
    n_t = max(3, int(round(frac * M)))
    score = S.mean(1)
    if kind == "random":
        tgt = rng.permutation(M)[:n_t]
    elif kind == "extrap":   # targets = strongest models; sources are all weaker than every target
        tgt = np.argsort(-score, kind="stable")[:n_t]
    elif kind == "group":    # leave-organisation-out: whole organisations become targets
        orgs = np.array([org_of(n) for n in names])
        uo = rng.permutation(np.unique(orgs))
        tgt = []
        for o in uo:
            if len(tgt) >= n_t:
                break
            tgt += list(np.where(orgs == o)[0])
        tgt = np.array(tgt)
    elif kind == "family":   # deterministic leave-family-out folds (family = organisation prefix of the model name; label noise)
        orgs = np.array([org_of(n) for n in names])
        uo, cnt = np.unique(orgs, return_counts=True)
        fold_of, size = {}, np.zeros(nfolds)
        for o, c in sorted(zip(uo, cnt), key=lambda t: (-t[1], t[0])):
            f = int(np.argmin(size)); fold_of[o] = f; size[f] += c
        tgt = np.where(np.array([fold_of[o] for o in orgs]) == fold % nfolds)[0]
    else:
        raise ValueError(kind)
    src = np.setdiff1d(np.arange(M), tgt)
    return src, np.sort(tgt)
