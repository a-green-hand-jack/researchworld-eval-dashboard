import sys; sys.path.insert(0,"/work/code")
from runner import *
procs=int(sys.argv[1]); nrep=int(sys.argv[2])
cells=[]
for tau in (0.0,0.05,0.1,0.2):
    for n in (100,400):
        for B in (8,72):
            cells.append(dict(world=dict(kind="synth",tau=tau,rho=0.8,seed=11,N=20000),n=n,algo="rs",kw=dict(B=B),method_set="rs_extras"))
run_cells(cells,nrep,"/work/results/synth_extras.parquet",procs)
