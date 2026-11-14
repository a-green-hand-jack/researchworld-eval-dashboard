"""Inference with the publicly released pretrained CIFAR-10 ResNet-20 (chenyaofo/pytorch-cifar-models, BSD-3-Clause).
Setup (see README):  curl -L -o data/resnet20.pt https://github.com/chenyaofo/pytorch-cifar-models/releases/download/resnet/cifar10_resnet20-4118986f.pt
                     curl -L -o data/pcm.zip https://github.com/chenyaofo/pytorch-cifar-models/archive/refs/heads/master.zip ; unzip into data/pcm
Writes data/cifar_logits_resnet20.npy (10000 x 10, CIFAR-10 test order)."""
import sys, numpy as np, torch
sys.path.insert(0, "data/pcm/pytorch-cifar-models-master")
from pytorch_cifar_models import cifar10_resnet20
torch.set_num_threads(4)
net = cifar10_resnet20(pretrained=False)
net.load_state_dict(torch.load("data/resnet20.pt", map_location="cpu"))
net.eval()
te = np.load("data/cifar/test.npz")
mean = np.array([0.4914, 0.4822, 0.4465], np.float32); std = np.array([0.2023, 0.1994, 0.2010], np.float32)
X = torch.from_numpy(((te["x"] / 255.0 - mean) / std).astype(np.float32)).permute(0, 3, 1, 2).contiguous()
out = []
with torch.no_grad():
    for k in range(0, 10000, 500):
        out.append(net(X[k:k + 500]).numpy())
L = np.concatenate(out)
print("test accuracy", (L.argmax(1) == te["y"]).mean())
np.save("data/cifar_logits_resnet20.npy", L)
