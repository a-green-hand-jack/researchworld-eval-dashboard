"""Supplemental timing replication; never replaces a frozen fitted model."""
import hashlib,json,pathlib,resource,time
import numpy as np
from benchsmall.pipeline import Study,check_freeze,digest,write
from benchsmall.mirt import MIRTModel
root=pathlib.Path(__file__).resolve().parents[1]
check_freeze(root);study=Study(root);benchmark='mmlu_pro';scenario='main';dimension=15
x,split=study.data(benchmark,scenario);source=x[split['train']]
path=study.out/'fits'/benchmark/scenario/f'development_d{dimension}.json'
original=json.loads(path.read_text());assert original['source_hash']==digest(source)
wall=time.perf_counter();cpu=time.process_time();model=MIRTModel(dimension=dimension).fit(source)
record={'purpose':'Timing replication of a fit whose perf_counter duration spans world suspension; original cache retained unchanged',
 'benchmark':benchmark,'scenario':scenario,'stage':'development','dimension':dimension,'source_hash':digest(source),
 'original_record':str(path.relative_to(root)),'original_record_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
 'original_elapsed_seconds':original['seconds'],'elapsed_seconds':time.perf_counter()-wall,'process_cpu_seconds':time.process_time()-cpu,
 'peak_process_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'fit_info':model.fit_info,
 'same_objective_atol_1e_6':bool(np.isclose(model.fit_info['objective'],original['fit_info']['objective'],atol=1e-6,rtol=0))}
assert model.fit_info['converged'] and record['same_objective_atol_1e_6']
write(study.out/'timing_replication.json',record)
print(json.dumps(record),flush=True)
print('HUTIAN_WAKE: suspension-affected source fit timing replication complete',flush=True)
