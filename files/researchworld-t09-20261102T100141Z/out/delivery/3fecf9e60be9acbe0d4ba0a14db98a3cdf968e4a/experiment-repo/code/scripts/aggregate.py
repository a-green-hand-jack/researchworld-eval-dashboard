"""Aggregate per-rep estimates into per-(tag, estimator) metrics. Usage: aggregate.py E3_gamma ..."""
import sys, os, json
import numpy as np, pandas as pd
R = os.path.join(os.path.dirname(__file__), "..", "..", "results")


def summarize(df):
    d = df.copy()
    d["err"] = d.est - d.gate
    d["valid"] = d.est.notna()
    z = 1.959964
    d["cover"] = (np.abs(d.err) <= z * d.se).where(d.se.notna())
    d["width"] = 2 * z * d.se
    g = d.groupby(["tag", "est_name"], sort=False)
    out = g.apply(lambda x: pd.Series(dict(
        n=x.n.mean(), dbar=x.dbar.mean(), gate=x.gate.mean(), n_rep=int(x.valid.sum()), frac_undefined=1 - x.valid.mean(),
        bias=x.err.mean(), bias_mcse=x.err.std() / np.sqrt(max(x.valid.sum(), 1)),
        sd=x.err.std(), rmse=np.sqrt((x.err ** 2).mean()),
        rel_rmse=np.sqrt((x.err ** 2).mean()) / abs(x.gate.mean()),
        rel_bias=x.err.mean() / abs(x.gate.mean()),
        # rmse MC se via per-graph block means of squared error (graph draws are the independent blocks)
        rmse_mcse=_rmse_se(x),
        cover=x.cover.mean(), width=x.width.mean(), se_mean=x.se.mean(),
        sd_graphbias=x.groupby("g").err.mean().std())), include_groups=False).reset_index()
    return out


def _rmse_se(x):
    x = x.dropna(subset=["est"])
    m2 = (x.est - x.gate) ** 2
    r = np.sqrt(m2.mean())
    if m2.empty or r == 0:
        return np.nan
    gm = m2.groupby(x.g).mean()
    k = len(gm)
    se_m2 = gm.std(ddof=1) / np.sqrt(k) if k > 1 else m2.std() / np.sqrt(len(m2))
    return se_m2 / (2 * r)


if __name__ == "__main__":
    for e in sys.argv[1:]:
        df = pd.read_parquet(os.path.join(R, "raw", f"{e}.parquet"))
        s = summarize(df)
        sp = json.load(open(os.path.join(R, "raw", f"{e}.specs.json")))
        s.to_csv(os.path.join(R, f"{e}_summary.csv"), index=False)
        print(e, len(s))
