"""Offline end-to-end reproduction with measured wall/CPU/peak child RSS."""
import json,os,pathlib,resource,subprocess,sys,time
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
    env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
    commands=[[sys.executable,'tests/test_statistics.py'],[sys.executable,'code/run_experiments.py','synthetic'],[sys.executable,'code/run_experiments.py','real'],[sys.executable,'code/plot_results.py'],[sys.executable,'code/budget_matched.py'],[sys.executable,'code/write_report.py'],['bash','build_paper.sh'],[sys.executable,'code/verify_delivery.py']]
    rows=[];start=time.perf_counter()
    with (ROOT/'artifacts/reproduction.log').open('w',buffering=1) as out:
      for cmd in commands:
        t=time.perf_counter();before=resource.getrusage(resource.RUSAGE_CHILDREN)
        out.write('\nCOMMAND '+repr(cmd)+'\n');out.flush();proc=subprocess.run(cmd,cwd=ROOT,env=env,stdout=out,stderr=subprocess.STDOUT)
        after=resource.getrusage(resource.RUSAGE_CHILDREN);row={'command':cmd,'exit_code':proc.returncode,'wall_s':time.perf_counter()-t,'user_cpu_s':after.ru_utime-before.ru_utime,'system_cpu_s':after.ru_stime-before.ru_stime,'max_child_RSS_kib_cumulative':after.ru_maxrss};rows.append(row)
        print(row,flush=True)
        if proc.returncode:break
    data={'commands':rows,'total_wall_s':time.perf_counter()-start,'total_user_cpu_s':sum(r['user_cpu_s'] for r in rows),'total_system_cpu_s':sum(r['system_cpu_s'] for r in rows),'scope':'One complete offline reproduction pass only; excludes original inference, source retrieval, prior development/reruns and agent compute. Inference wall and reported token use documented separately.'}
    (ROOT/'artifacts/reproduction_resources.json').write_text(json.dumps(data,indent=2))
    if any(r['exit_code'] for r in rows):raise SystemExit('Reproduction failed; see artifacts/reproduction.log')
if __name__=='__main__':main()
