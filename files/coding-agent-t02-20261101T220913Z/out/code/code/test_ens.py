import sys; sys.path.insert(0,'/work/code')
import grok, numpy as np
cfg=dict(arch='tf',p=37,frac=0.5,width=16,seed=0,lr=1e-3,wd=1.0,steps=300,eval_every=50,fine_until=0)
outs=grok.run_ens(cfg,[0,1,2])
for sd,o in zip([0,1,2],outs):
    r=grok.run(dict(cfg,seed=sd))
    for k in ['tr_loss','va_loss','wnorm']:
        print(sd,k,np.max(np.abs(np.array(o['curves'][k])-np.array(r['curves'][k]))), r['curves'][k][-1])
