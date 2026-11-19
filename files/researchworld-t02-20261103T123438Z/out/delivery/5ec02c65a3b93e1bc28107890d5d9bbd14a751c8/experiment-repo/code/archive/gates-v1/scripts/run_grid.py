"""Run an explicit grid; each config and every failed attempt remains recoverable."""
import argparse
import json
import sys
import traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from train import run

parser = argparse.ArgumentParser()
parser.add_argument('grid')
parser.add_argument('output')
parser.add_argument('--resume',action='store_true')
args = parser.parse_args()
grid = json.loads(Path(args.grid).read_text())
if isinstance(grid,dict):
    grid = grid['runs']
if len({item['name'] for item in grid}) != len(grid):
    raise ValueError('Duplicate run names')
failed = []
for item in grid:
    name = item['name']
    config = {k:v for k,v in item.items() if k not in ('name','family','block','stage')}
    destination = Path(args.output)/name
    if (destination/'summary.json').exists():
        actual = json.loads((destination/'metadata.json').read_text())['config']
        if actual != config:
            raise ValueError(f'Completed-run configuration mismatch at {destination}')
        print(f'Skip completed run {name}',flush=True)
        continue
    try:
        run(config,destination,args.resume and (destination/'metadata.json').exists())
        print(f'HUTIAN_WAKE: Completed run {name}',flush=True)
    except Exception:
        failed.append(name)
        traceback.print_exc()
        print(f'HUTIAN_WAKE: Failed run {name}',flush=True)
if failed:
    raise SystemExit(f'Failed configurations (retained): {failed}')
