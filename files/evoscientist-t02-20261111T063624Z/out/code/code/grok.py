"""Core library: modular-arithmetic data, small models, full-batch AdamW training with
grokking metrics (t_train, t_val). CPU only, single thread per run.

Metric definitions (used everywhere in the paper):
  t_train : first evaluation step with train accuracy >= ACC_THR (0.99)
  t_val   : first evaluation step with held-out accuracy >= ACC_THR (0.99)
  censored: run hit max_steps without reaching the threshold (value = max_steps, a lower bound)
"""
import math, time, json, os
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

ACC_THR = 0.99


# ----------------------------------------------------------------------------- data
def make_data(p, op, train_frac, seed):
    """All p^2 pairs (a,b); label from op. Random train/val split with `seed`."""
    a = torch.arange(p).repeat_interleave(p)
    b = torch.arange(p).repeat(p)
    if op == "add":
        y = (a + b) % p
    elif op == "sub":
        y = (a - b) % p
    elif op == "mul":
        y = (a * b) % p
    elif op == "sq":  # a^2 + b^2
        y = (a * a + b * b) % p
    else:
        raise ValueError(op)
    g = torch.Generator().manual_seed(10_000 + seed)
    perm = torch.randperm(p * p, generator=g)
    ntr = int(round(train_frac * p * p))
    tr, va = perm[:ntr], perm[ntr:]
    return (a[tr], b[tr], y[tr]), (a[va], b[va], y[va])


# ----------------------------------------------------------------------------- models
class TF1(nn.Module):
    """Pre-norm-free 1-layer (or L-layer) transformer on tokens [a, b, '='], read out at '='.
    d_model=d, heads=4 (or fewer if d small), d_mlp=4d, ReLU, no LayerNorm (as in Nanda et al.)."""

    def __init__(self, p, d, layers=1, heads=4, sigma=1.0):
        super().__init__()
        self.p, self.d = p, d
        h = min(heads, d)
        while d % h:
            h -= 1
        self.h = h
        self.emb = nn.Parameter(torch.randn(p + 1, d) * sigma / math.sqrt(d))
        self.pos = nn.Parameter(torch.randn(3, d) * sigma / math.sqrt(d))
        self.blocks = nn.ModuleList()
        for _ in range(layers):
            self.blocks.append(nn.ModuleDict(dict(
                qkv=nn.Linear(d, 3 * d, bias=False), o=nn.Linear(d, d, bias=False),
                m1=nn.Linear(d, 4 * d), m2=nn.Linear(4 * d, d))))
        self.unemb = nn.Linear(d, p, bias=False)
        self._init(sigma)

    def _init(self, sigma):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, sigma / math.sqrt(m.in_features))
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

    def forward(self, a, b):
        B = a.shape[0]
        eq = torch.full_like(a, self.p)
        x = self.emb[torch.stack([a, b, eq], 1)] + self.pos  # B,3,d
        for blk in self.blocks:
            q, k, v = blk["qkv"](x).chunk(3, -1)
            hd = self.d // self.h
            sp = lambda t: t.view(B, 3, self.h, hd).transpose(1, 2)
            att = F.scaled_dot_product_attention(sp(q), sp(k), sp(v), is_causal=True)
            x = x + blk["o"](att.transpose(1, 2).reshape(B, 3, self.d))
            x = x + blk["m2"](F.relu(blk["m1"](x)))
        return self.unemb(x[:, -1])


class MLP(nn.Module):
    """Embed a,b (dim w each), concat -> `layers` hidden ReLU layers of width w -> p logits."""

    def __init__(self, p, w, layers=2, sigma=1.0):
        super().__init__()
        self.p = p
        self.emb = nn.Parameter(torch.randn(p, w) * sigma)  # unit-variance entries
        dims = [2 * w] + [w] * layers
        self.hid = nn.ModuleList([nn.Linear(dims[i], dims[i + 1]) for i in range(layers)])
        self.out = nn.Linear(w, p, bias=False)
        for m in list(self.hid) + [self.out]:
            nn.init.normal_(m.weight, 0, sigma * math.sqrt(2.0 / m.in_features) if m is not self.out
                            else sigma / math.sqrt(m.in_features))
            if m.bias is not None:
                nn.init.zeros_(m.bias)

    def forward(self, a, b):
        x = torch.cat([self.emb[a], self.emb[b]], -1)
        for l in self.hid:
            x = F.relu(l(x))
        return self.out(x)


def build(arch, p, width, layers, sigma):
    if arch == "tf":
        return TF1(p, width, layers=layers, sigma=sigma)
    if arch == "mlp":
        return MLP(p, width, layers=layers, sigma=sigma)
    raise ValueError(arch)


def n_params(m):
    return sum(t.numel() for t in m.parameters())


# ----------------------------------------------------------------------------- training
def eval_steps(max_steps):
    s = set(range(0, 500, 10)) | set(range(500, 5000, 50)) | set(range(5000, max_steps + 1, 200))
    s.add(max_steps)
    return sorted(x for x in s if x <= max_steps)


@torch.no_grad()
def evaluate(model, data):
    a, b, y = data
    lo = model(a, b)
    return (lo.argmax(-1) == y).float().mean().item(), F.cross_entropy(lo, y).item()


def run(cfg):
    """cfg keys: arch,p,op,width,layers,train_frac,seed,lr,wd,sigma,max_steps,
    shuffle_labels(bool: memorisation probe), batch (0=full), tail (extra steps after t_val)."""
    c = dict(arch="tf", p=97, op="add", width=128, layers=1, train_frac=0.3, seed=0, lr=1e-3,
             wd=1.0, sigma=1.0, max_steps=30000, shuffle_labels=False, batch=0, tail=300,
             stop_on_val=True, record_curve=True)
    c.update(cfg)
    torch.set_num_threads(1)
    torch.manual_seed(c["seed"])
    np.random.seed(c["seed"])
    tr, va = make_data(c["p"], c["op"], c["train_frac"], c["seed"])
    if c["shuffle_labels"]:  # random labels on train set: pure-memorisation probe
        g = torch.Generator().manual_seed(777 + c["seed"])
        tr = (tr[0], tr[1], torch.randint(0, c["p"], tr[2].shape, generator=g))
    model = build(c["arch"], c["p"], c["width"], c["layers"], c["sigma"])
    opt = torch.optim.AdamW(model.parameters(), lr=c["lr"], weight_decay=c["wd"], betas=(0.9, 0.98))
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / 10))
    sched_steps = set(eval_steps(c["max_steps"]))
    t_train = t_val = None
    curve = []
    t0 = time.time()
    n = tr[0].shape[0]
    stop_at = None
    nonfinite = False
    for step in range(c["max_steps"] + 1):
        if step in sched_steps:
            model.eval()
            tra, trl = evaluate(model, tr)
            vaa, val = evaluate(model, va)
            model.train()
            wn = math.sqrt(sum((t.detach() ** 2).sum().item() for t in model.parameters()))
            if c["record_curve"]:
                curve.append([step, tra, trl, vaa, val, wn])
            if t_train is None and tra >= ACC_THR:
                t_train = step
            if t_val is None and vaa >= ACC_THR:
                t_val = step
                stop_at = step + c["tail"]
            if not (math.isfinite(trl) and math.isfinite(val)):
                nonfinite = True
                break
            if c["stop_on_val"] and stop_at is not None and step >= stop_at:
                break
            if c["shuffle_labels"] and t_train is not None:
                break
        if step == c["max_steps"]:
            break
        if c["batch"] and c["batch"] < n:
            idx = torch.randint(0, n, (c["batch"],))
            a, b, y = tr[0][idx], tr[1][idx], tr[2][idx]
        else:
            a, b, y = tr
        loss = F.cross_entropy(model(a, b), y)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
        sched.step()
    res = dict(cfg=c, n_params=n_params(model), t_train=t_train, t_val=t_val,
               train_cens=t_train is None, val_cens=t_val is None, nonfinite=nonfinite,
               final=curve[-1] if curve else None, secs=time.time() - t0)
    if c["record_curve"]:
        res["curve"] = curve
    return res
