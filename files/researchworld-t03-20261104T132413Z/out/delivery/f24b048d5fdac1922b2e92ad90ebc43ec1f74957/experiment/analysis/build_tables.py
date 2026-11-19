"""Stage 1: per-instance metric table from the raw explainer runs.

usage: python3 analysis/build_tables.py [raw_dir] [out_dir]
Writes <out>/per_instance.csv (one row per cell x explainer x budget x instance), <out>/cells.csv (model quality,
reference quality) and <out>/standards_instance.csv (model-/background-induced variation, null floors, per instance).
"""
import glob, json, os, sys, itertools
import numpy as np, pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import metrics as M

raw = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "results", "raw")
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), "..", "results", "tables")
os.makedirs(out, exist_ok=True)
cells = sorted({os.path.basename(p).rsplit("__", 1)[0] for p in glob.glob(f"{raw}/*__ref.npz")})
per, cellrows, stdrows = [], [], []
for cell in cells:
    ds, model = cell.split("__")
    ref = np.load(f"{raw}/{cell}__ref.npz")
    meta = json.loads(str(ref["meta"]))
    R0, se0, p = ref["ref"], ref["ref_se"], ref["p"]
    N, d = R0.shape
    exact = bool((se0 == 0).all())
    cellrows.append(dict(dataset=ds, model=model, d=d, n_inst=N, test_auc=meta["test_auc"], test_acc=meta["test_acc"],
                         B=meta["B"], R=meta["R"], reference="exact" if exact else "kernel20000x10",
                         ref_rel_se=float(np.mean(np.linalg.norm(se0, axis=1) / np.linalg.norm(R0, axis=1)))))
    for ex in ("kernel", "perm"):
        f = f"{raw}/{cell}__{ex}.npz"
        if not os.path.exists(f):
            continue
        z = np.load(f)
        phi, rows, bud = z["phi"], z["rows"], z["budgets"]
        for b in range(phi.shape[1]):
            for i in range(N):
                r = dict(dataset=ds, model=model, d=d, explainer=ex, budget_idx=b, budget=int(bud[b]),
                         rows=float(rows[i, b].mean()), frac_space=(int(bud[b]) / (2 ** d - 2) if ex == "kernel" else np.nan), inst=i, p=float(p[i]), ref_exact=exact)
                r.update(M.instance_metrics(phi[i, b], R0[i]))
                per.append(r)
    # ---- comparison standards (per instance) ----
    ks = [k for k in M.KS if k < d]
    rng = np.random.RandomState(0)
    retr = f"{raw}/{cell}__retrain.npz"
    bgf = f"{raw}/{cell}__bg.npz"
    if not os.path.exists(bgf):
        bgf = f"{raw}/{cell}__bgd.npz"      # reduced background standard of the d > 12 cells (3 redraws, 30 instances)
    sources = {}
    if os.path.exists(retr):
        sources["retrain"] = np.load(retr)["phi"]            # (K, N, d)
    if os.path.exists(bgf):
        zb = np.load(bgf)
        for kk in zb.files:
            if kk.startswith("phi_B"):
                sources["bg_" + kk[4:]] = zb[kk]                # (G, Ni, d)
    for name, arr in sources.items():
        K, Ni, _ = arr.shape
        for i in range(Ni):
            for k in ks:
                S = M.topk_ind(arr[:, i], k)
                pm, pj = M.pairwise_set_match(S, k)
                nr = np.linalg.norm(arr[:, i], axis=1)
                iu = np.triu_indices(K, 1)
                dist = np.linalg.norm(arr[:, i][iu[0]] - arr[:, i][iu[1]], axis=1) / np.sqrt(0.5 * (nr[iu[0]] ** 2 + nr[iu[1]] ** 2))
                stdrows.append(dict(dataset=ds, model=model, d=d, standard=name, inst=i, k=k, pair_match=pm, pair_jac=pj,
                                    nogueira=M.nogueira(S, k), pair_reldist=float(dist.mean())))
    for k in ks:  # null: references of two different random instances
        for i in range(N):
            S = M.topk_ind(R0, k)
            js = [(j, (S[i] & S[j]).sum()) for j in rng.choice([x for x in range(N) if x != i], min(20, N - 1), replace=False)]
            o = np.array([c for _, c in js])
            stdrows.append(dict(dataset=ds, model=model, d=d, standard="null_other_instance", inst=i, k=k,
                                pair_match=float((o == k).mean()), pair_jac=float((o / (2 * k - o)).mean()),
                                nogueira=np.nan, pair_reldist=float(np.mean([np.linalg.norm(R0[i] - R0[j]) / np.sqrt(0.5 * (np.linalg.norm(R0[i]) ** 2 + np.linalg.norm(R0[j]) ** 2)) for j, _ in js]))))
        ej, em = M.random_jaccard(d, k)
        stdrows.append(dict(dataset=ds, model=model, d=d, standard="null_random_subsets", inst=-1, k=k, pair_match=em, pair_jac=ej,
                            nogueira=0.0, pair_reldist=np.nan))
pd.DataFrame(per).to_csv(f"{out}/per_instance.csv", index=False)
pd.DataFrame(cellrows).to_csv(f"{out}/cells.csv", index=False)
pd.DataFrame(stdrows).to_csv(f"{out}/standards_instance.csv", index=False)
print("cells:", cells, "rows:", len(per), len(stdrows))
