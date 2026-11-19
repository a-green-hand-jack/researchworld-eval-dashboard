"""Stage 0: train base models, fix test instances and backgrounds, log accuracy/AUC."""
import os, sys, pickle, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from sklearn.metrics import roc_auc_score, accuracy_score
from common import *

rows = []
for ds in DATASETS:
    Xtr, Xte, ytr, yte, names, cat = split(ds)
    d = Xtr.shape[1]
    rng = np.random.RandomState(1)
    inst = rng.choice(len(Xte), N_INST, replace=False)
    bg_idx = rng.choice(len(Xtr), N_BG, replace=False)
    meta = dict(names=names, cat=cat, inst=inst, bg_idx=bg_idx, d=d)
    for m in MODELS:
        t = time.time()
        mod = make_model(m, cat, d, seed=0).fit(Xtr, ytr)
        p = mod.predict_proba(Xte)[:, 1]
        rows.append(dict(dataset=ds, model=m, n_train=len(Xtr), d=d, acc=accuracy_score(yte, p > .5),
                         auc=roc_auc_score(yte, p), base_rate=float(ytr.mean()), fit_s=time.time() - t))
        print(rows[-1], flush=True)
        pickle.dump(dict(model=mod, meta=meta), open(os.path.join(RES, f"model_{ds}_{m}.pkl"), "wb"))
import pandas as pd
pd.DataFrame(rows).to_csv(os.path.join(RES, "model_perf.csv"), index=False)
