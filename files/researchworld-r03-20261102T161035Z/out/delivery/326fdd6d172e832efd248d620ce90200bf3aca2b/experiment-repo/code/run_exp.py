"""Repeated-split new-model protocol. usage: [DENS=.95] [NTRAIN=n] run_exp.py DATASET SPLIT REPS OUT.csv [R]
DATASET in mteb|olb|helm ; SPLIT in random|group|time ; selection and model fitting use training models only."""
import os, sys, time, numpy as np, pandas as pd
sys.path.insert(0, __file__.rsplit("/", 1)[0]); from bench import *
D = "/hutian/repo/data/"
ds, split, reps, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
fixed_r = int(sys.argv[5]) if len(sys.argv) > 5 else None
if ds == "mteb":
    X = dense_core(pd.read_csv(D + "mteb_matrix.csv", index_col=0), float(os.environ.get("DENS", 0.95))); KS = [1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48]; RANKS = (1, 2, 3, 4, 6, 8); MAXTEST = 10**9
    grp = X.index.str.split("__").str[0]
elif ds == "olb":
    X = pd.read_csv(D + "olb_matrix.csv", index_col=0); meta = pd.read_csv(D + "olb_meta.csv", index_col=0); KS = [1, 2, 3, 4, 5]; RANKS = (1, 2, 3); MAXTEST = 300
    grp = X.index.str.split("/").str[0]; date = pd.to_datetime(meta.loc[X.index, "Submission Date"], errors="coerce")
elif ds == "helm":
    X = pd.read_csv(D + "helm_lite_matrix.csv", index_col=0); KS = [1, 2, 3, 4, 5, 6, 8]; RANKS = (1, 2, 3); MAXTEST = 10**9
    grp = pd.Index(X.index.str.split(" ").str[0])
V = X.values; M, N = V.shape; print(ds, X.shape, "obs", np.isfinite(V).mean(), flush=True)
rows = []; t0 = time.time()
for rep in range(reps):
    rng = np.random.default_rng(1000 + rep)
    if split == "random":
        perm = rng.permutation(M); te = np.sort(perm[: M // 4])
    elif split == "group":                      # hold out whole organisations / families
        gs = pd.Series(grp).unique(); rng.shuffle(gs); te = []
        for g in gs:
            if len(te) >= M // 4: break
            te += list(np.where(np.asarray(grp) == g)[0])
        te = np.sort(te)
    elif split == "time":                       # train on earlier submissions, test on the latest quarter (reps differ in subsample only)
        te = np.where(date.values >= date.quantile(0.75))[0]
    tr = np.setdiff1d(np.arange(M), te)
    if split == "time" and ds == "olb": tr = rng.choice(tr, min(len(tr), 2000), replace=False)
    if os.environ.get("NTRAIN"): tr = rng.choice(tr, min(len(tr), int(os.environ["NTRAIN"])), replace=False)   # training-set-size ablation
    if len(te) > MAXTEST: te = rng.choice(te, MAXTEST, replace=False)
    Xtr = V[tr]
    r, pm = (fixed_r, 0.15) if fixed_r else fa_cv_rank(Xtr, ranks=RANKS, seed=rep)
    fa = FA(r, iters=60, seed=rep, psi_min=pm).fit(Xtr); ctx = make_ctx(Xtr, fa)
    orders = {n: f(Xtr, np.random.default_rng(rep), fa=fa, Ximp=fa.impute(Xtr), kmax=max(KS) + 20) for n, f in SELECTORS.items()}
    for n, o in orders.items():
        for i in te:
            obs = np.isfinite(V[i]); avail = [j for j in o if obs[j]]
            for k in KS:
                S = np.array(avail[:k])
                if len(S) < k: continue
                tgt = np.setdiff1d(np.where(obs)[0], S)
                if len(tgt) == 0: continue
                for m, f in INFERENCE.items():
                    e = f(ctx, V[i, S], S)[tgt] - V[i, tgt]
                    rows.append((rep, n, m, k, i, r, len(tgt), (e ** 2).sum(), ((e / ctx["colsd"][tgt]) ** 2).sum(), np.abs(e).sum()))
    print(f"rep {rep} r={r} psi_min={pm} train={len(tr)} test={len(te)} t={time.time()-t0:.0f}s", flush=True)
    pd.DataFrame(rows, columns="rep sel inf k model r n se2 sez2 ae".split()).to_csv(out, index=False)
print("done", flush=True)
