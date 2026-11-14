"""Deterministic exhaustive modular-arithmetic width experiments (CPU)."""
import argparse
import csv
import hashlib
import json
import math
import os
import platform
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F


def dataset(p, fraction, seed, operation='add'):
    a = torch.arange(p).repeat_interleave(p)
    b = torch.arange(p).repeat(p)
    x = torch.cat([F.one_hot(a, p), F.one_hot(b, p)], dim=1).float()
    y = (a + b) % p if operation == 'add' else (a - b) % p
    rng = torch.Generator().manual_seed(10000 + seed)
    perm = torch.randperm(p * p, generator=rng)
    n = int(fraction * p * p)
    return x, y, perm[:n], perm[n:]


class Net(nn.Module):
    def __init__(self, p, width, activation='relu', init_scale=1., frozen=False, output_scale=1.):
        super().__init__()
        self.hidden = nn.Linear(2 * p, width, bias=False)
        self.readout = nn.Linear(width, p, bias=False)
        self.activation = activation
        self.output_scale = output_scale
        with torch.no_grad():
            self.hidden.weight.mul_(init_scale)
            self.readout.weight.mul_(init_scale)
        self.hidden.weight.requires_grad_(not frozen)

    def forward(self, x):
        z = self.hidden(x)
        z = z.square() if self.activation == 'square' else F.relu(z)
        return self.readout(z) * self.output_scale


def first_event(rows, key, threshold, consecutive=3):
    for i in range(len(rows) - consecutive + 1):
        if all(float(r[key]) >= threshold for r in rows[i:i + consecutive]):
            return int(rows[i]['step'])
    return None


def run(args):
    torch.set_num_threads(args.threads)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(20000 + args.seed)
    np.random.seed(args.seed)
    x, y, train, test = dataset(args.p, args.fraction, args.seed, args.operation)
    model = Net(args.p, args.width, args.activation, args.init_scale, args.frozen, args.output_scale)
    initial = model.hidden.weight.detach().clone()
    opt = torch.optim.AdamW([q for q in model.parameters() if q.requires_grad],
                            lr=args.lr, weight_decay=args.decay, betas=(.9, .98))
    cfg = vars(args).copy()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    tag = args.name or f'{args.operation}_p{args.p}_w{args.width}_s{args.seed}_wd{args.decay}_fr{int(args.frozen)}'
    target = out / tag
    if target.with_suffix('.json').exists() and not args.overwrite:
        raise FileExistsError(f'{target} already exists; no silent reuse')
    rows = []
    start = time.perf_counter()
    for step in range(args.steps + 1):
        if step % args.eval_every == 0 or step == args.steps:
            with torch.no_grad():
                logits = model(x)
                pred = logits.argmax(1)
                row = dict(step=step, seconds=time.perf_counter()-start,
                           train_loss=F.cross_entropy(logits[train], y[train]).item(),
                           test_loss=F.cross_entropy(logits[test], y[test]).item(),
                           train_acc=(pred[train] == y[train]).float().mean().item(),
                           test_acc=(pred[test] == y[test]).float().mean().item(),
                           norm=math.sqrt(sum(q.square().sum().item() for q in model.parameters())),
                           hidden_movement=((model.hidden.weight-initial).norm()/initial.norm()).item())
                rows.append(row)
        if step == args.steps:
            break
        opt.zero_grad(set_to_none=True)
        loss = F.cross_entropy(model(x[train]), y[train])
        if not torch.isfinite(loss):
            raise FloatingPointError(f'nonfinite loss at {step}')
        loss.backward()
        opt.step()
    runtime = time.perf_counter() - start
    with target.with_suffix('.csv').open('w') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
    config_hash = hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()
    result = dict(config=cfg, config_sha256=config_hash,
                  split_sha256=hashlib.sha256(train.numpy().tobytes()).hexdigest(),
                  n_train=len(train), n_test=len(test),
                  parameters=sum(q.numel() for q in model.parameters()),
                  trainable_parameters=sum(q.numel() for q in model.parameters() if q.requires_grad),
                  fit=first_event(rows, 'train_acc', .99),
                  generalize=first_event(rows, 'test_acc', .95),
                  final=rows[-1], runtime_seconds=runtime,
                  versions=dict(torch=torch.__version__, numpy=np.__version__, python=platform.python_version()),
                  source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    target.with_suffix('.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(dict(name=tag, width=args.width, seed=args.seed, fit=result['fit'],
                         gen=result['generalize'], final=rows[-1]['test_acc'], seconds=runtime)), flush=True)
    return result


def parser():
    p = argparse.ArgumentParser()
    p.add_argument('--p', type=int, default=31)
    p.add_argument('--fraction', type=float, default=.5)
    p.add_argument('--operation', choices=['add', 'sub'], default='add')
    p.add_argument('--width', type=int, default=64)
    p.add_argument('--seed', type=int, default=0)
    p.add_argument('--activation', choices=['relu', 'square'], default='relu')
    p.add_argument('--steps', type=int, default=20000)
    p.add_argument('--eval-every', type=int, default=100)
    p.add_argument('--lr', type=float, default=.003)
    p.add_argument('--decay', type=float, default=1.)
    p.add_argument('--init-scale', type=float, default=1.)
    p.add_argument('--output-scale', type=float, default=1.)
    p.add_argument('--threads', type=int, default=1)
    p.add_argument('--frozen', action='store_true')
    p.add_argument('--out', default='runs/pilot')
    p.add_argument('--name')
    p.add_argument('--overwrite', action='store_true')
    return p


if __name__ == '__main__':
    run(parser().parse_args())
