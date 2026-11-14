"""N4: size of explainer noise relative to other variation a deployed explanation has.

Two-level nested design at the 1x kernel budget (l1_reg off, K background rows):
  factor=background: L background redraws (different training rows), S explainer seeds within each;
  factor=refit:      L model refits (different training seeds, same split/background), S explainer seeds within each.
Saves results/<ds>/n4/<model>_<factor>.npz with phi [N, L, S, d] (+ test AUC of every refit).
Usage: python code/run_n4.py --ds german --models xgb rf mlp --factor background --L 10 --S 3 --N 20
"""
import argparse, os, sys, json, time, warnings
import numpy as np
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

ap = argparse.ArgumentParser()
ap.add_argument("--ds", required=True)
ap.add_argument("--models", nargs="+", default=["lr", "xgb", "rf", "mlp"])
ap.add_argument("--factor", choices=["background", "refit"], required=True)
ap.add_argument("--L", type=int, default=10)
ap.add_argument("--S", type=int, default=3)
ap.add_argument("--N", type=int, default=20)
ap.add_argument("--K", type=int, default=50)
ap.add_argument("--out", default=os.path.join(common.ROOT, "results"))
a = ap.parse_args()
out = os.path.join(a.out, a.ds, "n4"); os.makedirs(out, exist_ok=True)
data = common.load_dataset(a.ds)
inst = json.load(open(os.path.join(a.out, a.ds, "instances.json")))
pos = np.array(inst["test_positions"])[: a.N]
for kind in a.models:
    fp = os.path.join(out, f"{kind}_{a.factor}.npz")
    if os.path.exists(fp): continue
    t0 = time.time()
    phi, aucs = None, []
    for l in range(a.L):
        T = common.Task(a.ds, kind, K=a.K, data=data, **(dict(bg_seed=l + 1) if a.factor == "background" else dict(model_seed=l + 1)))
        aucs.append(T.auc)
        X = T.Xte[pos]
        ns = 2 * T.d + 2048
        runs = np.stack([common.run_kernel(T.f, T.bg, X, ns, 20000 + 100 * l + s) for s in range(a.S)], 1)  # [N,S,d]
        if phi is None: phi = np.empty((len(pos), a.L, a.S, T.d))
        phi[:, l] = runs
        print(f"  [{a.ds}/{kind}/{a.factor}] level {l+1}/{a.L} {time.time()-t0:.0f}s", flush=True)
    np.savez(fp, phi=phi, auc=np.array(aucs), nsamples=ns)
    print(f"HUTIAN_WAKE: done n4 {a.ds}/{kind}/{a.factor}", flush=True)
