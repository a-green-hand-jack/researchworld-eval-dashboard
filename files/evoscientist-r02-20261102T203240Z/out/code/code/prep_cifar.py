"""Convert HF parquet CIFAR-10 (uoft-cs/cifar10) to numpy; check test order against CIFAR-10H."""
import io, numpy as np, pandas as pd
from PIL import Image
for s in ["train", "test"]:
    d = pd.read_parquet(f"data/cifar/{s}.parquet")
    col = [c for c in d.columns if c.startswith("im")][0]
    X = np.stack([np.array(Image.open(io.BytesIO(b["bytes"])).convert("RGB")) for b in d[col]])
    y = d["label"].values.astype(np.int64)
    np.savez(f"data/cifar/{s}.npz", x=X, y=y)
    print(s, X.shape, np.bincount(y))
yt = np.load("data/cifar/test.npz")["y"]
h = np.load("data/c10h.npy")
print("CIFAR-10H mode == test label:", (h.argmax(1) == yt).mean())
