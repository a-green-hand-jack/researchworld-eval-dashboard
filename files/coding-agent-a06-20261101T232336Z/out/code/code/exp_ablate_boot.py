"""Ablation: number of bootstrap replays and the .632 variant (real pool)."""
import sys; sys.path.insert(0,"/work/code")
from runner import *
procs=int(sys.argv[1]); nrep=int(sys.argv[2])
W=dict(kind="real",cache="/work/cache/q15")
cells=[dict(world=W,n=n,algo=a,kw=kw,method_set="main",nboot=nb,wr=True) for n in (100,400) for a,kw in (("rs",dict(B=72)),("mipro",dict(B=40))) for nb in (10,25,100,300)]
run_cells(cells,nrep,"/work/results/ablate_boot.parquet",procs)
