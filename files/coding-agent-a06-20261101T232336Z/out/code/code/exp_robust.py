"""Robustness of reporting methods to the shape of the config-quality distribution and to the size of the pool (synthetic, iid-config worlds)."""
import sys; sys.path.insert(0,"/work/code")
from runner import *
procs=int(sys.argv[1]); nrep=int(sys.argv[2])
cells=[]
for dist in ("normal","sparse","heavy","bimodal"):
    for K in (72,500):
        for tau in (0.05,0.15):
            for n in (100,400):
                for B in (K,):
                    for ms in ("rs_extras", "main"):
                        cells.append(dict(world=dict(kind="synth",iid=True,K=K,tau=tau,dist=dist,rho=0.8,seed=21,N=20000),n=n,algo="rs",kw=dict(B=B),method_set=ms))
print(len(cells))
run_cells(cells,nrep,"/work/results/synth_robust.parquet",procs)
