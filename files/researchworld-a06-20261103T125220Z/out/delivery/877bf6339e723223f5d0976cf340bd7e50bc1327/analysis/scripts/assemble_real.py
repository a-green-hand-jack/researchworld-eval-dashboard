"""Validate every generated pair and export a complete, ordered binary matrix.

A prespecified analysis subset may use a parent generation partition. Every
supplied parent shard is still fully validated, and all generated cost retained.
"""
import argparse,hashlib,json,pathlib
import numpy as np
import pandas as pd
from prompt_bank import BANK_SHA256,render
from run_real import parse_answer

p=argparse.ArgumentParser();p.add_argument('--partition',required=True);p.add_argument('--generation-partition',help='Original generation manifest when analysis is a frozen subset');p.add_argument('--cache',nargs='+',required=True);p.add_argument('--out',required=True);a=p.parse_args()
partition_file=pathlib.Path(a.partition);partition=json.loads(partition_file.read_text());assert partition['bank_sha256']==BANK_SHA256
generation_file=pathlib.Path(a.generation_partition or a.partition);generation=json.loads(generation_file.read_text());assert generation['bank_sha256']==BANK_SHA256
active=sorted(partition.get('active_candidates',list(range(16))));generated_active=sorted(generation.get('active_candidates',list(range(16))))
qmeta={q['question_id']:q for q in partition['questions']};gmeta={q['question_id']:q for q in generation['questions']}
assert len(qmeta)==len(partition['questions']) and len(gmeta)==len(generation['questions'])
assert set(active)<=set(generated_active) and set(qmeta)<=set(gmeta)
assert all(qmeta[q]==gmeta[q] for q in qmeta),'Analysis must preserve parent question identity/pool/category'
expected={(q,c) for q in qmeta for c in active}
source=pd.read_parquet('data/raw/test.parquet');data_sha=hashlib.sha256(pathlib.Path('data/raw/test.parquet').read_bytes()).hexdigest();assert data_sha==partition['source_sha256']==generation['source_sha256']
records=[];configs=[];sources=[]
for file in a.cache:
 f=pathlib.Path(file);config=json.loads(f.with_suffix('.config.json').read_text());configs.append(config)
 assert config['partition_sha256']==hashlib.sha256(generation_file.read_bytes()).hexdigest()
 assert sorted(config['active_candidates'])==generated_active
 assert 0<=config['shard']<config['shards']
 shard_questions=generation['questions'][config['shard']::config['shards']]
 expected_shard={(q['question_id'],c) for q in shard_questions for c in generated_active};seen=set()
 sources.append(dict(path=file,sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
 for line in f.read_text().splitlines():
  r=json.loads(line);key=(r['question_id'],r['candidate_id']);assert key in expected_shard and key not in seen;seen.add(key)
  row=source.iloc[gmeta[r['question_id']]['row_index']];assert int(row.question_id)==r['question_id']
  assert r['answer']==row.answer and r['option_count']==len(row.options)
  assert r['prompt_sha256']==hashlib.sha256(render(row,r['candidate_id']).encode()).hexdigest()
  assert r['pool']==gmeta[r['question_id']]['pool'] and r['category']==gmeta[r['question_id']]['category']
  assert parse_answer(r['raw_output'])==r['prediction']
  assert r['correct']==(r['prediction']==r['answer'])
  assert r['invalid_format']==(r['prediction'] is None)
  assert r['invalid']==(r['invalid_format'] or r['out_of_range'])
  assert r['out_of_range']==(r['prediction'] is not None and ord(r['prediction'])-65>=r['option_count'])
  records.append(r)
 assert seen==expected_shard,'Incomplete generated shard: do not impute missing outputs'
assert len({c['model_sha256'] for c in configs})==1
assert len({c['script_sha256'] for c in configs})==1
xall=pd.DataFrame(records);assert not xall.duplicated(['question_id','candidate_id']).any()
x=xall[[key in expected for key in zip(xall.question_id,xall.candidate_id)]].copy()
assert set(zip(x.question_id,x.candidate_id))==expected,'Incomplete analysis response matrix: do not impute missing outputs'
ids=[q['question_id'] for q in partition['questions']]
scores=x.pivot(index='question_id',columns='candidate_id',values='correct').loc[ids,active].to_numpy(dtype=np.uint8)
out=pathlib.Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
np.savez_compressed(out,scores=scores,question_ids=np.array(ids),candidate_ids=np.array(active),pools=np.array([qmeta[i]['pool'] for i in ids]),categories=np.array([qmeta[i]['category'] for i in ids]))
x.to_csv(out.with_suffix('.responses.csv.gz'),index=False)
summary=dict(questions=len(ids),candidates=len(active),responses=len(x),actual_generated_responses=len(xall),generated_responses_excluded_from_analysis=len(xall)-len(x),sources=sources,model_sha256=configs[0]['model_sha256'],partition_sha256=hashlib.sha256(partition_file.read_bytes()).hexdigest(),generation_partition_sha256=hashlib.sha256(generation_file.read_bytes()).hexdigest(),matrix_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),generation_wall_seconds=float(xall.wall_seconds.sum()),generation_cpu_seconds=float(xall.cpu_seconds.sum()),prompt_tokens=sum(r['usage']['prompt_tokens'] for r in records),completion_tokens=sum(r['usage']['completion_tokens'] for r in records),invalid_format=int(xall.invalid_format.sum()),out_of_range=int(xall.out_of_range.sum()),max_token_endings=int((xall.finish_reason=='length').sum()),warning='Generation costs/diagnostics include all successful supplied cache responses, including those excluded from analysis. Session/resource costs separately retain startup, preflight and failed/interrupted attempts.')
out.with_suffix('.provenance.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
