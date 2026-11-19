"""Quick descriptive statistics of the PPI example datasets (used to choose experiment settings)."""
import numpy as np
from ppi_py.datasets import load_dataset

names = ['galaxies', 'forest', 'alphafold', 'gene_expression', 'census_income',
         'census_healthcare', 'census_education', 'plankton', 'ballots']
for nm in names:
    d = load_dataset('/work/data/', nm)
    Y = d['Y'].astype(float); Yh = d['Yhat'].astype(float)
    nu = len(d['Yhat_unlabeled']) if 'Yhat_unlabeled' in d.files else None
    uniqY = np.unique(Y)
    uniqYh = np.unique(Yh)
    r = Y - Yh
    print(f"{nm:18s} n={len(Y):7d} nU={nu} meanY={Y.mean():.4f} meanYh={Yh.mean():.4f} "
          f"#uniqY={len(uniqY)} #uniqYh={len(uniqYh)} "
          f"corr={np.corrcoef(Y, Yh)[0,1]:.3f} varY={Y.var():.4f} varRes={r.var():.4f} "
          f"Yhat range=[{Yh.min():.3f},{Yh.max():.3f}] Yrange=[{Y.min():.3f},{Y.max():.3f}]")
    if 'X' in d.files:
        print('   X shape', d['X'].shape, 'X min', d['X'].min(0), 'X max', d['X'].max(0))
