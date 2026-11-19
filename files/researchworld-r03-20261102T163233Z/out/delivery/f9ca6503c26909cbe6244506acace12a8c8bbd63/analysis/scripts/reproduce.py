"""Recompute the complete numerical study from the downloaded pinned sources."""
import argparse,subprocess,os,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--prepared',action='store_true');p.add_argument('--check-only',action='store_true',help='Validate delivered numerical artifacts without rerunning the study');a=p.parse_args()
commands=[]
if a.check_only:
 commands=[['validate.py']]
else:
 if not a.prepared:commands=[['acquire.py','mteb'],['acquire.py','open_llm'],['prepare.py','mteb'],['prepare.py','open_llm'],['cohorts.py']]
 commands += [['suite.py'],['diagnostics.py'],['task_diagnostics.py'],['summarize.py'],['diagnostic_summary.py'],['compact.py'],['validate.py'],['handoff.py']]
for command in commands:
 subprocess.run([sys.executable,str(ROOT/'scripts'/command[0])]+command[1:],cwd=ROOT,check=True,env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1'})
