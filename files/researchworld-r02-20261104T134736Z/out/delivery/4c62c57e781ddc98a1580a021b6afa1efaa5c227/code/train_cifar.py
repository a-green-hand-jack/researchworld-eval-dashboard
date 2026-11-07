"""Train a small CNN on CIFAR-10 (40k train / 10k holdout from the official train set; official test 10k).
Saves logits for holdout+test to results/cifar_logits.npz.  Usage: python train_cifar.py EPOCHS SEED"""
import sys, io, time, numpy as np, pandas as pd, torch, torch.nn as nn, torch.nn.functional as F
from PIL import Image
torch.set_num_threads(2)
EP, SEED = int(sys.argv[1]), int(sys.argv[2])
torch.manual_seed(SEED); rng = np.random.default_rng(SEED)

def load(path):
    df = pd.read_parquet(path)
    imgcol = [c for c in df.columns if "im" in c][0]; labcol = [c for c in df.columns if "label" in c][0]
    X = np.stack([np.array(Image.open(io.BytesIO(d["bytes"])).convert("RGB")) for d in df[imgcol]])
    return X.astype(np.float32) / 255.0, df[labcol].values.astype(np.int64)
Xa, ya = load("/hutian/data/cifar/train.parquet"); Xte, yte = load("/hutian/data/cifar/test.parquet")
perm = rng.permutation(len(Xa)); tr, ho = perm[:40000], perm[40000:]
mu, sd = Xa[tr].mean((0, 1, 2)), Xa[tr].std((0, 1, 2))
prep = lambda X: torch.tensor(((X - mu) / sd).transpose(0, 3, 1, 2))
Xtr, ytr, Xho, yho, Xt = prep(Xa[tr]), torch.tensor(ya[tr]), prep(Xa[ho]), ya[ho], prep(Xte)

def block(i, o): return nn.Sequential(nn.Conv2d(i, o, 3, padding=1, bias=False), nn.BatchNorm2d(o), nn.ReLU())
net = nn.Sequential(block(3, 32), block(32, 32), nn.MaxPool2d(2), block(32, 64), block(64, 64), nn.MaxPool2d(2),
                    block(64, 128), nn.MaxPool2d(2), nn.Flatten(), nn.Dropout(0.3), nn.Linear(128 * 16, 10))
opt = torch.optim.SGD(net.parameters(), lr=0.05, momentum=0.9, weight_decay=5e-4, nesterov=True)
steps = EP * (len(Xtr) // 128); sched = torch.optim.lr_scheduler.OneCycleLR(opt, 0.1, total_steps=steps)
def logits(X):
    net.eval(); out = []
    with torch.no_grad():
        for i in range(0, len(X), 1000): out.append(net(X[i:i + 1000]))
    return torch.cat(out).numpy()
for ep in range(EP):
    t0 = time.time(); net.train(); p = torch.randperm(len(Xtr))
    for i in range(0, len(p) - 127, 128):
        idx = p[i:i + 128]; xb = Xtr[idx]
        if True:  # random flip + shift augmentation
            fl = torch.rand(len(xb)) < 0.5; xb = torch.where(fl[:, None, None, None], xb.flip(3), xb)
            dx, dy = np.random.randint(-3, 4, 2); xb = torch.roll(xb, (int(dx), int(dy)), (2, 3))
        loss = F.cross_entropy(net(xb), ytr[idx]); opt.zero_grad(); loss.backward(); opt.step(); sched.step()
    acc = (logits(Xho).argmax(1) == yho).mean()
    print(f"epoch {ep} loss {loss.item():.3f} holdout acc {acc:.4f} {time.time()-t0:.0f}s", flush=True)
np.savez("/hutian/repo/results/cifar_logits.npz", logits_ho=logits(Xho), y_ho=yho, logits_te=logits(Xt), y_te=yte, seed=SEED)
print("done", flush=True)
