"""Independent raw-response and finite-interval audit for paper PR19.

Run: OPENBLAS_NUM_THREADS=1 python3 review/check_final19.py ROOT --revision PAPER_SHA
Downloads are performed separately with the pinned data-only acquisition command.
No inference, source modification, or study interval function import is performed.
"""
import argparse,hashlib,json,re,sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import hypergeom
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('root',type=Path)
parser.add_argument('--revision',required=True,help='Exact paper revision archived at root')
parser.add_argument('--output',type=Path,default=Path('review/final19-check.json'))
args=parser.parse_args()
root=args.root;a=root/'analysis';res=a/'results/real'
read=lambda p:json.loads(p.read_text())
test=pd.read_parquet(a/'data/raw/test.parquet');val=pd.read_parquet(a/'data/raw/validation.parquet')
assert (len(test),len(val),test.category.nunique())==(12032,70,14)
for item in read(a/'provenance/downloads.json'):
 if item['path'].startswith('data/'):
  f=a/item['path'];assert len(f.read_bytes())==item['bytes'] and hashlib.sha256(f.read_bytes()).hexdigest()==item['sha256']
part=read(a/'provenance/real-partition.json');sub=read(a/'provenance/real-partition-tier-c.json')
order=np.random.default_rng(20261104).permutation(len(test))
assert [q['row_index'] for q in part['questions']]==order[:1536].tolist()
assert part['candidate_order']==[0]+np.random.default_rng(20261105).permutation(np.arange(1,16)).tolist()
assert sub['questions']==part['questions'][::2] and sub['active_candidates']==part['active_candidates'][:4]
raw=[json.loads(line) for line in (a/'results/real-main-shard0.jsonl').read_text().splitlines()]
qm={q['question_id']:q for q in part['questions'][::2]};seen=set();lookup={}
# Inspect prompt renderer separately; import only its no-inference text function.
sys.path.insert(0,str(a/'scripts'));from prompt_bank import render
invalid=0;wall=cpu=0.;prompt_tokens=completion_tokens=0
for r in raw:
 q=qm[r['question_id']];row=test.iloc[q['row_index']]
 key=(r['question_id'],r['candidate_id']);assert key not in seen;seen.add(key)
 assert r['pool']==q['pool'] and r['category']==row.category and r['answer']==row.answer
 assert r['option_count']==len(row.options)
 assert r['prompt_sha256']==hashlib.sha256(render(row,r['candidate_id']).encode()).hexdigest()
 m=re.fullmatch(r'\s*[\[(]?([A-J])[\])]?[.)]?\s*',r['raw_output'])
 pred=m.group(1) if m else None
 wrong_range=pred is not None and ord(pred)-65>=len(row.options)
 assert r['prediction']==pred and r['invalid_format']==(pred is None)
 assert r['out_of_range']==wrong_range and r['invalid']==((pred is None) or wrong_range)
 assert r['correct']==(pred==row.answer)
 lookup[key]=int(pred==row.answer);invalid+=int(pred is None)
 wall+=r['wall_seconds'];cpu+=r['cpu_seconds'];prompt_tokens+=r['usage']['prompt_tokens'];completion_tokens+=r['usage']['completion_tokens']
assert seen=={(qid,c) for qid in qm for c in part['active_candidates']}
d=np.load(a/'results/real-main.npz');ids=d['candidate_ids'].tolist();qid=d['question_ids'].tolist()
assert qid==[q['question_id'] for q in sub['questions']] and ids==sorted(sub['active_candidates'])
score=np.array([[lookup[q,c] for c in ids] for q in qid],dtype=np.uint8)
assert np.array_equal(score,d['scores'])
S=score[d['pools']=='search'];A=score[d['pools']=='audit'];primary=read(res/'primary-result.json');j=int(S.sum(0).argmax());assert ids[j]==10
assert S[:,j].sum()==94 and A[:,j].sum()==130 and S[:,0].sum()==65 and A[:,0].sum()==86
assert primary['design_count']==2 and primary['per_design_alpha']==.025 and primary['actual_cache_calls']==6144

def direct(x,m,N,alpha):
 totals=np.arange(x,N-m+x+1)
 ok=(hypergeom.sf(x-1,N,totals,m)>=alpha/2)&(hypergeom.cdf(x,N,totals,m)>=alpha/2)
 return np.array([totals[ok][0],totals[ok][-1]])/N
R=11776;alpha=.025
aci=direct(130,512,R,alpha)
assert np.allclose(aci,primary['exact_audit_interval'],atol=1e-14,rtol=0)
search_ci=(12032*direct(94,256,12032,alpha/4)-94)/R
assert np.allclose(search_ci,primary['exact_simultaneous_remaining_interval'],atol=1e-14,rtol=0)
wins=int(((A[:,j]==1)&(A[:,0]==0)).sum());losses=int(((A[:,j]==0)&(A[:,0]==1)).sum());assert (wins,losses)==(61,17)
wci=direct(wins,512,R,alpha/2);lci=direct(losses,512,R,alpha/2);pci=np.array([wci[0]-lci[1],wci[1]-lci[0]])
assert np.allclose(pci,primary['exact_paired_contrast_interval'],atol=1e-14,rtol=0)
assert np.allclose(94/256-aci[::-1],primary['exact_gap_interval'],atol=1e-14,rtol=0)
assert primary['naive_reused_nonoverlap_claim'] is False and primary['independent_audit_nonoverlap_claim'] is True
for metric,values in [('covariance',np.cov(score,rowvar=False)),('correlation',np.corrcoef(score,rowvar=False))]:
 frame=pd.read_csv(res/f'candidate-{metric}.csv',index_col=0)
 assert frame.index.tolist()==ids and frame.columns.astype(int).tolist()==ids
 assert np.allclose(frame.to_numpy(),values)
ledger=read(res/'compute-ledger.json');main=ledger['successful_inference'][-1]
assert main['responses']==len(raw)==6144 and main['prompt_tokens']==prompt_tokens and main['completion_tokens']==completion_tokens
assert np.allclose(main['successful_response_wall_seconds'],wall) and np.allclose(main['successful_response_cpu_seconds'],cpu)
out={'revision':args.revision,'scope':'Independent raw-response and exact-interval audit; no new inference',
 'raw_pairs_checked':len(raw),'retained_matrix_shape':list(score.shape),'winner_search_successes':94,'winner_audit_successes':130,'default_search_successes':65,'default_audit_successes':86,'paired_wins_losses':[wins,losses],
 'independent_audit_interval':aci.tolist(),'independent_transformed_search_interval':search_ci.tolist(),'independent_paired_interval':pci.tolist(),
 'main_prompt_completion_tokens':[prompt_tokens,completion_tokens],'parent_malformed':invalid,
 'passed':['Pinned data hashes and permutation/prefix derivation','All raw answers scored independently and prompt hashes/gold labels verified','Retained matrix equals independently scored raw responses','Exhaustive hypergeometric inversion agrees with primary audit/search/paired/gap endpoints','Actual ID axes and covariance/correlation match paired matrix','All main generated calls/tokens and response costs reconcile with ledger']}
args.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
