"""Convert the HF mirror (uoft-cs/cifar10 parquet) of CIFAR-10 into uint8 npz arrays and check that the test order
matches the CIFAR-10H annotation order (argmax of human proportions vs true label)."""
import io, numpy as np, pandas as pd
from PIL import Image
def conv(f):
    d = pd.read_parquet(f)
    imgcol = [c for c in d.columns if "im" in c][0]; labcol = [c for c in d.columns if "label" in c][0]
    X = np.stack([np.array(Image.open(io.BytesIO(r["bytes"])).convert("RGB")) for r in d[imgcol]])
    return X, d[labcol].to_numpy()
Xtr, ytr = conv("data/cifar10_train.parquet"); Xte, yte = conv("data/cifar10_test.parquet")
print(Xtr.shape, Xte.shape, np.bincount(ytr), np.bincount(yte))
H = np.load("data/cifar10h-probs.npy")
print("agreement argmax(CIFAR-10H) vs HF test labels:", (H.argmax(1) == yte).mean())
np.savez("data/cifar10_uint8.npz", Xtr=Xtr, ytr=ytr, Xte=Xte, yte=yte)
