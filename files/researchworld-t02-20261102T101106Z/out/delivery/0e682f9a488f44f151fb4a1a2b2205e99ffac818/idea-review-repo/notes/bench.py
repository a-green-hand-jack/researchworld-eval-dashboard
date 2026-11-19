import torch, time, sys
torch.set_num_threads(1)
p=int(sys.argv[1]); d=int(sys.argv[2]); frac=0.3
torch.manual_seed(0)
a=torch.arange(p).repeat_interleave(p); b=torch.arange(p).repeat(p); y=(a+b)%p
perm=torch.randperm(p*p); n=int(frac*p*p); tr=perm[:n]
class M(torch.nn.Module):
    def __init__(s,p,d,L=1,h=4):
        super().__init__()
        s.e=torch.nn.Embedding(p+1,d); s.pos=torch.nn.Parameter(torch.randn(3,d)*.02)
        l=torch.nn.TransformerEncoderLayer(d,h,4*d,0.0,batch_first=True,norm_first=True)
        s.t=torch.nn.TransformerEncoder(l,L); s.o=torch.nn.Linear(d,p)
    def forward(s,x):
        z=s.e(x)+s.pos; return s.o(s.t(z)[:,-1])
m=M(p,d); opt=torch.optim.AdamW(m.parameters(),1e-3,weight_decay=1.0)
x=torch.stack([a,b,torch.full_like(a,p)],1)
t=time.time(); N=30
for i in range(N):
    l=torch.nn.functional.cross_entropy(m(x[tr]),y[tr]); opt.zero_grad(); l.backward(); opt.step()
dt=(time.time()-t)/N
print(p,d,sum(q.numel() for q in m.parameters()),"params, s/step",round(dt,4))
