"""Inspect first complete German checkpoints without an interim reliability claim."""
import json,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
pilot={}
for line in (ROOT/'results/pilot.jsonl').read_text().splitlines():
    x=json.loads(line)
    if x.get('kind')=='model':pilot[(x['dataset'],x['model'])]=x['info']
records=[];sig=json.loads((ROOT/'results/main_execution_manifest.json').read_text())['source_config_signature']
for model in ['logistic','forest','histboost']:
    cell=ROOT/'results/main'/f'german_{model}';m=json.loads((cell/'metadata.json').read_text());info=m['info'];old=pilot[('german',model)]
    assert m['signature']==sig
    for path,h in m['source_hashes'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==h
    # Original pilot predates separate source-ID fields; German positions equal
    # raw IDs, so the retained original selection indices are the correct check.
    for field in ['explain_ids','background_ids','train_ids','test_ids']:assert info[field]==old[field]
    assert info['source_explain_ids']==info['explain_ids'] and info['source_background_ids']==info['background_ids']
    assert not set(info['source_explain_ids'][:2])&set(info['source_explain_ids'][2:])
    with np.load(cell/'instance_000.npz',allow_pickle=False) as a:
        rows=json.loads(a['run_records'].item());rr=json.loads(a['reference_record'].item());ref=a['reference'];phis=a['attributions'];assert a['signature'].item()==sig
    assert len(rows)==180 and phis.shape==(180,20)
    ae=np.abs(phis-ref).sum(axis=1);nl1=ae/max(np.abs(ref).sum(),.01)
    assert np.max(np.abs(nl1-np.array([r['nl1_error'] for r in rows])))<1e-12
    re=abs(ref.sum()-(rr['v_full']-rr['v_empty']));se=np.abs(phis.sum(axis=1)-ref.sum()).max()
    assert re<1e-8 and se<1e-6
    records.append(dict(dataset='german',model=model,instance=0,actual_stochastic_calls=len(rows),reference_efficiency_residual=float(re),max_run_efficiency_residual=float(se),source_and_pilot_selection_match=True,warnings=sum(len(r['warnings']) for r in rows),exact_reference_cpu_seconds=rr['cpu_seconds'],stochastic_cpu_seconds=sum(r['cpu_seconds'] for r in rows)))
x=dict(status='initial_checkpoint_validation_not_complete_study',scope='first completed input in each German model; procedural checks only, no reliability-rate inference',signature=sig,records=records)
(ROOT/'results/main_initial_check.json').write_text(json.dumps(x,indent=2)+'\n');print(json.dumps(x),flush=True)
