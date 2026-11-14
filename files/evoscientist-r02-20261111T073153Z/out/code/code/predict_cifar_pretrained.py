"""Use a publicly available pretrained CIFAR-10 ResNet (chenyaofo/pytorch-cifar-models, trained on the CIFAR-10
*training* set only) to compute test-set logits. Output: data/cifar_test_logits.npy, data/cifar_test_labels.npy
Usage: python code/predict_cifar_pretrained.py [model_name]  (default cifar10_resnet56)"""
import sys, numpy as np, torch
torch.set_num_threads(8)
name = sys.argv[1] if len(sys.argv) > 1 else "cifar10_resnet56"
model = torch.hub.load("chenyaofo/pytorch-cifar-models", name, pretrained=True, trust_repo=True).eval()
d = np.load("data/cifar10_uint8.npz")
Xte, yte = d["Xte"].astype(np.float32) * (1.0 / 255.0), d["yte"]
mean = np.array([0.4914, 0.4822, 0.4465], np.float32)[None, :, None, None]
std = np.array([0.2470, 0.2435, 0.2616], np.float32)[None, :, None, None]
X = torch.tensor((Xte.transpose(0, 3, 1, 2) - mean) * (1.0 / std))
with torch.no_grad():
    lg = torch.cat([model(X[i:i + 500]) for i in range(0, 10000, 500)]).numpy()
print(name, "test acc", (lg.argmax(1) == yte).mean())
np.save("data/cifar_test_logits.npy", lg); np.save("data/cifar_test_labels.npy", yte)
