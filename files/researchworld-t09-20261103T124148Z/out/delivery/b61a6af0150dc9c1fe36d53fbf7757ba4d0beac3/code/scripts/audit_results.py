"""Audit executed checkpoints without rerunning scientific simulations."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

p=argparse.ArgumentParser();p.add_argument('--root',default='.');p.add_argument('--complete',action='store_true')
a=p.parse_args();root=Path(a.root)
code=root/'code' if (root/'code/configs').exists() else root
notes=root/'analysis' if code!=root else root/'notes'
ledger=[]
matched={('no_interference','linear'),('linear','linear'),('quadratic','quadratic'),
         ('cubic','cubic'),('threshold','threshold_oracle'),('twohop','twohop')}
report={'complete_required':a.complete,'stages':{},'total_rows':0,'files':[]}
for stage in ['core','noise','imbalance']:
    config=json.loads((code/f'configs/production_{stage}.json').read_text())
    folder=root/config['output'];files=sorted(f for f in folder.glob('*.parquet')
        if not f.name.endswith('.tmp.parquet') and f.with_suffix('.json').exists())
    expected=len(config['graphs'])*len(config['designs'])*len(config['probabilities'])*len(config['rhos'])*len(config['gammas'])
    record=dict(cells=len(files),expected_cells=expected,rows=0,max_matched_bias=0.,undefined=0,unsupported_defined=0)
    expected_ids=set()
    for spec in config['graphs']:
        graph_key=hashlib.sha256(json.dumps(spec,sort_keys=True).encode()).hexdigest()[:16]
        for design in config['designs']:
            for probability in config['probabilities']:
                for rho in config['rhos']:
                    for gamma in config['gammas']:
                        cell=f'{graph_key}_{design}_p{probability}_rho{rho}_gamma{gamma}'
                        expected_ids.add(cell)
                        file=folder/(cell+'.parquet')
                        status='completed' if file in files else 'unrun_or_in_progress'
                        ledger.append(dict(panel=stage,cell_id=cell,graph_spec=json.dumps(spec,sort_keys=True),
                            design=design,p=probability,rho=rho,gamma=gamma,master_seed=config['master_seed'],
                            planned_replicates=config['replicates'],status=status))
    assert {file.stem for file in files} <= expected_ids
    if a.complete:
        assert len(files)==expected,(stage,len(files),expected)
    for file in files:
        f=pd.read_parquet(file)
        meta=json.loads(file.with_suffix('.json').read_text())
        assert len(f)==config['replicates']*len(config['mechanisms'])*(len(config['models'])+2)
        assert f.master_seed.nunique()==1 and f.master_seed.iloc[0]==config['master_seed']
        assert set(f.mechanism)==set(config['mechanisms'])
        assert set(f.model)==set(config['models']+['ht','hajek'])
        assert set(f.design)<=set(config['designs']) and set(f.p)<=set(config['probabilities'])
        assert set(f.rho)<=set(config['rhos']) and set(f.gamma)<=set(config['gammas'])
        assert meta['config_sha256']==hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()
        assert f.cell_id.nunique()==1 and f.cell_id.iloc[0]==file.stem
        assert f.groupby(['mechanism','model']).replicate.nunique().eq(config['replicates']).all()
        assert len(f.pairing_id.unique())==config['replicates']
        assert not f.duplicated(['pairing_id','mechanism','model']).any()
        assert np.allclose(f.error,f.estimate-f.truth,equal_nan=True)
        assert f.groupby('pairing_id').assignment_seed.nunique().max()==1
        assert f.groupby('pairing_id').noise_seed.nunique().max()==1
        assert f.groupby('pairing_id').prediction_seed.nunique().max()==1
        chosen=np.array([(m,k) in matched for m,k in zip(f.mechanism,f.model)]) & f.valid.to_numpy(bool)
        max_bias=float(np.max(np.abs(f.loc[chosen,'conditional_bias'])))
        assert max_bias<1e-7,(file,max_bias)
        if 'source_sha256' in meta:
            # Compare to the recorded frozen source snapshot, not a different checkout.
            expected_hashes=json.loads((notes/'execution_manifest.json').read_text())['source_sha256']
            assert all(meta['source_sha256'][name]==expected_hashes[name] for name in meta['source_sha256'])
        finite=np.isfinite(f.estimate)
        record['rows']+=len(f);record['undefined']+=int((~finite).sum())
        record['unsupported_defined']+=int((finite & ~f.valid).sum())
        record['max_matched_bias']=max(record['max_matched_bias'],max_bias)
        report['files'].append(dict(path=str(file.relative_to(root)),sha256=hashlib.sha256(file.read_bytes()).hexdigest()))
    report['stages'][stage]=record;report['total_rows']+=record['rows']
if a.complete:
    assert report['total_rows']==2937600
out=notes/('production_audit.json' if a.complete else 'checkpoint_audit.json')
out.write_text(json.dumps(report,indent=2))
with (notes/'cell_ledger.csv').open('w') as handle:
    writer=csv.DictWriter(handle,fieldnames=list(ledger[0]));writer.writeheader();writer.writerows(ledger)
print(json.dumps({k:v for k,v in report.items() if k!='files'},indent=2))
