"""Execute frozen stages with checkpointing; restart safely after interruption."""
import argparse
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
os.environ.setdefault("GATEBENCH_DATA_DIR",str(root/"data"))
os.chdir(workspace)
manifest=json.loads((root/"configs/production_manifest.json").read_text())
if manifest["status"]!="frozen; independent feasibility cleared":
    raise ValueError("Independent production feasibility gate has not been recorded")
for name in ['core','noise','imbalance']:
    print(f'HUTIAN_WAKE: starting production stage {name}',flush=True)
    subprocess.run([sys.executable,'-u','-m','gatebench.run',str(root/f'configs/production_{name}.json')],check=True)
    subprocess.run([sys.executable,'-u','-m','gatebench.production_risk',str(root/f'configs/production_{name}.json')],check=True)
    print(f'HUTIAN_WAKE: finished production stage {name}',flush=True)
subprocess.run([sys.executable,'-m','gatebench.support_bounds'],check=True)
subprocess.run([sys.executable,'-m','gatebench.summarize','results/production_core',
                'results/production_noise','results/production_imbalance','--output','results/summary'],check=True)
print('HUTIAN_WAKE: all production and summaries complete',flush=True)
