"""Core library: modular-arithmetic data, models, training loop with grokking metrics.

All experiments in the paper go through `run(cfg)`; a cfg is a plain dict (JSON-serialisable).
"""
import math, time, json
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


# ----------------------------------------------------------------------------- data
def make_data(p, frac, seed, op="add"):
    """All p^2 pairs (a,b) -> (a op b) mod p; random split with `frac` of pairs in train."""
    a = torch.arange(p).repeat_interleave(p)
    b = torch.arange(p).repeat(p)
    if op == "add":
        y = (a + b) % p
    elif op == "sub":
        y = (a - b) % p
    elif op == "mul":  # a*b mod p on all pairs (including 0)
        y = (a * b) % p
    elif op == "x2y2":  # a^2 + b^2 mod p
        y = (a * a + b * b) % p
    else:
        raise ValueError(op)
    g = torch.Generator().manual_seed(10_000 + seed)
    perm = torch.randperm(p * p, generator=g)
    ntr = int(round(frac * p * p))
    tr, va = perm[:ntr], perm[ntr:]
    return (a[tr], b[tr], y[tr]), (a[va], b[va], y[va])


# ----------------------------------------------------------------------------- models
class Transformer1L(nn.Module):
    """Nanda-style one-layer decoder-only transformer, no LayerNorm, input [a, b, '='], read out at '='."""

    def __init__(self, p, d, n_heads=4, mlp_mult=4, n_layers=1):
        super().__init__()
        self.p, self.d, self.h = p, d, n_heads
        std = 1.0 / math.sqrt(d)
        self.tok = nn.Parameter(torch.randn(p + 1, d) * std)
        self.pos = nn.Parameter(torch.randn(3, d) * std)
        self.layers = nn.ModuleList()
        for _ in range(n_layers):
            m = nn.ModuleDict(dict(
                qkv=nn.Linear(d, 3 * d, bias=False), o=nn.Linear(d, d, bias=False),
                fc1=nn.Linear(d, mlp_mult * d), fc2=nn.Linear(mlp_mult * d, d)))
            self.layers.append(m)
        self.unembed = nn.Linear(d, p, bias=False)
        self.apply(self._init)

    @staticmethod
    def _init(m):
        if isinstance(m, nn.Linear):
            nn.init.normal_(m.weight, std=1.0 / math.sqrt(m.in_features))
            if m.bias is not None:
                nn.init.zeros_(m.bias)

    def forward(self, a, b):
        B = a.shape[0]
        eq = torch.full_like(a, self.p)
        x = self.tok[torch.stack([a, b, eq], 1)] + self.pos  # B,3,d
        for m in self.layers:
            q, k, v = m["qkv"](x).view(B, 3, 3, self.h, self.d // self.h).permute(2, 0, 3, 1, 4)
            att = F.scaled_dot_product_attention(q, k, v, is_causal=True)
            x = x + m["o"](att.transpose(1, 2).reshape(B, 3, self.d))
            x = x + m["fc2"](F.relu(m["fc1"](x)))
        return self.unembed(x[:, 2])


class MLP(nn.Module):
    """Embedding(a), Embedding(b) -> concat -> ReLU MLP -> logits.  width = hidden width = embedding dim."""

    def __init__(self, p, d, n_layers=2):
        super().__init__()
        self.p = p
        self.ea = nn.Parameter(torch.randn(p, d))  # unit variance, concat has 2d dims, fan_in scaling below
        self.eb = nn.Parameter(torch.randn(p, d))
        dims = [2 * d] + [d] * n_layers
        self.hid = nn.ModuleList([nn.Linear(dims[i], dims[i + 1]) for i in range(n_layers)])
        self.out = nn.Linear(d, p, bias=False)
        for m in list(self.hid) + [self.out]:
            nn.init.normal_(m.weight, std=1.0 / math.sqrt(m.in_features))
            if m.bias is not None:
                nn.init.zeros_(m.bias)

    def forward(self, a, b):
        x = torch.cat([self.ea[a], self.eb[b]], 1)
        for l in self.hid:
            x = F.relu(l(x))
        return self.out(x)


def build(cfg):
    p, d = cfg["p"], cfg["width"]
    if cfg["arch"] == "tf":
        heads = cfg.get("heads", 4)
        return Transformer1L(p, d, n_heads=heads, mlp_mult=cfg.get("mlp_mult", 4), n_layers=cfg.get("layers", 1))
    if cfg["arch"] == "mlp":
        return MLP(p, d, n_layers=cfg.get("layers", 2))
    raise ValueError(cfg["arch"])


def n_params(model):
    return sum(x.numel() for x in model.parameters())


# ----------------------------------------------------------------------------- fourier diagnostic
@torch.no_grad()
def fourier_sparsity(model, p):
    """Fraction of (mean-centred) first-token embedding energy that lies in the 5 strongest Fourier
    frequencies (out of (p-1)/2).  ~ 5/((p-1)/2)... for random, -> 1 for a few-frequency circuit."""
    E = model.tok[:p] if hasattr(model, "tok") else model.ea
    E = E - E.mean(0, keepdim=True)
    F_ = torch.fft.rfft(E, dim=0)  # (p//2+1, d)
    en = (F_.abs() ** 2).sum(1)[1:]
    return float(en.topk(5).values.sum() / en.sum())


# ----------------------------------------------------------------------------- training
def run(cfg):
    """Train one model; return dict(cfg, curves, summary).  Full-batch AdamW unless cfg['bs'] set."""
    torch.set_num_threads(cfg.get("threads", 1))
    seed = cfg["seed"]
    p = cfg["p"]
    (ta, tb, ty), (va, vb, vy) = make_data(p, cfg["frac"], cfg.get("split_seed", seed), cfg.get("op", "add"))
    torch.manual_seed(seed)
    model = build(cfg)
    opt = torch.optim.AdamW(model.parameters(), lr=cfg["lr"], weight_decay=cfg["wd"], betas=(0.9, cfg.get("beta2", 0.98)))
    warm = cfg.get("warmup", 10)
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / warm))
    steps, ev = cfg["steps"], cfg.get("eval_every", 50)
    fine_until, fine_ev = cfg.get("fine_until", 400), cfg.get("fine_every", 10)
    bs = cfg.get("bs", None)
    stop_after = cfg.get("stop_after_gen", 0.0)  # stop once val>=thr for this many consecutive evals
    N = ta.shape[0]
    curves = dict(step=[], tr_acc=[], va_acc=[], tr_loss=[], va_loss=[], wnorm=[], fsp=[])
    t0 = time.time()
    gen_streak = 0
    fit_step = None
    saf = cfg.get("stop_after_fit", 0)
    rescale, rescaled_at = cfg.get("rescale", None), None  # causal norm intervention at first train-fit
    g = torch.Generator().manual_seed(seed + 77)

    @torch.no_grad()
    def evaluate(step):
        model.eval()
        lt = model(ta, tb); lv = model(va, vb)
        curves["step"].append(step)
        curves["tr_acc"].append(float((lt.argmax(1) == ty).float().mean()))
        curves["va_acc"].append(float((lv.argmax(1) == vy).float().mean()))
        curves["tr_loss"].append(float(F.cross_entropy(lt, ty)))
        curves["va_loss"].append(float(F.cross_entropy(lv, vy)))
        curves["wnorm"].append(float(math.sqrt(sum((q ** 2).sum() for q in model.parameters()))))
        curves["fsp"].append(fourier_sparsity(model, p))
        model.train()

    for step in range(steps + 1):
        if step % (fine_ev if step < fine_until else ev) == 0:
            evaluate(step)
            if stop_after and curves["va_acc"][-1] >= 0.99 and curves["tr_acc"][-1] >= 0.99:
                gen_streak += 1
                if gen_streak * ev >= stop_after:
                    break
            else:
                gen_streak = 0
            if rescale is not None and rescaled_at is None and curves["tr_acc"][-1] >= 0.99:
                rescaled_at = step
                with torch.no_grad():
                    for q in model.parameters():
                        q.mul_(rescale)
            if saf:
                if fit_step is None and curves["tr_acc"][-1] >= 0.99:
                    fit_step = step
                if fit_step is not None and step - fit_step >= saf:
                    break
            if not math.isfinite(curves["tr_loss"][-1]):
                break
        if step == steps:
            break
        if bs is None or bs >= N:
            ia, ib, iy = ta, tb, ty
        else:
            idx = torch.randint(0, N, (bs,), generator=g)
            ia, ib, iy = ta[idx], tb[idx], ty[idx]
        loss = F.cross_entropy(model(ia, ib), iy)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step(); sched.step()
    out = dict(cfg=cfg, n_params=n_params(model), n_train=int(N), curves=curves, wall=time.time() - t0, rescaled_at=rescaled_at)
    out["summary"] = summarize(curves, cfg)
    return out


def first_crossing(steps, vals, thr, start=0):
    """first logged step >= start where vals >= thr and stays >= thr for >=3 logged points (or until end)."""
    n = len(steps)
    for i in range(n):
        if steps[i] >= start and vals[i] >= thr:
            if all(v >= thr * 0.97 for v in vals[i:i + 3]):
                return steps[i]
    return None


def summarize(c, cfg=None, thr=0.99):
    s = c["step"]
    t_fit = first_crossing(s, c["tr_acc"], thr)
    t_gen = first_crossing(s, c["va_acc"], thr)
    # val-acc at the time train acc first reached thr, and final / max accs
    va_at_fit = None
    if t_fit is not None:
        va_at_fit = c["va_acc"][s.index(t_fit)]
    return dict(t_fit=t_fit, t_gen=t_gen, va_at_fit=va_at_fit, final_tr=c["tr_acc"][-1], final_va=c["va_acc"][-1],
                max_va=max(c["va_acc"]), last_step=s[-1])


# ----------------------------------------------------------------------------- seed-ensemble training
# Overhead-bound small models are trained S seeds at a time as one batched model.  Members share nothing
# (own init, own train/val split, own Adam state, loss = sum of per-member mean CE), so this is mathematically
# identical to S separate runs; init is copied from the single-model constructor with the same seed.
class EnsTransformer(nn.Module):
    def __init__(self, singles, p, d, heads):
        super().__init__()
        self.p, self.d, self.h = p, d, heads
        st = lambda f: nn.Parameter(torch.stack([f(m).detach().clone() for m in singles]))
        self.tok = st(lambda m: m.tok); self.pos = st(lambda m: m.pos)
        self.qkv = st(lambda m: m.layers[0]["qkv"].weight.T); self.o = st(lambda m: m.layers[0]["o"].weight.T)
        self.fc1 = st(lambda m: m.layers[0]["fc1"].weight.T); self.b1 = st(lambda m: m.layers[0]["fc1"].bias[None])
        self.fc2 = st(lambda m: m.layers[0]["fc2"].weight.T); self.b2 = st(lambda m: m.layers[0]["fc2"].bias[None])
        self.un = st(lambda m: m.unembed.weight.T)

    def forward(self, a, b):  # a,b: (S,B)
        S, B = a.shape
        eq = torch.full_like(a, self.p)
        idx = torch.stack([a, b, eq], 2)  # S,B,3
        ar = torch.arange(S)[:, None, None]
        x = self.tok[ar, idx] + self.pos[:, None]  # S,B,3,d
        h, d = self.h, self.d
        q, k, v = (x.reshape(S, B * 3, d) @ self.qkv).view(S, B, 3, 3, h, d // h).permute(3, 0, 1, 4, 2, 5)
        att = F.scaled_dot_product_attention(q, k, v, is_causal=True)  # S,B,h,3,dh
        x = x + (att.transpose(2, 3).reshape(S, B * 3, d) @ self.o).view(S, B, 3, d)
        hid = F.relu(x.reshape(S, B * 3, d) @ self.fc1 + self.b1)
        x = x + (hid @ self.fc2 + self.b2).view(S, B, 3, d)
        return x[:, :, 2] @ self.un  # S,B,p

    def member_params(self, s):
        return [q[s] for q in self.parameters()]


def run_ens(cfg, seeds):
    """Train len(seeds) transformers (1 layer) at once. Returns list of per-seed result dicts, same format as run()."""
    assert cfg["arch"] == "tf" and cfg.get("layers", 1) == 1
    torch.set_num_threads(cfg.get("threads", 1))
    p, S = cfg["p"], len(seeds)
    data = [make_data(p, cfg["frac"], sd, cfg.get("op", "add")) for sd in seeds]
    stk = lambda j, k: torch.stack([data[s][j][k] for s in range(S)])
    ta, tb, ty = stk(0, 0), stk(0, 1), stk(0, 2)
    va, vb, vy = stk(1, 0), stk(1, 1), stk(1, 2)
    singles = []
    for sd in seeds:
        torch.manual_seed(sd)
        singles.append(build(dict(cfg, seed=sd)))
    model = EnsTransformer(singles, p, cfg["width"], cfg.get("heads", 4))
    nparams = n_params(singles[0])
    opt = torch.optim.AdamW(model.parameters(), lr=cfg["lr"], weight_decay=cfg["wd"], betas=(0.9, cfg.get("beta2", 0.98)))
    warm = cfg.get("warmup", 10)
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / warm))
    steps, ev = cfg["steps"], cfg.get("eval_every", 50)
    fine_until, fine_ev = cfg.get("fine_until", 400), cfg.get("fine_every", 10)
    stop_after = cfg.get("stop_after_gen", 0.0)
    N = ta.shape[1]
    keys = ["step", "tr_acc", "va_acc", "tr_loss", "va_loss", "wnorm", "fsp"]
    curves = [{k: [] for k in keys} for _ in range(S)]
    streak = [0] * S
    done = [False] * S
    fit_step = [None] * S
    saf = cfg.get("stop_after_fit", 0)
    t0 = time.time()

    @torch.no_grad()
    def evaluate(step):
        lt, lv = model(ta, tb), model(va, vb)
        for s in range(S):
            if done[s]:
                continue
            c = curves[s]
            c["step"].append(step)
            c["tr_acc"].append(float((lt[s].argmax(1) == ty[s]).float().mean()))
            c["va_acc"].append(float((lv[s].argmax(1) == vy[s]).float().mean()))
            c["tr_loss"].append(float(F.cross_entropy(lt[s], ty[s])))
            c["va_loss"].append(float(F.cross_entropy(lv[s], vy[s])))
            c["wnorm"].append(float(math.sqrt(sum(float((q ** 2).sum()) for q in model.member_params(s)))))
            E = model.tok[s, :p]; E = E - E.mean(0, keepdim=True)
            en = (torch.fft.rfft(E, dim=0).abs() ** 2).sum(1)[1:]
            c["fsp"].append(float(en.topk(5).values.sum() / en.sum()))
            if stop_after and c["va_acc"][-1] >= 0.99 and c["tr_acc"][-1] >= 0.99:
                streak[s] += 1
                if streak[s] * ev >= stop_after:
                    done[s] = True
            else:
                streak[s] = 0
            if saf:
                if fit_step[s] is None and c["tr_acc"][-1] >= 0.99:
                    fit_step[s] = step
                if fit_step[s] is not None and step - fit_step[s] >= saf:
                    done[s] = True

    for step in range(steps + 1):
        if step % (fine_ev if step < fine_until else ev) == 0:
            evaluate(step)
            if all(done):
                break
        if step == steps:
            break
        logits = model(ta, tb)
        loss = F.cross_entropy(logits.reshape(-1, p), ty.reshape(-1), reduction="none").view(S, N).mean(1).sum()
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step(); sched.step()
    wall = time.time() - t0
    outs = []
    for s, sd in enumerate(seeds):
        c = dict(cfg, seed=sd)
        o = dict(cfg=c, n_params=nparams, n_train=int(N), curves=curves[s], wall=wall / S, ens=S)
        o["summary"] = summarize(curves[s], c)
        outs.append(o)
    return outs
