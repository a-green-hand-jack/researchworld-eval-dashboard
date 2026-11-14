"""T1 post-processing: matrix summary (empirical analogues of T0 parameters), per-cell gap with delete-a-block SE,
closed-form prediction from the matrix's own (sigma, r, tau), subject breakdown, method summaries and decisions.
usage: t1_summary.py MODEL  -> results/*_t1.* (reads results/t1/MODEL.shard*)"""
import sys, os, glob, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import configs as C, lib, t1, aggregate as A
R = A.R

def matrix_summary(model, n_pool=2000, chunk=250):
    L, pool = t1.load_matrix(model, n_pool, chunk); test = C.load_test(); ans = test.answer_index.values[pool]
    Y, names = t1.correctness(L, ans); N = Y.shape[1]; rows = []
    for k in range(24):
        a = Y[k].mean(); rows.append(dict(kind="base_config", name=names[k], n_items=N, acc=a, se=np.sqrt(a * (1 - a) / N)))
    out = []
    for label, idx in (("base24", np.arange(24)), ("all300", np.arange(Y.shape[0]))):
        P = Y[idx].mean(1); th0 = P.mean(); sig2 = th0 * (1 - th0)
        Cm = np.corrcoef(Y[idx].astype(float)); r = float(Cm[np.triu_indices(len(idx), 1)].mean())
        tau2 = max(0.0, P.var(ddof=1) - sig2 * (1 - r) / N)
        out.append(dict(kind=f"candidate_set_{label}", name=label, n_items=N, K=len(idx), acc=th0, sigma=np.sqrt(sig2), r_binary=r, acc_sd_observed=P.std(ddof=1),
                        tau_prob_est=np.sqrt(tau2), acc_min=P.min(), acc_max=P.max(), base_acc=Y[0].mean(), best_obs_acc=P.max()))
    df = pd.DataFrame(rows + out); df.to_csv(f"{R}/t1_matrix_summary.csv", index=False); return df, out

def main(model):
    ms, sets = matrix_summary(model); st = {d["name"]: d for d in sets}
    runs, meth = A.load("T1", model)
    suf = "t1"; runs.to_parquet(f"{R}/runs_{suf}.parquet"); meth.to_parquet(f"{R}/methods_{suf}.parquet")
    gap, msum = A.summarise(runs, meth); runs["gap"] = runs.reported_naive - runs.theta
    # delete-a-block SE: replicate r belongs to block r % G; SE = sd of block means / sqrt(G)
    b = runs.groupby(["cell_id", "block"]).gap.mean().groupby("cell_id").agg(["std", "count"]); gap = gap.merge((b["std"] / np.sqrt(b["count"])).rename("gap_block_se"), left_on="cell_id", right_index=True)
    th = []
    for _, r in gap.iterrows():
        d = st["base24"] if r.K == 24 else st["all300"]
        th.append(lib.theory_gap(int(r.n), int(r.K), d["sigma"], d["r_binary"], d["tau_prob_est"]) if r.procedure == "exhaustive" else np.nan)
    gap["gap_theory_from_matrix"] = th
    gap.to_csv(f"{R}/summary_gap_{suf}.csv", index=False); msum.to_csv(f"{R}/summary_methods_{suf}.csv", index=False)
    A.decisions(meth, runs).to_csv(f"{R}/decisions_{suf}.csv", index=False)
    subs = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(f"{R}/t1/{model}.shard*.subjects.parquet"))], ignore_index=True)
    if len(subs):
        subs["gap"] = subs.reported - subs.fresh
        sb = subs.groupby(["cell_id", "subject"]).agg(reps=("gap", "size"), mean_gap=("gap", "mean"), sd_gap=("gap", "std"), n_search_items=("n_search_items", "mean"), n_fresh_items=("n_fresh_items", "mean"),
                                                      reported_mean=("reported", "mean"), fresh_mean=("fresh", "mean")).reset_index()
        sb["mcse"] = sb.sd_gap / np.sqrt(sb.reps); sb.to_csv(f"{R}/subject_breakdown.csv", index=False)
    print(gap.shape, msum.shape)

if __name__ == "__main__":
    main(sys.argv[1])
