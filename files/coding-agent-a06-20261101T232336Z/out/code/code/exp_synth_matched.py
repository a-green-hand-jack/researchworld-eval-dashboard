"""Synthetic world matched to the real cache (base accuracy, true spread, between-config correlation): used to check that the simulator reproduces the real audit."""
import sys; sys.path.insert(0,"/work/code")
from runner import *
procs=int(sys.argv[1]); nrep=int(sys.argv[2])
Wm=dict(kind="synth",tau=0.025,rho=0.87,seed=31,N=20000,a=-0.58)
ns=(50,100,200,400,800)
cells=[dict(world=Wm,n=n,algo=a,kw=kw,method_set="main") for n in ns for a,kw in [("rs",dict(B=8)),("rs",dict(B=72)),("sh",dict(B=72)),("ca",{}),("mipro",dict(B=40))]]
cells+=[dict(world=Wm,n=n,algo="rs",kw=dict(B=B),method_set="rs_extras") for n in ns for B in (8,72)]
run_cells(cells,nrep,"/work/results/synth_matched.parquet",procs)
cells=[dict(world=Wm,n=n,algo="rs",kw=dict(B=B),method_set="naive") for n in ns for B in (1,2,4,8,16,32,72)]
run_cells(cells,4*nrep,"/work/results/synth_matched_sweep.parquet",procs)
