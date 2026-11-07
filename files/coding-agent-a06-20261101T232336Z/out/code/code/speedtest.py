import sys, time, numpy as np
sys.path.insert(0,"/work/code")
from common import *
from scorer import Scorer
model, thr = sys.argv[1], int(sys.argv[2])
df = load_test(); val = load_val(); ds = demo_sets(val)
ids = population_ids(4000)
sc = Scorer(model, n_threads=thr)
lens=[len(sc.tok(fmt_question(df.iloc[i],0)[0])) for i in ids[:300]]
print("mean q tokens", np.mean(lens), np.percentile(lens,[50,90,99,100]))
for cfg in [dict(instr=2,fmt=1,demo=0), dict(instr=2,fmt=1,demo=4)]:
    sc.set_prefix(build_prefix(cfg,val,ds)); print("prefix toks",len(sc.prefix_toks))
    t=time.time(); acc=[]
    for i in ids[:40]:
        r=df.iloc[i]; q,c=fmt_question(r,cfg["fmt"]); lp=sc.score(q,c,len(r["options"])); acc.append(int(np.argmax(lp)==r["answer_index"]))
    dt=time.time()-t; print(cfg,"acc",np.mean(acc),"s/item",dt/40)
