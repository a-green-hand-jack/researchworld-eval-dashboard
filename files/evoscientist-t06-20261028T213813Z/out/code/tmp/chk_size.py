import pandas as pd, numpy as np
s = pd.read_csv('results/size_scaling.csv'); print(len(s), s.groupby(['i', 'j']).size().shape)
s['kap'] = s.K_flip / s.N; s['pred'] = s.gap / s.se_fisher ** 2
print(s.groupby('frac').agg(N=('N', 'first'), pres=('gap', lambda x: (x > 0).mean()), kap=('kap', lambda x: x[x > 0].median())))
g = s[s.gap > 0]
print((g.K_flip / g.pred).groupby(g.frac).median())
