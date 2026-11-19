"""CIFAR-10 predictors (CPU-light; the shared sandbox gave ~1 effective core, which made CNN training infeasible:
an attempted small CNN did not finish even one epoch in 12 min and was aborted -- see paper, Limitations).
Predictors: PCA(256) -> random ReLU features (RF) -> multinomial logistic regression (L-BFGS).
  rf    : 3000 random features, trained on all 50k CIFAR-10 train images
  lin   : linear on PCA(256), trained on 2000 train images, strong ridge
Saves test-set logits (10000 x 10, CIFAR-10 test order) to data/cifar_logits_{rf,lin}.npy.
usage: python code/cifar_train.py      (needs data/cifar/{train,test}.npz from code/prep_cifar.py)"""
import os
os.environ.setdefault("OMP_NUM_THREADS", "4"); os.environ.setdefault("OPENBLAS_NUM_THREADS", "4")
import time, numpy as np
from sklearn.decomposition import PCA
from scipy.optimize import minimize
from scipy.special import logsumexp

rng = np.random.default_rng(0)
tr, te = np.load("data/cifar/train.npz"), np.load("data/cifar/test.npz")
def prep(a): return (a.reshape(len(a), -1).astype(np.float32) / 255.0)
Xtr, ytr, Xte, yte = prep(tr["x"]), tr["y"], prep(te["x"]), te["y"]
mu = Xtr.mean(0); Xtr -= mu; Xte -= mu
t0 = time.time()
pca = PCA(256, svd_solver="randomized", random_state=0).fit(Xtr[:20000])
Ptr, Pte = pca.transform(Xtr), pca.transform(Xte)
sd = Ptr.std(0); Ptr /= sd; Pte /= sd
print("pca", time.time() - t0, flush=True)

def fit_lr(F, y, lam, maxiter=300):
    n, p = F.shape; Y = np.eye(10)[y]
    def fg(w):
        W = w.reshape(p, 10); Z = F @ W; L = logsumexp(Z, 1, keepdims=True); P = np.exp(Z - L)
        loss = -(Y * (Z - L)).sum() / n + 0.5 * lam * (W ** 2).sum()
        return loss, (F.T @ (P - Y) / n + lam * W).ravel()
    r = minimize(fg, np.zeros(p * 10), jac=True, method="L-BFGS-B", options=dict(maxiter=maxiter))
    return r.x.reshape(p, 10)

# strong: random ReLU features
D = 3000
Wr = rng.normal(0, 1 / np.sqrt(256), (256, D)).astype(np.float32); br = rng.normal(0, 0.5, D).astype(np.float32)
rf = lambda P: np.maximum(P @ Wr + br, 0)
Ftr, Fte = rf(Ptr), rf(Pte)
m, s = Ftr.mean(0), Ftr.std(0) + 1e-6
Ftr, Fte = (Ftr - m) / s, (Fte - m) / s
W = fit_lr(Ftr, ytr, lam=3e-3, maxiter=200)
L = Fte @ W; print("rf acc", (L.argmax(1) == yte).mean(), time.time() - t0, flush=True)
np.save("data/cifar_logits_rf.npy", L)
# weak: linear, 2000 images
idx = rng.choice(50000, 2000, replace=False)
W = fit_lr(Ptr[idx], ytr[idx], lam=3e-2)
L = Pte @ W; print("lin acc", (L.argmax(1) == yte).mean(), time.time() - t0, flush=True)
np.save("data/cifar_logits_lin.npy", L)
