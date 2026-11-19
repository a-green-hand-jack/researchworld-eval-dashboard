"""Sanity checks of the references used in E1/E3 (written to results/validation.json).
 V1: exact KernelSHAP (full enumeration) vs exact interventional TreeSHAP on the RF (small-d datasets).
 V2: German (d=20): KernelSHAP at B=REF_B vs TreeSHAP on RF (reference error of the high-budget reference).
 V3: German (d=20), non-tree models: two independent B=REF_B KernelSHAP runs (self-consistency of the reference)."""
import os, sys, json
os.environ["OMP_NUM_THREADS"] = "1"
import numpy as np, joblib
from joblib import Parallel, delayed
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C, explain


def rel(a, b):
    return float(np.linalg.norm(a - b) / np.linalg.norm(b))


def v1(dn, i):
    Dd = joblib.load(f"{C.ART}/{dn}_data.joblib"); m = joblib.load(f"{C.ART}/{dn}_rf.joblib")
    x, bg = Dd["Xte"][i], Dd["bg"]
    return rel(explain.exact_kernel(m.predict, x, bg), explain.tree_phi(m, x, bg))


def v2(i):
    Dd = joblib.load(f"{C.ART}/german_data.joblib"); m = joblib.load(f"{C.ART}/german_rf.joblib")
    x, bg = Dd["Xte"][i], Dd["bg"]
    return rel(explain.kernel_phi(m.predict, x, bg, C.REF_B, 12345), explain.tree_phi(m, x, bg))


def v3(k, i):
    Dd = joblib.load(f"{C.ART}/german_data.joblib"); m = joblib.load(f"{C.ART}/german_{k}.joblib")
    x, bg = Dd["Xte"][i], Dd["bg"]
    return rel(explain.kernel_phi(m.predict, x, bg, C.REF_B, 12345), explain.kernel_phi(m.predict, x, bg, C.REF_B, 777))


if __name__ == "__main__":
    out = {}; n = 20
    for dn in ["pima", "gmsc", "acs"]:
        out[f"V1_{dn}_rf_exactKernel_vs_TreeSHAP_relL2"] = Parallel(n_jobs=20)(delayed(v1)(dn, i) for i in range(n))
    out["V2_german_rf_kernelB_vs_TreeSHAP_relL2"] = Parallel(n_jobs=20)(delayed(v2)(i) for i in range(n))
    for k in ["lr", "xgb", "mlp"]:
        out[f"V3_german_{k}_kernelB_twoSeeds_relL2"] = Parallel(n_jobs=20)(delayed(v3)(k, i) for i in range(n))
    summ = {k: dict(mean=float(np.mean(v)), max=float(np.max(v))) for k, v in out.items()}
    json.dump(dict(raw=out, summary=summ), open(f"{C.RES}/validation.json", "w"), indent=1)
    print(json.dumps(summ, indent=1))
