import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
import sys,resource,json,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from shap_reliability.data import load_data
start=time.perf_counter();X,y,c,s=load_data('acs')
record=dict(n_rows=len(y),n_features=X.shape[1],categorical_features=c,wall_seconds=time.perf_counter()-start,peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,method='zip stream with required-column CSV projection')
Path('results/loading_check.json').write_text(json.dumps(record,indent=2)+'\n');print(record,flush=True)
