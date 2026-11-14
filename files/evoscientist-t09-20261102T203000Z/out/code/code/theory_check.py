"""Compare population-OLS theory predictions (bias = extrapolation residual; sd from sigma^2 d'M^-1 d / n)
with simulated bias / sd for every OLS-type estimator in every setting of every experiment."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analysis_lib import *

EXPS = sys.argv[1:] or ["E1", "E2grid", "E2deg", "E2n", "E3", "E3b", "E3c", "E4a", "E4b", "E4c", "E5gam"]
DROP = {"sid", "chunk", "reps", "g_gseed", "gate", "n", "dbar", "dharm", "sec", "n_clusters", "intra", "rep", "est",
        "estimate", "se_hc", "se_cl", "err", "cover_hc", "cover_cl"}
out = []
for e in EXPS:
    if not os.path.exists(os.path.join(RES, f"{e}_pred.csv")):
        print("skip", e)
        continue
    scen, df, pred = load(e)
    keys = [c for c in scen.columns if c not in DROP]
    dfp = df[df["est"].isin(pred["est"].unique())]
    # per-scenario stats
    g = dfp.groupby(["sid", "est"]).agg(bias_s=("err", "mean"), var_s=("err", lambda x: np.var(x, ddof=1)),
                                        nrep=("err", "size")).reset_index()
    g = g.merge(pred, on=["sid", "est"]).merge(scen[["sid"] + keys + ["n", "dharm", "dbar"]].drop_duplicates("sid"), on="sid")
    agg = g.groupby(keys + ["est"], dropna=False).agg(
        bias_obs=("bias_s", "mean"), bias_obs_sd=("bias_s", "std"), n_sc=("sid", "size"), nrep=("nrep", "sum"),
        var_obs=("var_s", "mean"), bias_pred=("bias_pred", "mean"), var_pred_noise=("var_pred_noise", "mean"),
        var_pred_total=("var_pred_total", "mean"), var_pred_design=("var_pred_design", "mean"), dMd=("dMd", "mean"), n=("n", "mean"), dharm=("dharm", "mean"),
        dbar=("dbar", "mean")).reset_index()
    agg["sd_obs"] = np.sqrt(agg["var_obs"])
    agg["sd_pred_noise"] = np.sqrt(agg["var_pred_noise"])
    agg["sd_pred_total"] = np.sqrt(agg["var_pred_total"])
    # standard error of the setting-level bias estimate: sd_obs / sqrt(total reps)
    agg["bias_obs_se"] = agg["sd_obs"] / np.sqrt(agg["nrep"])
    agg["exp"] = e
    out.append(agg)
T = pd.concat(out, ignore_index=True)
T.to_csv(os.path.join(RES, "theory_check.csv"), index=False)
print(len(T), "setting x estimator rows")
# summary statistics of agreement
for est, g in T.groupby("est"):
    err = g["bias_obs"] - g["bias_pred"]
    z = err / g["bias_obs_se"]
    print(f"{est:9s} n={len(g):4d} corr(bias)={np.corrcoef(g.bias_obs, g.bias_pred)[0,1]:.3f} "
          f"mean|diff|={err.abs().mean():.3f} med|z|={z.abs().median():.2f} "
          f"sd ratio obs/noise med={np.median(g.sd_obs/g.sd_pred_noise):.2f} obs/total med={np.median(g.sd_obs/g.sd_pred_total):.2f}")
