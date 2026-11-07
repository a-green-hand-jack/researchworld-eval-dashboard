"""One-command reproduction, with actual stage wall-time and CPU-use log.
Run from any directory; outputs live beside this script. No paid APIs/GPU.
--verify-only replays saved intervals and checks the supplied PDF without new trials.
"""
import argparse
import json
import os
from pathlib import Path
import platform
import resource
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parent


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--verify-only',action='store_true')
    parser.add_argument('--skip-download',action='store_true')
    args=parser.parse_args()
    env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
    python=sys.executable
    commands=[]
    if not args.skip_download:commands.append([python,'download_data.py'])
    commands.append([python,'-m','pytest','test_intervals.py','-q'])
    if not args.verify_only:
        commands += [[python,'run_experiments.py','--workers','4'],[python,'supplement_baselines.py'],
                     [python,'summarize.py'],[python,'mass_ablation.py'],[python,'prepare_submission.py'],
                     ['latexmk','-pdf','-interaction=nonstopmode','-halt-on-error','paper.tex']]
    commands.append([python,'verify_release.py','--recompute'])
    timing=[]
    for i,command in enumerate(commands):
        print('RUN',command,flush=True)
        start=time.perf_counter();before=resource.getrusage(resource.RUSAGE_CHILDREN)
        log=ROOT/f'reproduce_stage_{i:02d}.log'
        with log.open('w') as f:
            subprocess.run(command,cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
        after=resource.getrusage(resource.RUSAGE_CHILDREN)
        timing.append(dict(command=command,log=log.name,wall_seconds=time.perf_counter()-start,
                           child_cpu_user_seconds=after.ru_utime-before.ru_utime,
                           child_cpu_system_seconds=after.ru_stime-before.ru_stime,
                           cumulative_max_child_rss_kib=after.ru_maxrss))
    (ROOT/'reproduction_log.json').write_text(json.dumps(dict(mode='verify_only' if args.verify_only else 'full',
        python=platform.python_version(),stages=timing,
        memory_note='getrusage CHILDREN maximum child RSS, NOT concurrent total or original-run peak'),indent=2))
    print('SUCCESS',len(commands),'stages')


if __name__=='__main__':main()
