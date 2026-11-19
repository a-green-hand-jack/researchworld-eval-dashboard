"""Run independent changed-background cells in one managed resource queue."""
import argparse, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser()
p.add_argument('--pilot', action='store_true')
p.add_argument('--output', default='results/background')
p.add_argument('--main-results', default='results')
a = p.parse_args()
for d in ['acs', 'diabetes']:
    for m in ['logistic', 'forest', 'histboost']:
        command = [sys.executable, '-u', str(ROOT/'scripts/run_background_sensitivity.py'),
                   '--dataset', d, '--model', m, '--output', a.output, '--main-results', a.main_results]
        if a.pilot:
            command.append('--pilot')
        subprocess.run(command, cwd=ROOT, check=True)
print('HUTIAN_WAKE: all changed-background queue cells completed', flush=True)
