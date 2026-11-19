"""Analysis: reads results/*.npz, writes results/summary.csv, results/tex_*.tex and figs/*.pdf"""
import numpy as np, pandas as pd, itertools, os, json
from scipy.stats import spearmanr
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from common import DATASETS, MODELS, TREE_ONLY
MODELS_OF = lambda ds: ["rf", "xgb"] if ds in TREE_ONLY else MODELS
DATASETS = [d for d in DATASETS if all(os.path.exists(f"/work/results/{d}_{m}.npz") for m in MODELS_OF(d))]  # preview-safe
K = 3
os.makedirs("/work/figs", exist_ok=True)
rng = np.random.RandomState(0)

def topk(v, k=K): return set(np.argsort(-np.abs(v), kind="stable")[:k])
def jac(a, b): return len(a & b) / len(a | b)
def boot(x, B=2000):
    x = np.asarray(x); m = x.mean()
    bs = x[rng.randint(0, len(x), (B, len(x)))].mean(1)
    return m, *np.percentile(bs, [2.5, 97.5])
def pair_stats(V):  # V: [R,d] attribution vectors of repeated runs/models
    js = [jac(topk(a), topk(b)) for a, b in itertools.combinations(V, 2)]
    t1 = [float(np.argmax(np.abs(a)) == np.argmax(np.abs(b))) for a, b in itertools.combinations(V, 2)]
    return np.mean(js), np.mean(t1)

rows = []; inst = {}
for ds in DATASETS:
    for m in MODELS_OF(ds):
        z = np.load(f"/work/results/{ds}_{m}.npz"); phi, ref, B = z["phi"], z["ref"], z["budgets"]
        n, nb, R, d = phi.shape
        for b in range(nb):
            P = phi[:, b]
            relerr = np.linalg.norm(P - ref[:, None], axis=2).mean(1) / np.linalg.norm(ref, axis=1)
            match = np.array([np.mean([topk(P[i, r]) == topk(ref[i]) for r in range(R)]) for i in range(n)])
            top1 = np.array([np.mean([np.argmax(abs(P[i, r])) == np.argmax(abs(ref[i])) for r in range(R)]) for i in range(n)])
            ps = np.array([pair_stats(P[i]) for i in range(n)])
            sgn = np.array([np.mean([np.sign(P[i, r][list(topk(ref[i]))]) == np.sign(ref[i][list(topk(ref[i]))]) for r in range(R)]) for i in range(n)])
            inst[(ds, m, int(B[b]))] = dict(match=match, pj=ps[:, 0], relerr=relerr)
            row = dict(ds=ds, model=m, M=int(B[b]), d=d)
            for k, v in dict(relerr=relerr, match3=match, top1=top1, pairJ3=ps[:, 0], pairTop1=ps[:, 1], sign3=sgn).items():
                mm, lo, hi = boot(v); row[k] = mm; row[k + "_lo"] = lo; row[k + "_hi"] = hi
            row["frac_all_match"] = float(np.mean(match == 1.0))
            row["frac_match_lt50"] = float(np.mean(match < 0.5))
            rows.append(row)
        if "retrain" in z:  # other noise sources, exact attributions
            for name in ("retrain", "bgres"):
                V = z[name]; ps = np.array([pair_stats(V[:, i]) for i in range(n)])
                row = dict(ds=ds, model=m, M=-1 if name == "retrain" else -2, d=d)
                for k, v in dict(pairJ3=ps[:, 0], pairTop1=ps[:, 1]).items():
                    mm, lo, hi = boot(v); row[k] = mm; row[k + "_lo"] = lo; row[k + "_hi"] = hi
                rows.append(row)
df = pd.DataFrame(rows); df.to_csv("/work/results/summary.csv", index=False)

# ---- main table: single-run top-3 match to reference, per cell and budget
def fmt(r, k): return f"{r[k]:.2f} [{r[k+'_lo']:.2f},{r[k+'_hi']:.2f}]"
bud = [int(b) for b in sorted(df[df.M > 0].M.unique())]
lines = ["\\begin{tabular}{ll" + "c" * len(bud) + "}\\toprule", "Data & Model & " + " & ".join(f"$M{{=}}{b}$" for b in bud) + "\\\\\\midrule"]
for ds in DATASETS:
    for m in MODELS_OF(ds):
        s = df[(df.ds == ds) & (df.model == m) & (df.M > 0)].sort_values("M")
        lines.append(f"{ds} ($d{{=}}{int(s.d.iloc[0])}$) & {m} & " + " & ".join(("n/a ($M{<}d$)" if r.M < r.d else f"{r.match3:.2f} [{r.match3_lo:.2f},{r.match3_hi:.2f}]") for r in s.itertuples()) + "\\\\")
lines.append("\\bottomrule\\end{tabular}")
open("/work/results/tex_match3.tex", "w").write("\n".join(lines))

# ---- table: noise-source comparison (pairwise top-3 Jaccard), tree models
lines = ["\\begin{tabular}{llcccccc}\\toprule", "Data & Model & KS $M{=}128$ & KS $M{=}512$ & KS $M{=}2048$ & KS $M{=}8192$ & bg resample & retrain\\\\\\midrule"]
for ds in DATASETS:
    for m in ("rf", "xgb"):
        s = df[(df.ds == ds) & (df.model == m)]
        c = [("n/a" if M < s.d.iloc[0] else fmt(s[s.M == M].iloc[0], "pairJ3")) for M in (128, 512, 2048, 8192)] + [fmt(s[s.M == -2].iloc[0], "pairJ3"), "n/a" if m == "xgb" else fmt(s[s.M == -1].iloc[0], "pairJ3")]  # xgb retrain: seed has no effect (deterministic training)
        lines.append(f"{ds} & {m} & " + " & ".join(c) + "\\\\")
lines.append("\\bottomrule\\end{tabular}")
open("/work/results/tex_noise.tex", "w").write("\n".join(lines))

# ---- table: rel. error and sign
lines = ["\\begin{tabular}{llcccc}\\toprule", "Data & Model & $M{=}128$ & $M{=}512$ & $M{=}2048$ & $M{=}8192$\\\\\\midrule"]
for ds in DATASETS:
    for m in MODELS_OF(ds):
        s = df[(df.ds == ds) & (df.model == m) & (df.M > 0)].sort_values("M")
        lines.append(f"{ds} & {m} & " + " & ".join(("degenerate ($M{<}d$)" if r.relerr > 1e3 else f"{r.relerr:.3f} [{r.relerr_lo:.3f},{r.relerr_hi:.3f}]") for r in s.itertuples()) + "\\\\")
lines.append("\\bottomrule\\end{tabular}")
open("/work/results/tex_relerr.tex", "w").write("\n".join(lines))

# ---- fig 1: single-run top-3 match vs budget
fig, axs = plt.subplots(1, 6, figsize=(14, 2.6), sharey=True)
cols = dict(lr="#1f77b4", rf="#2ca02c", xgb="#d62728", mlp="#9467bd")
for ax, ds in zip(axs, DATASETS):
    for m in MODELS_OF(ds):
        s = df[(df.ds == ds) & (df.model == m) & (df.M > df.d)].sort_values("M")
        ax.errorbar(s.M, s.match3, yerr=[s.match3 - s.match3_lo, s.match3_hi - s.match3], marker="o", ms=3, capsize=2, label=m, color=cols[m])
    ax.set_xscale("log", base=2); ax.set_title(f"{ds} (d={int(s.d.iloc[0])})", fontsize=9); ax.set_xlabel("budget M (coalitions)")
axs[0].set_ylabel("P(single-run top-3 = ref)"); axs[0].legend(fontsize=7)
plt.tight_layout(); plt.savefig("/work/figs/match_vs_budget.pdf")

# ---- stochastic cells only: KernelSHAP enumerates all 2^d-2 coalitions (deterministic) when M >= 2^d-2; M<d is degenerate
def stochastic(ds, M, d): return d < M < 2 ** d - 2
dmap = {ds: int(df[df.ds == ds].d.iloc[0]) for ds in DATASETS}
df["stochastic"] = [stochastic(r.ds, r.M, r.d) if r.M > 0 else False for r in df.itertuples()]
df.to_csv("/work/results/summary.csv", index=False)
head = {}
for M in bud:
    ys = [(ds, m, inst[(ds, m, M)]["match"]) for ds in DATASETS for m in MODELS_OF(ds) if stochastic(ds, M, dmap[ds])]
    if not ys: continue
    cell_means = [y.mean() for _, _, y in ys]; allv = np.concatenate([y for _, _, y in ys])
    head[M] = dict(n_cells=len(ys), mean_match3=boot(allv), min_cell=min(cell_means), max_cell=max(cell_means), frac_instances_below_half=float(np.mean(allv < 0.5)))
# two-run diagnostic: do two runs agree -> does a *third, held-out* run match the reference? (cluster bootstrap over instances)
def cboot(A, Y, ID, which, B=2000):
    ids = np.unique(ID); out = []
    byid = {i: np.where(ID == i)[0] for i in ids}
    for _ in range(B):
        rows = np.concatenate([byid[i] for i in rng.choice(ids, len(ids))])
        sel = rows[A[rows] == which]
        if len(sel): out.append(Y[sel].mean())
    return float(Y[A == which].mean()), *np.percentile(out, [2.5, 97.5])
diag = {}
for M in bud:
    A, Y, ID = [], [], []
    for ds in DATASETS:
        for m in MODELS_OF(ds):
            if not stochastic(ds, M, dmap[ds]): continue
            z = np.load(f"/work/results/{ds}_{m}.npz"); P = z["phi"][:, list(z["budgets"]).index(M)]; ref = z["ref"]
            for i in range(len(P)):
                for a, b, c in [(0, 1, 2), (3, 4, 5), (6, 7, 8)]:
                    A.append(topk(P[i, a]) == topk(P[i, b])); Y.append(topk(P[i, c]) == topk(ref[i])); ID.append(f"{ds}-{m}-{i}")
    A, Y, ID = np.array(A), np.array(Y, dtype=float), np.array(ID)
    if len(A) == 0: continue
    diag[M] = dict(n=len(A), frac_agree=float(A.mean()), p_match_given_agree=cboot(A, Y, ID, True), p_match_given_disagree=cboot(A, Y, ID, False), n_disagree=int((~A).sum()))
# ---- fig 2: reliability vs ref margin (normalized gap between 3rd and 4th |phi|), stochastic cells
fig, axs = plt.subplots(1, 2, figsize=(7, 2.7), sharey=True)
summ = []
for ax, M in zip(axs, (512, 2048)):
    G, Y = [], []
    for ds in DATASETS:
        for m in MODELS_OF(ds):
            if not stochastic(ds, M, dmap[ds]): continue
            z = np.load(f"/work/results/{ds}_{m}.npz"); a = np.sort(np.abs(z["ref"]), 1)[:, ::-1]
            G += list((a[:, K - 1] - a[:, K]) / np.abs(z["ref"]).sum(1)); Y += list(inst[(ds, m, M)]["match"])
    G, Y = np.array(G), np.array(Y)
    qs = np.quantile(G, np.linspace(0, 1, 6)); b = np.clip(np.searchsorted(qs, G, side="right") - 1, 0, 4)
    mm = [Y[b == j].mean() for j in range(5)]; ax.plot(range(5), mm, "o-")
    ax.set_xticks(range(5)); ax.set_xticklabels([f"Q{j+1}" for j in range(5)]); ax.set_title(f"M={M}", fontsize=9); ax.set_xlabel("quintile of normalized rank-3/4 gap")
    summ.append(dict(M=M, spearman_gap_vs_match=spearmanr(G, Y)[0], quint_means=mm, n=len(G), gap_quintile_edges=list(qs)))
axs[0].set_ylabel("P(single-run top-3 = ref)")
plt.tight_layout(); plt.savefig("/work/figs/gap.pdf")
json.dump(dict(gap=summ, headline=head, two_run_diag=diag), open("/work/results/headline.json", "w"), indent=1, default=float)
print(json.dumps(dict(gap=summ, headline=head, two_run_diag=diag), indent=1, default=float))

