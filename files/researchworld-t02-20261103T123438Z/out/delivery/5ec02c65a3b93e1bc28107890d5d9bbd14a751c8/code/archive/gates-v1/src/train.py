"""Deterministic full-batch modular MLP experiments, with recoverable state."""
import argparse
import hashlib
import json
import math
import os
import platform
import resource
import shutil
import subprocess
import time
from pathlib import Path

os.environ.setdefault('OMP_NUM_THREADS', '1')
os.environ.setdefault('MKL_NUM_THREADS', '1')
import numpy as np
import torch
from torch import nn


class PairMLP(nn.Module):
    """Concatenated one-hot -> hidden -> class MLP evaluated with exact gathers."""
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


def sha_array(array):
    return hashlib.sha256(np.asarray(array,dtype='<i8').tobytes()).hexdigest()


def split_indices(p, fraction, split_seed, split_rule='ordered'):
    rng = np.random.default_rng(split_seed)
    orbit_hash = None
    if split_rule == 'ordered':
        order = rng.permutation(p*p)
        n = int(p*p*fraction)
        train, valid = order[:n], order[n:]
    elif split_rule == 'orbit':
        # Orbit IDs are lexicographic (a,b) with a<=b; diagonal size is one.
        orbits = [[a*p+b] if a==b else [a*p+b,b*p+a]
                  for a in range(p) for b in range(a,p)]
        order = rng.permutation(len(orbits))
        n = int(len(orbits)*fraction)
        train = np.array([pair for i in order[:n] for pair in orbits[i]])
        valid = np.array([pair for i in order[n:] for pair in orbits[i]])
        orbit_hash = sha_array(order)
    else:
        raise ValueError(f'Unknown split rule {split_rule}')
    if not 0 < len(train) < p*p:
        raise ValueError('Need nonempty train and validation sets')
    return torch.tensor(train),torch.tensor(valid),dict(
        split_sha256=sha_array(np.concatenate([train,valid])),orbit_id_sha256=orbit_hash,
        train_ids_sha256=sha_array(train),valid_ids_sha256=sha_array(valid),
        realized_fraction=len(train)/(p*p),split_rule=split_rule)


def dataset(p, fraction, split_seed, task, split_rule='ordered', return_metadata=False):
    a,b = torch.meshgrid(torch.arange(p),torch.arange(p),indexing='ij')
    pairs = torch.stack([a.flatten(),b.flatten()],dim=1)
    labels = {'add': lambda: (a+b)%p,'subtract': lambda: (a-b)%p,
              'multiply': lambda: (a*b)%p}[task]().flatten()
    train,valid,info = split_indices(p,fraction,split_seed,split_rule)
    result = (pairs,labels,train,valid,info['split_sha256'])
    return (*result,info) if return_metadata else result


def spectral_fraction(logits,p,task):
    """Class-centered logit energy in compatible translation Fourier modes."""
    if task not in ('add','subtract'):
        return None
    arr = logits.detach().numpy().reshape(p,p,p).astype(np.float64)
    arr -= arr.mean(axis=2,keepdims=True)
    energy = abs(np.fft.fftn(arr))**2
    k = np.arange(1,p)
    kb = k if task=='add' else (-k)%p
    return float(energy[k,kb,(-k)%p].sum()/max(energy.sum(),1e-300))


def tensor_hash(tensor):
    return hashlib.sha256(tensor.detach().contiguous().numpy().tobytes()).hexdigest()


def atomic_save(value,path):
    path = Path(path)
    temp = path.with_name(path.name+'.tmp')
    torch.save(value,temp)
    os.replace(temp,path)


def write_json(path,value):
    temp = path.with_name(path.name+'.tmp')
    temp.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    os.replace(temp,path)


def run(config,root,resume=False,stop_after=None,continuation_from=None):
    """Run or exactly resume a config. stop_after is for interruption validation."""
    if resume and continuation_from is not None:
        raise ValueError('Resume and new-horizon continuation are distinct operations')
    root = Path(root)
    root.mkdir(parents=True,exist_ok=True)
    if (root/'summary.json').exists():
        raise FileExistsError(f'Refusing to overwrite completed run {root}')
    if (root/'metadata.json').exists() and not resume:
        raise FileExistsError(f'Incomplete run exists at {root}; explicitly resume or preserve/rerun attempt')
    torch.set_num_threads(config.get('threads',1))
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(config['init_seed'])
    pairs,labels,train,valid,split_hash,data_info = dataset(
        config['p'],config['fraction'],config['split_seed'],config['task'],
        config.get('split_rule','ordered'),True)
    model = PairMLP(config['p'],config['width'],config['activation'])
    if config.get('frozen_hidden',False):
        model.input_weight.requires_grad_(False)
        model.input_bias.requires_grad_(False)
    initial = torch.cat([v.detach().flatten() for v in model.parameters()]).clone()
    hidden_initial_hash = tensor_hash(torch.cat([model.input_weight.flatten(),model.input_bias.flatten()]))
    optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],
        lr=config['lr'],weight_decay=config['weight_decay'],
        betas=tuple(config.get('betas',[0.9,0.999])),eps=config.get('eps',1e-8))
    source_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    metadata = dict(config=config,parameter_count=sum(p.numel() for p in model.parameters()),
        trainable_parameter_count=sum(p.numel() for p in model.parameters() if p.requires_grad),
        n_train=len(train),n_valid=len(valid),split_sha256=split_hash,data_info=data_info,
        train_label_counts=torch.bincount(labels[train],minlength=config['p']).tolist(),
        python=platform.python_version(),torch=torch.__version__,numpy=np.__version__,
        platform=platform.platform(),source_train_sha256=source_hash,
        source_git_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        hidden_initial_sha256=hidden_initial_hash,
        started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))
    zero_mask = (pairs[:,0]==0)|(pairs[:,1]==0)
    metadata['data_info'].update(zero_related_train=int(zero_mask[train].sum()),
                                 zero_related_valid=int(zero_mask[valid].sum()))
    start_step = 0
    elapsed_offset = cpu_offset = training_offset = evaluation_offset = 0.
    previous_rows = []
    if resume:
        prior = json.loads((root/'metadata.json').read_text())
        if prior['config'] != config or prior['source_train_sha256'] != source_hash:
            raise ValueError('Resume requires identical configuration and training source')
        metadata = prior
        checkpoint = torch.load(root/'checkpoint.pt',weights_only=False,map_location='cpu')
        model.load_state_dict(checkpoint['model'])
        optimizer.load_state_dict(checkpoint['optimizer'])
        initial = checkpoint['initial_vector']
        torch.set_rng_state(checkpoint['torch_rng_state'])
        start_step = checkpoint['step']
        elapsed_offset,cpu_offset = checkpoint['elapsed_s'],checkpoint['cpu_s']
        training_offset,evaluation_offset = checkpoint['training_s'],checkpoint['evaluation_s']
        rows = [json.loads(line) for line in (root/'curve.jsonl').read_text().splitlines()]
        previous_rows = [r for r in rows if r['step']<=start_step]
        discarded = [r for r in rows if r['step']>start_step]
        if discarded:
            archive = root/f'curve.discarded-after-{start_step}.{time.time_ns()}.jsonl'
            archive.write_text(''.join(json.dumps(r)+'\n' for r in discarded))
        (root/'curve.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in previous_rows))
    elif continuation_from is not None:
        parent = Path(continuation_from)
        prior = json.loads((parent/'metadata.json').read_text())
        allowed_changes = {'steps','onset_horizon'}
        if {k:v for k,v in prior['config'].items() if k not in allowed_changes} != {k:v for k,v in config.items() if k not in allowed_changes}:
            raise ValueError('Continuation permits only a prespecified horizon extension')
        if config['steps']<=prior['config']['steps'] or prior['source_train_sha256']!=source_hash:
            raise ValueError('Continuation requires longer horizon and identical training implementation')
        checkpoint = torch.load(parent/'final.pt',weights_only=False,map_location='cpu')
        model.load_state_dict(checkpoint['model'])
        optimizer.load_state_dict(checkpoint['optimizer'])
        initial = checkpoint['initial_vector']
        torch.set_rng_state(checkpoint['torch_rng_state'])
        start_step = checkpoint['step']
        elapsed_offset,cpu_offset = checkpoint['elapsed_s'],checkpoint['cpu_s']
        training_offset,evaluation_offset = checkpoint['training_s'],checkpoint['evaluation_s']
        previous_rows = [json.loads(line) for line in (parent/'curve.jsonl').read_text().splitlines()]
        metadata['continuation'] = dict(parent=str(parent),parent_final_sha256=hashlib.sha256((parent/'final.pt').read_bytes()).hexdigest(),start_step=start_step)
        write_json(root/'metadata.json',metadata)
        shutil.copy2(parent/'initial.pt',root/'initial.pt')
        (root/'curve.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in previous_rows))
    else:
        write_json(root/'metadata.json',metadata)
        atomic_save(model.state_dict(),root/'initial.pt')
    start = time.perf_counter()
    cpu_start = time.process_time()
    training_s,evaluation_s = training_offset,evaluation_offset
    attempt = dict(started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
                   resume=resume,start_step=start_step,source_train_sha256=source_hash)
    def save_checkpoint(step):
        atomic_save(dict(model=model.state_dict(),optimizer=optimizer.state_dict(),step=step,
            initial_vector=initial,torch_rng_state=torch.get_rng_state(),
            elapsed_s=elapsed_offset+time.perf_counter()-start,
            cpu_s=cpu_offset+time.process_time()-cpu_start,training_s=training_s,
            evaluation_s=evaluation_s,source_train_sha256=source_hash),root/'checkpoint.pt')
    row = previous_rows[-1] if previous_rows else None
    try:
        with (root/'curve.jsonl').open('a' if (resume or continuation_from is not None) else 'w',buffering=1) as stream:
            for step in range(start_step,config['steps']+1):
                already_evaluated = bool(previous_rows and step==start_step and row['step']==step)
                scheduled = step%config['eval_every']==0 or step==config['steps']
                if scheduled and not already_evaluated:
                    begin = time.perf_counter()
                    model.eval()
                    with torch.no_grad():
                        logits = model(pairs)
                        params = torch.cat([v.flatten() for v in model.parameters()])
                        pred = logits.argmax(1)
                        correct = pred==labels
                        row = dict(step=step,
                            train_loss=nn.functional.cross_entropy(logits[train],labels[train]).item(),
                            valid_loss=nn.functional.cross_entropy(logits[valid],labels[valid]).item(),
                            train_acc=correct[train].float().mean().item(),
                            valid_acc=correct[valid].float().mean().item(),
                            weight_norm=params.norm().item(),displacement_norm=(params-initial).norm().item(),
                            spectral_fraction=spectral_fraction(logits,config['p'],config['task']),
                            elapsed_s=elapsed_offset+time.perf_counter()-start,
                            cpu_s=cpu_offset+time.process_time()-cpu_start,training_s=training_s)
                        if config['task']=='multiply':
                            for subset,mask in [('zero',zero_mask[valid]),('nonzero',~zero_mask[valid])]:
                                row[f'valid_{subset}_n'] = int(mask.sum())
                                row[f'valid_{subset}_acc'] = correct[valid][mask].float().mean().item() if mask.any() else None
                    evaluation_s += time.perf_counter()-begin
                    stream.write(json.dumps(row,allow_nan=False)+'\n')
                    if step==0 or step%config.get('report_every',10000)==0 or step==config['steps']:
                        print(json.dumps(dict(run=root.name,**row),allow_nan=False),flush=True)
                    model.train()
                if step%config.get('checkpoint_every',10000)==0 or step==config['steps'] or step==stop_after:
                    save_checkpoint(step)
                if stop_after is not None and step>=stop_after and step<config['steps']:
                    attempt.update(status='validation_interruption',end_step=step)
                    return dict(status='validation_interruption',step=step)
                if step==config['steps']:
                    break
                begin = time.perf_counter()
                optimizer.zero_grad(set_to_none=True)
                loss = nn.functional.cross_entropy(model(pairs[train]),labels[train])
                if not torch.isfinite(loss):
                    raise FloatingPointError(f'Nonfinite loss at step {step}')
                loss.backward()
                optimizer.step()
                training_s += time.perf_counter()-begin
        hidden_final_hash = tensor_hash(torch.cat([model.input_weight.flatten(),model.input_bias.flatten()]))
        if config.get('frozen_hidden',False) and hidden_final_hash != hidden_initial_hash:
            raise AssertionError('Frozen hidden parameters changed')
        # The final checkpoint already retains model + optimizer and resume state.
        # A hard link gives a stable terminal name without duplicating stored bytes.
        if (root/'final.pt').exists():
            (root/'final.pt').unlink()
        os.link(root/'checkpoint.pt',root/'final.pt')
        summary = dict(**metadata,final=row,
            elapsed_s=elapsed_offset+time.perf_counter()-start,
            cpu_s=cpu_offset+time.process_time()-cpu_start,training_s=training_s,evaluation_s=evaluation_s,
            process_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            hidden_final_sha256=hidden_final_hash,
            frozen_hidden_unchanged=(hidden_initial_hash==hidden_final_hash) if config.get('frozen_hidden',False) else None)
        write_json(root/'summary.json',summary)
        attempt.update(status='completed',end_step=step)
        return summary
    except BaseException as error:
        attempt.update(status='failed',error_type=type(error).__name__,error=str(error))
        raise
    finally:
        attempt.update(ended_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
                       segment_wall_s=time.perf_counter()-start,segment_cpu_s=time.process_time()-cpu_start)
        with (root/'attempts.jsonl').open('a') as f:
            f.write(json.dumps(attempt)+'\n')


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--resume',action='store_true')
    parser.add_argument('--continue-from')
    args = parser.parse_args()
    run(json.loads(Path(args.config).read_text()),args.output,args.resume,continuation_from=args.continue_from)
