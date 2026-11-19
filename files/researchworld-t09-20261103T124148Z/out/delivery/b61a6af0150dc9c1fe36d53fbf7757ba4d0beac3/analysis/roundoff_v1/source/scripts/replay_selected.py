"""Clean replay of predeclared core cells, comparing every scientific output.

Selection is structural (sparse and dense regular graphs, both designs), not a
selection by estimator success. Repetition count and streams equal production.
Run in a separate output workspace to avoid checkpoint reuse.
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
import numpy as np
import pandas as pd

p=argparse.ArgumentParser();p.add_argument('--source',default='.')
p.add_argument('--workspace',required=True);a=p.parse_args()
root=Path(a.source).resolve();work=Path(a.workspace).resolve()
source_code=root/'code' if (root/'code/configs').exists() else root
notes=root/'analysis' if source_code!=root else root/'notes'
if work==root or (work/'results').exists():
    raise ValueError('Replay requires a clean workspace, distinct from the source')
work.mkdir(parents=True,exist_ok=True)
# Reproduce from a separate source copy, without inheriting an editable install.
code=work/'code'
for name in ['src','configs']:
    shutil.copytree(source_code/name,code/name,ignore=shutil.ignore_patterns('__pycache__'))
config=json.loads((code/'configs/production_core.json').read_text())
config['graphs']=[s for s in config['graphs'] if s.get('seed')==201 and s.get('n')==2000 and s.get('degree') in [4,80] and s['kind']=='regular']
assert len(config['graphs'])==2
config_file=work/'replay_config.json';config_file.write_text(json.dumps(config,indent=2))
env=os.environ.copy();env['PYTHONPATH']=str(code/'src')
env['GATEBENCH_DATA_DIR']=str(source_code/'data')
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:env[key]='1'
start=time.perf_counter()
subprocess.run([sys.executable,'-u','-m','gatebench.run',str(config_file)],cwd=work,env=env,check=True)
records=[]
for file in sorted((work/config['output']).glob('*.parquet')):
    old=root/config['output']/file.name
    assert old.exists(),f'Original production cell not complete: {old}'
    f=pd.read_parquet(file);g=pd.read_parquet(old)
    # Exact array comparison preserves NaNs, strings, failure flags and seeds.
    pd.testing.assert_frame_equal(f,g,check_exact=True)
    records.append(dict(cell=file.stem,rows=len(f),all_columns_bitwise_equal=True,
        original_sha256=hashlib.sha256(old.read_bytes()).hexdigest(),
        replay_sha256=hashlib.sha256(file.read_bytes()).hexdigest()))
report=dict(status='passed',selection='regular n2000 degree4/80 seed201, both designs; original R400 streams',
    cells=records,rows=sum(r['rows'] for r in records),wall_seconds=time.perf_counter()-start,
    source_sha256={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in (code/'src/gatebench').glob('*.py')},
    command='python3 scripts/replay_selected.py --source . --workspace CLEAN_DIRECTORY')
(notes/'reproduction_audit.json').write_text(json.dumps(report,indent=2))
print('HUTIAN_WAKE: clean selected-cell replay '+report['status'],flush=True)
