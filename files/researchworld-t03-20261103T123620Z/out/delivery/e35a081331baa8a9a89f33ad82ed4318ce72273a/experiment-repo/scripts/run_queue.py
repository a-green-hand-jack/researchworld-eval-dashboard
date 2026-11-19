"""Sequential cell queue inside one managed resource job; no shell/backgrounding."""
import argparse,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('cells',nargs='+',help='dataset:model');p.add_argument('--output',default='results/main');args=p.parse_args()
for cell in args.cells:
 dataset,model=cell.split(':',1)
 print(f'HUTIAN_WAKE: starting main cell {cell}',flush=True)
 subprocess.run([sys.executable,'-u',str(ROOT/'scripts/run_study.py'),'--dataset',dataset,'--model',model,'--output',args.output],cwd=ROOT,check=True)
print('HUTIAN_WAKE: all queued main cells completed',flush=True)
