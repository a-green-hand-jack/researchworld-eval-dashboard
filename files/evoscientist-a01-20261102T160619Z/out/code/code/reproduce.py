#!/usr/bin/env python3
"""Portable offline recomputation in a fresh filesystem tree, with result comparison.
Run using the interpreter/environment to audit. Raw files are copied, not refetched.
Use download.py separately to demonstrate online retrieval/checksum verification.
"""
from pathlib import Path
import argparse,json,shutil,subprocess,tempfile,time,sys,os,resource,hashlib
import pandas as pd
import numpy as np
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser();p.add_argument('--keep',action='store_true');p.add_argument('--skip-plots',action='store_true');args=p.parse_args()
    dest=Path(tempfile.mkdtemp(prefix='reproduce_',dir=ROOT/'artifacts'));t0=time.perf_counter();times=[];before=resource.getrusage(resource.RUSAGE_CHILDREN);env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
    for d in ['code','tests','data/raw']:shutil.copytree(ROOT/d,dest/d)
    (dest/'data/processed').mkdir();(dest/'artifacts').mkdir();(dest/'paper/generated').mkdir(parents=True)
    scripts=[['code/prepare.py'],['code/run.py'],['code/validate.py'],['code/summarize.py'],['code/task_influence.py'],['code/counterexamples.py'],['-m','pytest','-q','tests','-p','no:cacheprovider']]
    if not args.skip_plots:scripts.append(['code/plot.py'])
    with (ROOT/'artifacts/clean_reproduction.log').open('w') as f:
      for command in scripts:
        t=time.perf_counter();print('RUN',command,flush=True);f.write('RUN '+repr(command)+'\n');f.flush()
        subprocess.run([sys.executable,*command],cwd=dest,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
        times.append({'command':command,'wall_s':time.perf_counter()-t})
    comparisons=[]
    for p in sorted((ROOT/'artifacts').glob('results_*.csv')):
        original=pd.read_csv(p);fresh=pd.read_csv(dest/'artifacts'/p.name)
        columns=[c for c in original.columns if c not in ['mask','witness_L1','gap','dual']]
        pd.testing.assert_frame_equal(original[columns],fresh[columns],check_exact=False,rtol=1e-12,atol=1e-14)
        comparisons.append({'file':p.name,'rows':len(original),'columns_checked':columns})
    for name in ['primary_summary.csv','paired_contrasts.csv','fixed_cohort.csv','sensitivity_summary.csv','task_influence_summary.csv','heuristics.csv']:
        pd.testing.assert_frame_equal(pd.read_csv(ROOT/'artifacts'/name),pd.read_csv(dest/'artifacts'/name),check_exact=False,rtol=1e-12,atol=1e-14)
    assert json.loads((dest/'artifacts/validation_summary.json').read_text())['all_checks_passed']
    after=resource.getrusage(resource.RUSAGE_CHILDREN)
    result={'success':True,'python':sys.executable,'wall_s':time.perf_counter()-t0,'child_cpu_s':(after.ru_utime+after.ru_stime)-(before.ru_utime+before.ru_stime),'max_child_rss_kib_linux':after.ru_maxrss,'runs':times,'results_compared':comparisons,'excluded_witness_columns':'nonunique optimal endpoint masks/costs and numerical gap/bound bookkeeping; every fresh witness independently validated','fresh_virtualenv':'.repro_venv' in sys.executable,'new_directory':str(dest.relative_to(ROOT)),'retained':args.keep}
    (ROOT/'artifacts/reproduction_check.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
    if not args.keep:shutil.rmtree(dest)
if __name__=='__main__':main()
