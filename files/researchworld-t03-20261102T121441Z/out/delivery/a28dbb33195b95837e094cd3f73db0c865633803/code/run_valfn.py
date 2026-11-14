"""Value-function sensitivity (PLAN v3 §0a, story-repo#2): the same models/instances/background as the main study, but
explaining the *other* value function: probability for LR/XGB/MLP (main study: log-odds). Kernel SHAP at 1x (l1_reg off),
R runs, exact target by full enumeration of all 2^d coalitions (d=16, ACSEmployment). Written as a pseudo-dataset
results/<ds>_probfn/ so that code/analyze.py treats it like any other dataset (cell kernel_1 only).
Usage: python code/run_valfn.py --ds acs_employment --models lr xgb mlp
"""
import argparse, os, sys, time, json, shutil, warnings
import numpy as np
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

ap = argparse.ArgumentParser()
ap.add_argument("--ds", required=True)
ap.add_argument("--models", nargs="+", default=["lr", "xgb", "mlp"])
ap.add_argument("--N", type=int, default=50); ap.add_argument("--R", type=int, default=20); ap.add_argument("--K", type=int, default=50)
a = ap.parse_args()
src = os.path.join(common.ROOT, "results", a.ds)
out = os.path.join(common.ROOT, "results", a.ds + "_probfn")
os.makedirs(os.path.join(out, "targets"), exist_ok=True)
inst = json.load(open(os.path.join(src, "instances.json")))
pos = np.array(inst["test_positions"])[: a.N]
json.dump(dict(test_positions=pos.tolist(), stratum=inst["stratum"][: a.N]), open(os.path.join(out, "instances.json"), "w"))
data = common.load_dataset(a.ds)
meta = {}
for kind in a.models:
    T = common.Task(a.ds, kind, K=a.K, data=data)
    f_logit = T.f
    f = lambda z, f_logit=f_logit: 1 / (1 + np.exp(-f_logit(z)))   # probability value function
    X = T.Xte[pos]; d = T.d; ns = 2 * d + 2048
    meta[kind] = dict(value_function="probability", test_auc=T.auc, test_acc=T.acc, n_train=len(T.Xtr), n_test=len(T.Xte), d=d, K=a.K,
                      default_nsamples=ns, params="same model as the main study (results/%s/models.json)" % a.ds)
    mp = os.path.join(out, "models.json")  # merge: model jobs may run in parallel
    old = json.load(open(mp)) if os.path.exists(mp) else {}
    json.dump({**old, **meta}, open(mp, "w"), indent=1)
    tp = os.path.join(out, "targets", f"{kind}.npz")
    if not os.path.exists(tp):
        t0 = time.time()
        phi_e = np.array([common.exact_enum(f, T.bg, x)[0] for x in X])
        np.savez(tp, fx=f(X), base=f(T.bg).mean(), phi_enum=phi_e)
        print(f"  [{kind}] enumeration targets {time.time()-t0:.0f}s", flush=True)
    t0 = time.time()
    for r in range(a.R):
        fp = os.path.join(out, "raw", kind, f"kernel_1_r{r:02d}.npz")
        if os.path.exists(fp): continue
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        t = time.time()
        phi = common.run_kernel(f, T.bg, X, ns, 10000 + r, l1_reg=False)
        np.savez(fp, phi=phi, seconds=time.time() - t, nsamples=ns, evals=ns * a.K)
    print(f"  [{kind}] kernel_1 probability value function nsamples={ns} done in {time.time()-t0:.0f}s", flush=True)
    print(f"HUTIAN_WAKE: done valfn {a.ds}/{kind}", flush=True)
