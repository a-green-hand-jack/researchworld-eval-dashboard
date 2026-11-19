"""Artificial cache fixture verifies parent-shard accounting and subset validation."""
import hashlib,json,pathlib,subprocess,sys,tempfile
import numpy as np
import pandas as pd
sys.path.insert(0,'scripts')
from prompt_bank import render
root=pathlib.Path.cwd();parent=json.loads((root/'provenance/real-partition.json').read_text());source=pd.read_parquet(root/'data/raw/test.parquet')
parent['questions']=[q for q in parent['questions'] if q['pool']=='search'][:2]+[q for q in parent['questions'] if q['pool']=='audit'][:2];parent['active_candidates']=[0,10];parent.update(n_search=2,n_audit=2)
subset=dict(parent);subset['questions']=parent['questions'][::2];subset['active_candidates']=[0];subset.update(n_search=1,n_audit=1)
with tempfile.TemporaryDirectory() as folder:
 p=pathlib.Path(folder);(p/'data').mkdir();(p/'data/raw').symlink_to(root/'data/raw');(p/'parent.json').write_text(json.dumps(parent));(p/'subset.json').write_text(json.dumps(subset))
 config=dict(partition_sha256=hashlib.sha256((p/'parent.json').read_bytes()).hexdigest(),active_candidates=[0,10],model_sha256='artificial-fixture',script_sha256='artificial-fixture',shard=0,shards=1)
 (p/'cache.config.json').write_text(json.dumps(config));records=[]
 for q in parent['questions']:
  row=source.iloc[q['row_index']]
  for c in [0,10]:
   records.append(dict(question_id=q['question_id'],candidate_id=c,answer=row.answer,option_count=len(row.options),prompt_sha256=hashlib.sha256(render(row,c).encode()).hexdigest(),pool=q['pool'],category=q['category'],raw_output='A',prediction='A',correct=row.answer=='A',invalid=False,invalid_format=False,out_of_range=False,wall_seconds=1.,cpu_seconds=2.,usage=dict(prompt_tokens=3,completion_tokens=1),finish_reason='stop'))
 def run(rows):
  (p/'cache.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
  return subprocess.run([sys.executable,str(root/'scripts/assemble_real.py'),'--partition','subset.json','--generation-partition','parent.json','--cache','cache.jsonl','--out','out.npz'],cwd=p,capture_output=True,text=True)
 result=run(records);assert result.returncode==0,result.stderr
 d=np.load(p/'out.npz');meta=json.loads((p/'out.provenance.json').read_text())
 assert d['scores'].shape==(2,1) and d['question_ids'].tolist()==[q['question_id'] for q in subset['questions']]
 assert meta['responses']==2 and meta['actual_generated_responses']==8 and meta['generated_responses_excluded_from_analysis']==6
 assert meta['generation_cpu_seconds']==16 and meta['prompt_tokens']==24
 assert run(records[:-1]).returncode!=0,'Missing extra parent answer must fail even when subset is complete'
 assert run(records+[records[-1]]).returncode!=0,'Duplicate parent pair must fail'
 damaged=[dict(r) for r in records];damaged[-1]['prompt_sha256']='bad';assert run(damaged).returncode!=0,'Excluded corrupt prompt must fail'
print('PASS: artificial subset fixture preserves IDs, accounts all parent costs, rejects missing/duplicate/corrupt excluded parent outputs.')
