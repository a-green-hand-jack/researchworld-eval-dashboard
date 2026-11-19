import numpy as np, pandas as pd
def summarize(df, by):
    d = df.copy()
    d["err"] = d.est - d.truth
    d["cov"] = ((d.lo <= d.truth) & (d.truth <= d.hi)).astype(float)
    d["width"] = d.hi - d.lo
    d.loc[~np.isfinite(d.width), "cov"] = np.nan
    g = d.groupby(by)
    out = g.agg(bias=("err", "mean"), rmse=("err", lambda x: np.sqrt(np.mean(x ** 2))), cover=("cov", "mean"),
                width=("width", "median"), truth=("truth", "mean"), est=("est", "mean"), nrep=("err", "size"))
    out["bias_se"] = g["err"].std() / np.sqrt(out.nrep)
    out["cover_se"] = np.sqrt(out.cover * (1 - out.cover) / out.nrep)
    return out.reset_index()
