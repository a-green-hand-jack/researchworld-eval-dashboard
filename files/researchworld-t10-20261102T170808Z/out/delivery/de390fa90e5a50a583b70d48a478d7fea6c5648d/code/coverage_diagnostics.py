#!/usr/bin/env python3
"""Exploratory undercoverage tests; Holm adjusts across cells within each method."""
import numpy as np
import pandas as pd
from scipy.stats import binomtest
f=pd.read_csv('results/summary.csv'); f['undercoverage_p']=[binomtest(int(k),int(n),.95,alternative='less').pvalue for k,n in zip(f.hits,f.reps)]
f['undercoverage_holm_p']=np.nan
for method,g in f.groupby('method'):
 order=np.argsort(g.undercoverage_p.to_numpy()); raw=g.undercoverage_p.to_numpy()[order]; adjusted=np.minimum(1,np.maximum.accumulate(raw*(len(raw)-np.arange(len(raw)))))
 f.loc[g.index.to_numpy()[order],'undercoverage_holm_p']=adjusted
f['undercoverage_holm_05']=f.undercoverage_holm_p<.05
f.to_csv('results/coverage_diagnostics.csv',index=False)
