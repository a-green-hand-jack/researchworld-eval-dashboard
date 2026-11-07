"""Synthetic main sweep: all reporting methods x search algorithms x (n, tau, rho).  -> results/synth_main.parquet"""
import sys; sys.path.insert(0,"/work/code")
from runner import *
procs=int(sys.argv[1]) if len(sys.argv)>1 else 3
nrep=int(sys.argv[2]) if len(sys.argv)>2 else 300
cells=[]
for tau in (0.0,0.05,0.1,0.2):
  for rho in (0.5,0.8):
    for n in (50,100,200,400,800):
      for algo,kw in [("rs",dict(B=8)),("rs",dict(B=72)),("sh",dict(B=72)),("ca",{}),("mipro",dict(B=40))]:
        cells.append(dict(world=dict(kind="synth",tau=tau,rho=rho,seed=11,N=20000),n=n,algo=algo,kw=kw,method_set="main"))
print(len(cells),"cells")
run_cells(cells,nrep,"/work/results/synth_main.parquet",procs)
