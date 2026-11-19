"""Independently audit registered raw runs; require all204 before final handoff."""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import torch
from train import dataset,PairMLP

parser = argparse.ArgumentParser()
parser.add_argument('root')
parser.add_argument('--registry',default='configs/confirmatory.json')
parser.add_argument('--require-complete',action='store_true')
parser.add_argument('--output',required=True)
args = parser.parse_args()
torch.set_num_threads(1)
registry = {r['name']:r for r in json.loads(Path(args.registry).read_text())['runs']}
missing,incomplete,passed = [],[],[]
diagnostics = []
for name,entry in registry.items():
    directory = Path(args.root)/name
    if not (directory/'metadata.json').exists():
        missing.append(name)
        continue
    if not (directory/'summary.json').exists():
        incomplete.append(name)
        continue
    metadata = json.loads((directory/'metadata.json').read_text())
    config = {k:v for k,v in entry.items() if k not in ['name','family','block','stage']}
    assert metadata['config']==config, name
    pairs,labels,train,valid,digest,info = dataset(config['p'],config['fraction'],config['split_seed'],
        config['task'],config['split_rule'],True)
    assert digest==metadata['split_sha256'] and info['orbit_id_sha256']==metadata['data_info']['orbit_id_sha256'],name
    train_ids,valid_ids = set(train.tolist()),set(valid.tolist())
    assert train_ids.isdisjoint(valid_ids) and train_ids|valid_ids==set(range(config['p']**2)),name
    def orbit_ids(indices):
        return {min(i//config['p'],i%config['p'])*config['p']+max(i//config['p'],i%config['p']) for i in indices}
    train_orbits,valid_orbits = orbit_ids(train_ids),orbit_ids(valid_ids)
    overlap = train_orbits&valid_orbits
    if config['split_rule']=='orbit':
        assert not overlap,name
    diagnostics.append(dict(name=name,task=config['task'],split_rule=config['split_rule'],
        split_sha256=digest,orbit_id_sha256=info['orbit_id_sha256'],
        n_train=len(train),n_valid=len(valid),realized_fraction=len(train)/(config['p']**2),
        ordered_pairs_disjoint=True,exhaustive_union=True,
        n_train_orbits=len(train_orbits),n_valid_orbits=len(valid_orbits),
        overlapping_unordered_orbits=len(overlap),unordered_orbits_disjoint=not overlap))
    assert metadata['n_train']==len(train) and metadata['n_valid']==len(valid),name
    assert metadata['parameter_count']==94*config['width']+31,name
    expected_trainable=31*config['width']+31 if config['frozen_hidden'] else 94*config['width']+31
    assert metadata['trainable_parameter_count']==expected_trainable,name
    curve = [json.loads(line) for line in (directory/'curve.jsonl').read_text().splitlines()]
    assert [r['step'] for r in curve]==list(range(0,60201,100)),name
    assert all(0<=r['train_acc']<=1 and 0<=r['valid_acc']<=1 for r in curve),name
    assert all(math.isfinite(r[k]) for r in curve for k in ['train_loss','valid_loss','weight_norm','cpu_s']),name
    assert all(a['cpu_s']<=b['cpu_s'] for a,b in zip(curve,curve[1:])),name
    final = torch.load(directory/'final.pt',weights_only=False)
    assert final['step']==60200,name
    assert final['optimizer']['state'],name
    assert all(int(state['step'])==60200 for state in final['optimizer']['state'].values()),name
    assert all(torch.isfinite(value).all() for value in final['model'].values()),name
    summary = json.loads((directory/'summary.json').read_text())
    assert summary['final']==curve[-1],name
    assert final['source_train_sha256']==metadata['source_train_sha256'],name
    # Validate seed identity and scientific endpoints independently of stored metrics.
    initial = torch.load(directory/'initial.pt',weights_only=True)
    torch.manual_seed(config['init_seed'])
    seeded = PairMLP(config['p'],config['width'],config['activation']).state_dict()
    assert initial.keys()==seeded.keys(),name
    assert all(torch.equal(initial[k],seeded[k]) for k in initial),name
    weights=final['model']
    # Replay the actual float32 indexed implementation at strict metric tolerance.
    replay=PairMLP(config['p'],config['width'],config['activation'])
    replay.load_state_dict(weights)
    with torch.no_grad():
        logits=replay(pairs)
    pred=logits.argmax(1)
    for subset,indices in [('train',train),('valid',valid)]:
        accuracy=(pred[indices]==labels[indices]).float().mean().item()
        loss=torch.nn.functional.cross_entropy(logits[indices],labels[indices]).item()
        assert abs(accuracy-curve[-1][subset+'_acc'])<1e-7,(name,subset,'accuracy')
        assert math.isclose(loss,curve[-1][subset+'_loss'],rel_tol=1e-5,abs_tol=1e-5),(name,subset,'loss')
    # Independent dense float64 evaluation and scale-aware float32 forward bound.
    # All registered activations are ReLU (exact,1-Lipschitz). A different
    # activation needs its own rounding/error propagation before this audit applies.
    assert config['activation']=='relu',(name,'unimplemented activation error bound')
    encoded=torch.nn.functional.one_hot(pairs,num_classes=config['p']).double().reshape(len(pairs),-1)
    wi,bi=weights['input_weight'].double(),weights['input_bias'].double()
    wo,bo=weights['output.weight'].double(),weights['output.bias'].double()
    hidden=torch.relu(encoded@wi.T+bi)
    reference=hidden@wo.T+bo
    unit_roundoff=torch.finfo(torch.float32).eps/2
    gamma=lambda n:n*unit_roundoff/(1-n*unit_roundoff)
    hidden_error=gamma(2)*(encoded@wi.abs().T+bi.abs())
    bound=(hidden_error@wo.abs().T + gamma(2*config['width']+1)*
           ((hidden.abs()+hidden_error)@wo.abs().T+bo.abs()))
    error=(logits.double()-reference).abs()
    assert torch.all(error<=bound+1e-10),(name,'float32 forward roundoff bound')
    reference_pred=reference.argmax(1)
    differences=(reference_pred!=pred)
    top=reference.topk(2,dim=1).values
    certified=(top[:,0]-top[:,1])>2*bound.max(1).values+2e-10
    assert not torch.any(differences&certified),(name,'prediction differs outside roundoff ambiguity')
    precision=dict(reference_dtype='float64 dense one-hot',production_dtype='float32 indexed',
        forward_bound='gamma2 input sum, ReLU Lipschitz1, gamma(2width+1) output dot; see reproduction/numerical_audit.md',
        max_abs_logit_error=error.max().item(),max_abs_logit_bound=bound.max().item(),
        max_error_fraction_of_bound=(error/(bound+1e-10)).max().item(),
        total_prediction_differences=int(differences.sum()),
        roundoff_certified_prediction_count=int(certified.sum()),
        roundoff_ambiguous_prediction_count=int((~certified).sum()),
        differing_ordered_pair_ids=torch.nonzero(differences).flatten().tolist(),subsets={})
    for subset,indices in [('train',train),('valid',valid)]:
        loss64=torch.nn.functional.cross_entropy(reference[indices],labels[indices]).item()
        precision['subsets'][subset]=dict(reference_loss=loss64,
            recorded_float32_loss=curve[-1][subset+'_loss'],
            reference_accuracy=(reference_pred[indices]==labels[indices]).double().mean().item(),
            recorded_float32_accuracy=curve[-1][subset+'_acc'],
            prediction_differences=int(differences[indices].sum()))
    vector=torch.cat([v.flatten() for v in weights.values()])
    initial_vector=torch.cat([v.flatten() for v in initial.values()])
    assert torch.equal(initial_vector,final['initial_vector']),name
    assert math.isclose(vector.norm().item(),curve[-1]['weight_norm'],rel_tol=1e-6),name
    assert math.isclose((vector-initial_vector).norm().item(),curve[-1]['displacement_norm'],rel_tol=1e-6,abs_tol=1e-6),name
    diagnostics[-1].update(initial_seed_tensors_verified=True,terminal_predictions_recomputed=True,
        terminal_prediction_sha256=hashlib.sha256(pred.numpy().astype('<i8').tobytes()).hexdigest(),
        numerical_precision=precision)
    if config['frozen_hidden']:
        initial = torch.load(directory/'initial.pt',weights_only=True)
        assert torch.equal(initial['input_weight'],final['model']['input_weight']),name
        assert torch.equal(initial['input_bias'],final['model']['input_bias']),name
        peer = Path(args.root)/f'main_w{config["width"]:03d}_b{entry["block"]:02d}'/'initial.pt'
        if peer.exists():
            full = torch.load(peer,weights_only=True)
            assert all(torch.equal(initial[k],full[k]) for k in initial),name
    if config['task']=='multiply':
        zero=(pairs[:,0]==0)|(pairs[:,1]==0)
        assert int(zero.sum())==61,name
        nz,nnz = int(zero[valid].sum()),int((~zero[valid]).sum())
        assert all(r['valid_zero_n']==nz and r['valid_nonzero_n']==nnz for r in curve),name
        assert all(abs((r['valid_zero_acc']*nz+r['valid_nonzero_acc']*nnz)/len(valid)-r['valid_acc'])<1e-6 for r in curve),name
        diagnostics[-1].update(zero_total=61,zero_train=int(zero[train].sum()),
            zero_valid=nz,nonzero_valid=nnz)
    passed.append(name)
result = dict(status='PASS' if not missing and not incomplete else 'PARTIAL',completed_audited=len(passed),
              missing=missing,incomplete=incomplete,passed=passed,registered_total=len(registry),split_diagnostics=diagnostics)
Path(args.output).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['missing','incomplete','passed','split_diagnostics']}))
if args.require_complete and (missing or incomplete):
    raise SystemExit('Incomplete registered matrix')
