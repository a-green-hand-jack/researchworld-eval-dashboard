"""Audit-ready data/format/cost diagnostics and a descriptive primary gap decomposition."""
import argparse,hashlib,json,pathlib
import numpy as np
import pandas as pd

p=argparse.ArgumentParser();p.add_argument('--matrix',required=True);p.add_argument('--partition',required=True);p.add_argument('--responses',required=True);p.add_argument('--out-dir',required=True);a=p.parse_args()
out=pathlib.Path(a.out_dir);out.mkdir(parents=True,exist_ok=True);d=np.load(a.matrix);part=json.loads(pathlib.Path(a.partition).read_text());x=pd.read_csv(a.responses);test=pd.read_parquet('data/raw/test.parquet');val=pd.read_parquet('data/raw/validation.parquet')
assert len(test)==12032 and len(val)==70 and test.question_id.is_unique and val.question_id.is_unique
assert len(x)==d['scores'].size and not x.duplicated(['question_id','candidate_id']).any()
lookup=x.set_index(['question_id','candidate_id'])['correct']
assert all(bool(d['scores'][i,j])==bool(lookup.loc[(q,c)]) for i,q in enumerate(d['question_ids']) for j,c in enumerate(d['candidate_ids']))
rows=[]
for (pool,c),g in x.groupby(['pool','candidate_id']):
 rows.append(dict(pool=pool,candidate_id=int(c),responses=len(g),correct=int(g.correct.sum()),accuracy=float(g.correct.mean()),invalid_format=int(g.invalid_format.sum()),out_of_range=int(g.out_of_range.sum()),max_token_endings=int((g.finish_reason=='length').sum()),mean_response_wall_seconds=float(g.wall_seconds.mean()),mean_response_cpu_seconds=float(g.cpu_seconds.mean())))
pd.DataFrame(rows).to_csv(out/'format-diagnostics.csv',index=False)
pools={}
for name,frame in [('full_test',test),('validation',val)]:
 pools[name]=dict(questions=len(frame),category_counts={str(k):int(v) for k,v in frame.category.value_counts().sort_index().items()},option_count_counts={str(k):int(v) for k,v in frame.options.map(len).value_counts().sort_index().items()},question_ids_unique=bool(frame.question_id.is_unique))
for pool in ['search','audit']:
 ids=d['question_ids'][d['pools']==pool];frame=test.set_index('question_id').loc[ids]
 pools[pool]=dict(questions=len(frame),category_counts={str(k):int(v) for k,v in frame.category.value_counts().sort_index().items()},option_count_counts={str(k):int(v) for k,v in frame.options.map(len).value_counts().sort_index().items()})
(out/'data-diagnostics.json').write_text(json.dumps(dict(pools=pools,weighting='question-weighted micro accuracy, no category reweighting or exclusion',test_sha256=hashlib.sha256(pathlib.Path('data/raw/test.parquet').read_bytes()).hexdigest(),matrix_sha256=hashlib.sha256(pathlib.Path(a.matrix).read_bytes()).hexdigest()),indent=2)+'\n')
primary=json.loads((out/'primary-result.json').read_text());candidates=pd.read_csv(out/'candidate-audit.csv').set_index('candidate_id');base=candidates.loc[0];selected=candidates.loc[primary['candidate_id']]
search_gain=primary['reused_score']-primary['default_reused_score'];audit_gain=primary['paired_audit_contrast_to_default'];ci=primary['exact_paired_contrast_interval']
decomposition=dict(selected_candidate_id=primary['candidate_id'],winner_search_minus_audit=primary['reused_minus_audit'],default_search_minus_audit=float(base.search_accuracy-base.audit_accuracy),search_gain_vs_default=search_gain,audit_gain_vs_default=audit_gain,excess_gap_beyond_default=search_gain-audit_gain,excess_gap_interval_from_paired_audit=[search_gain-ci[1],search_gain-ci[0]],warning='Descriptive decomposition of one observed split; total winner gap is not identified as selection-only optimism. Gap-of-gains interval subtracts adjusted paired audit contrast endpoints from fixed observed search gain; guarantee is unconditional across the two possible designs, separately for this endpoint.')
assert np.isclose(decomposition['winner_search_minus_audit'],decomposition['default_search_minus_audit']+decomposition['excess_gap_beyond_default'])
(out/'primary-gap-decomposition.json').write_text(json.dumps(decomposition,indent=2)+'\n')
print(json.dumps(decomposition,indent=2))
