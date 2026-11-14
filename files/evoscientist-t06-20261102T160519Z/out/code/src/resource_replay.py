"""Measure a separately rooted isolated-env replay without modifying accepted results."""
import argparse,json,os,platform,resource,subprocess,time
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--python',required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
 env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONPATH=str(args.root/'src'))
 command=[args.python,str(args.root/'src/run.py'),'--repeats','100','--bootstrap','200']
 start=time.perf_counter()
 with (args.output.parent/'replay_run.log').open('w') as log:r=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT)
 u=resource.getrusage(resource.RUSAGE_CHILDREN)
 result=dict(command=command,returncode=r.returncode,elapsed_seconds=time.perf_counter()-start,user_cpu_seconds=u.ru_utime,system_cpu_seconds=u.ru_stime,max_rss_kib=u.ru_maxrss,max_rss_mib=u.ru_maxrss/1024,platform=platform.platform(),python=args.python,threads=1,scope='main run only; child-process max RSS on Linux; not total project peak',gpu_used=False)
 args.output.write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
 if r.returncode:raise SystemExit(r.returncode)
 for cmd in [[args.python,str(args.root/'src/supplement.py')],[args.python,'-m','pytest','-q',str(args.root/'tests')]]:
  subprocess.run(cmd,env=env,check=True)
if __name__=='__main__':main()
