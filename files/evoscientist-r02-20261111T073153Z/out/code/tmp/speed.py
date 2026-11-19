import sys, time, os
sys.path.insert(0,'code')
os.environ['NTHREADS']='16'
import torch, numpy as np
import train_cifar as T
for w in [16,32]:
    m=T.net(w); opt=torch.optim.SGD(m.parameters(),lr=0.05,momentum=0.9)
    x=torch.randn(256,3,32,32); y=torch.randint(0,10,(256,))
    t=time.time()
    for i in range(5):
        l=torch.nn.functional.cross_entropy(m(x),y); opt.zero_grad(); l.backward(); opt.step()
    print(w,(time.time()-t)/5,'s/step ->',(time.time()-t)/5*195,'s/epoch',flush=True)
