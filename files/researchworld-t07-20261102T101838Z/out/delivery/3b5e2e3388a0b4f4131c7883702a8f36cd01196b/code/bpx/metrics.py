import numpy as np
from scipy.stats import spearmanr, kendalltau


def metrics(true, pred):
    true, pred = np.asarray(true, float), np.asarray(pred, float)
    e = pred - true
    if np.ptp(pred) == 0 or np.ptp(true) == 0:
        sp = kt = 0.0
    else:
        sp = spearmanr(true, pred)[0]; kt = kendalltau(true, pred)[0]
    return dict(mae=np.abs(e).mean(), rmse=np.sqrt((e ** 2).mean()), bias=e.mean(), spearman=sp, kendall=kt)
