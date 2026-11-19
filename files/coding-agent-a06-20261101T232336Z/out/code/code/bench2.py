import sys, time, numpy as np
sys.path.insert(0,"/work/code")
from common import *
from scorer import Scorer
model, thr = sys.argv[1], int(sys.argv[2])
df = load_test(); val = load_val(); ds = demo_sets(val)
ids = population_ids(4000)
sc = Scorer(model, n_threads=thr)
cfg=dict(instr=2,fmt=1,demo=0)
sc.set_prefix(build_prefix(cfg,val,ds))
t=time.time(); acc=[]; ntok=0
for i in ids[:30]:
    r=df.iloc[i]; q,c=fmt_question(r,cfg["fmt"]); lp=sc.score(q,c,len(r["options"])); acc.append(int(np.argmax(lp)==r["answer_index"])); ntok+=len(sc.tok(q))
dt=time.time()-t; print(model.split("/")[-1],thr,"acc",np.mean(acc),"s/item",dt/30,"tok/s",ntok/dt)
