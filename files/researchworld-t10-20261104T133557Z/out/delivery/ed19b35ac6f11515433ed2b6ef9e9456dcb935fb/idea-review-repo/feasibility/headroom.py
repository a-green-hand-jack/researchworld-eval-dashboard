import numpy as np
from sklearn.isotonic import IsotonicRegression
from ppi_py.datasets import load_dataset
D='/hutian/scratch/dl/data/'
rows=[]
for name in ['galaxies','forest','alphafold','gene_expression','census_income','census_healthcare','census_education','plankton','ballots']:
    d=load_dataset(D,name); Y,F=d['Y'].astype(float),d['Yhat'].astype(float)
    uniq=len(np.unique(F))
    vy=Y.var()
    # best linear in f
    b=np.cov(Y,F)[0,1]/F.var(); rl=Y-Y.mean()-b*(F-F.mean()); vl=rl.var()
    # unit-slope (PPI classic: Y-f)
    vc=(Y-F).var()
    # monotone nonparametric g(f), in-sample on big pool (near-population for n_pool large)
    # use 2-fold to avoid in-sample optimism
    idx=np.random.default_rng(0).permutation(len(Y)); h=len(Y)//2; r=np.empty(len(Y))
    for a,bb in [(idx[:h],idx[h:]),(idx[h:],idx[:h])]:
        ir=IsotonicRegression(out_of_bounds='clip').fit(F[a],Y[a]); r[bb]=Y[bb]-ir.predict(F[bb])
    vi=r.var()
    print(f"{name:18s} n={len(Y):7d} uniqF={uniq:7d} VarY={vy:.4g} corr={np.corrcoef(Y,F)[0,1]:.3f} V_lin/VarY={vl/vy:.3f} V_unitslope/VarY={vc/vy:.3f} V_iso/V_lin={vi/vl:.3f} (width ratio {np.sqrt(vi/vl):.3f})")
