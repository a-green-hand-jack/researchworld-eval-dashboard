"""Non-outcome-selected controls, exact resume, continuation, and horizon checks."""
import hashlib
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import torch
from train import PairMLP,dataset,run
from events import sustained_event,summarize_curve,paired_binary_interval

root = Path(sys.argv[1])
root.mkdir(parents=True,exist_ok=True)
torch.set_num_threads(1)
for w in [32,64,128,256,512]:
    model = PairMLP(31,w)
    assert sum(p.numel() for p in model.parameters())==94*w+31
for seed in [100,1100,1107]:
    x,y,tr,va,digest,info = dataset(31,.5,seed,'add','orbit',True)
    assert set(tr.tolist()).isdisjoint(va.tolist())
    assert sorted(tr.tolist()+va.tolist())==list(range(961))
    train_set = set(tr.tolist())
    assert all((b*31+a in train_set)==(a*31+b in train_set) for a in range(31) for b in range(31))
    assert info['orbit_id_sha256'] is not None
    x,y,_,_,_ = dataset(31,.5,seed,'multiply')
    assert torch.equal(y,(x[:,0]*x[:,1])%31)
    assert (y==0).sum()==61
rows = [dict(step=i,train_acc=1.,valid_acc=.96 if i>=60000 else .2) for i in range(59800,60201,100)]
e = summarize_curve(rows,horizon=60000)
assert e['valid_event']['step']==60000 and e['valid_event']['confirmed_step']==60200
assert e['restricted_valid_time']==60000 and e['valid_event']['observed']
rows = [dict(step=i,train_acc=1.,valid_acc=.96 if i>=60100 else .2) for i in range(59800,60301,100)]
assert not summarize_curve(rows,horizon=60000)['valid_event']['observed']
assert paired_binary_interval([0]*8,[0]*8)['ci_high']>.4
assert paired_binary_interval([0]*8,[1]*8)['ci_low']>0
assert paired_binary_interval([1]*8,[0]*8)['ci_high']<0
base = dict(p=7,width=13,fraction=.5,task='add',activation='relu',lr=.001,weight_decay=1.,
            steps=600,eval_every=100,report_every=10000,checkpoint_every=200,
            split_seed=100,init_seed=200,threads=1,split_rule='ordered',frozen_hidden=False)
run(base,root/'uninterrupted')
run(base,root/'resumed',stop_after=200)
run(base,root/'resumed',resume=True)
run(dict(base,steps=200),root/'short')
parent_hash = hashlib.sha256((root/'short/final.pt').read_bytes()).hexdigest()
run(base,root/'continued',continuation_from=root/'short')
assert parent_hash==hashlib.sha256((root/'short/final.pt').read_bytes()).hexdigest()
reference = torch.load(root/'uninterrupted/final.pt',weights_only=False)
for name in ['resumed','continued']:
    actual = torch.load(root/name/'final.pt',weights_only=False)
    assert all(torch.equal(reference['model'][k],actual['model'][k]) for k in reference['model'])
    assert reference['optimizer']['param_groups']==actual['optimizer']['param_groups']
    for index in reference['optimizer']['state']:
        for key,value in reference['optimizer']['state'][index].items():
            other = actual['optimizer']['state'][index][key]
            assert torch.equal(value,other) if isinstance(value,torch.Tensor) else value==other
    reference_rows = [json.loads(s) for s in (root/'uninterrupted/curve.jsonl').read_text().splitlines()]
    actual_rows = [json.loads(s) for s in (root/name/'curve.jsonl').read_text().splitlines()]
    for a,b in zip(reference_rows,actual_rows):
        assert {k:v for k,v in a.items() if k not in ['elapsed_s','cpu_s','training_s']}=={k:v for k,v in b.items() if k not in ['elapsed_s','cpu_s','training_s']}
run(dict(base,frozen_hidden=True),root/'frozen')
a = torch.load(root/'uninterrupted/initial.pt',weights_only=True)
b = torch.load(root/'frozen/initial.pt',weights_only=True)
assert all(torch.equal(a[k],b[k]) for k in a)
summary = json.loads((root/'frozen/summary.json').read_text())
assert summary['frozen_hidden_unchanged']
assert summary['trainable_parameter_count']==7*13+7
result = dict(status='PASS',checks=['exact width parameter counts','orbit disjointness and reverse-pair grouping',
    'multiplication labels including zeros','60000 onset confirmed at60200','after-horizon events excluded',
    'nondegenerate exact paired binary bounds','bitwise model/optimizer resume','bitwise optional continuation',
    'parent result immutable','identical full/frozen initialization','frozen hidden hashes unchanged'])
(root/'checks.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
