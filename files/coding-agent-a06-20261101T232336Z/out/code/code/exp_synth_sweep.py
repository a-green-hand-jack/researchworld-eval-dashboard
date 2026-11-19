"""Dense synthetic sweep of the status-quo optimism over n, B, tau, rho and base accuracy (naive report only)."""
import sys; sys.path.insert(0,"/work/code")
from runner import *
procs=int(sys.argv[1]); nrep=int(sys.argv[2])
cells=[]
for a in (-1.0,-0.4,0.5):
  for tau in (0.0,0.03,0.06,0.1,0.2):
    for rho in ((0.5,0.8) if a==-0.4 else (0.8,)):
      for n in (50,100,200,400,800):
        for B in (1,2,4,8,16,32,72):
            cells.append(dict(world=dict(kind="synth",tau=tau,rho=rho,seed=11,N=20000,a=a),n=n,algo="rs",kw=dict(B=B),method_set="naive"))
print(len(cells))
run_cells(cells,nrep,"/work/results/synth_sweep.parquet",procs)
