"""Train a small CNN on CIFAR-10 (HF uoft-cs/cifar10 parquet copy) on CPU; save test logits at epochs in --save_at."""
import argparse, io, sys, time
import numpy as np, pandas as pd, torch, torch.nn as nn, torch.nn.functional as F
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument("--data", default="/hutian/data/cifar"); ap.add_argument("--epochs", type=int, default=12)
ap.add_argument("--save_at", type=int, nargs="+", default=[2, 12]); ap.add_argument("--out", default="results/e23")
ap.add_argument("--seed", type=int, default=0)
a = ap.parse_args()
torch.manual_seed(a.seed); np.random.seed(a.seed); torch.set_num_threads(2)


def load(split):
    df = pd.read_parquet(f"{a.data}/{split}-00000-of-00001.parquet")
    X = np.stack([np.array(Image.open(io.BytesIO(d["bytes"])).convert("RGB")) for d in df["img"]])
    return X.astype(np.float32) / 255, df["label"].values


Xtr, ytr = load("train"); Xte, yte = load("test")
mean, std = Xtr.mean((0, 1, 2)), Xtr.std((0, 1, 2))
prep = lambda X: torch.tensor(((X - mean) / std).transpose(0, 3, 1, 2))
Xtr_t, Xte_t = prep(Xtr), prep(Xte)
ytr_t = torch.tensor(ytr)


def block(i, o):
    return nn.Sequential(nn.Conv2d(i, o, 3, padding=1, bias=False), nn.BatchNorm2d(o), nn.ReLU(),
                         nn.Conv2d(o, o, 3, padding=1, bias=False), nn.BatchNorm2d(o), nn.ReLU(), nn.MaxPool2d(2))


net = nn.Sequential(block(3, 32), block(32, 64), block(64, 128), nn.Flatten(), nn.Dropout(0.3), nn.Linear(128 * 16, 10))
opt = torch.optim.SGD(net.parameters(), lr=0.05, momentum=0.9, weight_decay=5e-4, nesterov=True)
steps = a.epochs * (len(Xtr_t) // 128)
sched = torch.optim.lr_scheduler.OneCycleLR(opt, 0.1, total_steps=steps)
t0 = time.time()
for ep in range(1, a.epochs + 1):
    net.train()
    perm = torch.randperm(len(Xtr_t))
    for i in range(0, len(perm) - 127, 128):
        idx = perm[i:i + 128]
        x = Xtr_t[idx]
        flip = torch.rand(len(x)) < 0.5
        x = torch.where(flip[:, None, None, None], x.flip(3), x)  # random horizontal flip
        loss = F.cross_entropy(net(x), ytr_t[idx])
        opt.zero_grad(); loss.backward(); opt.step(); sched.step()
    net.eval()
    with torch.no_grad():
        lg = torch.cat([net(Xte_t[i:i + 1000]) for i in range(0, len(Xte_t), 1000)]).numpy()
    print(f"epoch {ep} acc {(lg.argmax(1) == yte).mean():.4f} t={time.time()-t0:.0f}s", flush=True)
    if ep in a.save_at:
        np.save(f"{a.out}/cnn_logits_ep{ep}.npy", lg)
np.save(f"{a.out}/cifar10_test_labels.npy", yte)
