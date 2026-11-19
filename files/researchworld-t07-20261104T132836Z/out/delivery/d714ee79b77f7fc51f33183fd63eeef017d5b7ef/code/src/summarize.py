import sys, pandas as pd, numpy as np
sys.path.insert(0, __import__('os').path.dirname(__file__))
import protocol as P
def per_rep(df):
    rows = []
    for k, g in df.groupby(["bench", "protocol", "method", "n", "rep"]):
        rows.append(dict(zip(["bench", "protocol", "method", "n", "rep"], k)) | P.metrics(g.true.values, g.pred.values))
    return pd.DataFrame(rows)
if __name__ == "__main__":
    df = pd.concat([pd.read_parquet(f) for f in sys.argv[1:]])
    r = per_rep(df)
    pd.set_option("display.width", 200)
    print(r.groupby(["bench", "protocol", "method", "n"])[["mae", "rmse", "spearman", "kendall"]].mean().round(4).unstack("method")["mae"].to_string())
    print(r.groupby(["method", "n"])[["spearman"]].mean().round(3).unstack("method").to_string())
