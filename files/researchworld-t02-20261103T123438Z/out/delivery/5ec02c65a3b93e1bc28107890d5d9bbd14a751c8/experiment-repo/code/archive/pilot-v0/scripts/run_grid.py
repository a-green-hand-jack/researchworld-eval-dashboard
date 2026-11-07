"""Run an explicit grid sequentially; each experiment is separately recoverable."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from train import run

parser = argparse.ArgumentParser()
parser.add_argument('grid')
parser.add_argument('output')
args = parser.parse_args()
grid = json.loads(Path(args.grid).read_text())
for item in grid:
    name = item['name']
    config = {k:v for k,v in item.items() if k != 'name'}
    destination = Path(args.output)/name
    if (destination/'summary.json').exists():
        print(f'Skip completed run {name}',flush=True)
        continue
    run(config,destination)
    print(f'HUTIAN_WAKE: Completed exploratory run {name}',flush=True)
