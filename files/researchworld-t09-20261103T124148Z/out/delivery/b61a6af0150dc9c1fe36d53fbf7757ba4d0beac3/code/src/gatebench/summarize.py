"""Performance uncertainty conditional on graph, plus graph-family variation.

Raw minimum-norm estimates remain in overall summaries, including nonestimable
endpoint fits; valid_fraction identifies that limitation. Additional estimable-only
summaries are conditional on that event and cannot be substituted for overall risk.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import norm, t

KEYS=['graph','graph_kind','graph_seed','n','degree_target','cluster_size','mixing',
      'design','p','rho','gamma','mechanism','model','truth']


def mean_se(values):
    a=np.asarray(values,dtype=float)
    a=a[np.isfinite(a)]
    return (float(a.mean()),float(a.std(ddof=1)/np.sqrt(len(a)))) if len(a)>1 else (float(a[0]) if len(a) else np.nan,np.nan)


def wilson(values):
    a=np.asarray(values,dtype=float);a=a[np.isfinite(a)];n=len(a)
    if not n:
        return np.nan,np.nan,np.nan
    p=a.mean();z=norm.ppf(.975);den=1+z*z/n
    mid=(p+z*z/(2*n))/den
    half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return float(p),float(mid-half),float(mid+half)


def performance(frame):
    error=frame.error.to_numpy(dtype=float)
    error=error[np.isfinite(error)]
    n=len(error)
    mse,mse_se=mean_se(error**2)
    bias,bias_se=mean_se(error)
    rmse=np.sqrt(mse)
    out=dict(replicates=len(frame),defined_replicates=n,defined_fraction=n/len(frame),
             bias=bias,bias_mcse=bias_se,bias_lo=bias-1.96*bias_se,bias_hi=bias+1.96*bias_se,
             mse=mse,mse_mcse=mse_se,rmse=rmse,
             rmse_mcse=mse_se/(2*rmse) if rmse>0 else np.nan,
             error_sd=float(error.std(ddof=1)) if n>1 else np.nan,
             valid_fraction=float(frame.valid.mean()))
    if np.isfinite(rmse) and np.isfinite(out['rmse_mcse']):
        out['rmse_lo']=max(0,rmse-1.96*out['rmse_mcse'])
        out['rmse_hi']=rmse+1.96*out['rmse_mcse']
    else:
        out['rmse_lo']=np.nan
        out['rmse_hi']=np.nan
    for name in ['conditional_bias','oracle_variance','conditional_mse','weight_norm2','prediction_mse',
                 'prediction_mean_mse','exposure_sd','expected_full_treated','expected_full_control',
                 'full_treated','full_control','hc3_se','oracle_se','condition','estimability_error']:
        if name in frame:
            out[name+'_mean'],out[name+'_mcse']=mean_se(frame[name])
    for name in ['cover_hc3','cover_oracle']:
        if name in frame:
            out[name],out[name+'_lo'],out[name+'_hi']=wilson(frame[name])
    if 'conditional_mse' in frame and frame.conditional_mse.notna().any():
        residual=frame.error**2-frame.conditional_mse
        out['mse_identity_residual'],out['mse_identity_residual_mcse']=mean_se(residual)
        out['assignment_bias2_mean']=float(np.nanmean(frame.conditional_bias**2))
    defined=np.isfinite(frame.error.to_numpy(dtype=float))
    supported=frame.valid.astype(bool).to_numpy() & defined
    out['undefined_count']=int((~defined).sum())
    out['unsupported_defined_count']=int((defined & ~supported).sum())
    out['estimable_replicates']=int(supported.sum())
    out['estimable_fraction']=float(supported.mean())
    es=frame.loc[supported,'error'].to_numpy(dtype=float)
    eb,ebse=mean_se(es);em,emse=mean_se(es**2);er=np.sqrt(em)
    out.update(estimable_bias=eb,estimable_bias_mcse=ebse,estimable_mse=em,estimable_mse_mcse=emse,
               estimable_rmse=er,estimable_rmse_mcse=emse/(2*er) if er>0 else np.nan)
    for name in ['cover_hc3','cover_oracle']:
        if name in frame:
            out[name+'_denominator']=int(frame[name].notna().sum())
            out['estimable_'+name+'_denominator']=int(frame.loc[supported,name].notna().sum())
            v,lo,hi=wilson(frame.loc[supported,name])
            out['estimable_'+name]=v;out['estimable_'+name+'_lo']=lo;out['estimable_'+name+'_hi']=hi
    return out


def paired_comparisons(frame):
    keys=[k for k in KEYS if k!='model']
    rows=[]
    for key,g in frame.groupby(keys,dropna=False,sort=True):
        groups={name:part.set_index('replicate') for name,part in g.groupby('model')}
        for reference in ['naive','linear']:
            if reference not in groups:
                continue
            for model,model_frame in groups.items():
                if model==reference or model=='naive':
                    continue
                joined=model_frame[['error','prediction_mse','conditional_mse','valid']].join(
                    groups[reference][['error','prediction_mse','conditional_mse','valid']],
                    lsuffix='_model',rsuffix='_reference',how='inner')
                both=np.isfinite(joined.error_model)&np.isfinite(joined.error_reference)
                j=joined[both]
                valid_both=both & joined.valid_model & joined.valid_reference
                row=dict(zip(keys,key));row.update(model=model,reference=reference,
                    valid_pairs=int(valid_both.sum()),pair_valid_fraction=float(valid_both.mean()),
                    pairs=len(j),total_pairs=len(joined),pair_defined_fraction=len(j)/len(joined))
                if len(j):
                    ea=j.error_model.to_numpy();eb=j.error_reference.to_numpy()
                    row['delta_mse'],row['delta_mse_mcse']=mean_se(ea**2-eb**2)
                    jv=joined[valid_both]
                    row['estimable_delta_mse'],row['estimable_delta_mse_mcse']=mean_se(jv.error_model**2-jv.error_reference**2)
                    ra=np.sqrt(np.mean(ea**2));rb=np.sqrt(np.mean(eb**2))
                    row['delta_rmse']=ra-rb
                    influence=ea**2/(2*ra)-eb**2/(2*rb)
                    row['delta_rmse_mcse']=mean_se(influence)[1]
                    row['delta_prediction_mse'],row['delta_prediction_mse_mcse']=mean_se(j.prediction_mse_model-j.prediction_mse_reference)
                    row['delta_conditional_mse'],row['delta_conditional_mse_mcse']=mean_se(j.conditional_mse_model-j.conditional_mse_reference)
                rows.append(row)
    return rows


def summarize(files, output):
    # Stream one checkpoint at a time: production raw rows need not fit in RAM.
    rows=[];pairs=[];total_rows=0
    for file in files:
        frame=pd.read_parquet(file)
        total_rows+=len(frame)
        for key in KEYS:
            if key not in frame:
                frame[key]=np.nan
        for key,g in frame.groupby(KEYS,dropna=False,sort=True):
            row=dict(zip(KEYS,key));row.update(performance(g));rows.append(row)
        pairs.extend(paired_comparisons(frame))
    result=pd.DataFrame(rows)
    paired=pd.DataFrame(pairs)
    output.mkdir(parents=True,exist_ok=True)
    result.to_csv(output/'performance_by_graph.csv',index=False)
    paired.to_csv(output/'paired_by_graph.csv',index=False)
    # Equal graph weights; these intervals capture between-graph variation,
    # separately from conditional Monte Carlo intervals above. n=1 yields no CI.
    family_keys=[k for k in KEYS if k not in ['graph','graph_seed','truth']]
    families=[]
    for key,g in result.groupby(family_keys,dropna=False,sort=True):
        row=dict(zip(family_keys,key));row['graphs']=int(g.graph.nunique())
        row['truth_min']=float(g.truth.min());row['truth_max']=float(g.truth.max())
        if len(g)!=row['graphs']:
            raise ValueError('Duplicate graph/scenario summaries: do not pool overlapping checkpoints')
        for metric in ['bias','mse','rmse','valid_fraction','cover_hc3','cover_oracle',
                       'oracle_variance_mean','assignment_bias2_mean','prediction_mse_mean','defined_fraction',
                       'estimable_bias','estimable_rmse','estimable_fraction','estimable_cover_hc3','estimable_cover_oracle']:
            if metric not in g:
                continue
            value,se=mean_se(g[metric]);count=g[metric].notna().sum()
            critical=t.ppf(.975,count-1) if count>1 else np.nan
            row[metric+'_graphs_defined']=int(count)
            row[metric+'_graph_mean']=value
            row[metric+'_graph_se']=se
            row[metric+'_graph_lo']=value-critical*se
            row[metric+'_graph_hi']=value+critical*se
        row['pooled_rmse']=np.sqrt(g.mse.mean())
        families.append(row)
    pd.DataFrame(families).to_csv(output/'performance_by_family.csv',index=False)
    pair_families=[]
    for key,g in paired.groupby(family_keys+['reference'],dropna=False,sort=True):
        row=dict(zip(family_keys+['reference'],key));row['graphs']=int(g.graph.nunique())
        row['truth_min']=float(g.truth.min());row['truth_max']=float(g.truth.max())
        if len(g)!=row['graphs']:
            raise ValueError('Duplicate graph/scenario paired summaries: do not pool overlapping checkpoints')
        for metric in ['delta_mse','delta_rmse','delta_prediction_mse','delta_conditional_mse']:
            value,se=mean_se(g[metric]);count=g[metric].notna().sum()
            critical=t.ppf(.975,count-1) if count>1 else np.nan
            row[metric+'_graph_mean']=value;row[metric+'_graph_se']=se
            row[metric+'_graph_lo']=value-critical*se;row[metric+'_graph_hi']=value+critical*se
        pair_families.append(row)
    pd.DataFrame(pair_families).to_csv(output/'paired_by_family.csv',index=False)
    return total_rows,result


def main():
    p=argparse.ArgumentParser();p.add_argument('input',nargs='+');p.add_argument('--output',required=True)
    a=p.parse_args()
    files=[]
    for path in a.input:
        files.extend(sorted(f for f in Path(path).glob('*.parquet') if not f.name.endswith('.tmp.parquet')))
    total_rows,summary=summarize(files,Path(a.output))
    manifest=dict(rows=total_rows,cells=len(files),summary_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  inputs=[dict(path=str(f),sha256=hashlib.sha256(f.read_bytes()).hexdigest()) for f in files])
    (Path(a.output)/'summary_manifest.json').write_text(json.dumps(manifest,indent=2))
    print(f'Summarized {total_rows} rows across {len(files)} cell files into {len(summary)} graph/model/scenario groups')

if __name__=='__main__':
    main()
