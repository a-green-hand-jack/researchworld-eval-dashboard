"""From raw runs to tidy result tables (results/tidy/*.csv). See results/SCHEMA.md for the columns.

Inference unit = instance. Cell estimates are means (or medians where stated) over instances of per-instance
quantities that are themselves averages over the R repeated runs (pairwise metrics: all R(R-1)/2 pairs).
Intervals: nested bootstrap (resample instances, then runs within each selected instance; n_boot draws).
Usage: python code/analyze.py [--results results] [--n_boot 1000]
"""
import argparse, glob, json, os, sys
import numpy as np, pandas as pd
from scipy.stats import wilcoxon
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import metrics as M

ap = argparse.ArgumentParser()
ap.add_argument("--results", default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results"))
ap.add_argument("--n_boot", type=int, default=1000)
ap.add_argument("--seed", type=int, default=2024)
ap.add_argument("--min_runs", type=int, default=20, help="cells with fewer runs are listed as incomplete, not analysed")
a = ap.parse_args()
tidy = os.path.join(a.results, "tidy"); os.makedirs(tidy, exist_ok=True)
rng = np.random.RandomState(a.seed)

LEVEL = {"kernel_q": 0.25, "kernel_1": 1, "kernel_4": 4, "kernel_16": 16, "kernel_1_l1default": 1, "perm_1": 1, "perm_4": 4}
EXPL = {c: ("perm" if c.startswith("perm") else "kernel") for c in LEVEL}
ARM = {c: ("shap_default_l1" if "l1default" in c else "l1_off" if c.startswith("kernel") else "none") for c in LEVEL}
ALL_CELLS = list(LEVEL)
CONTROLS = {"acs_income", "pima"}
PAIR_KEYS = ["spearman_abs", "top1_jaccard", "top3_jaccard", "top5_jaccard", "rbo", "sign_top3", "rel_l2_pair_dist"]
TGT_KEYS = ["rel_l2_err", "max_abs_err_over_scale", "spearman_abs_target", "top1_hit", "top3_hit", "top5_hit",
            "top3_exact_order", "sign_top3_target", "sign_all_target"]


def pair_mean(m, runs=None, inst=None):
    """Mean over off-diagonal pairs of m[N,R,R] -> [N]. With a bootstrap draw, row b uses instance inst[b] and the
    runs runs[b] (drawn with replacement; pairs of identical draws are excluded)."""
    N, R, _ = m.shape
    if runs is None:
        mask = ~np.eye(R, dtype=bool)[None]
        return (m * mask).sum((1, 2)) / mask.sum((1, 2))
    ii = inst[:, None, None]
    sub = m[ii, runs[:, :, None], runs[:, None, :]]
    mask = runs[:, :, None] != runs[:, None, :]
    return (sub * mask).sum((1, 2)) / np.maximum(mask.sum((1, 2)), 1)


def boot_stat(per_inst_fn, N, R, stat="mean", n_boot=a.n_boot):
    """per_inst_fn(runs[N,R] or None) -> per-instance values [N]. Nested bootstrap of the mean/median over instances."""
    est_vals = per_inst_fn(None)
    est = np.mean(est_vals) if stat == "mean" else np.median(est_vals)
    bs = np.empty(n_boot)
    for b in range(n_boot):
        inst = rng.randint(0, N, N)
        runs = rng.randint(0, R, (N, R))
        v = per_inst_fn(runs, inst)
        bs[b] = v.mean() if stat == "mean" else np.median(v)
    return est, np.percentile(bs, 2.5), np.percentile(bs, 97.5), est_vals


def sub_instances(d, inst):
    return {k: v[inst] for k, v in d.items()}


def gather(ds_dir, kind, cell):
    fs = sorted(glob.glob(os.path.join(ds_dir, "raw", kind, f"{cell}_r*.npz")))
    if not fs: return None
    z = [np.load(f) for f in fs]
    return np.stack([x["phi"] for x in z], 1), np.array([float(x["seconds"]) for x in z]), int(z[0]["nsamples"]), len(fs)


def load_target(ds_dir, kind):
    p = os.path.join(ds_dir, "targets", f"{kind}.npz")
    if not os.path.exists(p): return None, None
    z = np.load(p)
    if "phi_enum" in z.files and len(z["phi_enum"]) == len(z["fx"]):
        return z["phi_enum"], "enumeration"
    if "phi_struct" in z.files:
        return z["phi_struct"], "closed_form" if kind == "lr" else "treeshap"
    return (z["phi_enum"], "enumeration_subset") if "phi_enum" in z.files else (None, None)


rows_inst, rows_sum, rows_gap, rows_lvl, rows_models, rows_notrun, rows_verdict = [], [], [], [], [], [], []
store = {}  # (ds, kind, cell) -> dict for contrasts
for ds_dir in sorted(glob.glob(os.path.join(a.results, "*", "models.json"))):
    ds_dir = os.path.dirname(ds_dir)
    ds = os.path.basename(ds_dir)
    meta = json.load(open(os.path.join(ds_dir, "models.json")))
    inst = json.load(open(os.path.join(ds_dir, "instances.json")))
    stratum = np.array(inst["stratum"])
    for kind, mm in meta.items():
        rows_models.append(dict(dataset=ds, model=kind, **{k: v for k, v in mm.items()}))
        tgt, tkind = load_target(ds_dir, kind)
        for cell in ALL_CELLS:
            g = gather(ds_dir, kind, cell)
            if g is None:
                if ds.endswith("_probfn") and cell != "kernel_1": continue  # value-function sensitivity runs only the 1x kernel cell
                if ds in CONTROLS and (cell.startswith("perm") or cell == "kernel_16"): why = "not planned (deterministic-regime control: Tier 1 only)"
                elif cell == "kernel_16" and ds != "german": why = "cut for throughput (PLAN §0a.6 cut order); 16x kept on German only"
                else: why = "not run (tier not started or cut; see REPRODUCE.md)"
                rows_notrun.append(dict(dataset=ds, model=kind, cell=cell, reason=why))
                continue
            phi, secs, ns, R = g
            if R < a.min_runs:
                rows_notrun.append(dict(dataset=ds, model=kind, cell=cell, reason=f"incomplete: {R}/{a.min_runs} runs present"))
                continue
            N = phi.shape[0]
            tg = tgt[:N] if tgt is not None else None
            if tg is not None and len(tg) < N:
                phi_t = phi[: len(tg)]; tg_n = len(tg)
            else:
                phi_t = phi; tg_n = N
            base = dict(dataset=ds, model=kind, explainer=EXPL[cell], arm=ARM[cell], cell=cell, level_x_default=LEVEL[cell],
                        nsamples=ns, background=mm["K"], budget_evals=ns * mm["K"], target=tkind or "none")
            rows_lvl.append(dict(base, n_instances=N, R=R, sec_per_explanation_mean=float(secs.mean() / N),
                                 us_per_model_eval=float(secs.mean() / N / (ns * mm["K"]) * 1e6),
                                 cpu="shared host, 1 thread/job (see REPRODUCE.md)"))
            P = M.pairwise(phi)
            V = M.versus_target(phi_t, tg) if tg is not None else {}
            store[(ds, kind, cell)] = dict(P=P, V=V, phi=phi, tg=tg, stratum=stratum[:N], N=N, R=R)
            # per-instance rows (average over runs/pairs)
            for k in PAIR_KEYS:
                if k not in P: continue
                v = pair_mean(P[k])
                est, lo, hi, _ = boot_stat(lambda runs, inst=None, k=k: pair_mean(P[k], runs, inst), N, R)
                rows_inst += [dict(base, instance=i, stratum=stratum[i], metric=k, value=float(v[i])) for i in range(N)]
                rows_sum.append(dict(base, metric=k, stat="mean", est=est, lo=lo, hi=hi, n_instances=N, R=R, n_boot=a.n_boot, seed=a.seed))
            for k in TGT_KEYS:
                if k not in V: continue
                n2 = tg_n
                def fn(runs, inst=None, k=k, n2=n2):
                    x = V[k]
                    if runs is None: return x.mean(1)
                    return np.take_along_axis(x[inst], runs, 1).mean(1)
                for stat in (["mean", "median"] if k == "rel_l2_err" else ["mean"]):
                    est, lo, hi, _ = boot_stat(fn, n2, R, stat)
                    rows_sum.append(dict(base, metric=k, stat=stat, est=est, lo=lo, hi=hi, n_instances=n2, R=R, n_boot=a.n_boot, seed=a.seed))
                v = V[k].mean(1)
                rows_inst += [dict(base, instance=i, stratum=stratum[i], metric=k, value=float(v[i])) for i in range(n2)]
            if tg is not None:
                gap, sd, ratio, ok = M.gap_to_noise(phi_t, tg)
                for i in range(gap.shape[0]):
                    for j in range(gap.shape[1]):
                        rows_gap.append(dict(base, instance=i, stratum=stratum[i], pair_rank=j + 1, gap=gap[i, j], sd_diff=sd[i, j],
                                             ratio=ratio[i, j], p_order_reproduced=ok[i, j]))
            # permuted-feature null (chance level) for the 1x primary arm
            if cell == "kernel_1":
                sh = np.stack([[rng.permutation(x) for _ in range(R)] for x in phi.reshape(N, R, -1)[:, 0, :]])  # independent shuffles of run 0
                Pn = M.pairwise(sh)
                for k in PAIR_KEYS:
                    if k not in Pn: continue
                    v = pair_mean(Pn[k])
                    est, lo, hi, _ = boot_stat(lambda runs, inst=None, k=k: pair_mean(Pn[k], runs, inst), N, R)
                    rows_sum.append(dict(base, explainer="null_perm", arm="none", cell="null_perm", metric=k, stat="mean", est=est, lo=lo, hi=hi,
                                         n_instances=N, R=R, n_boot=a.n_boot, seed=a.seed))
    # ---- missing cell bookkeeping handled above

pd.DataFrame(rows_inst).to_csv(os.path.join(tidy, "runs_metrics.csv"), index=False)
S = pd.DataFrame(rows_sum); S.to_csv(os.path.join(tidy, "summary_ci.csv"), index=False)
pd.DataFrame(rows_gap).to_csv(os.path.join(tidy, "gap_to_noise.csv"), index=False)
pd.DataFrame(rows_lvl).to_csv(os.path.join(tidy, "budget_levels.csv"), index=False)
pd.DataFrame(rows_models).to_csv(os.path.join(tidy, "models.csv"), index=False)
pd.DataFrame(rows_notrun).to_csv(os.path.join(tidy, "cells_not_run.csv"), index=False)

# ---------------------------------------------------------------- pre-stated decision rule (PLAN §0) per cell
def get(df, **kw):
    q = df
    for k, v in kw.items(): q = q[q[k] == v]
    return q.iloc[0] if len(q) else None

if len(S):
    for (ds, kind, cell), g in S[S.cell != "null_perm"].groupby(["dataset", "model", "cell"]):
        t3 = get(g, metric="top3_hit", stat="mean"); l2 = get(g, metric="rel_l2_err", stat="median")
        sg = get(g, metric="sign_top3_target", stat="mean"); t1 = get(g, metric="top1_jaccard", stat="mean")
        if t3 is None: continue
        reliable = t3.lo >= 0.9 and l2.est <= 0.1 and sg.lo >= 0.95
        unreliable = t3.hi < 0.7 or t1.hi < 0.5
        rows_verdict.append(dict(dataset=ds, model=kind, cell=cell, top3_hit_mean=t3.est, top3_hit_lo=t3.lo, top3_hit_hi=t3.hi,
                                 rel_l2_median=l2.est, sign_top3_lo=sg.lo, top1_repro_mean=t1.est, top1_repro_hi=t1.hi,
                                 verdict="reliable" if reliable else "unreliable" if unreliable else "conditional"))
    pd.DataFrame(rows_verdict).to_csv(os.path.join(tidy, "verdicts.csv"), index=False)

# ---------------------------------------------------------------- planned paired contrasts (per-instance, same instances)
CONTR = [("kernel_1", "kernel_q", "budget 1x vs 0.25x"), ("kernel_4", "kernel_1", "budget 4x vs 1x"), ("kernel_16", "kernel_4", "budget 16x vs 4x"),
         ("kernel_1", "kernel_1_l1default", "l1 off vs shap default (1x)"), ("perm_1", "kernel_1", "permutation vs kernel (1x)"),
         ("perm_4", "kernel_4", "permutation vs kernel (4x)")]
CM = ["top3_hit", "rel_l2_err", "top3_jaccard", "spearman_abs"]
rows_c = []
for (ds, kind, c1) in {(k[0], k[1], k[2]) for k in store}:
    for A, B, name in CONTR:
        if A != c1 or (ds, kind, B) not in store: continue
        sa, sb = store[(ds, kind, A)], store[(ds, kind, B)]
        for m in CM:
            def per(s, m=m):
                if m in s["P"]: return pair_mean(s["P"][m])
                return s["V"][m].mean(1) if m in s["V"] else None
            va, vb = per(sa), per(sb)
            if va is None or vb is None: continue
            n = min(len(va), len(vb)); dlt = va[:n] - vb[:n]
            bs = np.array([dlt[rng.randint(0, n, n)].mean() for _ in range(a.n_boot)])
            try: pval = wilcoxon(dlt).pvalue if np.any(dlt != 0) else 1.0
            except Exception: pval = np.nan
            rows_c.append(dict(dataset=ds, model=kind, contrast=name, A=A, B=B, metric=m, mean_diff_A_minus_B=dlt.mean(), lo=np.percentile(bs, 2.5),
                               hi=np.percentile(bs, 97.5), wilcoxon_p=pval, n_instances=n, n_boot=a.n_boot))
C = pd.DataFrame(rows_c)
if len(C):
    # Holm correction within metric over all planned contrasts
    C["wilcoxon_p_holm"] = np.nan
    for m, idx in C.groupby("metric").groups.items():
        p = C.loc[idx, "wilcoxon_p"].fillna(1.0).values; o = np.argsort(p); adj = np.empty_like(p); run = 0
        for r_, j in enumerate(o):
            run = max(run, (len(p) - r_) * p[j]); adj[j] = min(1.0, run)
        C.loc[idx, "wilcoxon_p_holm"] = adj
C.to_csv(os.path.join(tidy, "contrasts.csv"), index=False)

# ---------------------------------------------------------------- S2: equal total budget, one run at B vs mean of g runs at B/g
rows_e = []
for (ds, kind, c) in list(store):
    for hi_cell, lo_cell, g in [("kernel_1", "kernel_q", 4), ("kernel_4", "kernel_1", 4)]:
        if c != hi_cell or (ds, kind, lo_cell) not in store: continue
        sh, sl = store[(ds, kind, hi_cell)], store[(ds, kind, lo_cell)]
        if sh["tg"] is None: continue
        n = len(sh["tg"]); R = sl["R"]; ng = R // g
        if ng < 2: continue
        avg = sl["phi"][:n, : ng * g].reshape(n, ng, g, -1).mean(2)  # averages of g disjoint runs
        Va = M.versus_target(avg, sh["tg"]); Vs = sh["V"]
        for m in ["rel_l2_err", "top3_hit", "top1_hit"]:
            da = Va[m].mean(1) - Vs[m].mean(1)
            bs = np.array([da[rng.randint(0, n, n)].mean() for _ in range(a.n_boot)])
            rows_e.append(dict(dataset=ds, model=kind, single_cell=hi_cell, averaged_cell=lo_cell, g=g, metric=m, single_mean=Vs[m].mean(),
                               averaged_mean=Va[m].mean(), diff_avg_minus_single=da.mean(), lo=np.percentile(bs, 2.5), hi=np.percentile(bs, 97.5),
                               n_instances=n, note="equal total evaluations: g runs at B/g averaged vs one run at B"))
pd.DataFrame(rows_e, columns=["dataset", "model", "single_cell", "averaged_cell", "g", "metric", "single_mean", "averaged_mean", "diff_avg_minus_single", "lo", "hi", "n_instances", "note"]).to_csv(os.path.join(tidy, "equal_budget.csv"), index=False)
print("tidy tables written to", tidy, {f: os.path.getsize(os.path.join(tidy, f)) for f in sorted(os.listdir(tidy))})

# ---------------------------------------------------------------- N4: variance components (explainer seed vs background redraw / model refit)
rows_v, rows_vs = [], []
for fpth in sorted(glob.glob(os.path.join(a.results, "*", "n4", "*.npz"))):
    ds = fpth.split(os.sep)[-3]; kind, factor = os.path.basename(fpth)[:-4].rsplit("_", 1)
    z = np.load(fpth); phi = z["phi"]  # [N,L,S,d]
    N, L, S, d = phi.shape
    v_exp = phi.var(2, ddof=1).mean(1)                       # [N,d] explainer-seed variance (within level)
    v_fac = np.maximum(phi.mean(2).var(1, ddof=1) - v_exp / S, 0)  # [N,d] between-level variance net of seed noise
    scale = np.linalg.norm(phi.mean((1, 2)), axis=-1)       # attribution vector norm
    for i in range(N):
        for j in range(d):
            rows_v.append(dict(dataset=ds, model=kind, factor=factor, instance=i, feature=j, var_explainer=v_exp[i, j], var_factor=v_fac[i, j]))
    tot_e, tot_f = v_exp.sum(1), v_fac.sum(1)
    def ratio(idx): return tot_f[idx].mean() / max(tot_e[idx].mean(), 1e-30)
    bs = np.array([ratio(rng.randint(0, N, N)) for _ in range(a.n_boot)])
    rel = lambda t, idx: np.sqrt(t[idx]).mean() / max(scale[idx].mean(), 1e-30)
    bsr = np.array([[rel(tot_e, ii), rel(tot_f, ii)] for ii in (rng.randint(0, N, N) for _ in range(a.n_boot))])
    rows_vs.append(dict(dataset=ds, model=kind, factor=factor, L=L, S=S, n_instances=N, ratio_factor_to_explainer=ratio(np.arange(N)),
                        ratio_lo=np.percentile(bs, 2.5), ratio_hi=np.percentile(bs, 97.5),
                        rel_sd_explainer=rel(tot_e, np.arange(N)), rel_sd_explainer_lo=np.percentile(bsr[:, 0], 2.5), rel_sd_explainer_hi=np.percentile(bsr[:, 0], 97.5),
                        rel_sd_factor=rel(tot_f, np.arange(N)), rel_sd_factor_lo=np.percentile(bsr[:, 1], 2.5), rel_sd_factor_hi=np.percentile(bsr[:, 1], 97.5),
                        explainer_at_machine_eps=bool(rel(tot_e, np.arange(N)) < 1e-9),  # exact explainer (additive model): ratio undefined
                        auc_mean=float(z["auc"].mean()), auc_min=float(z["auc"].min()), auc_max=float(z["auc"].max()), n_boot=a.n_boot, seed=a.seed))
pd.DataFrame(rows_v, columns=["dataset", "model", "factor", "instance", "feature", "var_explainer", "var_factor"]).to_csv(os.path.join(tidy, "variance_components.csv"), index=False)
dfv = pd.DataFrame(rows_vs)
if len(dfv):
    for c in ("ratio_factor_to_explainer", "ratio_lo", "ratio_hi"): dfv.loc[dfv.explainer_at_machine_eps, c] = np.nan
dfv.to_csv(os.path.join(tidy, "variance_components_summary.csv"), index=False)

# ---------------------------------------------------------------- value-function sensitivity (log-odds vs probability, kernel_1)
sc = pd.read_csv(os.path.join(tidy, "summary_ci.csv"))
rows_vf = []
for ds in sorted({d for d in sc.dataset.unique() if d.endswith("_probfn")}):
    base = ds[: -len("_probfn")]
    for kind in sc[sc.dataset == ds].model.unique():
        for metric in ("spearman_abs", "top3_jaccard", "top5_jaccard", "rbo", "rel_l2_pair_dist", "rel_l2_err", "top3_hit"):
            q = lambda dd: sc[(sc.dataset == dd) & (sc.model == kind) & (sc.cell == "kernel_1") & (sc.metric == metric) & (sc.stat == "mean")]
            A, B = q(base), q(ds)
            if len(A) and len(B):
                rows_vf.append(dict(dataset=base, model=kind, metric=metric, est_logodds=A.est.iloc[0], lo_logodds=A.lo.iloc[0], hi_logodds=A.hi.iloc[0],
                                    est_probability=B.est.iloc[0], lo_probability=B.lo.iloc[0], hi_probability=B.hi.iloc[0], cell="kernel_1",
                                    note="same model/instances/background/seeds; only the explained scalar differs"))
pd.DataFrame(rows_vf).to_csv(os.path.join(tidy, "valfn_sensitivity.csv"), index=False)
