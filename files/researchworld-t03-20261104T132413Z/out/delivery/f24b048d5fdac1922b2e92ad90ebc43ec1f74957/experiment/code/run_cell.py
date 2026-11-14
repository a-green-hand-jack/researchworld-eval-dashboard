"""One (dataset, model) cell of the study.

Outputs results/raw/<dataset>__<model>.npz with
  inst_idx, x, p (model prob. at x), ref (N,d) reference attributions, ref_se (N,d) or zeros if exact,
  kernel (N, nb, R, d), kernel_rows (nb,), perm (N, nb, R, d), perm_rows (nb,),
  retrain_ref (K, N, d), and metadata (json string).
Stages are written to separate files as soon as they finish so that an interrupted job can resume.
"""
import argparse, json, os, sys, time
import numpy as np
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

sys.path.insert(0, os.path.dirname(__file__))
import data as datamod, models, explain

BUDGETS = {"pima": [20, 40, 80, 160, 240], "gmsc": [25, 50, 100, 200, 500, 1000], "acs": [25, 50, 100, 200, 500, 1000],
           "german": [60, 100, 200, 500, 1000, 2088, 5000],
           "acs_emp": [40, 64, 128, 256, 512, 1024, 2080, 5000]}  # 2088 / 2080 = shap default nsamples 2d+2048
EXACT_MAX_D = 16


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dataset"); ap.add_argument("model")
    ap.add_argument("--n_inst", type=int, default=50)
    ap.add_argument("--R", type=int, default=30)
    ap.add_argument("--B", type=int, default=50)
    ap.add_argument("--K_retrain", type=int, default=5)
    ap.add_argument("--m_ref", type=int, default=20000)
    ap.add_argument("--K_ref", type=int, default=10)
    ap.add_argument("--stages", default="ref,kernel,perm,retrain,bg")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "results", "raw"))
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--rc_from", type=int, default=3); ap.add_argument("--rc_to", type=int, default=13, help="instances of stage refcheck_more")
    ap.add_argument("--output", default="prob", choices=["prob", "logit"], help="explained model output (sensitivity check)")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    tag = f"{a.dataset}{'_logit' if a.output == 'logit' else ''}__{a.model}"
    D = datamod.LOADERS[a.dataset]()
    d = D.d
    idx_tr, idx_te = train_test_split(np.arange(len(D.y)), test_size=0.3, random_state=a.seed, stratify=D.y)
    Atr, ytr, Ate, yte = D.A[idx_tr], D.y[idx_tr], D.A[idx_te], D.y[idx_te]
    mdl = models.fit(a.model, D.encode(Atr), ytr, a.seed)
    def out_fn(p):
        return np.log(np.clip(p, 1e-6, 1 - 1e-6) / (1 - np.clip(p, 1e-6, 1 - 1e-6))) if a.output == "logit" else p
    f = lambda Z: out_fn(models.predict_pos(mdl, D.encode(Z)))
    pte = models.predict_pos(mdl, D.encode(Ate))
    meta = dict(output=a.output, dataset=a.dataset, model=a.model, d=d, n=len(D.y), B=a.B, R=a.R, n_inst=a.n_inst, seed=a.seed,
                test_auc=float(roc_auc_score(yte, pte)), test_acc=float(((pte > .5) == yte).mean()),
                budgets=BUDGETS[a.dataset], names=D.names)
    rng = np.random.RandomState(1000 + a.seed)
    bg = Atr[rng.choice(len(Atr), a.B, replace=False)]
    sel = rng.choice(len(Ate), a.n_inst, replace=False)
    X = Ate[sel]
    N = len(X)
    print(tag, meta["test_auc"], meta["test_acc"], flush=True)
    stages = a.stages.split(",")
    path = lambda s: f"{a.out}/{tag}__{s}.npz"
    t0 = time.time()
    if "ref" in stages and not os.path.exists(path("ref")):
        ref = np.zeros((N, d)); se = np.zeros((N, d))
        for i in range(N):
            if d <= EXACT_MAX_D:
                ref[i] = explain.exact_shapley(f, X[i], bg)[0]
            else:
                runs = np.array([explain.kernel_shap(f, X[i], bg, a.m_ref, 7_000_000 + 100 * i + r)[0] for r in range(a.K_ref)])
                ref[i], se[i] = runs.mean(0), runs.std(0, ddof=1) / np.sqrt(a.K_ref)
            if i % 10 == 0:
                print("ref", i, time.time() - t0, flush=True)
        np.savez(path("ref"), x=X, sel=sel, p=models.predict_pos(mdl, D.encode(X)), ref=ref, ref_se=se, meta=json.dumps(meta))
    for ex, fn in [("kernel", explain.kernel_shap), ("perm", explain.perm_shap)]:
        if ex in stages and not os.path.exists(path(ex)):
            bud = BUDGETS[a.dataset]
            out = np.zeros((N, len(bud), a.R, d)); rows = np.zeros((N, len(bud), a.R), int)
            for i in range(N):
                for b, m in enumerate(bud):
                    for r in range(a.R):
                        out[i, b, r], rows[i, b, r] = fn(f, X[i], bg, m, 10_000 * (i + 1) + 100 * b + r)
                if i % 5 == 0:
                    print(ex, i, time.time() - t0, flush=True)
            np.savez(path(ex), phi=out, rows=rows, budgets=np.array(bud), meta=json.dumps(meta))
    if "kernell1" in stages and not os.path.exists(path("kernell1")):
        # Kernel SHAP with the library default l1_reg="num_features(10)" (LARS pre-selection when d > 10)
        bud = BUDGETS[a.dataset]
        out = np.zeros((N, len(bud), a.R, d)); rows = np.zeros((N, len(bud), a.R), int)
        for i in range(N):
            for b, m in enumerate(bud):
                for r in range(a.R):
                    out[i, b, r], rows[i, b, r] = explain.kernel_shap(f, X[i], bg, m, 10_000 * (i + 1) + 100 * b + r,
                                                                      l1_reg="num_features(10)")
            if i % 5 == 0:
                print("kernell1", i, time.time() - t0, flush=True)
        np.savez(path("kernell1"), phi=out, rows=rows, budgets=np.array(bud), meta=json.dumps(meta))
    if "refcheck" in stages and not os.path.exists(path("refcheck")):
        # validate the converged Kernel reference against full 2^d enumeration on the first n_check instances
        nc = 3
        ex = np.array([explain.exact_shapley(f, X[i], bg)[0] for i in range(nc)])
        np.savez(path("refcheck"), exact=ex, meta=json.dumps(meta))
        print("refcheck", time.time() - t0, flush=True)
    if "refcheck_more" in stages:
        # further instances for the enumeration check of the German reference (instances rc_from..rc_to-1)
        pm = path(f"refcheckmore_{a.rc_from}_{a.rc_to}")
        if not os.path.exists(pm):
            ex = np.array([explain.exact_shapley(f, X[i], bg)[0] for i in range(a.rc_from, min(a.rc_to, N))])
            np.savez(pm, exact=ex, first=a.rc_from, meta=json.dumps(meta))
            print("refcheck_more", a.rc_from, a.rc_to, time.time() - t0, flush=True)
    # retrain standard: 80% subsamples (main), 50% / 95% subsamples (sensitivity, `retrain_f50` / `retrain_f95`), and the 80% retrains
    # explained a second time with other Kernel seeds (`retrain_rep`, d > 16 only: estimator error of the retrain explanations)
    for stage, frac, kbase in [("retrain", 0.8, 8_000_000), ("retrain_f50", 0.5, 8_000_000), ("retrain_f95", 0.95, 8_000_000),
                               ("retrain_rep", 0.8, 8_500_000)]:
        if stage not in stages or os.path.exists(path(stage)) or (stage == "retrain_rep" and d <= EXACT_MAX_D):
            continue
        refs = np.zeros((a.K_retrain, N, d)); aucs = []
        for k in range(a.K_retrain):
            rr = np.random.RandomState(500 + k)
            sub = rr.choice(len(Atr), int(frac * len(Atr)), replace=False)
            mk = models.fit(a.model, D.encode(Atr[sub]), ytr[sub], 100 + k)
            fk = lambda Z, mk=mk: out_fn(models.predict_pos(mk, D.encode(Z)))
            aucs.append(float(roc_auc_score(yte, fk(Ate))))
            for i in range(N):
                if d <= EXACT_MAX_D:
                    refs[k, i] = explain.exact_shapley(fk, X[i], bg)[0]
                else:
                    refs[k, i] = explain.kernel_shap(fk, X[i], bg, 10000, kbase + 100 * k + i)[0]
            print(stage, k, time.time() - t0, flush=True)
        np.savez(path(stage), phi=refs, auc=np.array(aucs), frac=frac, meta=json.dumps(meta))
    if "bg" in stages and d <= 12 and not os.path.exists(path("bg")):
        # background-induced variation with the estimator exact: G redraws of size B and of size 4B
        Ni, G = min(30, N), 8
        out = {}
        for Bk in (a.B, 4 * a.B):
            ph = np.zeros((G, Ni, d))
            for g in range(G):
                rb = np.random.RandomState(9000 + 10 * g + (Bk > a.B))
                bgg = Atr[rb.choice(len(Atr), Bk, replace=False)]
                for i in range(Ni):
                    ph[g, i] = explain.exact_shapley(f, X[i], bgg)[0]
            out[f"phi_B{Bk}"] = ph
            print("bg", Bk, time.time() - t0, flush=True)
        np.savez(path("bg"), **out, meta=json.dumps(meta))
    if "bgd" in stages and d > 12 and not os.path.exists(path("bgd")):
        # background-induced variation for d > 12 (reduced): G = 3 redraws of B rows (same seeds as the first redraws of the `bg` stage), 30 instances;
        # exact value function for d <= 16, a single Kernel run at 10000 coalitions otherwise (seed 9_500_000 + 100*g + i)
        Ni, G = min(30, N), 3
        ph = np.zeros((G, Ni, d))
        for g in range(G):
            rb = np.random.RandomState(9000 + 10 * g)
            bgg = Atr[rb.choice(len(Atr), a.B, replace=False)]
            for i in range(Ni):
                ph[g, i] = explain.exact_shapley(f, X[i], bgg)[0] if d <= EXACT_MAX_D else explain.kernel_shap(f, X[i], bgg, 10000, 9_500_000 + 100 * g + i)[0]
            print("bgd", g, time.time() - t0, flush=True)
        np.savez(path("bgd"), **{f"phi_B{a.B}": ph}, meta=json.dumps(meta))
    print("done", tag, time.time() - t0, flush=True)


if __name__ == "__main__":
    main()
