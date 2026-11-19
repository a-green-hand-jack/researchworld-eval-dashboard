import sys, json, grok
from multiprocessing import Pool
def f(c):
    r=grok.run(c); r['curve']=None if r['t_gen'] is None else r['curve'][-1:]
    return {k:r[k] for k in ('t_fit','t_gen','final_val_acc','wall','n_params')}|dict(d=c['d'],p=c['p'],lr=c['lr'],wd=c['wd'],fr=c['train_frac'])
if __name__=="__main__":
    cfgs=[]
    for d in (16,64):
        for lr,wd in ((1e-3,1.0),(3e-3,1.0),(3e-3,0.3)):
            cfgs.append(dict(p=29,train_frac=0.5,d=d,n_heads=4,lr=lr,wd=wd,steps=15000,eval_every=100,seed=0,log_curve=True))
    with Pool(6) as p:
        for r in p.imap_unordered(f,cfgs): print(r,flush=True)
