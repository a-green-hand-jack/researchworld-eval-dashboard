"""Multidimensional 2PL IRT fitted on source models (torch, CPU); MAP ability estimation for new models."""
import numpy as np, torch

torch.set_num_threads(2)


class IRT:
    def __init__(self, d=4, lam_theta=1.0, lam_a=0.05, steps=300, lr=0.05, seed=0):
        self.d, self.lt, self.la, self.steps, self.lr, self.seed = d, lam_theta, lam_a, steps, lr, seed

    def fit(self, S):
        g = torch.Generator().manual_seed(self.seed)
        Y = torch.as_tensor(S, dtype=torch.float32)
        M, N = Y.shape
        q = Y.mean(0).clamp(0.02, 0.98)
        b = torch.log(q / (1 - q)).clone().requires_grad_(True)
        th = (0.1 * torch.randn(M, self.d, generator=g)).requires_grad_(True)
        A = (0.1 * torch.randn(N, self.d, generator=g)).requires_grad_(True)
        # fix scale of the first dimension: global ability (all items load positively at init)
        with torch.no_grad():
            th[:, 0] = (Y.mean(1) - Y.mean()) * 4
            A[:, 0] = 0.5
        opt = torch.optim.Adam([b, th, A], lr=self.lr)
        for _ in range(self.steps):
            opt.zero_grad()
            z = th @ A.T + b
            loss = torch.nn.functional.binary_cross_entropy_with_logits(z, Y, reduction="sum") / (M * N)
            loss = loss + (self.lt * (th ** 2).sum() / (M * N) + self.la * (A ** 2).sum() / (M * N))
            loss.backward(); opt.step()
        self.A, self.b, self.th_src = A.detach(), b.detach(), th.detach()
        self.train_loss = float(loss.detach())
        return self

    def ability(self, idx, Yobs, steps=150, lr=0.1):
        """MAP ability for target rows given observed responses on items idx. Yobs: (T, n)."""
        Y = torch.as_tensor(Yobs, dtype=torch.float32)
        A, b = self.A[idx], self.b[idx]
        th = torch.zeros(Y.shape[0], self.d, requires_grad=True)
        opt = torch.optim.Adam([th], lr=lr)
        for _ in range(steps):
            opt.zero_grad()
            z = th @ A.T + b
            loss = torch.nn.functional.binary_cross_entropy_with_logits(z, Y, reduction="sum") + self.lt * (th ** 2).sum()
            loss.backward(); opt.step()
        return th.detach()

    def prob(self, th):
        return torch.sigmoid(th @ self.A.T + self.b).numpy()
