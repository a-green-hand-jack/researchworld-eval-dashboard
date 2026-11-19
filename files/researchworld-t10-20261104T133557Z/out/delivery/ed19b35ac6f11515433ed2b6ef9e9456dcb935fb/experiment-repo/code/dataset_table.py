"""Dataset descriptors for the paper's data table (ppi-python v0.2.3 .npz files)."""
import numpy as np, pandas as pd
from run_real import load
rows = []
for d in ["galaxies", "forest", "alphafold", "gene_expression", "census_income", "census_healthcare", "census_education"]:
    Y, F, X = load(d)
    rows.append(dict(dataset=d, pool_size=len(Y), outcome="binary" if set(np.unique(Y)) <= {0., 1.} else "continuous/ordinal",
                     y_mean=Y.mean(), y_sd=Y.std(), skew=float(((Y - Y.mean())**3).mean() / Y.std()**3), corr_y_yhat=np.corrcoef(Y, F)[0, 1],
                     yhat_distinct_values=len(np.unique(F)), n_features=0 if X is None else X.shape[1]))
pd.DataFrame(rows).to_csv("../results/datasets.csv", index=False); print(pd.DataFrame(rows).round(3).to_string())
