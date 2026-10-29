import pandas as pd
d=pd.read_parquet("data/arena140k", columns=["id","model_a","model_b","winner","language","timestamp","evaluation_order"])
print(d.shape); print(d.winner.value_counts()); print(d.model_a.nunique(), pd.concat([d.model_a,d.model_b]).value_counts().describe()); print(d.timestamp.min(), d.timestamp.max()); print(d.evaluation_order.value_counts().head())
