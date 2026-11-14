"""Turn raw attribution arrays (results/E*) into per-instance metric tables (results/tables/*.csv)."""
import os, sys, itertools
import numpy as np, pandas as pd, joblib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C, metrics as M

TAB = f"{C.RES}/tables"; os.makedirs(TAB, exist_ok=True)
K = 3


def pair_idx(R):
    return np.array(list(itertools.combinations(range(R), 2)))


def pairwise_mean(phi, k=K, rbo_depth=None):
    """phi: (R,d) runs of one instance -> dict of mean pairwise metrics over all run pairs."""
    pi = pair_idx(phi.shape[0])
    m = M.all_metrics(phi[pi[:, 0]], phi[pi[:, 1]], k, rbo_depth)
    return {f"pair_{a}": float(v.mean()) for a, v in m.items()}


def vs_ref(phi, ref, k=K, rbo_depth=None):
    Rn = phi.shape[0]
    refs = np.repeat(ref[None], Rn, 0)
    m = M.all_metrics(phi, refs, k, rbo_depth)
    out = {f"ref_{a}": float(v.mean()) for a, v in m.items()}
    out["ref_relL2"] = float(M.rel_l2(phi, refs).mean())
    out["set_recover"] = float((M.jaccard_topk(phi, refs, k) == 1).mean())
    return out


def noise_stats(phi, ref, k=K):
    sd = phi.std(0, ddof=1)
    rn = np.linalg.norm(ref)
    out = dict(sd_rel=float(np.sqrt((sd ** 2).sum()) / max(rn, 1e-12)))
    order = np.argsort(-np.abs(ref))
    if len(ref) > k:
        a, b = order[k - 1], order[k]
        gap = abs(ref[a]) - abs(ref[b])
        s = np.sqrt(sd[a] ** 2 + sd[b] ** 2)
        out.update(gap=float(gap), gap_rel=float(gap / max(rn, 1e-12)), z=float(gap / max(s, 1e-12)) if s > 0 else np.inf)
    return out


def build_E1():
    rows, diag = [], []
    for dn in C.DATASETS:
        Dd = joblib.load(f"{C.ART}/{dn}_data.joblib")
        for k in C.MODELS:
            m = joblib.load(f"{C.ART}/{dn}_{k}.joblib")
            pr = m.predict(Dd["Xte"])
            for est in C.ESTIMATORS:
                fn = f"{C.RES}/E1/{dn}_{k}_{est}.npz"
                if not os.path.exists(fn):
                    print("missing", fn); continue
                z = np.load(fn, allow_pickle=True)
                phi, ref, bud = z["phi"], z["ref"], z["budgets"]
                d = phi.shape[-1]
                for i in range(phi.shape[0]):
                    for bi, B in enumerate(bud):
                        exact = bool(est == "kernel" and B >= 2 ** d - 2)
                        P = phi[i, bi]
                        row = dict(ds=dn, model=k, est=est, B=int(B), inst=i, exact=exact, d=d, pred=float(pr[i]))
                        row.update(pairwise_mean(P)); row.update(vs_ref(P, ref[i])); row.update(noise_stats(P, ref[i]))
                        rows.append(row)
                        # two-run diagnostic: disjoint run pairs (2r, 2r+1); outcome = run 2r top-3 set != reference set
                        for r in range(0, P.shape[0] - 1, 2):
                            jd = M.jaccard_topk(P[r:r + 1], P[r + 1:r + 2], K)[0]
                            jr = M.jaccard_topk(P[r:r + 1], ref[i:i + 1], K)[0]
                            diag.append((dn, k, est, int(B), i, exact, jd, jr))
    pd.DataFrame(rows).to_csv(f"{TAB}/E1_instance.csv", index=False)
    pd.DataFrame(diag, columns=["ds", "model", "est", "B", "inst", "exact", "diag_jac", "ref_jac"]).to_csv(f"{TAB}/E1_diag.csv", index=False)


def build_E2():
    rows = []
    for dn in C.DATASETS:
        for k in C.MODELS:
            z = np.load(f"{C.RES}/E2/{dn}_{k}.npz")
            for key in z.files:
                A = z[key]
                for i in range(A.shape[0]):
                    row = dict(ds=dn, model=k, m=int(key[1:]), inst=i); row.update(pairwise_mean(A[i])); rows.append(row)
    pd.DataFrame(rows).to_csv(f"{TAB}/E2_instance.csv", index=False)


def build_E3():
    rows = []
    for dn in C.DATASETS:
        Dd = joblib.load(f"{C.ART}/{dn}_data.joblib")
        for k in C.MODELS:
            z = np.load(f"{C.RES}/E3/{dn}_{k}.npz")
            ref = z["ref"]  # (K, N, d)
            for i in range(ref.shape[1]):
                row = dict(ds=dn, model=k, inst=i)
                row.update(pairwise_mean(ref[:, i]))
                row["pred_sd"] = float(z["pred"][:, i].std(ddof=1))
                rows.append(row)
            # cross-instance baseline: top-3 Jaccard between attributions of different instances (base model, E1 reference)
            e1 = np.load(f"{C.RES}/E1/{dn}_{k}_kernel.npz", allow_pickle=True)["ref"]
            rs = np.random.RandomState(0); n = len(e1)
            a = rs.randint(0, n, 2000); b = (a + rs.randint(1, n, 2000)) % n
            mm = M.all_metrics(e1[a], e1[b], K)
            rows.append(dict(ds=dn, model=k, inst=-1, **{f"cross_{x}": float(v.mean()) for x, v in mm.items()}))
    pd.DataFrame(rows).to_csv(f"{TAB}/E3_instance.csv", index=False)


def build_E4():
    rows = []
    for dn in C.DATASETS:
        for k in C.MODELS:
            phi = np.load(f"{C.RES}/E4/{dn}_{k}.npz")["phi"]
            ref = np.load(f"{C.RES}/E1/{dn}_{k}_kernel.npz", allow_pickle=True)["ref"]
            for i in range(phi.shape[0]):
                row = dict(ds=dn, model=k, inst=i, d=phi.shape[-1], n_zero=float((phi[i] == 0).sum(1).mean()))
                row.update(pairwise_mean(phi[i])); row.update(vs_ref(phi[i], ref[i])); rows.append(row)
    pd.DataFrame(rows).to_csv(f"{TAB}/E4_instance.csv", index=False)


def build_E5():
    rows = []
    kk = 10
    for k in C.E5_MODELS:
        for est in C.ESTIMATORS:
            z = np.load(f"{C.RES}/E5/{k}_{est}.npz")
            phi, ref, bud = z["phi"], z["ref"], z["budgets"]
            for i in range(phi.shape[0]):
                for bi, B in enumerate(bud):
                    row = dict(ds=C.E5_DS, model=k, est=est, B=int(B), inst=i, d=phi.shape[-1])
                    row.update(pairwise_mean(phi[i, bi], k=kk, rbo_depth=20))
                    if not np.isnan(ref[i]).any():
                        row.update(vs_ref(phi[i, bi], ref[i], k=kk, rbo_depth=20))
                    rows.append(row)
    pd.DataFrame(rows).to_csv(f"{TAB}/E5_instance.csv", index=False)


if __name__ == "__main__":
    for s in sys.argv[1:]:
        dict(E1=build_E1, E2=build_E2, E3=build_E3, E4=build_E4, E5=build_E5)[s]()
        print("built", s, flush=True)
