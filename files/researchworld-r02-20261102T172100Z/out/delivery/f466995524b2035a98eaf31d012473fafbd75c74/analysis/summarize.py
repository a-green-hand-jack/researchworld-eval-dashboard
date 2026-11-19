"""Aggregate independent replication estimates and paired method contrasts."""
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import t,norm

KEYS=['k','ncal','scenario','shift','epsilon','alpha']
METRICS=['coverage','coverage_g0','coverage_g1','volume_fraction','mean_radius','radius_infinite_fraction','infinite_threshold']

def interval(values):
    v=np.asarray(values,dtype=float); v=v[np.isfinite(v)]; n=len(v)
    if n<2: return (n,float(v.mean()) if n else None,None,None,None)
    avg=float(v.mean()); se=float(v.std(ddof=1)/np.sqrt(n)); half=float(t.ppf(.975,n-1)*se)
    return n,avg,se,avg-half,avg+half

def wilson(hits,total):
    z=norm.ppf(.975); p=hits/total; den=1+z*z/total
    center=(p+z*z/(2*total))/den
    half=z*np.sqrt(p*(1-p)/total+z*z/(4*total*total))/den
    return float(center-half),float(center+half)

def summarize(files,outdir):
    outdir=Path(outdir); outdir.mkdir(parents=True,exist_ok=True)
    frame=pd.concat([pd.read_json(f,lines=True) for f in files],ignore_index=True)
    if 'alpha' not in frame: frame['alpha']=.1
    assert not frame.duplicated(KEYS+['method','seed']).any(),'duplicate replication cells'
    result=[]; contrasts=[]; diagnostic=[]
    for keys,cell in frame.groupby(KEYS+['method']):
        for metric in METRICS:
            if metric not in cell: continue
            n,mean,se,lo,hi=interval(cell[metric])
            status='complete' if n==len(cell) else 'missing'
            if metric=='mean_radius' and n<len(cell):
                mean=se=lo=hi=None; status='omitted_due_to_infinite_radius'
            result.append(dict(zip(KEYS+['method'],keys))|dict(metric=metric,n_rep=n,n_rep_total=len(cell),summary_status=status,mean=mean,se=se,ci_low=lo,ci_high=hi))
        cv=cell['coverage'].to_numpy()
        fraction_low,fraction_high=wilson(int(np.sum(cv<1-cell['alpha'].iloc[0]-.05)),len(cv))
        diagnostic.append(dict(zip(KEYS+['method'],keys))|dict(fraction_below_tolerance_ci_low=fraction_low,fraction_below_tolerance_ci_high=fraction_high,n_rep=len(cell),coverage_sd=float(np.std(cv,ddof=1)),coverage_q10=float(np.quantile(cv,.1)),coverage_q50=float(np.quantile(cv,.5)),coverage_q90=float(np.quantile(cv,.9)),empirical_fraction_below_nominal_minus_05=float(np.mean(cv<1-cell['alpha'].iloc[0]-.05)),infinite_threshold_replications=int(cell['infinite_threshold'].sum()),nonfinite_radius_replications=int(cell['mean_radius'].isna().sum())))
    # Planned comparisons, alpha .05 descriptive pointwise intervals, no multiplicity claims.
    pairs=[('clr_scaled','clr_l2'),('clr_mondrian','clr_l2'),('raw_l2','clr_l2'),('raw_linf','clr_l2'),('coord_bonferroni','coord_naive'),('clr_weighted','clr_l2'),('clr_weighted','clr_mondrian'),('tv','raw_l2'),('tv','raw_linf'),('tv','clr_l2'),('kl_forward','raw_l2'),('kl_forward','raw_linf'),('kl_forward','clr_l2')]
    for keys,cell in frame.groupby(KEYS):
        for a,b in pairs:
            if a not in cell.method.values or b not in cell.method.values: continue
            for metric in ['coverage','coverage_g0','coverage_g1','volume_fraction']:
                pivot=cell.pivot(index='seed',columns='method',values=metric)
                n,mean,se,lo,hi=interval(pivot[a]-pivot[b])
                contrasts.append(dict(zip(KEYS,keys))|dict(method_a=a,method_b=b,metric=metric,n_rep=n,mean_difference=mean,se=se,ci_low=lo,ci_high=hi))
    shift_rows=[]
    shift_keys=[key for key in KEYS if key!='shift']+['method']
    for keys,cell in frame.groupby(shift_keys):
        if set(cell['shift'])!={False,True}: continue
        for metric in ['coverage','coverage_g0','coverage_g1','volume_fraction']:
            pivot=cell.pivot(index='seed',columns='shift',values=metric)
            n,mean,se,lo,hi=interval(pivot[True]-pivot[False])
            shift_rows.append(dict(zip(shift_keys,keys))|dict(metric=metric,n_rep=n,mean_shift_minus_iid=mean,se=se,ci_low=lo,ci_high=hi))
    if shift_rows: pd.DataFrame(shift_rows).to_csv(outdir/'shift_contrasts.csv',index=False)
    pd.DataFrame(diagnostic).to_csv(outdir/'diagnostics.csv',index=False)
    pd.DataFrame(result).to_csv(outdir/'summary.csv',index=False)
    pd.DataFrame(contrasts).to_csv(outdir/'paired_contrasts.csv',index=False)
    frame.to_csv(outdir/'replications.csv',index=False)
    metadata=dict(inputs=[str(f) for f in files],rows=len(frame),confidence='95% pointwise t intervals across independent dataset replications; paired contrasts within seed; not simultaneous; no hypothesis-selection correction',metrics='Coverage is simultaneous composition coverage. volume_fraction is uniform Euclidean simplex volume fraction, evaluated only at K=3. mean_radius is geometry-specific, not comparable across methods.')
    (outdir/'summary_manifest.json').write_text(json.dumps(metadata,indent=2))

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('files',nargs='+'); ap.add_argument('--outdir',required=True); args=ap.parse_args(); summarize(args.files,args.outdir)
