"""Core library: modular-arithmetic data, small transformer, full-batch AdamW training with
grokking metrics.  CPU only.  Everything is deterministic given (seed, config)."""
import math, time, json
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


def make_data(p, train_frac, seed, op="add"):
    """All p^2 pairs (a,b); label=(a+b)%p (or a*b for 'mul' on nonzero residues).
    Input tokens: [a, b, '=' (id p)].  Returns train/val tensors (random split)."""
    a = torch.arange(p).repeat_interleave(p)
    b = torch.arange(p).repeat(p)
    if op == "add":
        y = (a + b) % p
    elif op == "sub":
        y = (a - b) % p
    elif op == "mul":
        y = (a * b) % p
    else:
        raise ValueError(op)
    x = torch.stack([a, b, torch.full_like(a, p)], 1)
    g = torch.Generator().manual_seed(10_000 + seed)
    perm = torch.randperm(p * p, generator=g)
    n_tr = int(round(train_frac * p * p))
    tr, va = perm[:n_tr], perm[n_tr:]
    return x[tr], y[tr], x[va], y[va]


class Block(nn.Module):
    def __init__(self, d, n_heads, d_mlp):
        super().__init__()
        self.h = n_heads
        self.qkv = nn.Linear(d, 3 * d, bias=False)
        self.o = nn.Linear(d, d, bias=False)
        self.up = nn.Linear(d, d_mlp)
        self.down = nn.Linear(d_mlp, d)

    def forward(self, x):
        B, T, D = x.shape
        q, k, v = self.qkv(x).view(B, T, 3, self.h, D // self.h).permute(2, 0, 3, 1, 4)
        a = F.scaled_dot_product_attention(q, k, v, is_causal=True)
        x = x + self.o(a.transpose(1, 2).reshape(B, T, D))
        return x + self.down(F.relu(self.up(x)))


class TinyTransformer(nn.Module):
    """Nanda-style: no LayerNorm, learned pos-emb, ReLU MLP, untied unembedding."""
    def __init__(self, p, d, n_layers=1, n_heads=4, mlp_mult=4, init_scale=1.0):
        super().__init__()
        self.emb = nn.Embedding(p + 1, d)
        self.pos = nn.Parameter(torch.randn(3, d) / math.sqrt(d))
        self.blocks = nn.ModuleList([Block(d, n_heads, mlp_mult * d) for _ in range(n_layers)])
        self.out = nn.Linear(d, p, bias=False)
        if init_scale != 1.0:
            with torch.no_grad():
                for prm in self.parameters():
                    prm.mul_(init_scale)

    def forward(self, x):
        h = self.emb(x) + self.pos
        for b in self.blocks:
            h = b(h)
        return self.out(h[:, -1])


class OneHotMLP(nn.Module):
    """Second architecture: embeddings of a and b concatenated -> ReLU MLP (width = hidden units)."""
    def __init__(self, p, d, n_layers=1, **kw):
        super().__init__()
        self.emb = nn.Embedding(p, d)
        self.net = nn.Sequential(nn.Linear(2 * d, 4 * d), nn.ReLU(), nn.Linear(4 * d, 4 * d), nn.ReLU(),
                                 nn.Linear(4 * d, p)) if n_layers == 2 else \
            nn.Sequential(nn.Linear(2 * d, 4 * d), nn.ReLU(), nn.Linear(4 * d, p))

    def forward(self, x):
        e = self.emb(x[:, :2])
        return self.net(e.flatten(1))


def n_params(m):
    return sum(q.numel() for q in m.parameters())


@torch.no_grad()
def evaluate(model, x, y):
    lo = model(x)
    return (lo.argmax(-1) == y).float().mean().item(), F.cross_entropy(lo, y).item()


def run(cfg):
    """cfg keys: p, train_frac, seed, d, arch, n_layers, lr, wd, steps, eval_every, op, init_scale,
    thr (accuracy threshold, default .99), patience (consecutive evals val>=thr to stop)."""
    c = dict(p=97, train_frac=0.4, seed=0, d=64, arch="tf", n_layers=1, n_heads=4, lr=1e-3, wd=1.0,
             steps=30000, eval_every=50, op="add", init_scale=1.0, thr=0.99, patience=6,
             betas=(0.9, 0.98), log_curve=True)
    c.update(cfg)
    torch.set_num_threads(1)
    torch.manual_seed(c["seed"])
    np.random.seed(c["seed"])
    xtr, ytr, xva, yva = make_data(c["p"], c["train_frac"], c["seed"], c["op"])
    M = TinyTransformer if c["arch"] == "tf" else OneHotMLP
    model = M(c["p"], c["d"], n_layers=c["n_layers"], n_heads=c["n_heads"], init_scale=c["init_scale"]) \
        if c["arch"] == "tf" else M(c["p"], c["d"], n_layers=c["n_layers"])
    opt = torch.optim.AdamW(model.parameters(), lr=c["lr"], weight_decay=c["wd"], betas=tuple(c["betas"]))
    t0 = time.time()
    curve = []
    t_fit = t_gen = None          # first eval step where train/val acc >= thr (t_fit: and stays, see below)
    streak_tr = streak_va = 0
    fit_first = gen_first = None
    for step in range(0, c["steps"] + 1):
        if step % c["eval_every"] == 0:
            model.eval()
            tra, trl = evaluate(model, xtr, ytr)
            vaa, val = evaluate(model, xva, yva)
            wn = math.sqrt(sum((q ** 2).sum().item() for q in model.parameters()))
            model.train()
            if c["log_curve"]:
                curve.append((step, tra, trl, vaa, val, wn))
            streak_tr = streak_tr + 1 if tra >= c["thr"] else 0
            streak_va = streak_va + 1 if vaa >= c["thr"] else 0
            if streak_tr == 1 and fit_first is None:
                fit_first = step
            if streak_tr >= 3 and t_fit is None:    # sustained 3 consecutive evals
                t_fit = fit_first
            if streak_va == 1 and gen_first is None:
                gen_first = step
            if streak_va >= c["patience"] and t_gen is None:
                t_gen = gen_first
                break
            if not math.isfinite(trl):
                break
        loss = F.cross_entropy(model(xtr), ytr)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
    # fall back: if train fit was recorded only through val-break, fit streak may be incomplete
    if t_fit is None and fit_first is not None and t_gen is not None:
        t_fit = fit_first
    best_val = max(r[3] for r in curve) if curve else None
    res = dict(cfg=c, n_params=n_params(model), n_train=len(ytr), t_fit=t_fit, t_gen=t_gen,
               final_train_acc=tra, final_val_acc=vaa, max_val_acc=best_val,
               wall=time.time() - t0, steps_run=step, curve=curve if c["log_curve"] else None)
    return res


if __name__ == "__main__":
    import sys
    d = int(sys.argv[1]) if len(sys.argv) > 1 else 64
    r = run(dict(d=d, steps=int(sys.argv[2]) if len(sys.argv) > 2 else 3000))
    print({k: v for k, v in r.items() if k not in ("curve", "cfg")})
