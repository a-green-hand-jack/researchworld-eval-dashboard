"""Compute logits of three pretrained CIFAR-10 classifiers on the 10,000 CIFAR-10 test images
(HF mirror of the official test set; order verified against CIFAR-10H labels).
Usage: python extract_logits.py  -> /work/data/logits_{model}.npy"""
import sys, io
sys.path.insert(0, "/work/data/models")
import numpy as np, pandas as pd, torch
from PIL import Image
import resnet, vgg

torch.set_num_threads(16)
df = pd.read_parquet("/work/data/cifar10_hf/test.parquet")
X = np.stack([np.array(Image.open(io.BytesIO(d["bytes"])).convert("RGB")) for d in df["img"]])
y = df["label"].values
np.save("/work/data/cifar10_test_labels.npy", y)
mean = torch.tensor([0.4914, 0.4822, 0.4465]).view(1, 3, 1, 1)
std = torch.tensor([0.2470, 0.2435, 0.2616]).view(1, 3, 1, 1)
Xt = (torch.from_numpy(X).permute(0, 3, 1, 2).float() / 255 - mean) / std

specs = {
    "resnet20": (resnet.cifar10_resnet20, "cifar10_resnet20-4118986f.pt"),
    "resnet56": (resnet.cifar10_resnet56, "cifar10_resnet56.pt"),
    "vgg11_bn": (vgg.cifar10_vgg11_bn, "cifar10_vgg11_bn-eaeebf42.pt"),
}
for name, (ctor, f) in specs.items():
    m = ctor(pretrained=False)
    m.load_state_dict(torch.load(f"/work/data/models/{f}", map_location="cpu"))
    m.eval()
    out = []
    with torch.no_grad():
        for i in range(0, len(Xt), 500):
            out.append(m(Xt[i:i + 500]))
    L = torch.cat(out).numpy()
    np.save(f"/work/data/logits_{name}.npy", L)
    print(name, "acc vs CIFAR-10 label", (L.argmax(1) == y).mean())
