"""Install completed corrected shards, summarize, audit and replay the fixed grid.

Run as a tracked resource job after all three shard receipts exist. This never
runs on partial shards and never mixes old-source raw rows into corrected data.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

p=argparse.ArgumentParser();p.add_argument('--workspace',required=True)
p.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));a=p.parse_args()
root=Path(a.root).resolve();workspace=Path(a.workspace).resolve()
code=root/'code' if (root/'code/configs').exists() else root
notes=root/('analysis' if code!=root else 'notes')
launch=json.loads((notes/'execution_manifest.json').read_text())
assert all(hashlib.sha256((code/'src/gatebench'/n).read_bytes()).hexdigest()==v for n,v in launch['source_sha256'].items())
receipts=[json.loads((workspace/f'shard{s}_receipt.json').read_text()) for s in range(3)]
assert all(r['status']=='completed' and len(r['cells'])==34 for r in receipts)
keys=[(c['panel'],c['cell_id']) for r in receipts for c in r['cells']]
assert len(keys)==102 and len(set(keys))==102
# Retain local pre-correction artifacts in addition to the pushed archive branch.
archive=root.parent/'roundoff-v1-local';archive.mkdir(exist_ok=True)
for name in ['production_core','production_noise','production_imbalance','core_summary','summary','diagnostics']:
    destination=root/'results'/name
    if destination.exists():
        saved=archive/name
        if saved.exists():raise RuntimeError(f'Archive already exists; reconcile explicitly: {saved}')
        shutil.move(destination,saved)
    source=workspace/'results'/name
    if source.exists():shutil.copytree(source,destination)
(notes/'corrected_shard_receipts.json').write_text(json.dumps(receipts,indent=2))
env=os.environ.copy();env['PYTHONPATH']=str(code/'src');env['GATEBENCH_DATA_DIR']=str(code/'data')
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:env[key]='1'
commands=[
    [sys.executable,'-m','gatebench.support_bounds'],
    [sys.executable,'-m','gatebench.summarize','results/production_core','results/production_noise','results/production_imbalance','--output','results/summary'],
    [sys.executable,'-m','gatebench.summarize','results/production_core','--output','results/core_summary'],
    [sys.executable,str(code/'scripts/finalize_results.py'),'--root',str(root)],
    [sys.executable,str(code/'scripts/audit_v2_dependencies.py'),'--root',str(root)],
    [sys.executable,str(code/'scripts/replay_selected.py'),'--source',str(root),'--workspace',str(root.parent/'corrected-replay')],
    [sys.executable,str(code/'scripts/core_report.py')],
    [sys.executable,str(code/'scripts/final_report.py')],
]
records=[]
for command in commands:
    start=time.perf_counter();subprocess.run(command,cwd=root,env=env,check=True)
    records.append(dict(command=command,wall_seconds=time.perf_counter()-start))
    (notes/'corrected_finalization_timings.json').write_text(json.dumps(records,indent=2))
    print('HUTIAN_WAKE: corrected finalization completed '+command[1],flush=True)
print('HUTIAN_WAKE: corrected full study audits replay and claim map complete',flush=True)
