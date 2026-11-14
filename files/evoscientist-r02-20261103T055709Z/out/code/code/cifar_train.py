"""Train a small ResNet on CIFAR-10 (hard labels, 50k train) on CPU and dump test-set logits.

Usage: python code/cifar_train.py SEED [EPOCHS] [THREADS]
Output: results/cifar_logits_seed{SEED}.npy  (10000 x 10 float32 logits, CIFAR-10 test order)
Data: data/cifar10_{train,test}.parquet (HF mirror uoft-cs/cifar10, identical to the original CIFAR-10 split/order).
CIFAR-10H labels are never used for training.
"""
import io, sys, time, os
import numpy as np, pandas as pd, torch, torch.nn as nn, torch.nn.functional as F
from PIL import Image

seed = int(sys.argv[1]); epochs = int(sys.argv[2]) if len(sys.argv) > 2 else 15
threads = int(sys.argv[3]) if len(sys.argv) > 3 else 12
torch.set_num_threads(threads); torch.manual_seed(seed); np.random.seed(seed)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(split):
    cache = f"{ROOT}/data/cifar10_{split}.npz"
    if os.path.exists(cache):
        d = np.load(cache); return d["x"], d["y"]
    df = pd.read_parquet(f"{ROOT}/data/cifar10_{split}.parquet")
    icol = [c for c in df.columns if "im" in c][0]; lcol = [c for c in df.columns if "label" in c][0]
    x = np.stack([np.array(Image.open(io.BytesIO(d["bytes"])).convert("RGB")) for d in df[icol]])
    y = df[lcol].values.astype(np.int64)
    np.savez(cache, x=x, y=y); return x, y


xtr, ytr = load("train"); xte, yte = load("test")
mean = xtr.reshape(-1, 3).mean(0) / 255; std = xtr.reshape(-1, 3).std(0) / 255
prep = lambda x: torch.tensor(((x / 255.0 - mean) / std).transpose(0, 3, 1, 2), dtype=torch.float32)
Xtr, Xte = prep(xtr), prep(xte); Ytr = torch.tensor(ytr)


def cb(i, o):
    return nn.Sequential(nn.Conv2d(i, o, 3, padding=1, bias=False), nn.BatchNorm2d(o), nn.ReLU(inplace=True))


class Res(nn.Module):
    def __init__(s, c):
        super().__init__(); s.a = cb(c, c); s.b = cb(c, c)
    def forward(s, x): return x + s.b(s.a(x))


net = nn.Sequential(cb(3, 24), nn.MaxPool2d(2), cb(24, 48), nn.MaxPool2d(2), cb(48, 96), nn.MaxPool2d(2),
                    cb(96, 128), nn.AdaptiveMaxPool2d(1), nn.Flatten(), nn.Linear(128, 10))
bs = 256; steps = epochs * (len(Xtr) // bs)
opt = torch.optim.SGD(net.parameters(), lr=0.1, momentum=0.9, nesterov=True, weight_decay=5e-4)
sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=0.08, total_steps=steps, pct_start=0.25)


def aug(x):
    n = x.shape[0]
    flip = torch.rand(n) < 0.5; x = torch.where(flip[:, None, None, None], x.flip(3), x)
    xp = F.pad(x, (4, 4, 4, 4), mode="reflect"); i, j = np.random.randint(0, 9, 2)
    return xp[:, :, i:i + 32, j:j + 32]  # one random shift per batch (cheap)


def predict(X):
    net.eval(); out = []
    with torch.no_grad():
        for k in range(0, len(X), 1000): out.append(net(X[k:k + 1000]))
    net.train(); return torch.cat(out).numpy()


t0 = time.time()
for ep in range(epochs):
    perm = torch.randperm(len(Xtr)); tl = 0
    for k in range(len(Xtr) // bs):
        idx = perm[k * bs:(k + 1) * bs]
        loss = F.cross_entropy(net(aug(Xtr[idx])), Ytr[idx])
        opt.zero_grad(); loss.backward(); opt.step(); sched.step(); tl += loss.item()
    lg = predict(Xte); acc = (lg.argmax(1) == yte).mean()
    print(f"seed {seed} ep {ep+1}/{epochs} loss {tl/(len(Xtr)//bs):.3f} test_acc {acc:.4f} t={time.time()-t0:.0f}s", flush=True)
np.save(f"{ROOT}/results/cifar_logits_seed{seed}.npy", lg.astype(np.float32))
print("saved")
