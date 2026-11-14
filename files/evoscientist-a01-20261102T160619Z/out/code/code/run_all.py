#!/usr/bin/env python3
"""One-command reproduction, from workspace root or any current directory."""
from pathlib import Path
import argparse,subprocess,sys,os,time,json,resource
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser();p.add_argument('--offline',action='store_true',help='Use bundled existing raw files; do not contact any website');p.add_argument('--no-pdf',action='store_true');p.add_argument('--no-plots',action='store_true');args=p.parse_args()
    env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
    cmds=[]
    if not args.offline:cmds.append(['code/download.py','--template'])
    cmds += [['code/prepare.py'],['code/run.py'],['code/validate.py'],['code/summarize.py'],['code/task_influence.py'],['code/counterexamples.py'],['code/paper_assets.py'],['-m','pytest','-q','tests','-p','no:cacheprovider']]
    if not args.no_plots:cmds.append(['code/plot.py'])
    if not args.no_pdf:cmds.append(['code/build_paper.py'])
    (ROOT/'artifacts').mkdir(exist_ok=True);wall=time.perf_counter();runs=[]
    with (ROOT/'artifacts/run_all.log').open('w') as log:
      for c in cmds:
        print('Running',' '.join(c),flush=True);start=time.perf_counter();log.write('COMMAND '+repr(c)+'\n');log.flush();subprocess.run([sys.executable,*c],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True);runs.append({'command':c,'elapsed_s':time.perf_counter()-start})
    usage=resource.getrusage(resource.RUSAGE_CHILDREN);(ROOT/'artifacts/run_all_timing.json').write_text(json.dumps({'wall_s':time.perf_counter()-wall,'child_cpu_s':usage.ru_utime+usage.ru_stime,'max_child_rss_kib_linux':usage.ru_maxrss,'runs':runs},indent=2));print('All steps passed.')
if __name__=='__main__':main()
