import numpy as np
from shap_reliability.metrics import run_metrics,pairwise_metrics,cluster_bootstrap

def test():
    ref=np.array([.3,-.2,.1,.0]); m=run_metrics(ref,ref)
    assert m['nl1_error']==0 and m['top1_match']==1 and m['joint_success_0p1']==1
    assert m['sign_agreement']==1 and m['topk_jaccard']==1
    other=np.array([-.1,.4,.1,0]); m=run_metrics(other,ref)
    assert m['top1_match']==0 and m['sign_agreement']==1/3
    assert pairwise_metrics([ref,ref,other],ref)['pairwise_top1_agreement']==1/3
    assert run_metrics(np.array([0.,0]),np.array([0.,0]))['low_signal']==1
    # The primary event is signed top-3 recovery, not top1 alone.
    small=np.array([.3,-.01,.005,0]);same_top1=np.array([.3,.01,-.005,0]);m=run_metrics(same_top1,small)
    assert m['nl1_error']<.2 and m['top1_match']==1 and m['signed_topk_overlap']==1/3 and m['joint_success_0p2']==0
    m=run_metrics(np.array([.29,-.3,.01,0]),np.array([.3,-.29,.01,0]))
    assert m['top1_match']==0 and m['joint_success_0p2']==1
    low=run_metrics(np.array([.001,0]),np.array([0.,0]))
    assert abs(low['nl1_error']-.1)<1e-12  # denominator floor .01
    a=np.ones((60,30)); ci=cluster_bootstrap(a,n_bootstrap=20,bounded_01=True)
    assert ci['estimate']==1 and 0<ci['ci_low']<1 and ci['ci_high']==1
    assert ci['boundary_adjusted'] and not ci['certifies_mean_ge_0p95']
    zero=cluster_bootstrap(np.zeros((60,30)),n_bootstrap=20,bounded_01=True)
    assert zero['ci_low']==0 and 0<zero['ci_high']<1
    # Independent derivation of the one-sided bounded-cluster radius.
    assert abs(ci['bounded_mean_low95']-(1-np.sqrt(np.log(20)/120)))<1e-12
    pair=pairwise_metrics([np.array([.001,0]),np.array([0.,0])],np.array([.1,0]))
    assert abs(pair['pairwise_normalized_l1']-.01)<1e-12
    assert abs(pair['pairwise_run_normalized_l1']-.1)<1e-12
    print('PASS: metric identity, sign errors, pair dependence, zero signal, bootstrap')
if __name__=='__main__': test()
