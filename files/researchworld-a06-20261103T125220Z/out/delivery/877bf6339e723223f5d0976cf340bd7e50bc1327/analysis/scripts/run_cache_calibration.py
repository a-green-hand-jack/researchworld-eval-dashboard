"""Known-truth protocol calibration conditional on a real generated-response cache.

This empirical-population experiment draws iid question identities with
replacement. It is separate from the disjoint fresh-question audit analysis.
"""
import argparse,json,pathlib,time,resource,hashlib
import numpy as np
from run_synthetic import run_cell


def main():
 p=argparse.ArgumentParser();p.add_argument('--matrix',required=True);p.add_argument('--partition',required=True);p.add_argument('--reps',type=int,default=20000);p.add_argument('--out',required=True);a=p.parse_args()
 f=pathlib.Path(a.matrix);d=np.load(f);matrix=d['scores'];ids=d['candidate_ids'].tolist();active=set(ids)
 partition=json.loads(pathlib.Path(a.partition).read_text());order_ids=[c for c in partition['candidate_order'] if c in active];order=[ids.index(c) for c in order_ids];N=len(matrix)
 assert N==partition['n_search']+partition['n_audit']
 assert matrix.shape==(N,len(ids)) and np.isin(matrix,[0,1]).all()
 specs=[(n,k) for n in [16,32,64,128,256,512,1024] if n<=partition['n_search'] for k in [1,2,4,8,16] if k<=len(ids)]
 seeds=np.random.SeedSequence(20261106).spawn(len(specs));out=pathlib.Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
 start=time.perf_counter();cpu=time.process_time()
 with out.open('w') as stream:
  for (n,k),ss in zip(specs,seeds):
   bank=matrix[:,order[:k]];means=bank.mean(axis=0)
   def cache_counts(rng,reps,size,p,rho):
    counts=np.empty((reps,k),dtype=np.int32)
    for lo in range(0,reps,500):
     hi=min(lo+500,reps);indices=rng.integers(0,N,size=(hi-lo,size));counts[lo:hi]=bank[indices].sum(axis=1)
    return counts
   seed=int(ss.generate_state(1)[0]);rows=run_cell(a.reps,n,k,0.,0.,seed,candidate_means=means,counts_fn=cache_counts)
   for row in rows:
    del row['rho'];del row['spread'];row.update(target='fixed_empirical_cache_iid_with_replacement',population_questions=N,candidate_order=order_ids[:k]);stream.write(json.dumps(row)+'\n')
   stream.flush();print(json.dumps(dict(n=n,k=k,elapsed_wall_seconds=time.perf_counter()-start)),flush=True)
 summary=dict(cells=len(specs),reps=a.reps,wall_seconds=time.perf_counter()-start,cpu_seconds=time.process_time()-cpu,maxrss_kb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,matrix_sha256=hashlib.sha256(f.read_bytes()).hexdigest(),partition_sha256=hashlib.sha256(pathlib.Path(a.partition).read_bytes()).hexdigest(),master_seed=20261106,warning='Conditional empirical-population truth, not population accuracy or disjoint unseen questions.')
 out.with_suffix('.summary.json').write_text(json.dumps(summary,indent=2)+'\n');print('HUTIAN_WAKE: real-cache calibration complete '+json.dumps(summary),flush=True)
if __name__=='__main__':main()
