"""Recompute all endpoints/uncertainty from frozen per-checkpoint measurements.
Run after all manifest jobs: python analyze.py. No successful-only primary analysis.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import norm
from train import make_data

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'analysis';OUT.mkdir(exist_ok=True)
RNG=np.random.default_rng(20261103)
B=20000


def crossing(rows,key,threshold=.99,sustained=5):
    for i in range(len(rows)-sustained+1):
        if all(r[key]>=threshold for r in rows[i:i+sustained]):return i
    return None


def bootstrap(x,level=.95):
    x=np.asarray(x,float)
    vals=x[RNG.integers(len(x),size=(B,len(x)))].mean(axis=1)
    q=(1-level)/2
    return dict(mean=float(x.mean()),lo=float(np.quantile(vals,q)),hi=float(np.quantile(vals,1-q)),n=len(x))


def wilson(k,n,level=.95):
    z=norm.ppf((1+level)/2); q=k/n;d=1+z*z/n
    mid=(q+z*z/(2*n))/d;h=z*np.sqrt(q*(1-q)/n+z*z/(4*n*n))/d
    return [float(mid-h),float(mid+h)]


def extract(c,threshold=.99,sustained=5):
    out=Path(c['out']);s=json.loads((out/'summary.json').read_text())
    rows=[json.loads(x) for x in (out/'metrics.jsonl').read_text().splitlines()]
    assert rows[-1]['step']==c['steps']
    assert s['config']==c
    assert s['params']==3*c['p']*c['width']
    assert s.get('reverse_overlap',0)==0 or c['split']=='ordered'
    im=crossing(rows,'train_acc',threshold,sustained)
    ig=crossing(rows,'val_acc',threshold,sustained)
    tm=None if im is None else rows[im]['step']
    tg=None if ig is None else rows[ig]['step']
    C=c['steps']-(sustained-1)*c['eval_every']
    um=C if tm is None else tm; ug=C if tg is None else tg
    grok=tm is not None and tg is not None and tg>=10*max(tm,25) and rows[im]['val_acc']<=.5
    strict=grok and all(r['train_acc']>=threshold for r in rows[im:ig+1])
    x,y,tr,te=make_data(c['p'],c['fraction'],c['split_seed'],c.get('operation','add'),c['split'],c.get('random_labels',False))
    majority=int(y[tr].bincount(minlength=c['p']).argmax())
    majority_acc=float((y[te]==majority).float().mean())
    known={int(i):int(y[i]) for i in tr}
    reverse=np.array([known.get((int(i)%c['p'])*c['p']+int(i)//c['p'],majority) for i in te])
    reverse_acc=float(np.mean(reverse==y[te].numpy()))
    row=dict(group=c['group'],seed=c['seed'],split_seed=c['split_seed'],p=c['p'],width=c['width'],wd=c['wd'],params=s['params'],n_train=s['n_train'],n_test=s['n_val'],tM=tm,tG=tg,eventM=tm is not None,eventG=tg is not None,uM=um,uG=ug,C=C,L=np.log2((ug+25)/(um+25)),delay=ug-um,grok=grok,strict_grok=strict,final_train=rows[-1]['train_acc'],final_test=rows[-1]['val_acc'],best_test=max(r['val_acc'] for r in rows),initial_logit_std=rows[0]['logit_std'],initial_norm=rows[0]['norm'],final_norm=rows[-1]['norm'],final_fourier=rows[-1]['fourier'],train_at_grok=None if ig is None else rows[ig]['train_acc'],test_at_fit=None if im is None else rows[im]['val_acc'],post_grok_regressions=0 if ig is None else sum(r['val_acc']<threshold for r in rows[ig:]),reverse_overlap=s.get('reverse_overlap'),majority_acc=majority_acc,reverse_lookup_acc=reverse_acc,runtime=s['runtime_seconds'],cpu_seconds=s.get('cpu_seconds'),source_sha256=s.get('source_sha256'),out=str(out))
    return row,rows


def main():
    configs=json.loads((ROOT/'main_manifest.json').read_text())
    extension_path=ROOT/'extension_manifest.json'
    if extension_path.exists():
        extension=json.loads(extension_path.read_text())
        if all((Path(c['out'])/'summary.json').exists() for c in extension):
            configs+=extension
    extracted=[extract(c) for c in configs]
    df=pd.DataFrame([r for r,_ in extracted]);df.to_csv(OUT/'runs.csv',index=False)
    # Curves in long format, retaining every frozen run and checkpoint.
    curves=pd.DataFrame([dict(group=r['group'],seed=r['seed'],width=r['width'],p=r['p'],**v) for r,rows in extracted for v in rows])
    curves.to_csv(OUT/'curves.csv',index=False)
    agg=[]
    for (g,w),t in df.groupby(['group','width'],sort=False):
        ci=bootstrap(t.final_test)
        agg.append(dict(group=g,width=int(w),p=int(t.p.iloc[0]),n=len(t),fit=int(t.eventM.sum()),generalized=int(t.eventG.sum()),grok=int(t.grok.sum()),strict_grok=int(t.strict_grok.sum()),success_wilson=wilson(int(t.eventG.sum()),len(t)),median_fit=float(t.uM.median()),median_restricted_generalization=float(t.uG.median()),mean_final_test=ci,median_L=float(t.L.median()),mean_fourier=None if t.final_fourier.isna().all() else float(t.final_fourier.mean()),post_regression_runs=int((t.post_grok_regressions>0).sum())))
    (OUT/'group_summary.json').write_text(json.dumps(agg,indent=2)+'\n')
    pd.json_normalize(agg).to_csv(OUT/'group_summary.csv',index=False)
    a=df.query("group=='primary' and width==64").set_index('seed').sort_index()
    b=df.query("group=='primary' and width==256").set_index('seed').sort_index()
    assert a.index.equals(b.index)
    dL=b.L-a.L; dM=np.log2((b.uM+25)/(a.uM+25));dG=np.log2((b.uG+25)/(a.uG+25))
    paired=pd.DataFrame(dict(seed=a.index,dL=dL.to_numpy(),dM=dM.to_numpy(),dG=dG.to_numpy(),eventM64=a.eventM.to_numpy(),eventG64=a.eventG.to_numpy(),eventM256=b.eventM.to_numpy(),eventG256=b.eventG.to_numpy()))
    paired.to_csv(OUT/'primary_pairs.csv',index=False)
    zero=df.query("group=='decay0' and width==256").set_index('seed').sort_index()
    dp=b.eventG.astype(int)-zero.eventG.astype(int)
    stats=dict(P1=dict(relative_clock=bootstrap(dL),relative_clock_adjusted=bootstrap(dL,.975),train_clock=bootstrap(dM),generalization_clock=bootstrap(dG),all_endpoint_clocks_observed=bool(a.eventM.all() and b.eventM.all() and a.eventG.all() and b.eventG.all()),observed_endpoint_count=dict(fit64=int(a.eventM.sum()),fit256=int(b.eventM.sum()),generalized64=int(a.eventG.sum()),generalized256=int(b.eventG.sum()))),P2=dict(paired_success_difference=bootstrap(dp),paired_success_difference_adjusted=bootstrap(dp,.975),decay1_wilson=wilson(int(b.eventG.sum()),len(b)),decay0_wilson=wilson(int(zero.eventG.sum()),len(zero))),n_runs=len(df),n_updates=sum(c['steps'] for c in configs),total_training_cpu_seconds=float(df.cpu_seconds.sum()),total_training_wall_seconds_sum=float(df.runtime.sum()))
    # Descriptive difference of marginals ONLY: no 95% simultaneous/paired coverage claim.
    # Calibrated conservative bounds and exact empirical-bootstrap intervals are generated
    # by analysis/independent_audit_recompute.py and used in the paper.
    l1,h1=stats['P2']['decay1_wilson'];l0,h0=stats['P2']['decay0_wilson']
    stats['P2']['uncalibrated_difference_of_95pct_marginal_wilson_intervals']=[l1-h0,h1-l0]
    # Compare all saved scalar trajectories for replication vs rate-matched narrow.
    inv=[]
    for seed in range(100,110):
        ca=curves.query("group=='replicated' and seed==@seed").sort_values('step')
        cb=curves.query("group=='rate_matched' and seed==@seed").sort_values('step')
        inv.append(dict(seed=seed,max_train_loss_difference=float(np.max(abs(ca.train_loss.to_numpy()-cb.train_loss.to_numpy()))),max_test_loss_difference=float(np.max(abs(ca.val_loss.to_numpy()-cb.val_loss.to_numpy()))),max_test_accuracy_difference=float(np.max(abs(ca.val_acc.to_numpy()-cb.val_acc.to_numpy())))))
    stats['replication_trajectory_differences']=inv
    (OUT/'statistics.json').write_text(json.dumps(stats,indent=2)+'\n')
    sensitivity=[]
    for threshold in [.95,.99,.999]:
        for sustained in [3,5,9]:
            rr=pd.DataFrame([extract(c,threshold,sustained)[0] for c in configs if c['group']=='primary'])
            for w,t in rr.groupby('width'):
                sensitivity.append(dict(threshold=threshold,sustained=sustained,width=int(w),fit=int(t.eventM.sum()),generalized=int(t.eventG.sum()),grok=int(t.grok.sum()),median_uG=float(t.uG.median())))
    pd.DataFrame(sensitivity).to_csv(OUT/'sensitivity.csv',index=False)
    # Main LaTeX table uses censored restricted medians, explicitly marked.
    lines=[]
    for row in agg:
        if row['group']!='primary':continue
        w=row['width'];sub=df.query("group=='primary' and width==@w")
        med_g=row['median_restricted_generalization']; suffix='^{\\dagger}' if row['generalized']<len(sub)/2 else ''
        lines.append(f"{w} & {int(sub.params.iloc[0]):,} & {row['fit']}/10 & {row['generalized']}/10 & {row['median_fit']:g} & ${med_g:g}{suffix}$ & {row['grok']}/10 \\\\")
    (OUT/'main_table.tex').write_text('\n'.join(lines)+'\n')
    header='\\begin{tabular}{rrrrrrr}\n\\toprule\n$m$ & Params & $M$ & $G$ & $t_M$ & $u_G$ & $D$ \\\\\n\\midrule\n'
    (OUT/'main_table_full.tex').write_text(header+'\n'.join(lines)+'\n\\bottomrule\n\\end{tabular}\n')
    report=['# Measured results (auto-generated)','',json.dumps(stats,indent=2),'','## Cells']
    for v in agg:report.append(json.dumps(v))
    (OUT/'results_summary.md').write_text('\n'.join(report)+'\n')
    print(json.dumps(stats,indent=2))


if __name__=='__main__':main()
