"""Core library: synthetic modular-arithmetic data, small models, full-batch AdamW training with
logging of train/val accuracy, loss, parameter norm. CPU, single thread per run."""
import math, time, json, os
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

torch.set_num_threads(1)

# ---------------------------------------------------------------- data
def make_data(p, op, frac, seed):
    """All p^2 pairs (a,b); label = a op b mod p. Random train/val split with train fraction `frac`.
    op in {'add','sub','mul'(over a,b in 1..p-1 handled by plain a*b mod p over 0..p-1),'sq' (a^2+b^2)}"""
    a, b = np.meshgrid(np.arange(p), np.arange(p), indexing="ij")
    a, b = a.ravel(), b.ravel()
    if op == "add": y = (a + b) % p
    elif op == "sub": y = (a - b) % p
    elif op == "mul": y = (a * b) % p
    elif op == "sq": y = (a * a + b * b) % p
    else: raise ValueError(op)
    rng = np.random.RandomState(seed)
    perm = rng.permutation(p * p)
    ntr = int(round(frac * p * p))
    tr, va = perm[:ntr], perm[ntr:]
    X = torch.tensor(np.stack([a, b], 1), dtype=torch.long)
    Y = torch.tensor(y, dtype=torch.long)
    return X[tr], Y[tr], X[va], Y[va]

# ---------------------------------------------------------------- models
class Block(nn.Module):
    def __init__(self, d, nh, dff):
        super().__init__()
        self.nh, self.d = nh, d
        self.qkv = nn.Linear(d, 3 * d, bias=False)
        self.o = nn.Linear(d, d, bias=False)
        self.w1 = nn.Linear(d, dff)
        self.w2 = nn.Linear(dff, d)
    def forward(self, x):
        B, T, d = x.shape
        q, k, v = self.qkv(x).view(B, T, 3, self.nh, d // self.nh).unbind(2)
        q, k, v = [t.transpose(1, 2) for t in (q, k, v)]
        att = F.scaled_dot_product_attention(q, k, v)  # no causal mask: 3 tokens, predict at last
        x = x + self.o(att.transpose(1, 2).reshape(B, T, d))
        return x + self.w2(F.relu(self.w1(x)))

class TransformerLM(nn.Module):
    """Nanda-style: tokens (a, b, '='), L blocks, no LayerNorm, ReLU MLP (dff=4d), unembed at '=' position."""
    def __init__(self, p, d, L=1, nh=None, init_scale=1.0):
        super().__init__()
        nh = nh or max(1, min(4, d // 8))
        while d % nh: nh -= 1
        self.p = p
        self.emb = nn.Embedding(p + 1, d)
        self.pos = nn.Parameter(torch.randn(3, d) / math.sqrt(d))
        self.blocks = nn.ModuleList([Block(d, nh, 4 * d) for _ in range(L)])
        self.unemb = nn.Linear(d, p, bias=False)
        self.apply(self._init)
        if init_scale != 1.0:
            with torch.no_grad():
                for prm in self.parameters(): prm.mul_(init_scale)
    @staticmethod
    def _init(m):
        if isinstance(m, nn.Linear):
            nn.init.normal_(m.weight, std=1 / math.sqrt(m.in_features))
            if m.bias is not None: nn.init.zeros_(m.bias)
        elif isinstance(m, nn.Embedding):
            nn.init.normal_(m.weight, std=1.0)
    def forward(self, X):
        B = X.shape[0]
        eq = torch.full((B, 1), self.p, dtype=torch.long)
        x = self.emb(torch.cat([X, eq], 1)) + self.pos
        for blk in self.blocks: x = blk(x)
        return self.unemb(x[:, -1])

class MLP(nn.Module):
    """Embedding of each operand -> concat -> L hidden ReLU layers of width h -> logits."""
    def __init__(self, p, h, de=None, L=1, init_scale=1.0):
        super().__init__()
        de = de or h // 2 if (de or h // 2) else 1
        de = max(de, 1)
        self.emb = nn.Embedding(p, de)
        dims = [2 * de] + [h] * L
        self.hid = nn.ModuleList([nn.Linear(dims[i], dims[i + 1]) for i in range(L)])
        self.out = nn.Linear(h, p, bias=False)
        self.apply(TransformerLM._init)
        if init_scale != 1.0:
            with torch.no_grad():
                for prm in self.parameters(): prm.mul_(init_scale)
    def forward(self, X):
        x = self.emb(X).flatten(1)
        for l in self.hid: x = F.relu(l(x))
        return self.out(x)

def build(arch, p, width, depth=1, init_scale=1.0):
    if arch == "tf": return TransformerLM(p, width, L=depth, init_scale=init_scale)
    if arch == "mlp": return MLP(p, width, de=min(width, 128), L=depth, init_scale=init_scale)
    raise ValueError(arch)

def nparams(m): return sum(x.numel() for x in m.parameters())

# ---------------------------------------------------------------- training
@torch.no_grad()
def evaluate(model, X, Y):
    lg = model(X)
    return F.cross_entropy(lg, Y).item(), (lg.argmax(-1) == Y).float().mean().item()

def run(cfg):
    """cfg keys: arch,p,op,frac,width,depth,lr,wd,seed,data_seed,steps,eval_every,init_scale,
    betas, stop_after (steps after val acc>=thr to stop), thr. Returns summary dict with curves."""
    c = dict(arch="tf", p=97, op="add", frac=0.3, width=128, depth=1, lr=1e-3, wd=1.0, seed=0,
             data_seed=0, steps=30000, eval_every=50, init_scale=1.0, beta2=0.98, thr=0.99,
             stop_extra=500, randlabel=False)
    c.update(cfg)
    torch.manual_seed(c["seed"]); np.random.seed(c["seed"])
    Xtr, Ytr, Xva, Yva = make_data(c["p"], c["op"], c["frac"], c["data_seed"])
    if c.get("randlabel"):  # random labels on the training inputs (capacity probe); val set untouched
        g = torch.Generator().manual_seed(1000 + c["data_seed"]); Ytr = torch.randint(0, c["p"], Ytr.shape, generator=g)
    model = build(c["arch"], c["p"], c["width"], c["depth"], c["init_scale"])
    opt = torch.optim.AdamW(model.parameters(), lr=c["lr"], weight_decay=c["wd"], betas=(0.9, c["beta2"]))
    curve = []  # step, tr_loss, tr_acc, va_loss, va_acc, param_norm
    t_fit = t_gen = t_fit95 = t_gen95 = None
    t0 = time.time(); stop_at = None
    for step in range(c["steps"] + 1):
        if step % c["eval_every"] == 0:
            tl, ta = evaluate(model, Xtr, Ytr); vl, va = evaluate(model, Xva, Yva)
            pn = math.sqrt(sum((q ** 2).sum().item() for q in model.parameters()))
            curve.append((step, tl, ta, vl, va, pn))
            if t_fit95 is None and ta >= 0.95: t_fit95 = step
            if t_fit is None and ta >= c["thr"]: t_fit = step
            if t_gen95 is None and va >= 0.95: t_gen95 = step
            if t_gen is None and va >= c["thr"]: t_gen = step; stop_at = step + c["stop_extra"]
            if not math.isfinite(tl): break
            if c["randlabel"] and t_fit is not None: break
            if stop_at is not None and step >= stop_at: break
        if step == c["steps"]: break
        loss = F.cross_entropy(model(Xtr), Ytr)
        opt.zero_grad(set_to_none=True); loss.backward(); opt.step()
    out = dict(cfg=c, n_params=nparams(model), n_train=len(Xtr), t_fit=t_fit, t_gen=t_gen,
               t_fit95=t_fit95, t_gen95=t_gen95, final_tr_acc=curve[-1][2], final_va_acc=curve[-1][4],
               max_va_acc=max(r[4] for r in curve), steps_run=curve[-1][0], secs=time.time() - t0,
               curve=curve)
    return out
