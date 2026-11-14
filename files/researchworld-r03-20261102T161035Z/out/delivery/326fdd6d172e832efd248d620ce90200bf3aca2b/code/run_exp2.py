"""Common-target-set protocol (supersedes run_exp.py for selector comparisons) + full-information reference.
usage: [DENS=.95] [MASK=p] [NTRAIN=n] [REP0=0] [PEN=1] [DEDUP=1] [ONLY=sel1,sel2] [PRED=1] run_exp2.py DATASET SPLIT REPS OUT.csv
SPLIT: random | group (organisation) | time; for mteb also family (model_meta adapted_from / name key) and time (release_date, newest 25% = test).
DEDUP=1 (mteb): of tasks with the same name up to a '.vN' suffix (STS22/STS22.v2, ...) keep the one with more observations.
ONLY=a,b: run only these selectors ('full' = the full-information reference; names of SELECTORS, SELECTORS_PEN, SELECTORS_EXTRA = backelim, plus random_pm = an independent random order per test model);
  split/targets/FA are identical to a full run with the same REP0 (same seeds), so results pair with it.
PRED=1: also write OUT.pred.csv.gz with true and predicted z-score per test cell (selectors random, random_pm, greedy_ridge, full; ridge and mean inference).
Per split/repeat a target set T of benchmarks is fixed for ALL selectors: MTEB (dense core or 'mtebsparse'): random 25% of columns per repeat;
OLB/HELM: leave-one-benchmark-out over every benchmark (T = {j}).  Selectors may only pick from candidates = columns not in T
(their objectives still see all training columns); every method is scored on the observed cells of T only.  k=9999 = full-information
reference (all observed candidates of the model).  Learning (FA, imputation, ridge, kNN, ordering) uses training models only."""
import os, sys, time, numpy as np, pandas as pd
sys.path.insert(0, __file__.rsplit("/", 1)[0]); from bench import *
D = "/hutian/repo/data/"
ds, split, reps, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
REP0 = int(os.environ.get("REP0", 0)); ONLY = os.environ.get("ONLY"); PRED = bool(int(os.environ.get("PRED", 0))); PENSEL = bool(int(os.environ.get("PEN", 0)))
FULL = 9999
if ds == "mteb":
    X = dense_core(pd.read_csv(D + "mteb_matrix.csv", index_col=0), float(os.environ.get("DENS", 0.95)))
    KS = [1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64, 96, 128, FULL]; RANKS = (2, 4, 8, 12, 16, 24); PSIS = (0.15, 0.3, 0.5, 0.8); MAXTEST = 10**9; LOBO = False
    grp = X.index.str.split("__").str[0]
    meta = pd.read_csv(D + "mteb_meta.csv", index_col=0).loc[X.index]; fam = meta.family.values; date = pd.to_datetime(meta.release_date, errors="coerce")
    if int(os.environ.get("DEDUP", 0)):
        import re; base = pd.Series([re.sub(r"\.v\d+$", "", c) for c in X.columns], index=X.columns); keep = []
        for b, cs in base.groupby(base): keep.append(max(cs.index, key=lambda c: X[c].notna().sum()))
        X = X[[c for c in X.columns if c in set(keep)]]
elif ds == "mtebsparse":      # realistic missingness: tasks with >=60 models, models with >=30 of those tasks
    A = pd.read_csv(D + "mteb_matrix.csv", index_col=0); A = A.loc[:, A.notna().sum() >= 60]; X = A.loc[A.notna().sum(1) >= 30]
    KS = [1, 2, 3, 4, 6, 8, 12, 16, 24, 32, FULL]; RANKS = (2, 4, 8, 12); PSIS = (0.15, 0.3, 0.5, 0.8); MAXTEST = 10**9; LOBO = False
    grp = X.index.str.split("__").str[0]
elif ds == "olb":
    X = pd.read_csv(D + "olb_matrix.csv", index_col=0); meta = pd.read_csv(D + "olb_meta.csv", index_col=0); KS = [1, 2, 3, 4, FULL]; RANKS = (1, 2, 3); PSIS = (0.05, 0.15, 0.3); MAXTEST = 150; LOBO = True
    grp = X.index.str.split("/").str[0]; date = pd.to_datetime(meta.loc[X.index, "Submission Date"], errors="coerce")
elif ds == "helm":
    X = pd.read_csv(D + "helm_lite_matrix.csv", index_col=0); KS = [1, 2, 3, 4, 5, 6, 7, 8, FULL]; RANKS = (1, 2, 3); PSIS = (0.05, 0.15, 0.3); MAXTEST = 10**9; LOBO = True
    grp = pd.Index(X.index.str.split(" ").str[0])
Vraw = X.values.copy(); M, N = Vraw.shape
mask_p = float(os.environ.get("MASK", 0))
if mask_p: Vraw[np.random.default_rng(7).random(Vraw.shape) < mask_p] = np.nan      # controlled extra MCAR missingness, fixed benchmark and model set
print(ds, split, X.shape, "obs", np.isfinite(Vraw).mean(), flush=True)
sels = dict(SELECTORS); sels.update(SELECTORS_PEN if PENSEL else {}); sels.update(SELECTORS_EXTRA)
if ONLY: sels = {n: sels.get(n, sel_random) for n in ONLY.split(",") if n != "full"}      # random_pm: placeholder order, replaced per test model below
PREDSEL = {"random", "random_pm", "greedy_ridge", "full"}; PRED_ROWS = []
rows = []; t0 = time.time()
for rep in range(REP0, REP0 + reps):
    rng = np.random.default_rng(1000 + rep)
    if split == "random": te = np.sort(rng.permutation(M)[: M // 4])
    elif split == "group":
        gs = pd.Series(grp).unique(); rng.shuffle(gs); te = []
        for g in gs:
            if len(te) >= M // 4: break
            te += list(np.where(np.asarray(grp) == g)[0])
        te = np.sort(te)
    elif split == "family":
        gs = pd.Series(fam).unique(); rng.shuffle(gs); te = []
        for g in gs:
            if len(te) >= M // 4: break
            te += list(np.where(fam == g)[0])
        te = np.sort(te)
    elif split == "time": te = np.where(date.values >= date.quantile(0.75))[0]
    tr = np.setdiff1d(np.arange(M), te)
    if split == "time" and ds == "olb": tr = rng.choice(tr, min(len(tr), 2000), replace=False)
    if os.environ.get("NTRAIN"): tr = rng.choice(tr, min(len(tr), int(os.environ["NTRAIN"])), replace=False)
    if len(te) > MAXTEST: te = rng.choice(te, MAXTEST, replace=False)
    good = np.where(np.isfinite(Vraw[tr]).sum(0) >= 8)[0]      # benchmarks with <8 training observations are dropped for this split
    V = Vraw[:, good]; Nn = len(good); Xtr = V[tr]
    r, pm = fa_cv_rank(Xtr, ranks=RANKS, psis=PSIS, seed=rep)
    fa = FA(r, iters=60, seed=rep, psi_min=pm).fit(Xtr); ctx = make_ctx(Xtr, fa); Ximp = fa.impute(Xtr)
    tsets = [np.array([j]) for j in range(Nn)] if LOBO else [np.sort(rng.choice(Nn, max(1, Nn // 4), replace=False))]
    for T in tsets:
        cand = [j for j in range(Nn) if j not in set(T)]
        orders = {n: f(Xtr, np.random.default_rng(rep), fa=fa, Ximp=Ximp, kmax=max(k for k in KS if k != FULL) + 20, cand=cand) for n, f in sels.items()}
        cs = set(cand)
        orders = {n: [j for j in o if j in cs] for n, o in orders.items()}
        if not ONLY or "full" in ONLY.split(","): orders["full"] = [j for j in range(Nn) if j in cs]
        for n, o in orders.items():
            for i in te:
                if n == "random_pm": o = list(np.random.default_rng([rep, int(i), int(T[0])]).permutation(cand))
                obs = np.isfinite(V[i]); avail = [j for j in o if obs[j]]; tgt = np.array([j for j in T if obs[j]])
                if len(tgt) == 0: continue
                for k in KS:
                    if (n == "full") != (k == FULL): continue
                    S = np.array(avail if k == FULL else avail[:k])
                    if len(S) < (1 if k == FULL else k): continue
                    for m, f in INFERENCE.items():
                        if k == FULL and m in ("mean",): pass
                        e = f(ctx, V[i, S], S)[tgt] - V[i, tgt]
                        if PRED and n in PREDSEL and m in ("ridge", "mean"):
                            for jj, pz in zip(tgt, (f(ctx, V[i, S], S)[tgt] - ctx["colmean"][tgt]) / ctx["colsd"][tgt]):
                                PRED_ROWS.append((rep, n, m, k, i, good[jj], (V[i, jj] - ctx["colmean"][jj]) / ctx["colsd"][jj], pz))
                        rows.append((rep, n, m, k, i, r, len(tgt), (e ** 2).sum(), ((e / ctx["colsd"][tgt]) ** 2).sum(), np.abs(e).sum(), T[0] if LOBO else -1, len(S)))
    print(f"rep {rep} r={r} psi_min={pm} train={len(tr)} test={len(te)} t={time.time()-t0:.0f}s", flush=True)
    pd.DataFrame(rows, columns="rep sel inf k model r n se2 sez2 ae target ksz".split()).to_csv(out, index=False)
    if PRED: pd.DataFrame(PRED_ROWS, columns="rep sel inf k model col z_true z_pred".split()).to_csv(out.replace(".csv", ".pred.csv.gz"), index=False)
print("done", flush=True)
