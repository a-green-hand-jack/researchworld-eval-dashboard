"""Population-level check of how much side information X adds beyond the fixed predictor on the census_* sets:
5-fold cross-validated MSE of gradient-boosting regressions of Y on f, X, and (f,X), relative to Var(Y), and the linear recalibration."""
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor as H
from sklearn.model_selection import cross_val_predict, KFold
rows = []
for nm in ['census_income', 'census_healthcare', 'census_education']:
    d = np.load(f'/work/data/{nm}.npz'); y = d['Y'].astype(float); f = d['Yhat'].astype(float); X = d['X'].astype(float)
    cv = KFold(5, shuffle=True, random_state=0); r = {}
    for lab, F in [('f', f[:, None]), ('X', X), ('f+X', np.c_[f, X])]:
        p = cross_val_predict(H(max_iter=200, random_state=0), F, y, cv=cv); r[lab] = ((y - p) ** 2).mean() / y.var()
    b = np.cov(y, f)[0, 1] / f.var(); r['linear(f)'] = ((y - y.mean() - b * (f - f.mean())) ** 2).mean() / y.var()
    rows.append(dict(dataset=nm, **r, extra_share_of_X=1 - r['f+X'] / r['linear(f)']))
df = pd.DataFrame(rows); df.to_csv('/work/results/xgain.csv', index=False); print(df.round(4).to_string())
