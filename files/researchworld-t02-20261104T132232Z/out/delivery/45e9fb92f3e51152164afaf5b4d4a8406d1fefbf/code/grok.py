"""Training harness for grokking on modular arithmetic (CPU, full batch).

One run = one (task, p, model, width, depth, lr, wd, init_scale, train_frac, seed).
Writes one JSON with the config, the logged curves and summary stats.
"""
import argparse, json, math, os, time
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

OPS = {
    "add": lambda a, b, p: (a + b) % p,
    "sub": lambda a, b, p: (a - b) % p,
    "mul": lambda a, b, p: (a * b) % p,          # includes zero; label set still 0..p-1
    "x2y2": lambda a, b, p: (a * a + b * b) % p,
}


def make_data(task, p, train_frac, seed):
    a, b = np.meshgrid(np.arange(p), np.arange(p), indexing="ij")
    a, b = a.ravel(), b.ravel()
    if task == "rand":    # E0b capacity calibration: labels are a fixed random function of (a,b); val is chance
        y = np.random.RandomState(20_000 + seed).randint(0, p, len(a))
    else:
        y = OPS[task](a, b, p)
    rng = np.random.RandomState(10_000 + seed)       # split depends on seed
    perm = rng.permutation(len(a))
    ntr = int(round(train_frac * len(a)))
    tr, va = perm[:ntr], perm[ntr:]
    X = torch.tensor(np.stack([a, b, np.full_like(a, p)], 1), dtype=torch.long)  # token p = '='
    Y = torch.tensor(y, dtype=torch.long)
    return X[tr], Y[tr], X[va], Y[va]


class Block(nn.Module):
    def __init__(self, d, heads, dmlp):
        super().__init__()
        self.h = heads
        self.qkv = nn.Linear(d, 3 * d, bias=False)
        self.o = nn.Linear(d, d, bias=False)
        self.up = nn.Linear(d, dmlp)
        self.down = nn.Linear(dmlp, d)

    def forward(self, x, last_only=False):
        # last_only: only the final position is needed (readout), so queries/residual/MLP are
        # computed for it alone -- identical output, ~3x cheaper.
        B, T, D = x.shape
        q, k, v = self.qkv(x).view(B, T, 3, self.h, D // self.h).unbind(2)
        if last_only:
            q = q[:, -1:]; x = x[:, -1:]
        att = F.scaled_dot_product_attention(q.transpose(1, 2), k.transpose(1, 2), v.transpose(1, 2))
        x = x + self.o(att.transpose(1, 2).reshape(B, -1, D))
        return x + self.down(F.relu(self.up(x)))


class TFM(nn.Module):
    """Nanda-style transformer: no LayerNorm, learned pos-emb, readout from last token."""
    def __init__(self, p, d, depth, heads=4, mlp_mult=4):
        super().__init__()
        self.emb = nn.Embedding(p + 1, d)
        nn.init.normal_(self.emb.weight, std=1 / math.sqrt(d))   # Nanda-style small embedding init
        self.pos = nn.Parameter(torch.randn(3, d) / math.sqrt(d))
        self.blocks = nn.ModuleList([Block(d, heads, mlp_mult * d) for _ in range(depth)])
        self.out = nn.Linear(d, p, bias=False)

    def forward(self, x):
        h = self.emb(x) + self.pos
        n = len(self.blocks)
        for i, b in enumerate(self.blocks):
            h = b(h, last_only=(i == n - 1))
        return self.out(h[:, -1])


class MLP(nn.Module):
    """Embeddings of a, b concatenated -> `depth` ReLU layers of width 4d -> logits."""
    def __init__(self, p, d, depth, **_):
        super().__init__()
        self.emb = nn.Embedding(p + 1, d)
        nn.init.normal_(self.emb.weight, std=1 / math.sqrt(d))
        layers, i = [], 2 * d
        for _ in range(depth):
            layers += [nn.Linear(i, 4 * d), nn.ReLU()]
            i = 4 * d
        self.net = nn.Sequential(*layers)
        self.out = nn.Linear(i, p, bias=False)

    def forward(self, x):
        h = self.emb(x[:, :2]).flatten(1)
        return self.out(self.net(h))


def build(model, p, d, depth, init_scale):
    m = {"tfm": TFM, "mlp": MLP}[model](p, d, depth)
    if init_scale != 1.0:
        with torch.no_grad():
            for prm in m.parameters():
                prm.mul_(init_scale)
    return m


def first_cross(steps, acc, thr):
    for s, a in zip(steps, acc):
        if a >= thr:
            return int(s)
    return None


def run(cfg, hook=None):
    """hook(step, model), if given, is called at every evaluation step (read-only; used by fourier.py)."""
    torch.manual_seed(cfg["seed"]); np.random.seed(cfg["seed"])
    torch.set_num_threads(cfg.get("threads", 1))
    Xtr, Ytr, Xva, Yva = make_data(cfg["task"], cfg["p"], cfg["train_frac"], cfg["seed"])
    m = build(cfg["model"], cfg["p"], cfg["width"], cfg["depth"], cfg["init_scale"])
    nparams = sum(x.numel() for x in m.parameters())
    nparams_noemb = nparams - m.emb.weight.numel()
    opt = torch.optim.AdamW(m.parameters(), lr=cfg["lr"], weight_decay=cfg["wd"], betas=(0.9, 0.98))
    log = {k: [] for k in ["step", "train_acc", "val_acc", "train_loss", "val_loss", "wnorm"]}
    t0 = time.time()
    stop_after = None
    for step in range(cfg["max_steps"] + 1):
        if step % cfg["eval_every"] == 0:
            with torch.no_grad():
                lt, lv = m(Xtr), m(Xva)
                log["step"].append(step)
                log["train_acc"].append((lt.argmax(1) == Ytr).float().mean().item())
                log["val_acc"].append((lv.argmax(1) == Yva).float().mean().item())
                log["train_loss"].append(F.cross_entropy(lt, Ytr).item())
                log["val_loss"].append(F.cross_entropy(lv, Yva).item())
                log["wnorm"].append(math.sqrt(sum((q ** 2).sum().item() for q in m.parameters())))
                if hook is not None:
                    hook(step, m)
            if log["train_loss"][-1] != log["train_loss"][-1]:
                break
            # stop `patience` steps after val acc first >= 0.999 (generalisation reached)
            gate = log["train_acc"][-1] if cfg["task"] == "rand" else log["val_acc"][-1]   # rand: stop once memorised
            if stop_after is None and gate >= cfg["stop_val"]:
                stop_after = step + cfg["patience"]
            if stop_after is not None and step >= stop_after:
                break
        loss = F.cross_entropy(m(Xtr), Ytr)
        opt.zero_grad(set_to_none=True); loss.backward(); opt.step()
    s, ta, va = log["step"], log["train_acc"], log["val_acc"]
    res = dict(
        n_params=nparams, n_params_noemb=nparams_noemb, wall=time.time() - t0, steps_run=s[-1],
        t_fit95=first_cross(s, ta, .95), t_fit99=first_cross(s, ta, .99),
        t_gen50=first_cross(s, va, .5), t_gen95=first_cross(s, va, .95), t_gen99=first_cross(s, va, .99),
        final_train_acc=ta[-1], final_val_acc=va[-1], max_val_acc=max(va),
        diverged=bool(log["train_loss"][-1] != log["train_loss"][-1]),
    )
    return dict(config=cfg, summary=res, log=log)


DEFAULT = dict(task="add", p=97, model="tfm", width=128, depth=1, lr=1e-3, wd=1.0, init_scale=1.0,
               train_frac=0.3, seed=0, max_steps=30000, eval_every=50, stop_val=0.99, patience=500, threads=1)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    for k, v in DEFAULT.items():
        ap.add_argument("--" + k, type=type(v), default=v)
    ap.add_argument("--out", default=None)
    a = vars(ap.parse_args())
    out = a.pop("out")
    r = run(a)
    print(json.dumps(r["summary"]), flush=True)
    if out:
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
        json.dump(r, open(out, "w"))
