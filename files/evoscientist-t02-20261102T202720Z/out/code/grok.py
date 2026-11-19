"""Grokking vs. model scale on modular arithmetic (CPU, single-thread per run).

One run = one (arch, width, p, op, train_frac, lr, wd, init_scale, seed) config.
Full-batch AdamW training; train accuracy is read from the training forward pass
(every step), validation accuracy on the held-out pairs every `eval_every` steps.
Results are appended to a JSONL file (one line per run), so sweeps are resumable.
"""
import argparse, json, math, os, sys, time, hashlib
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

torch.set_num_threads(1)


def make_data(p, op, frac, seed):
    a = np.arange(p).repeat(p)
    b = np.tile(np.arange(p), p)
    if op == "add":
        y = (a + b) % p
    elif op == "sub":
        y = (a - b) % p
    elif op == "mul":  # on all of Z_p (incl. 0); still a binary modular operation
        y = (a * b) % p
    else:
        raise ValueError(op)
    rng = np.random.RandomState(seed)  # split depends only on (p, frac, seed) -> paired across widths
    perm = rng.permutation(p * p)
    ntr = int(round(frac * p * p))
    tr, va = perm[:ntr], perm[ntr:]
    X = torch.tensor(np.stack([a, b], 1), dtype=torch.long)
    Y = torch.tensor(y, dtype=torch.long)
    return X[tr], Y[tr], X[va], Y[va]


class Transformer(nn.Module):
    """1-layer decoder-style transformer, no LayerNorm, ReLU MLP (as in Nanda et al.),
    input tokens [a, b], prediction read from the last position."""

    def __init__(self, p, d, n_heads=4, mlp_mult=4, init_scale=1.0):
        super().__init__()
        self.p, self.d, self.h = p, d, n_heads
        s = init_scale
        self.emb = nn.Parameter(torch.randn(p, d) * s / math.sqrt(d))
        self.pos = nn.Parameter(torch.randn(2, d) * s / math.sqrt(d))
        self.Wqkv = nn.Parameter(torch.randn(d, 3 * d) * s / math.sqrt(d))
        self.Wo = nn.Parameter(torch.randn(d, d) * s / math.sqrt(d))
        self.W1 = nn.Parameter(torch.randn(d, mlp_mult * d) * s / math.sqrt(d))
        self.b1 = nn.Parameter(torch.zeros(mlp_mult * d))
        self.W2 = nn.Parameter(torch.randn(mlp_mult * d, d) * s / math.sqrt(mlp_mult * d))
        self.b2 = nn.Parameter(torch.zeros(d))
        self.U = nn.Parameter(torch.randn(d, p) * s / math.sqrt(d))

    def forward(self, x):
        B = x.shape[0]
        h = self.emb[x] + self.pos  # B,2,d
        q, k, v = (h @ self.Wqkv).chunk(3, -1)
        sp = lambda t: t.view(B, 2, self.h, self.d // self.h).transpose(1, 2)
        o = F.scaled_dot_product_attention(sp(q), sp(k), sp(v), is_causal=True)
        h = h + o.transpose(1, 2).reshape(B, 2, self.d) @ self.Wo
        h = h + F.relu(h @ self.W1 + self.b1) @ self.W2 + self.b2
        return h[:, -1] @ self.U


class MLP(nn.Module):
    """concat(E[a], E[b]) -> ReLU hidden (4d) -> ReLU hidden (4d) -> logits."""

    def __init__(self, p, d, mlp_mult=4, init_scale=1.0):
        super().__init__()
        s = init_scale
        self.p, self.d = p, d
        self.emb = nn.Parameter(torch.randn(p, d) * s / math.sqrt(d))
        hdim = mlp_mult * d
        self.W1 = nn.Parameter(torch.randn(2 * d, hdim) * s / math.sqrt(2 * d))
        self.b1 = nn.Parameter(torch.zeros(hdim))
        self.W2 = nn.Parameter(torch.randn(hdim, hdim) * s / math.sqrt(hdim))
        self.b2 = nn.Parameter(torch.zeros(hdim))
        self.U = nn.Parameter(torch.randn(hdim, p) * s / math.sqrt(hdim))

    def forward(self, x):
        h = self.emb[x].flatten(1)
        h = F.relu(h @ self.W1 + self.b1)
        h = F.relu(h @ self.W2 + self.b2)
        return h @ self.U


def n_params(m):
    return sum(t.numel() for t in m.parameters())


def run(cfg, log_every=50):
    cfg = dict(cfg)
    p, d = cfg["p"], cfg["d"]
    Xtr, Ytr, Xva, Yva = make_data(p, cfg["op"], cfg["frac"], cfg["seed"])
    ih = int(hashlib.md5(f"{cfg['arch']}-{d}-{cfg['seed']}".encode()).hexdigest()[:7], 16)
    torch.manual_seed(ih)
    cls = Transformer if cfg["arch"] == "tf" else MLP
    model = cls(p, d, init_scale=cfg.get("init_scale", 1.0))
    opt = torch.optim.AdamW(model.parameters(), lr=cfg["lr"], betas=(0.9, 0.98), weight_decay=cfg["wd"])
    max_steps, thr = cfg["max_steps"], cfg.get("thr", 0.99)
    warm = 10
    t_fit = t_gen = None
    curve = []
    t0 = time.time()
    for step in range(1, max_steps + 1):
        for g in opt.param_groups:
            g["lr"] = cfg["lr"] * min(1.0, step / warm)
        logits = model(Xtr)
        loss = F.cross_entropy(logits, Ytr)
        tr_acc = (logits.argmax(-1) == Ytr).float().mean().item()
        if t_fit is None and tr_acc >= thr:
            t_fit = step
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
        if step % log_every == 0:
            with torch.no_grad():
                lv = model(Xva)
                va_loss = F.cross_entropy(lv, Yva).item()
                va_acc = (lv.argmax(-1) == Yva).float().mean().item()
                wn = math.sqrt(sum((t ** 2).sum().item() for t in model.parameters()))
            curve.append([step, round(loss.item(), 5), round(tr_acc, 4), round(va_loss, 5), round(va_acc, 4), round(wn, 3)])
            if va_acc >= thr and t_gen is None:
                t_gen = step
            if t_gen is not None and t_fit is not None:
                break
            if not math.isfinite(loss.item()):
                break
    out = dict(cfg)
    out.update(n_params=n_params(model), n_train=len(Ytr), t_fit=t_fit, t_gen=t_gen, steps_run=step,
               final_train_acc=curve[-1][2] if curve else None, final_val_acc=curve[-1][4] if curve else None,
               max_val_acc=max(c[4] for c in curve) if curve else None,
               wnorm_at_end=curve[-1][5] if curve else None, wall=round(time.time() - t0, 1), curve=curve)
    return out


def _worker(cfg):
    try:
        return run(cfg)
    except Exception as e:  # keep the sweep alive; record failure
        return dict(cfg, error=repr(e))


def key(cfg):
    return json.dumps({k: cfg[k] for k in sorted(cfg) if k != "curve"}, sort_keys=True)


def sweep(cfgs, out_path, workers):
    import multiprocessing as mp
    done = set()
    if os.path.exists(out_path):
        for l in open(out_path):
            r = json.loads(l)
            if "error" not in r:
                done.add(key({k: r[k] for k in cfgs[0].keys()}))
    todo = [c for c in cfgs if key(c) not in done]
    # longest jobs first (largest width, largest frac) for better packing
    todo.sort(key=lambda c: -(c["d"] * c["frac"] * c["p"] ** 2))
    print(f"{len(todo)} to run ({len(cfgs) - len(todo)} done)", flush=True)
    ctx = mp.get_context("spawn")
    t0 = time.time()
    with ctx.Pool(workers) as pool, open(out_path, "a") as f:
        for i, r in enumerate(pool.imap_unordered(_worker, todo, chunksize=1)):
            f.write(json.dumps(r) + "\n"); f.flush()
            print(f"[{i + 1}/{len(todo)} {time.time() - t0:.0f}s] arch={r['arch']} d={r['d']} p={r['p']} frac={r['frac']} "
                  f"seed={r['seed']} t_fit={r.get('t_fit')} t_gen={r.get('t_gen')} {r.get('error', '')}", flush=True)


def base(**kw):
    c = dict(arch="tf", d=32, p=53, op="add", frac=0.3, lr=1e-3, wd=1.0, init_scale=1.0, seed=0, max_steps=30000, thr=0.99)
    c.update(kw)
    return c


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cfg", type=str, help="JSON config for a single run")
    a = ap.parse_args()
    r = run(base(**json.loads(a.cfg or "{}")))
    r.pop("curve")
    print(json.dumps(r))
