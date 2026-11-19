import time, torch, sys
import torch.nn.functional as F
from multiprocessing import Pool
def work(_):
    torch.set_num_threads(1)
    a=torch.randn(512,512); t=time.time()
    for i in range(200): a@a
    return time.time()-t
if __name__=="__main__":
    for n in (1,8,20,40):
        t=time.time()
        with Pool(n) as p: r=p.map(work,range(n))
        print(n, 'mean per-proc', sum(r)/n, 'wall', time.time()-t, flush=True)
