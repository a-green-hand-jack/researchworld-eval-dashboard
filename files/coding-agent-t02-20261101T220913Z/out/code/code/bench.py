import sys,time; sys.path.insert(0,'/work/code')
import torch, grok
torch.set_num_threads(1)
import torch.nn.functional as F
for p,frac in [(59,0.4),(37,0.5)]:
  for d in [16,32,64,128]:
    (ta,tb,ty),_=grok.make_data(p,frac,0)
    m=grok.build(dict(arch='tf',p=p,width=d)); opt=torch.optim.AdamW(m.parameters(),lr=1e-3,weight_decay=1)
    for i in range(3):
        l=F.cross_entropy(m(ta,tb),ty); opt.zero_grad(); l.backward(); opt.step()
    t=time.time()
    for i in range(30):
        l=F.cross_entropy(m(ta,tb),ty); opt.zero_grad(); l.backward(); opt.step()
    print(p,frac,d,ta.shape[0],(time.time()-t)/30,flush=True)
