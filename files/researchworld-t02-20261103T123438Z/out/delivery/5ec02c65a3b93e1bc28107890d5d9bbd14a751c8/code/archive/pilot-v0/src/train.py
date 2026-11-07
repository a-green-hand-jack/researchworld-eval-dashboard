"""Reproducible full-batch modular arithmetic MLP experiments (CPU)."""
import argparse
import hashlib
import json
import math
import os
import platform
import resource
import subprocess
import time
from pathlib import Path

os.environ.setdefault('OMP_NUM_THREADS', '1')
os.environ.setdefault('MKL_NUM_THREADS', '1')
import numpy as np
import torch
from torch import nn


class PairMLP(nn.Module):
    """Exactly a concatenated one-hot -> hidden -> class MLP, using gathers."""
    def __init__(self, p, width, activation='relu'):
        super().__init__()
        self.p = p
        self.input_weight = nn.Parameter(torch.empty(width, 2*p))
        self.input_bias = nn.Parameter(torch.empty(width))
        nn.init.kaiming_uniform_(self.input_weight, a=math.sqrt(5))
        nn.init.uniform_(self.input_bias, -1/math.sqrt(2*p), 1/math.sqrt(2*p))
        self.output = nn.Linear(width, p)
        self.activation = {'relu': torch.relu, 'gelu': torch.nn.functional.gelu,
                           'square': torch.square}[activation]

    def forward(self, pairs):
        h = self.input_weight[:, pairs[:, 0]].T + self.input_weight[:, self.p+pairs[:, 1]].T
        return self.output(self.activation(h+self.input_bias))


def dataset(p, fraction, split_seed, task):
    a, b = torch.meshgrid(torch.arange(p), torch.arange(p), indexing='ij')
    pairs = torch.stack([a.flatten(), b.flatten()], dim=1)
    labels = {'add': lambda: (a+b) % p, 'subtract': lambda: (a-b) % p,
              'multiply': lambda: (a*b) % p}[task]().flatten()
    order = np.random.default_rng(split_seed).permutation(p*p)
    n = int(p*p*fraction)
    if not 0 < n < p*p:
        raise ValueError('Need a nonempty training and validation partition')
    train = torch.tensor(order[:n])
    valid = torch.tensor(order[n:])
    digest = hashlib.sha256(order.astype('<i8').tobytes()).hexdigest()
    return pairs, labels, train, valid, digest


def spectral_fraction(logits, p, task):
    """Fraction class-centered logit energy in operation-compatible Fourier modes.

    For addition, modes (k,k,-k); subtraction (k,-k,-k). Multiplication
    has no such translation template; return None. No labels or fitted probes.
    """
    if task not in ('add', 'subtract'):
        return None
    arr = logits.detach().numpy().reshape(p,p,p).astype(np.float64)
    arr -= arr.mean(axis=2, keepdims=True)
    energy = abs(np.fft.fftn(arr))**2
    k = np.arange(1,p)
    kb = k if task == 'add' else (-k) % p
    return float(energy[k, kb, (-k) % p].sum()/max(energy.sum(), 1e-300))


def run(config, root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    if (root/'summary.json').exists():
        raise FileExistsError(f'Refusing to overwrite completed run {root}')
    torch.set_num_threads(config.get('threads',1))
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(config['init_seed'])
    pairs, labels, train, valid, split_hash = dataset(config['p'],config['fraction'],config['split_seed'],config['task'])
    model = PairMLP(config['p'],config['width'],config['activation'])
    initial = torch.cat([v.detach().flatten() for v in model.parameters()]).clone()
    optimizer = torch.optim.AdamW(model.parameters(), lr=config['lr'], weight_decay=config['weight_decay'],
                                  betas=tuple(config.get('betas',[0.9,0.999])), eps=config.get('eps',1e-8))
    metadata = dict(config=config, parameter_count=sum(v.numel() for v in model.parameters()),
                    n_train=len(train), n_valid=len(valid), split_sha256=split_hash,
                    python=platform.python_version(), torch=torch.__version__, numpy=np.__version__,
                    platform=platform.platform(),
                    source_train_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    source_git_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
                    started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))
    (root/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    torch.save(model.state_dict(),root/'initial.pt')
    start = time.perf_counter()
    cpu_start = time.process_time()
    step_seconds = 0.
    eval_seconds = 0.
    with (root/'curve.jsonl').open('w',buffering=1) as stream:
        for step in range(config['steps']+1):
            if step % config['eval_every'] == 0 or step == config['steps']:
                begin = time.perf_counter()
                model.eval()
                with torch.no_grad():
                    logits = model(pairs)
                    params = torch.cat([v.flatten() for v in model.parameters()])
                    row = dict(step=step, train_loss=nn.functional.cross_entropy(logits[train],labels[train]).item(),
                               valid_loss=nn.functional.cross_entropy(logits[valid],labels[valid]).item(),
                               train_acc=(logits[train].argmax(1)==labels[train]).float().mean().item(),
                               valid_acc=(logits[valid].argmax(1)==labels[valid]).float().mean().item(),
                               weight_norm=params.norm().item(), displacement_norm=(params-initial).norm().item(),
                               spectral_fraction=spectral_fraction(logits,config['p'],config['task']),
                               elapsed_s=time.perf_counter()-start, cpu_s=time.process_time()-cpu_start,
                               training_s=step_seconds)
                eval_seconds += time.perf_counter()-begin
                stream.write(json.dumps(row)+'\n')
                if step == 0 or step % config.get('report_every',2000) == 0 or step == config['steps']:
                    print(json.dumps(dict(run=root.name,**row)),flush=True)
                model.train()
            if step == config['steps']:
                break
            begin = time.perf_counter()
            optimizer.zero_grad(set_to_none=True)
            loss = nn.functional.cross_entropy(model(pairs[train]),labels[train])
            if not torch.isfinite(loss):
                raise FloatingPointError(f'Nonfinite loss at step {step}')
            loss.backward()
            optimizer.step()
            step_seconds += time.perf_counter()-begin
    torch.save(dict(model=model.state_dict(),optimizer=optimizer.state_dict(),step=step),root/'final.pt')
    summary = dict(**metadata, final=row, elapsed_s=time.perf_counter()-start,
                   cpu_s=time.process_time()-cpu_start,training_s=step_seconds,evaluation_s=eval_seconds,
                   process_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    (root/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config',required=True)
    parser.add_argument('--output',required=True)
    args = parser.parse_args()
    run(json.loads(Path(args.config).read_text()),args.output)
