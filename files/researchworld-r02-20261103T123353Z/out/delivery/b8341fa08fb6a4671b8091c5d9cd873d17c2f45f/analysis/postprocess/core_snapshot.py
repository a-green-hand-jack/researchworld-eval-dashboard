#!/usr/bin/env python3
"""Release complete prespecified core-cell coverage while sensitivities compute.

No trial is selected by its result; exactly R100 in all ten frozen core cells.
Area estimates remain unaudited until the full scheduled audit is finished.
"""
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

root=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
analysis=Path(__file__).resolve().parents[1]
cfg=json.loads((analysis/'configs/frozen.json').read_text())
core=[c for c in cfg['cells'] if c['id']==c['scenario']+'_k'+str(c['k'])]
assert len(core)==10
manifest=[];rows=[];cases=[];started=time.time()
for cell in core:
    for repeat in range(cfg['repeats']):
        matches=[p for s in [0,1] if (p:=root/f'shard_{s}/checkpoints/{cell["id"]}__{repeat}.json').exists()]
        assert len(matches)==1
        p=matches[0];raw=p.read_bytes();saved=json.loads(raw)
        rr=saved['rows'];allrows=[r for r in rr if r['group']=='all'];valid=[r for r in allrows if r['status']=='ok']
        assert len(valid)==(8 if cell['scenario']=='heterogeneous' else 6)
        assert len(allrows)==(7 if cell['scenario']=='zeros' else len(valid))
        assert all(r['id']==cell['id'] and r['repeat']==repeat and r['seed']==cell['seed']+repeat for r in rr)
        assert len({r['input_hashes'] for r in valid})==len({r['location_coefficients'] for r in valid})==1
        for r in valid:
            assert r['n']==cell['n_test']
            assert 0<=r['covered']<=r['n']
        rows+=rr;cases+=saved['region_cases']
        manifest.append({'path':str(p.relative_to(root)),'sha256':hashlib.sha256(raw).hexdigest()})
with gzip.open(out/'trials.jsonl.gz','wt') as f:
    for row in rows:f.write(json.dumps(row,allow_nan=True)+'\n')
with (out/'region_cases.jsonl').open('w') as f:
    for case in cases:f.write(json.dumps(case,allow_nan=True)+'\n')
source_hashes=[]
for s in [0,1]:
    m=json.load(open(root/f'shard_{s}/run_metadata.json'));source_hashes.append(m['source_hashes'])
assert source_hashes[0]==source_hashes[1]
for path,digest in source_hashes[0].items():
    assert hashlib.sha256((analysis/path).read_bytes()).hexdigest()==digest
subprocess.run([sys.executable,str(analysis/'scripts/summarize.py'),'--input',str(out/'trials.jsonl.gz'),'--output',str(out/'summary')],check=True)
subprocess.run([sys.executable,str(analysis/'postprocess/study_summaries.py'),'--input',str(out/'trials.jsonl.gz'),'--summary',str(out/'summary'),'--config',str(analysis/'configs/frozen.json'),'--output',str(out/'derived')],check=True)
meta={'status':'complete core-cell coverage; entire 19-cell study and numerical audit still running',
      'cells':[c['id'] for c in core],'independent_trials':len(manifest),'rows':len(rows),'cases':len(cases),
      'source_hashes':source_hashes[0],'checkpoint_manifest':manifest,
      'postprocess_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),analysis/'postprocess/study_summaries.py']},
      'started_at_unix':started,'finished_at_unix':time.time(),
      'area_policy':'Retained for reproducibility; final prescribed numerical audit pending, so area rankings withheld.',
      'selection':'Every frozen core cell, every repeat 0..99; no outcome selection; pilots excluded.'}
(out/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
print('HUTIAN_WAKE: complete 1000-trial core coverage bundle with uncertainty and provenance; area rankings pending full audit',flush=True)
