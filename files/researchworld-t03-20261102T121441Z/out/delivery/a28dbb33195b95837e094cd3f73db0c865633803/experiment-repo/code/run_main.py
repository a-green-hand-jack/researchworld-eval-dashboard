"""Main experiment (PLAN v3): repeated runs of Kernel / permutation SHAP at several budgets, plus exact targets.

For one dataset: trains LR / XGBoost / RF / MLP (fixed split and seeds), picks 50 shared instances (25 random,
25 near the decision boundary, interleaved), computes exact targets, then runs the explainer cells R times each
(explainer seeds 10000+r) on the same model, background (K rows) and instances. All outputs go to results/<ds>/:
  models.json, instances.json, targets/<kind>.npz, raw/<kind>/<cell>_r<rr>.npz  (phi [N,d], seconds)
Cells: name -> (explainer, multiple of the library default nsamples=2d+2048, l1_reg, number of instances)
Resumable: finished files are skipped. Budget in model evaluations = nsamples * K.
Usage: python code/run_main.py --ds german [--models lr xgb rf mlp] [--tiers 1 2 3] [--N 50 --R 20 --K 50]
"""
import argparse, os, sys, time, json, warnings
import numpy as np
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

ap = argparse.ArgumentParser()
ap.add_argument("--ds", required=True)
ap.add_argument("--models", nargs="+", default=common.KINDS)
ap.add_argument("--tiers", nargs="+", type=int, default=[1])
ap.add_argument("--N", type=int, default=50)
ap.add_argument("--R", type=int, default=20)
ap.add_argument("--K", type=int, default=50)
ap.add_argument("--enum_n", type=int, default=0, help="instances for full-enumeration targets (0: only if d<=16)")
ap.add_argument("--skip_cells", nargs="*", default=[], help="cells to leave out (cut order, PLAN §0a.6)")
ap.add_argument("--out", default=os.path.join(common.ROOT, "results"))
a = ap.parse_args()
out = os.path.join(a.out, a.ds)
for sub in ("raw", "targets"):
    os.makedirs(os.path.join(out, sub), exist_ok=True)

# cell -> (explainer, multiple of default nsamples, l1_reg, n_instances, tier)
CELLS = {
    "kernel_q": ("kernel", 0.25, False, a.N, 1),
    "kernel_1": ("kernel", 1, False, a.N, 1),
    "kernel_4": ("kernel", 4, False, a.N, 1),
    "kernel_1_l1default": ("kernel", 1, "num_features(10)", a.N, 1),
    "perm_1": ("perm", 1, None, a.N, 2),
    "perm_4": ("perm", 4, None, a.N, 2),
    "kernel_16": ("kernel", 16, False, 20, 3),
}

data = common.load_dataset(a.ds)
tasks = {k: common.Task(a.ds, k, K=a.K, data=data) for k in common.KINDS}
d = tasks["lr"].d
default_ns = 2 * d + 2048
idx, stratum = common.select_instances(tasks)  # 25 random then 25 near-boundary
rnd, near = np.where(stratum == "random")[0], np.where(stratum == "near_boundary")[0]
order = np.ravel(np.column_stack([rnd, near]))  # interleave so that any prefix is balanced
idx, stratum = idx[order][: a.N], stratum[order][: a.N]
json.dump(dict(test_positions=idx.tolist(), stratum=stratum.tolist()), open(os.path.join(out, "instances.json"), "w"))
models_meta = {}
for k, T in tasks.items():
    models_meta[k] = dict(value_function=common.VALUE_FN[k], test_auc=T.auc, test_acc=T.acc, n_train=len(T.Xtr),
                          n_test=len(T.Xte), d=d, K=a.K, default_nsamples=default_ns, params=str(T.model.get_params())
                          if k not in ("lr", "mlp") else str(T.model.named_steps["m"].get_params()))
json.dump(models_meta, open(os.path.join(out, "models.json"), "w"), indent=1)
print(f"[{a.ds}] d={d} N={len(idx)} default nsamples={default_ns}", flush=True)

for kind in a.models:
    T = tasks[kind]
    X = T.Xte[idx]
    # ---- exact targets
    tp = os.path.join(out, "targets", f"{kind}.npz")
    if not os.path.exists(tp):
        t0 = time.time()
        st = common.target_exact(T, X)
        res = dict(fx=T.f(X), base=T.f(T.bg).mean())
        if st is not None: res["phi_struct"] = st
        ne = len(X) if d <= 16 else a.enum_n
        if kind == "mlp" or ne:  # enumeration: always for the MLP when requested; all models for d<=16
            if ne:
                res["phi_enum"] = np.array([common.exact_enum(T.f, T.bg, x)[0] for x in X[:ne]])
        np.savez(tp, **res)
        print(f"  [{kind}] targets in {time.time()-t0:.0f}s", flush=True)
    # ---- explainer cells
    for cell, (ex, mult, l1, n_i, tier) in CELLS.items():
        if tier not in a.tiers or cell in a.skip_cells: continue
        ns = int(round(default_ns * mult))
        if ex == "perm": ns = int(round(default_ns * mult))
        t0 = time.time()
        for r in range(a.R):
            fp = os.path.join(out, "raw", kind, f"{cell}_r{r:02d}.npz")
            if os.path.exists(fp): continue
            os.makedirs(os.path.dirname(fp), exist_ok=True)
            t = time.time()
            if ex == "kernel": phi = common.run_kernel(T.f, T.bg, X[:n_i], ns, 10000 + r, l1_reg=l1)
            else: phi = common.run_perm(T.f, T.bg, X[:n_i], ns, 10000 + r)
            np.savez(fp, phi=phi, seconds=time.time() - t, nsamples=ns, evals=ns * a.K)
        print(f"  [{kind}] {cell} nsamples={ns} done in {time.time()-t0:.0f}s", flush=True)
    print(f"HUTIAN_WAKE: done {a.ds}/{kind} tiers {a.tiers}", flush=True)
