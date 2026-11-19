"""Run complete-production audits and supplementary analyses, timed by stage."""
import argparse
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time

p=argparse.ArgumentParser();p.add_argument('--root',default='.')
a=p.parse_args();root=Path(a.root).resolve()
code=root/'code' if (root/'code/configs').exists() else root
notes=root/'analysis' if code!=root else root/'notes'
env=os.environ.copy();env['PYTHONPATH']=str(code/'src')
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:env[key]='1'
records=[]
for script,extra in [('audit_results.py',['--complete']),('audit_boundaries.py',[]),('analyze_results.py',[]),('audit_summaries.py',[])]:
    command=[sys.executable,'-u',str(code/'scripts'/script),'--root',str(root),*extra]
    start=time.perf_counter();before=resource.getrusage(resource.RUSAGE_CHILDREN)
    subprocess.run(command,cwd=root,env=env,check=True)
    after=resource.getrusage(resource.RUSAGE_CHILDREN)
    records.append(dict(command=command,wall_seconds=time.perf_counter()-start,
                        cpu_seconds=after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,
                        children_cumulative_peak_rss_kib=after.ru_maxrss))
    (notes/'postprocessing_timings.json').write_text(json.dumps(records,indent=2))
    print('HUTIAN_WAKE: final analysis stage completed '+script,flush=True)
