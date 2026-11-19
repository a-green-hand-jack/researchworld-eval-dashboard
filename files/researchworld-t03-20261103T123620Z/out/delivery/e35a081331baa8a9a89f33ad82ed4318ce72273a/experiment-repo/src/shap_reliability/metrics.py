"""Run-level diagnostics. Thresholds are operational choices, not utility claims."""
import numpy as np
from scipy.stats import spearmanr

def rank_indices(phi):
    # Stable secondary order is raw feature index. Ambiguity is separately flagged.
    return np.argsort(-np.abs(phi),kind='stable')

def run_metrics(phi,reference,k=3,denominator_floor=.01):
    phi=np.asarray(phi); ref=np.asarray(reference)
    scale=float(np.abs(ref).sum()); denom=max(scale,denominator_floor)
    order=rank_indices(phi); target=rank_indices(ref); k=min(k,len(phi))
    top=set(order[:k]); rt=set(target[:k]); intersection=len(top&rt)
    active=np.abs(ref)>=.01*denom
    sign_agreement=float(np.mean(np.sign(phi[active])==np.sign(ref[active]))) if active.any() else float('nan')
    absolute_error=float(np.abs(phi-ref).sum())
    err=absolute_error/denom
    signed_overlap=sum(j in rt and np.sign(phi[j])==np.sign(ref[j]) for j in top)/k
    tie_tolerance=1e-6
    boundary=abs(ref[target[k-1]])
    tie_overlap=sum(abs(ref[j])>=boundary-tie_tolerance and (abs(ref[j])<=tie_tolerance or np.sign(phi[j])==np.sign(ref[j])) for j in top)/k
    rho=float(spearmanr(np.abs(phi),np.abs(ref)).statistic) if np.std(np.abs(phi))>0 and np.std(np.abs(ref))>0 else float('nan')
    gap1=float((abs(ref[target[0]])-abs(ref[target[1]]))/denom)
    gapk=float((abs(ref[target[k-1]])-abs(ref[target[k]]))/denom) if k<len(ref) else float('nan')
    result=dict(reference_l1=scale,absolute_l1_error=absolute_error,nl1_error=err,signed_topk_overlap=signed_overlap,tie_aware_signed_topk_overlap=tie_overlap,signed_top1_match=float(order[0]==target[0] and np.sign(phi[order[0]])==np.sign(ref[target[0]])),linf_error=float(np.max(np.abs(phi-ref))),top1_match=float(order[0]==target[0]),topk_overlap=intersection/k,topk_jaccard=intersection/(2*k-intersection),topk_exact_match=float(top==rt),sign_agreement=sign_agreement,abs_rank_spearman=rho,top1_gap_normalized=gap1,topk_gap_normalized=gapk,low_signal=float(scale<.01),near_tie_top1=float(gap1<=.02),efficiency_residual=float(phi.sum()-ref.sum()),top1_estimate=int(order[0]),top1_reference=int(target[0]),active_sign_features=int(active.sum()))
    for threshold in [.1,.2,.4]:
        tag=str(threshold).replace('.','p')
        result[f'error_success_{tag}']=float(err<=threshold)
        result[f'joint_success_{tag}']=float(err<=threshold and signed_overlap>=2/3)
        result[f'strict_joint_success_{tag}']=float(err<=threshold and signed_overlap==1)
        result[f'tie_aware_joint_success_{tag}']=float(err<=threshold and tie_overlap>=2/3)
    return result

def pairwise_metrics(phis,reference,k=3):
    """All distinct run pairs, summarized once per independent instance.

    The primary vector difference uses the exact reference denominator, matching
    reference-error metrics. Average-run normalization is retained separately.
    """
    phis=np.asarray(phis); orders=[rank_indices(p) for p in phis]
    top=np.array([order[0] for order in orders]); n=len(top);k=min(k,phis.shape[1])
    counts=np.bincount(top,minlength=phis.shape[1])
    top1_agree=float(np.sum(counts*(counts-1))/(n*(n-1))) if n>1 else float('nan')
    denom=max(float(np.abs(reference).sum()),.01)
    selected=[set(order[:k]) for order in orders]
    signed=[{(int(j),int(np.sign(phis[i,j]))) for j in orders[i][:k]} for i in range(n)]
    diffs=[];run_diffs=[];signed_overlap=[];unsigned_overlap=[];events=[]
    for i in range(n):
        for j in range(i):
            absolute=float(np.abs(phis[i]-phis[j]).sum())
            scale=max((np.abs(phis[i]).sum()+np.abs(phis[j]).sum())/2,.01)
            diffs.append(absolute/denom);run_diffs.append(absolute/scale)
            overlap=len(signed[i]&signed[j])/k
            signed_overlap.append(overlap);unsigned_overlap.append(len(selected[i]&selected[j])/k)
            events.append(float(absolute/denom<=.2 and overlap>=2/3))
    avg=lambda a:float(np.mean(a)) if a else float('nan')
    return dict(pairwise_top1_agreement=top1_agree,pairwise_normalized_l1=avg(diffs),pairwise_run_normalized_l1=avg(run_diffs),pairwise_signed_topk_overlap=avg(signed_overlap),pairwise_topk_overlap=avg(unsigned_overlap),pairwise_joint_agreement_0p2=avg(events),modal_top1_share=float(counts.max()/n))

def cluster_bootstrap(values,seed=8127,n_bootstrap=2000,bounded_01=False):
    """Percentile interval for the mean over held-out cases and random runs.

    Resample independent explained instances as clusters. Their run means already
    include finite-repeat Monte Carlo noise; resampling runs a second time would
    add that noise again. Model-fitting and background selection are conditional.
    """
    a=np.asarray(values,dtype=float); n,r=a.shape
    if n<2: raise ValueError('at least 2 instances needed for population interval')
    per_case=np.nanmean(a,axis=1)
    rng=np.random.default_rng(seed)
    means=np.nanmean(per_case[rng.integers(0,n,size=(n_bootstrap,n))],axis=1)
    lo,hi=np.nanquantile(means,[.025,.975])
    estimate=float(np.nanmean(a))
    result=dict(estimate=estimate,ci_low=float(lo),ci_high=float(hi),bootstrap_ci_low=float(lo),bootstrap_ci_high=float(hi),n_instances=n,n_metric_instances=int(np.isfinite(per_case).sum()),n_repeats=r,n_bootstrap=n_bootstrap,interval='95% percentile instance-cluster bootstrap; fixed model/background',boundary_adjusted=False)
    if bounded_01 and np.all(np.isfinite(per_case)):
        if np.nanmin(a)<0 or np.nanmax(a)>1:raise ValueError('bounded statistic outside [0,1]')
        # Hoeffding applied to independent bounded instance means: within-instance
        # replicates/pairs never increase n. No nested seed bootstrap is used.
        one_sided_radius=np.sqrt(np.log(1/.05)/(2*n))
        two_sided_radius=np.sqrt(np.log(2/.05)/(2*n))
        result.update(bounded_mean_low95=float(max(0,estimate-one_sided_radius)),bounded_mean_high95=float(min(1,estimate+one_sided_radius)),bounded_mean_two_sided_low=float(max(0,estimate-two_sided_radius)),bounded_mean_two_sided_high=float(min(1,estimate+two_sided_radius)),certifies_mean_ge_0p95=bool(estimate-one_sided_radius>=.95),bounded_mean_guard='Hoeffding, independent instance means in [0,1]; n is instances')
        if np.all(per_case==0) or np.all(per_case==1):
            result.update(ci_low=result['bounded_mean_two_sided_low'],ci_high=result['bounded_mean_two_sided_high'],boundary_adjusted=True,interval='95% two-sided Hoeffding bounded-instance-mean interval at observed boundary; bootstrap interval separately retained')
    return result
