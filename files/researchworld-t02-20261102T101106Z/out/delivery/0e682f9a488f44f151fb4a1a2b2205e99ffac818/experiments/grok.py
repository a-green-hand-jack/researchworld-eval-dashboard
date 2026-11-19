"""Grokking on modular arithmetic: one seeded run, width as the scale axis.

Usage: python grok.py --arch tf --width 64 --p 97 --frac 0.3 --wd 1.0 --seed 0 --out runs/x.json
Writes a JSON with the config, a log of (step, train/val acc/loss, weight norms) and
t_fit / t_gen (first logged step with train / val acc >= thr; None if never reached).
"""
import argparse, json, math, os, time
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


def make_data(p, op, frac, seed):  # seed = split seed
    a, b = torch.meshgrid(torch.arange(p), torch.arange(p), indexing="ij")
    a, b = a.reshape(-1), b.reshape(-1)
    if op == "add":
        y = (a + b) % p
    elif op == "sub":
        y = (a - b) % p
    elif op == "mul":  # on all residues incl. 0
        y = (a * b) % p
    else:
        raise ValueError(op)
    g = torch.Generator().manual_seed(10_000 + seed)  # split depends on seed
    perm = torch.randperm(p * p, generator=g)
    ntr = int(round(frac * p * p))
    tr, va = perm[:ntr], perm[ntr:]
    return (a[tr], b[tr], y[tr]), (a[va], b[va], y[va])


class TF(nn.Module):
    """1-layer decoder-only transformer, tokens [a, b, '='], read-out at '='. No LayerNorm (as Nanda et al.)."""
    def __init__(self, p, d, heads=4, mlp_mult=4):
        super().__init__()
        self.p = p
        self.emb = nn.Embedding(p + 1, d)
        nn.init.normal_(self.emb.weight, std=1 / math.sqrt(d))  # N(0,1) default makes the init far too large
        self.pos = nn.Parameter(torch.randn(3, d) / math.sqrt(d))
        self.heads = heads if d % heads == 0 and d >= heads * 4 else 1
        self.qkv = nn.Linear(d, 3 * d, bias=False)
        self.o = nn.Linear(d, d, bias=False)
        self.up = nn.Linear(d, mlp_mult * d)
        self.down = nn.Linear(mlp_mult * d, d)
        self.unemb = nn.Linear(d, p, bias=False)

    def forward(self, a, b):
        B = a.shape[0]
        eq = torch.full_like(a, self.p)
        x = self.emb(torch.stack([a, b, eq], 1)) + self.pos
        d = x.shape[-1]; h = self.heads
        q, k, v = self.qkv(x).view(B, 3, 3, h, d // h).unbind(2)
        att = F.scaled_dot_product_attention(q.transpose(1, 2), k.transpose(1, 2), v.transpose(1, 2), is_causal=True)
        x = x + self.o(att.transpose(1, 2).reshape(B, 3, d))
        x = x + self.down(F.relu(self.up(x)))
        return self.unemb(x[:, -1])


class MLP(nn.Module):
    """Embed a and b, concatenate, 1 hidden ReLU layer of size 4*width... (width = embedding dim)."""
    def __init__(self, p, d, mlp_mult=4):
        super().__init__()
        self.emb = nn.Embedding(p, d)
        nn.init.normal_(self.emb.weight, std=1 / math.sqrt(d))
        self.net = nn.Sequential(nn.Linear(2 * d, mlp_mult * d), nn.ReLU(), nn.Linear(mlp_mult * d, mlp_mult * d), nn.ReLU(), nn.Linear(mlp_mult * d, p))

    def forward(self, a, b):
        return self.net(torch.cat([self.emb(a), self.emb(b)], 1))


def evaluate(model, data):
    with torch.no_grad():
        out = model(data[0], data[1])
        return (out.argmax(1) == data[2]).float().mean().item(), F.cross_entropy(out, data[2]).item()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arch", default="tf", choices=["tf", "mlp"])
    ap.add_argument("--width", type=int, default=64)
    ap.add_argument("--p", type=int, default=97)
    ap.add_argument("--op", default="add")
    ap.add_argument("--frac", type=float, default=0.3)
    ap.add_argument("--wd", type=float, default=1.0)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--max_steps", type=int, default=30000)
    ap.add_argument("--log_every", type=int, default=100)
    ap.add_argument("--thr", type=float, default=0.99)
    ap.add_argument("--extra", type=int, default=500, help="steps to continue after t_gen")
    ap.add_argument("--init_mult", type=float, default=1.0, help="multiply every parameter at init by this (init-scale intervention)")
    ap.add_argument("--split_seed", type=int, default=-1, help="seed of the train/val split; -1 = same as --seed")
    ap.add_argument("--lr_ref", type=int, default=0, help="if >0, lr is scaled by sqrt(lr_ref/width) (width-scaled regime)")
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    torch.set_num_threads(args.threads)
    torch.manual_seed(args.seed); np.random.seed(args.seed)
    train, val = make_data(args.p, args.op, args.frac, args.seed if args.split_seed < 0 else args.split_seed)
    model = (TF if args.arch == "tf" else MLP)(args.p, args.width)
    with torch.no_grad():
        for q in model.parameters():
            q.mul_(args.init_mult)
    lr = args.lr * math.sqrt(args.lr_ref / args.width) if args.lr_ref > 0 else args.lr
    nparams = sum(x.numel() for x in model.parameters())
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=args.wd, betas=(0.9, 0.98))
    warm = lambda s: min(1.0, (s + 1) / 10)
    sched = torch.optim.lr_scheduler.LambdaLR(opt, warm)
    log, t_fit, t_gen, t0, stop_at = [], None, None, time.time(), None
    for step in range(args.max_steps + 1):
        if step % args.log_every == 0:
            tra, trl = evaluate(model, train); vaa, val_l = evaluate(model, val)
            wn = math.sqrt(sum((q ** 2).sum().item() for q in model.parameters()))
            log.append(dict(step=step, train_acc=tra, train_loss=trl, val_acc=vaa, val_loss=val_l, wnorm=wn))
            if t_fit is None and tra >= args.thr: t_fit = step
            if t_gen is None and vaa >= args.thr: t_gen = step; stop_at = step + args.extra
            if stop_at is not None and step >= stop_at: break
            if not math.isfinite(trl): break
        model.train()
        loss = F.cross_entropy(model(train[0], train[1]), train[2])  # full batch
        opt.zero_grad(set_to_none=True); loss.backward(); opt.step(); sched.step()
    res = dict(config=vars(args), lr_effective=lr, nparams=nparams, t_fit=t_fit, t_gen=t_gen, steps_run=log[-1]["step"],
               wall_s=time.time() - t0, final=log[-1], log=log, torch=torch.__version__)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    json.dump(res, open(args.out, "w"))
    print(f"arch={args.arch} w={args.width} seed={args.seed} params={nparams} t_fit={t_fit} t_gen={t_gen} steps={res['steps_run']} wall={res['wall_s']:.0f}s", flush=True)


if __name__ == "__main__":
    main()
