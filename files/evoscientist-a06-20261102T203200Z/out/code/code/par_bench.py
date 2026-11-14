import torch,time,sys
from multiprocessing import Process, Queue
def w(q):
    torch.set_num_threads(1)
    a=torch.randn(1024,1024);b=torch.randn(1024,1024); a@b
    t=time.time()
    for _ in range(40): a@b
    q.put(40*2*1024**3/(time.time()-t)/1e9)
if __name__=="__main__":
    for n in [1,4,8,16,32]:
        q=Queue(); ps=[Process(target=w,args=(q,)) for _ in range(n)]
        [p.start() for p in ps]; r=[q.get() for _ in ps]; [p.join() for p in ps]
        print(n,"procs: per-proc",round(sum(r)/n,1),"total",round(sum(r),1),flush=True)
