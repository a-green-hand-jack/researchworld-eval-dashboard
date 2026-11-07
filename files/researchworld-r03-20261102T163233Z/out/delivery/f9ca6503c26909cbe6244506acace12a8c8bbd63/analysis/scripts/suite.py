import os,pathlib,subprocess,time,json,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
conditions=[('mteb','random'),('mteb','provider'),('mteb','missing30'),('mteb','missing60'),('mteb','dense_history'),('mteb_wide','random'),('mteb_mixed','random'),('open_llm','random'),('open_llm','provider'),('open_llm','temporal')]
import argparse
p=argparse.ArgumentParser();p.add_argument('--secondary',action='store_true');a=p.parse_args()
if a.secondary:conditions=[c for c in conditions if c[0]=='open_llm']
start=time.time()
for dataset,condition in conditions:
 command=[sys.executable,'-u','scripts/run.py','--dataset',dataset,'--condition',condition,'--seeds','10','--out',f'results/{dataset}_{condition}']
 print('RUN',command,flush=True);subprocess.run(command,cwd=ROOT,check=True)
print('HUTIAN_WAKE: full experiment suite completed',time.time()-start,flush=True)
