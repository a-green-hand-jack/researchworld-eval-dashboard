import sys; sys.path.insert(0,'/work/code')
import sweep
cfgs=[]
for arch in ['tf','mlp']:
  for d in [8,16,32,64,128,256]:
    for seed in [0]:
      cfgs.append(dict(arch=arch,p=59,frac=0.4,width=d,seed=seed,lr=1e-3,wd=1.0,steps=20000,eval_every=100,stop_after_gen=500))
sweep.run_grid(cfgs,'/work/results/pilot2',38)
