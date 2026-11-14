"""Pilot: train models, check accuracy, validate exact code vs shap enumeration, time KernelSHAP."""
import time

import numpy as np
import shap
from sklearn.metrics import roc_auc_score

from common import DATASETS, MODELS, get_model, split, output_fn
from exact import exact_shapley

for ds in DATASETS:
    s = split(ds)
    for mn in MODELS:
        m = get_model(ds, mn, 0)
        auc = roc_auc_score(s["yte"], m.predict_proba(s["Xte"])[:, 1])
        print(f"{ds:7s} {mn:5s} test AUC={auc:.3f}", flush=True)

# validation on pima (d=8): exact enumeration vs shap enumeration (nsamples=2^d)
s = split("pima")
bg = s["background"][:100]
for mn in ["LGBM", "MLP"]:
    m = get_model("pima", mn, 0)
    f = output_fn(m, mn, "prob")
    phi_ex, gap = exact_shapley(f, s["X_inst"][:5], bg)
    ke = shap.KernelExplainer(f, bg)
    for seed in [1, 2]:
        np.random.seed(seed)
        sv = ke.shap_values(s["X_inst"][:5], nsamples=2 ** 8, l1_reg=False, silent=True)
        print(f"pima {mn} shap-enum vs exact max|diff|={np.abs(sv - phi_ex).max():.2e} (additivity gap {gap:.1e})")

# timing: KernelSHAP single-instance call, German (d=20) and ACS (d=10)
for ds, mn in [("german", "LGBM"), ("german", "RF"), ("acs", "LGBM"), ("acs", "RF")]:
    s = split(ds)
    m = get_model(ds, mn, 0)
    f = output_fn(m, mn, "prob")
    ke = shap.KernelExplainer(f, s["background"][:100])
    for b in [100, 1000, 4000]:
        np.random.seed(0)
        t0 = time.time()
        for i in range(5):
            ke.shap_values(s["X_inst"][i:i + 1], nsamples=b, l1_reg=False, silent=True)
        print(f"time {ds} {mn} nsamples={b}: {(time.time() - t0) / 5:.3f}s per instance", flush=True)
