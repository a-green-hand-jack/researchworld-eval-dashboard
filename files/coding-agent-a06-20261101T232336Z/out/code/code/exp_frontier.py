"""Hold-out fraction frontier: reporting error of the hold-out estimate vs. quality of the configuration that is deployed (search on fewer items)."""
import sys; sys.path.insert(0,"/work/code")
from runner import *
procs=int(sys.argv[1]); nrep=int(sys.argv[2])
W=dict(kind="real",cache="/work/cache/q15"); Wm=dict(kind="synth",tau=0.1,rho=0.8,seed=11,N=20000)
cells=[]
for w in (W,Wm):
  for n in (100,400):
    for algo,kw in (("rs",dict(B=72)),("mipro",dict(B=40))):
      for rh in (0.1,0.2,0.3,0.5):
        cells.append(dict(world=w,n=n,algo=algo,kw=kw,method_set="main",rho_hold=rh,wr=(w["kind"]=="real"),nboot=20))
run_cells(cells,nrep,"/work/results/frontier.parquet",procs)
