import time, torch, grok
torch.set_num_threads(1)
x,y,xv,yv=grok.make_data(97,0.4,0)
m=grok.TinyTransformer(97,64)
opt=torch.optim.AdamW(m.parameters(),1e-3,weight_decay=1.0)
import torch.nn.functional as F
t=time.time()
for i in range(20):
    l=F.cross_entropy(m(x),y);opt.zero_grad();l.backward();opt.step()
print((time.time()-t)/20,'s/step', x.shape)
