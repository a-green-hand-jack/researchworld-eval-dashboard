"""Execute frozen stages with checkpointing; restart safely after interruption."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument("--workspace",default=str(root),help="Output workspace; delivery-root users pass .")
args=parser.parse_args()
workspace=Path(args.workspace).resolve()
workspace.mkdir(parents=True,exist_ok=True)
# Child modules must come from this copied source, even with another editable
# gatebench install on the host. Data likewise belong to this source layout.
os.environ['PYTHONPATH']=str(root/'src')
os.environ['GATEBENCH_DATA_DIR']=str(root/'data')
os.chdir(workspace)
manifest=json.loads((root/"configs/production_manifest.json").read_text())
if manifest["status"]!="frozen; independent feasibility cleared":
    raise ValueError("Independent production feasibility gate has not been recorded")
# Refuse to resume superseded/mixed-source cells (for example v1 boundary
# outputs with corrected v2 code). Keep the old files and name the mismatch.
current_sources={name:hashlib.sha256((root/'src/gatebench'/name).read_bytes()).hexdigest()
                 for name in ['core.py','graphs.py','run.py']}
for stage in ['core','noise','imbalance']:
    config=json.loads((root/f'configs/production_{stage}.json').read_text())
    for checkpoint in (workspace/config['output']).glob('*.parquet'):
        if checkpoint.name.endswith('.tmp.parquet'):continue
        metadata=checkpoint.with_suffix('.json')
        if not metadata.exists():raise RuntimeError(f'Missing checkpoint metadata: {checkpoint}')
        recorded=json.loads(metadata.read_text())
        if recorded.get('source_sha256')!=current_sources:
            raise RuntimeError(f'Superseded or mixed-source checkpoint: {checkpoint}. Preserve it as provenance and use a clean workspace.')
        config_hash=hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()
        if recorded.get('config_sha256')!=config_hash:
            raise RuntimeError(f'Checkpoint config mismatch: {checkpoint}')
for name in ['core','noise','imbalance']:
    print(f'HUTIAN_WAKE: starting production stage {name}',flush=True)
    subprocess.run([sys.executable,'-u','-m','gatebench.run',str(root/f'configs/production_{name}.json')],check=True)
    subprocess.run([sys.executable,'-u','-m','gatebench.production_risk',str(root/f'configs/production_{name}.json')],check=True)
    print(f'HUTIAN_WAKE: finished production stage {name}',flush=True)
subprocess.run([sys.executable,'-m','gatebench.support_bounds'],check=True)
subprocess.run([sys.executable,'-m','gatebench.summarize','results/production_core',
                'results/production_noise','results/production_imbalance','--output','results/summary'],check=True)
print('HUTIAN_WAKE: all production and summaries complete',flush=True)
