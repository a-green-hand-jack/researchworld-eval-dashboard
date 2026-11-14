#!/usr/bin/env python3
"""Finalize completed result directories; never inspect incomplete runs."""
import argparse,json,subprocess,sys
from pathlib import Path
ap=argparse.ArgumentParser(); ap.add_argument('directories',nargs='+'); ap.add_argument('--out',default='results'); a=ap.parse_args()
for d in a.directories:
 m=json.loads((Path(d)/'metadata.json').read_text())
 if 'elapsed_seconds' not in m: raise RuntimeError('Run incomplete: '+d)
for script in ['add_exact_baseline.py','add_full_eb_baseline.py']:
 subprocess.run([sys.executable,'code/'+script,*a.directories],check=True)
subprocess.run([sys.executable,'code/summarize.py',*a.directories,'--out',a.out],check=True)
if a.out=='results': subprocess.run([sys.executable,'code/coverage_diagnostics.py'],check=True)
print('HUTIAN_WAKE: finalized numeric summaries in '+a.out,flush=True)
