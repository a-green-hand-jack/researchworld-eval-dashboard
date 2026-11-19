"""Checkpointed timing/validation pilot; these instances are not main evidence."""
import os
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']: os.environ[key]='1'
import sys,time,json,resource,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
import joblib
import shap  # Warm library import before per-call timings.
from shap_reliability.models import prepare
from shap_reliability.estimators import Game,timed_run
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'results/pilot.jsonl'; out.parent.mkdir(exist_ok=True)
art=ROOT/'artifacts/pilot'; art.mkdir(parents=True,exist_ok=True)

def emit(record):
    record['peak_process_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    with out.open('a') as f: f.write(json.dumps(record)+'\n')
    print(json.dumps(record),flush=True)

def main():
    datasets=sys.argv[1:] or ['german','diabetes','acs']
    for dataset in datasets:
      for model in ['logistic','forest','histboost']:
        base={'dataset':dataset,'model':model,'stage':'pilot'}
        try:
          bundle=prepare(dataset,model,n_instances=62)
          joblib.dump(bundle,art/f'{dataset}_{model}.joblib')
          info=bundle['info']; (art/f'{dataset}_{model}.json').write_text(json.dumps(info,indent=2))
          emit(dict(base,kind='model',info=info))
          for i in range(2):
            case=dict(base,instance_index=i,source_id=info['explain_ids'][i])
            args=(bundle['model'],bundle['background'],bundle['instances'][i],bundle['groups'])
            for estimator in ['permutation','kernel']:
              for budget in [128,2048]:
                phi,details=timed_run(Game(*args),estimator,budget,9000+i)
                emit(dict(case,kind='estimator',estimator=estimator,budget=budget,phi=phi.tolist(),**details))
            if dataset!='german':
                phi,details=timed_run(Game(*args),'exact',0,0)
                emit(dict(case,kind='reference',estimator='exact',phi=phi.tolist(),**details))
            else:
                g=Game(*args); start=time.perf_counter(); cpu=time.process_time()
                phi,pairs=g.permutation(1024,9900+i,return_pairs=True)
                emit(dict(case,kind='reference',estimator='permutation',n_permutations=1024,phi=phi.tolist(),pair_se=(pairs.std(axis=0,ddof=1)/np.sqrt(len(pairs))).tolist(),wall_seconds=time.perf_counter()-start,cpu_seconds=time.process_time()-cpu,prediction_rows=g.prediction_rows,unique_coalitions=len(g.cache)))
          print(f'HUTIAN_WAKE: pilot completed {dataset}/{model}',flush=True)
        except Exception as exc:
          emit(dict(base,kind='failure',error=repr(exc),traceback=traceback.format_exc()))
          raise
if __name__=='__main__': main()
