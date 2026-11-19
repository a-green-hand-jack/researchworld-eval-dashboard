"""Low-rank logistic latent-trait (multidimensional 2PL-style) model on a binary (models x items) matrix.

logit P(y_sj=1) = r_s + c_j + u_s . v_j .  Fitted on source models; item parameters (c, V) are then held
fixed and a target model's trait (r, u) is estimated from its responses on a subset (MAP, Gaussian prior).
"""
import numpy as np
import torch

torch.set_num_threads(1)


class Latent:
    def __init__(self, k=2, lam_item=1e-2, lam_model=1e-2, steps=300, lr=0.05, seed=0):
        self.k, self.lam_item, self.lam_model, self.steps, self.lr, self.seed = k, lam_item, lam_model, steps, lr, seed

    def fit(self, Xs):
        g = torch.Generator().manual_seed(self.seed)
        X = torch.as_tensor(Xs, dtype=torch.float32)
        S, N = X.shape
        k = self.k
        r = torch.logit(X.mean(1).clamp(0.02, 0.98)).clone().requires_grad_()
        c = torch.zeros(N, requires_grad=True)
        U = (0.1 * torch.randn(S, k, generator=g)).requires_grad_()
        V = (0.1 * torch.randn(N, k, generator=g)).requires_grad_()
        opt = torch.optim.Adam([r, c, U, V], lr=self.lr)
        for t in range(self.steps):
            opt.zero_grad()
            z = r[:, None] + c[None, :] + U @ V.T
            loss = torch.nn.functional.binary_cross_entropy_with_logits(z, X, reduction="sum") / (S * N)
            loss = loss + self.lam_item * (c.pow(2).mean() * 0.1 + V.pow(2).mean()) + self.lam_model * U.pow(2).mean()
            loss.backward()
            opt.step()
        self.c = c.detach()
        self.V = V.detach()
        self.loss = float(loss.detach())
        self.r_s, self.U_s = r.detach(), U.detach()
        return self

    def features(self):
        """Per-item features phi_j = [1, v_j] (so that logit = c_j + theta . phi_j, theta=(r,u))."""
        return torch.cat([torch.ones(self.V.shape[0], 1), self.V], 1)

    def infer(self, idx, Y, prior_var=(10.0, 1.0), iters=20):
        """MAP trait for each target. idx: item indices (n,), Y: (T, n) responses. Returns theta (T, 1+k)."""
        idx = torch.as_tensor(idx, dtype=torch.long)
        Y = torch.as_tensor(Y, dtype=torch.float32)
        Phi = self.features()[idx]                    # n x d
        c = self.c[idx]
        T, d = Y.shape[0], Phi.shape[1]
        P0 = torch.tensor([1.0 / prior_var[0]] + [1.0 / prior_var[1]] * (d - 1))
        th = torch.zeros(T, d)
        th[:, 0] = torch.logit(Y.mean(1).clamp(0.05, 0.95))
        for _ in range(iters):
            p = torch.sigmoid(th @ Phi.T + c)          # T x n
            g = (Y - p) @ Phi - th * P0
            W = p * (1 - p)                            # T x n
            H = torch.einsum("tn,nd,ne->tde", W, Phi, Phi) + torch.diag(P0)
            step = torch.linalg.solve(H, g[..., None])[..., 0]
            th = th + step.clamp(-3, 3)
        return th

    def prob_all(self, th):
        """Predicted P(y=1) for all items, (T, N)."""
        return torch.sigmoid(th @ self.features().T + self.c).numpy()
