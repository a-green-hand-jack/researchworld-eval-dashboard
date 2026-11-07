"""Real search-versus-disjoint-audit analysis; never treats audit means as truth."""
import argparse,hashlib,json,pathlib,time,resource
import numpy as np
import pandas as pd
from finite_population import hypergeom_interval,paired_difference_interval
from run_synthetic import cp_table


def select(rng,counts):
 return np.argmax(counts+rng.random(counts.shape),axis=1)


def paired_counts(rng,matrix,n,reps):
 counts=np.empty((reps,matrix.shape[1]),dtype=np.int32);split=np.empty_like(counts);hold=np.empty_like(counts)
 for r in range(reps):
  ids=rng.choice(len(matrix),size=n,replace=False);ns=n//2
  split[r]=matrix[ids[:ns]].sum(axis=0);hold[r]=matrix[ids[ns:]].sum(axis=0);counts[r]=split[r]+hold[r]
 return counts,split,hold


def export_dependence(scores, candidate_ids, out):
 """Both axes name actual prompt IDs in matrix-column order."""
 ids=list(candidate_ids);assert scores.shape[1]==len(ids) and len(set(ids))==len(ids)
 for name, values in [('covariance',np.cov(scores,rowvar=False)),('correlation',np.corrcoef(scores,rowvar=False))]:
  pd.DataFrame(np.atleast_2d(values),index=ids,columns=ids).to_csv(out/f'candidate-{name}.csv',index_label='candidate_id')


def main():
 p=argparse.ArgumentParser();p.add_argument('--matrix',required=True);p.add_argument('--partition',required=True);p.add_argument('--reps',type=int,default=20000);p.add_argument('--out-dir',required=True);p.add_argument('--design-count',type=int,default=1,help='Union over predeclared possible delivered designs');p.add_argument('--actual-generated-responses',type=int,help='Include all generated calls even when subset analyzed');a=p.parse_args();assert a.design_count>=1
 alpha=.05/a.design_count
 out=pathlib.Path(a.out_dir);out.mkdir(parents=True,exist_ok=True);f=pathlib.Path(a.matrix);d=np.load(f);S=d['scores'][d['pools']=='search'];A=d['scores'][d['pools']=='audit'];categories=d['categories'];partition=json.loads(pathlib.Path(a.partition).read_text())
 ids=d['candidate_ids'].tolist();C=len(ids);assert ids[0]==0
 assert S.shape==(partition['n_search'],C) and A.shape==(partition['n_audit'],C)
 N=12032-len(S);m=len(A);order=[ids.index(c) for c in partition['candidate_order'] if c in ids];audit_means=A.mean(axis=0)
 audit_ci=np.array([hypergeom_interval(int(A[:,c].sum()),m,N,alpha) for c in range(C)])
 simultaneous=np.array([hypergeom_interval(int(A[:,c].sum()),m,N,alpha/C) for c in range(C)])
 candidate_rows=[]
 for c in range(C):
  wins=int(((A[:,c]==1)&(A[:,0]==0)).sum());losses=int(((A[:,c]==0)&(A[:,0]==1)).sum())
  contrast_ci=(0.,0.) if c==0 else paired_difference_interval(wins,losses,m,N,alpha)
  contrast_sim=(0.,0.) if c==0 else paired_difference_interval(wins,losses,m,N,alpha/max(1,C-1))
  diff=A[:,c].astype(float)-A[:,0]
  candidate_rows.append(dict(candidate_id=ids[c],search_accuracy=float(S[:,c].mean()),audit_accuracy=float(audit_means[c]),audit_ci_lower=audit_ci[c,0],audit_ci_upper=audit_ci[c,1],audit_simultaneous_lower=simultaneous[c,0],audit_simultaneous_upper=simultaneous[c,1],audit_contrast_to_default=float(diff.mean()),paired_wins=wins,paired_losses=losses,paired_contrast_se=float(np.sqrt(diff.var(ddof=1)/m*(N-m)/(N-1))),paired_contrast_ci_lower=contrast_ci[0],paired_contrast_ci_upper=contrast_ci[1],paired_contrast_bank_ci_lower=contrast_sim[0],paired_contrast_bank_ci_upper=contrast_sim[1],audit_population_questions=N,audit_questions=m))
 pd.DataFrame(candidate_rows).to_csv(out/'candidate-audit.csv',index=False)
 # One primary full-search configuration is frozen by search labels and a dedicated tie seed.
 full_counts=S.sum(axis=0);primary_rng=np.random.default_rng(20261109)
 primary_index=int(np.array(order)[select(primary_rng,full_counts[np.array(order)][None,:])[0]]);primary_id=ids[primary_index]
 primary_cp=cp_table(len(S),.05);primary_cp_sim=cp_table(len(S),.05/C)
 total_intervals=np.array([hypergeom_interval(int(full_counts[c]),len(S),12032,alpha/C) for c in range(C)])
 # The search is a uniform subset of the benchmark. Subtract its observed successes
 # to transform a simultaneous total-success interval into a remaining-item interval.
 remaining_intervals=np.clip((12032*total_intervals-full_counts[:,None])/N,0,1)
 pcount=int(full_counts[primary_index]);bcount=int(full_counts[0]);audit_contrast=candidate_rows[primary_index]
 primary=dict(n_search=len(S),k=C,candidate_id=primary_id,tie_seed=20261109,search_successes=pcount,reused_score=pcount/len(S),default_reused_score=bcount/len(S),naive_binomial_interval=[float(primary_cp[0][pcount]),float(primary_cp[1][pcount])],simultaneous_binomial_interval=[float(primary_cp_sim[0][pcount]),float(primary_cp_sim[1][pcount])],binomial_warning='Not asserted exact for the without-replacement fresh-benchmark target; exact finite-population simultaneous interval below.',exact_simultaneous_remaining_interval=remaining_intervals[primary_index].tolist(),audit_successes=int(A[:,primary_index].sum()),audit_questions=m,audit_accuracy=float(audit_means[primary_index]),exact_audit_interval=audit_ci[primary_index].tolist(),reused_minus_audit=float(pcount/len(S)-audit_means[primary_index]),exact_gap_interval=[float(pcount/len(S)-audit_ci[primary_index,1]),float(pcount/len(S)-audit_ci[primary_index,0])],paired_audit_contrast_to_default=audit_contrast['audit_contrast_to_default'],exact_paired_contrast_interval=[audit_contrast['paired_contrast_ci_lower'],audit_contrast['paired_contrast_ci_upper']],naive_reused_nonoverlap_claim=bool(primary_index!=0 and primary_cp[0][pcount]>primary_cp[1][bcount]),exact_simultaneous_search_nonoverlap_claim=bool(primary_index!=0 and remaining_intervals[primary_index,0]>remaining_intervals[0,1]),independent_audit_nonoverlap_claim=bool(primary_index!=0 and audit_ci[primary_index,0]>audit_ci[0,1]),paired_audit_positive_claim=bool(primary_index!=0 and audit_contrast['paired_contrast_ci_lower']>0),search_calls=len(S)*C,logical_selected_accuracy_audit_calls=m,logical_selected_default_paired_audit_calls=m*(1+int(primary_index!=0)),logical_search_plus_accuracy_audit_calls=len(S)*C+m,logical_search_plus_paired_audit_calls=len(S)*C+m*(1+int(primary_index!=0)),analysis_cache_responses=(len(S)+m)*C,actual_cache_calls=a.actual_generated_responses or (len(S)+m)*C,design_count=a.design_count,per_design_alpha=alpha,exact_interval_guarantee='At least95% unconditional over original partition and choice among predeclared designs; not conditional on runtime trigger' if a.design_count>1 else 'At least95% for the fixed design; audit conditional on search',target='uniform benchmark questions outside entire search pool; audit is an estimate with exact finite-population sampling uncertainty')
 (out/'primary-result.json').write_text(json.dumps(primary,indent=2)+'\n')
 export_dependence(d['scores'],ids,out)
 subgroup=[]
 for pool in ['search','audit']:
  for cat in sorted(set(categories)):
   mask=(d['pools']==pool)&(categories==cat)
   for c in range(C):subgroup.append(dict(pool=pool,category=cat,candidate_id=ids[c],questions=int(mask.sum()),accuracy=float(d['scores'][mask,c].mean())))
 pd.DataFrame(subgroup).to_csv(out/'category-accuracy.csv',index=False)
 rng=np.random.default_rng(20261107);all_rows=[];frequencies=[];idx=np.arange(a.reps);start=time.perf_counter();cpu=time.process_time()
 with (out/'conditional-selection.jsonl').open('w') as stream:
  for n in [v for v in [16,32,64,128,256,512,1024] if v<=len(S)]:
   assert n<=len(S)
   counts,split,hold=paired_counts(rng,S,n,a.reps)
   for k in [v for v in [1,2,4,8,16] if v<=C]:
    candidates=np.array(order[:k]);winner_index=select(rng,counts[:,candidates]);winner=candidates[winner_index]
    split_index=select(rng,split[:,candidates]);split_winner=candidates[split_index]
    selected=counts[idx,winner]/n;split_report=hold[idx,split_winner]/(n-n//2)
    fresh=audit_means[winner];split_fresh=audit_means[split_winner]
    cp=cp_table(n,.05);sim=cp_table(n,.05/k);sel_count=counts[idx,winner]
    claim=(cp[0][sel_count]>cp[1][counts[:,0]])&(winner!=0)
    sim_claim=(sim[0][sel_count]>sim[1][counts[:,0]])&(winner!=0)
    proxy_nonpositive=audit_means[winner]<=audit_means[0]
    metrics={
      'reused_minus_audit':selected-fresh,
      'split_report_minus_audit':split_report-split_fresh,
      'reused_report':selected,'split_report':split_report,
      'full_selected_audit_accuracy':fresh,'split_selected_audit_accuracy':split_fresh,
      'full_audit_contrast_to_default':fresh-audit_means[0],
      'split_audit_contrast_to_default':split_fresh-audit_means[0],
      'reused_squared_difference_from_audit':(selected-fresh)**2,
      'split_squared_difference_from_audit':(split_report-split_fresh)**2,
      'naive_interval_width':cp[1][sel_count]-cp[0][sel_count],
      'simultaneous_interval_width':sim[1][sel_count]-sim[0][sel_count],
      'naive_superiority_claim_frequency':claim,
      'simultaneous_superiority_claim_frequency':sim_claim,
      'naive_claim_audit_sign_disagreement':claim&proxy_nonpositive,
      'simultaneous_claim_audit_sign_disagreement':sim_claim&proxy_nonpositive,
      'apparent_point_gain_audit_sign_disagreement':(counts[idx,winner]>counts[:,0])&proxy_nonpositive,
      'selection_is_default':winner==0,
    }
    weights=np.bincount(winner,minlength=C)/a.reps;split_weights=np.bincount(split_winner,minlength=C)/a.reps
    for c in range(C):frequencies.append(dict(n=n,k=k,candidate_id=ids[c],full_selection_frequency=weights[c],split_selection_frequency=split_weights[c],reps=a.reps))
    for metric,values in metrics.items():
     values=np.asarray(values,dtype=float);record=dict(n=n,k=k,reps=a.reps,seed=20261107,metric=metric,mean=float(values.mean()),mcse=float(values.std(ddof=1)/np.sqrt(a.reps)),uncertainty='MCSE conditional on one fixed search/audit response matrix')
     if metric in ['reused_minus_audit','split_report_minus_audit']:
      w=weights if metric=='reused_minus_audit' else split_weights
      report=float(selected.mean()) if metric=='reused_minus_audit' else float(split_report.mean())
      record.update(audit_simultaneous_gap_lower=float(report-w@simultaneous[:,1]),audit_simultaneous_gap_upper=float(report-w@simultaneous[:,0]),audit_interval_target='mean true gap for the finite Monte Carlo mixture, fixed-bank simultaneous and adjusted over predeclared designs; not conditional on runtime trigger')
     stream.write(json.dumps(record)+'\n');all_rows.append(record)
    stream.flush();print(json.dumps(dict(n=n,k=k,elapsed_wall_seconds=time.perf_counter()-start)),flush=True)
 pd.DataFrame(all_rows).to_csv(out/'conditional-selection.csv',index=False)
 pd.DataFrame(frequencies).to_csv(out/'selection-frequencies.csv',index=False)
 summary=dict(matrix_sha256=hashlib.sha256(f.read_bytes()).hexdigest(),partition_sha256=hashlib.sha256(pathlib.Path(a.partition).read_bytes()).hexdigest(),master_seed=20261107,reps=a.reps,search_questions=len(S),audit_questions=len(A),unseen_benchmark_population_questions=N,design_count=a.design_count,per_design_alpha=alpha,target='uniform remaining pinned-benchmark questions outside entire selection pool',wall_seconds=time.perf_counter()-start,cpu_seconds=time.process_time()-cpu,maxrss_kb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,warnings=['Audit/gap/paired exact intervals adjust over possible designs; no conditional-on-runtime-trigger coverage or audit-unbiasedness claim.','Conditional resampling MCSE omits audit sampling uncertainty; exact intervals are separate.','Audit sign disagreement is not known population decision error.','Squared difference from audit is not squared error against known truth.','Sampling without replacement from the fixed search pool; no coverage of population truth inferred from audit overlap.'])
 (out/'disjoint-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print('HUTIAN_WAKE: disjoint-audit analysis complete '+json.dumps(summary),flush=True)
if __name__=='__main__':main()
