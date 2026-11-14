"""Analysis from stored vectors; percentile intervals cluster on distinct explained source IDs."""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']: os.environ[k]='1'
from pathlib import Path
import json,math,time,hashlib
import numpy as np
import pandas as pd
from shap_audit import metrics,topk
from run_experiments import ROOT,OUT,DS,MODELS,SEEDS,PS,path_for
A=ROOT/'analysis'; A.mkdir(exist_ok=True)

def pair_stats(m,phi):
    et=np.sort(m['et'],axis=1); r=len(et); up=np.triu(np.ones((r,r),bool),1)
    eq=(et[:,None,:]==et[None,:,:]).all(axis=-1)&up; n=eq.sum(); fail=~m['success']; anyfail=(eq&(fail[:,None]|fail[None,:])).sum(); members=(eq*(fail[:,None].astype(int)+fail[None,:].astype(int))).sum()
    common=(et[:,None,:,None]==et[None,:,None,:]).sum(axis=(-1,-2)); jac=np.mean((common/(6-common))[up])
    ss=np.take_along_axis(np.sign(phi),et,axis=1); strict=eq&(ss[:,None,:]==ss[None,:,:]).all(axis=-1)
    return dict(pairs=int(up.sum()),agree=int(n),anyfail=int(anyfail),failed_members=int(members),pair_jaccard=float(jac),strict_agree=int(strict.sum()),strict_anyfail=int((strict&(fail[:,None]|fail[None,:])).sum()))

def summarize_records():
    rows=[]; refs=[]; runs=[]; controls=[]
    files=sorted((OUT/'main').glob('*.npz')); assert len(files)==648, f'{len(files)} tasks !=648'
    for file in files:
        a=np.load(file); ds=str(a['dataset']); model=str(a['model']); seed=int(a['seed']); slot=int(a['slot']); d=int(a['d']); ref=a['reference']; qual=bool(a['qualified'])
        rr=dict(dataset=ds,model=model,seed=seed,slot=slot,point=int(a['point']),qualified=qual,initial_qualified=bool(a.get('initial_qualified',a['qualified'])),split_error=float(a['split_error']),split_max=float(a['split_max']),split_top3=bool(a['split_top3']),reference_pairs=int(a['reference_pairs']),escalated=bool(a.get('escalated',False)),audit_qualified=bool(a.get('audit_qualified',True)),audit_error=float(a.get('audit_error',np.nan)),norm=float(np.abs(ref).sum()))
        if ds=='german':
            pair=np.concatenate([a['pairs_a'],a['pairs_b']]+([a['pairs_extra']] if 'pairs_extra' in a else []),axis=0)
            # Nonparametric reference-only pair bootstrap, independent of main runs.
            rg=np.random.default_rng([20261110,MODELS.index(model),seed,slot]); count=rg.multinomial(len(pair),np.full(len(pair),1/len(pair)),size=200)
            bp=count@pair/len(pair); rr['ref_boot_max_coordinate_width']=float(np.max(np.quantile(bp,.975,axis=0)-np.quantile(bp,.025,axis=0)))
        refs.append(rr)
        mm0=metrics(np.array([np.zeros(d),np.full(d,ref.sum()/d)]),ref)
        for i,ct in enumerate(['zero','efficiency_only']): controls.append(dict(dataset=ds,model=model,seed=seed,slot=slot,control=ct,success=bool(mm0['success'][i]),error=float(mm0['error'][i])))
        for im,method in enumerate(['kernel','perm']):
            for ip,p in enumerate(PS):
                est=a['attributions'][im,ip]; m=metrics(est,ref); ma=metrics(est,a['ref_a']); mb=metrics(est,a['ref_b']); pair=pair_stats(m,est)
                row=dict(dataset=ds,model=model,seed=seed,slot=slot,point=int(a['point']),method=method,p=p,requests=2+2*(d-1)*p,rows=16*(2+2*(d-1)*p),qualified=qual,**{k:float(np.mean(m[k])) for k in ['success','success10','success40','top3','top1','error','signok','regret']},error_median=float(np.median(m['error'])),error90=float(np.quantile(m['error'],.9)),gap=m['gap'],norm=m['norm'],floor=m['norm']<.02,material_n=m['material_n'],rank_def=float(np.mean(a['ranks'][ip]<(d-1))) if method=='kernel' else 0.,ref_label_discord=float(np.mean(ma['success']!=mb['success'])),ref_a_success=float(ma['success'].mean()),ref_b_success=float(mb['success'].mean()),**pair)
                row['gap_stratum']='near' if row['gap']<=.02 else ('middle' if row['gap']<=.1 else 'separated'); rows.append(row)
                for rep in range(len(est)):
                    runs.append(dict(dataset=ds,model=model,seed=seed,slot=slot,method=method,p=p,rep=rep,qualified=qual,**{k:float(m[k][rep]) for k in ['success','success10','success40','top3','top1','error','signok','regret']}))
    df=pd.DataFrame(rows); df.to_csv(A/'instance_metrics.csv',index=False); pd.DataFrame(refs).to_csv(A/'reference_diagnostics.csv',index=False); pd.DataFrame(runs).to_csv(A/'run_metrics.csv.gz',index=False,compression='gzip'); pd.DataFrame(controls).to_csv(A/'controls.csv',index=False)
    return df

def boot_idx(df,n=2000):
    rng=np.random.default_rng(20261111); out=[]
    for seed in sorted(df.seed.unique()):
        ids=np.flatnonzero(df.seed.to_numpy()==seed); out.append(rng.choice(ids,size=(n,len(ids)),replace=True))
    return np.concatenate(out,axis=1)

def summarize_cells(df):
    result=[]; gaps=[]
    for (ds,model,method,p),g in df.groupby(['dataset','model','method','p'],sort=False):
        g=g.sort_values(['seed','slot']).reset_index(drop=True); ii=boot_idx(g); qual=g.qualified.to_numpy(bool); weights=qual.astype(float); den=weights.sum(); row=dict(dataset=ds,model=model,method=method,p=int(p),n=len(g),qualified_n=int(den),requests=int(g.requests.iloc[0]),rows=int(g.rows.iloc[0]))
        for k in ['success','success10','success40','top3','top1','error','signok','regret','rank_def','pair_jaccard','ref_label_discord','ref_a_success','ref_b_success']:
            vals=g[k].to_numpy(); row[k]=float(vals.mean()); row[k+'_qualified']=float(np.sum(vals*weights)/den) if den else np.nan
            bs=vals[ii].mean(axis=1); row[k+'_lo'],row[k+'_hi']=np.quantile(bs,[.025,.975])
            qb=weights[ii].sum(axis=1); v=(vals*weights)[ii].sum(axis=1); qb=np.where(qb>0,qb,np.nan); row[k+'_qualified_lo'],row[k+'_qualified_hi']=np.nanquantile(v/qb,[.025,.975])
        for key,nu,de in [('agreement','agree','pairs'),('false_any','anyfail','agree'),('false_member','failed_members','agree'),('strict_false_any','strict_anyfail','strict_agree')]:
            numerator=g[nu].to_numpy(float); denominator=g[de].to_numpy(float)*(2 if key=='false_member' else 1)
            ds0=denominator.sum(); row[key]=float(numerator.sum()/ds0) if ds0 else np.nan; row[key+'_numerator']=int(numerator.sum()); row[key+'_denominator']=int(ds0)
            bb=numerator[ii].sum(axis=1)/np.maximum(denominator[ii].sum(axis=1),1); row[key+'_lo'],row[key+'_hi']=np.quantile(bb,[.025,.975])
        row['unresolved_lower']=float((g.success*weights).sum()/len(g)); row['unresolved_upper']=row['unresolved_lower']+1-den/len(g)
        # Conservative bounded-cluster sensitivity with three-stratum union bound.
        rad=np.sqrt(np.log(6/.05)/(2*(len(g)/3))); row['hoeffding_lo']=max(0,row['success']-rad); row['hoeffding_hi']=min(1,row['success']+rad)
        row['error_median_instances']=float(g.error_median.median()); row['error90_instances']=float(g.error90.median()); row['success_q10']=float(g.success.quantile(.1)); row['success_q90']=float(g.success.quantile(.9)); row['floor_n']=int(g.floor.sum()); row['material_empty_n']=int((g.material_n==0).sum()); result.append(row)
        for st in ['near','middle','separated']:
            sub=g[g.gap_stratum==st]; rr=dict(dataset=ds,model=model,method=method,p=p,stratum=st,n=len(sub),success=float(sub.success.mean()),top3=float(sub.top3.mean()),regret=float(sub.regret.mean()),error=float(sub.error.mean()))
            if len(sub):
                ids=boot_idx(sub.reset_index(drop=True)); vv=sub.success.to_numpy()[ids].mean(axis=1); rr['success_lo'],rr['success_hi']=np.quantile(vv,[.025,.975])
            gaps.append(rr)
    res=pd.DataFrame(result); res.to_csv(A/'cell_summary.csv',index=False); pd.DataFrame(gaps).to_csv(A/'gap_summary.csv',index=False)
    seed=df.groupby(['dataset','model','method','p','seed'])[['success','top3','error','signok','regret','rank_def']].mean().reset_index(); seed.to_csv(A/'seed_summary.csv',index=False)
    return res

def summarize_diagnostics():
    bg=[]
    for ds in ['acs','pima']:
        for model in MODELS:
            for slot in range(8):
                main=np.load(path_for(ds,model,11,slot)); ref16=main['reference']; den=max(np.abs(ref16).sum(),.02)
                for b in [4,16,64]:
                    a=main if b==16 else np.load(path_for(ds,model,11,slot,f'background_b{b}')); ref=a['reference']; drift=np.abs(ref-ref16).sum()/den
                    for im,method in enumerate(['kernel','perm']):
                        for ip,p in enumerate(PS):
                            m=metrics(a['attributions'][im,ip],ref); bg.append(dict(dataset=ds,model=model,slot=slot,b=b,method=method,p=p,drift=drift,success=float(m['success'].mean()),error=float(m['error'].mean())))
    pd.DataFrame(bg).to_csv(A/'background_metrics.csv',index=False)
    timing=[]; lib=[]
    for file in sorted((OUT/'timing').glob('*.npz')): timing+=json.loads(str(np.load(file)['records']))
    for file in sorted((OUT/'library').glob('*.npz')): lib+=json.loads(str(np.load(file)['records']))
    pd.DataFrame(timing).to_csv(A/'timing_raw.csv',index=False); pd.DataFrame(lib).to_csv(A/'library_raw.csv',index=False)
    tt=pd.DataFrame(timing).groupby(['dataset','model','method','p']).agg(cpu_median=('cpu_s','median'),cpu_q25=('cpu_s',lambda v: v.quantile(.25)),cpu_q75=('cpu_s',lambda v:v.quantile(.75)),wall_median=('wall_s','median'),requests=('requests','first'),rows=('rows','first')).reset_index(); tt.to_csv(A/'timing_summary.csv',index=False)
    ll=pd.DataFrame(lib).groupby(['dataset','model','mode','p']).agg(n=('success','size'),success=('success','mean'),error=('error','mean'),nonzero=('nonzero','mean'),adapter_calls=('adapter_calls','mean'),actual_interior_samples=('actual_interior_samples','mean')).reset_index(); ll.to_csv(A/'library_summary.csv',index=False)

def resource_summary():
    out={}; total=0.; actual=0
    for folder in ['pilot','main','background_b4','background_b64']:
        cpu=rows=predcpu=0.; files=list((OUT/folder).glob('*.npz'))
        for f in files:
            a=np.load(f); cpu+=float(a.get('cpu_s',0))+float(a.get('escalation_cpu_s',0)); rows+=int(a.get('actual_rows',0))+int(a.get('escalation_rows',0)); predcpu+=float(a.get('prediction_cpu_s',0))
        out[folder]=dict(tasks=len(files),instrumented_cpu_s=cpu,actual_rows=rows,prediction_cpu_s=predcpu); total+=cpu; actual+=rows
    for folder in ['library','timing']:
        cpu=0.; n=0
        for f in (OUT/folder).glob('*.npz'):
            a=np.load(f); rr=json.loads(str(a['records'])); cpu+=sum(r['cpu_s'] for r in rr); n+=len(rr)
        out[folder]=dict(records=n,instrumented_cpu_s=cpu); total+=cpu
    mm=json.loads((ROOT/'artifacts/model_metrics.json').read_text()); out['training']=dict(instrumented_cpu_s=sum(m['cpu_s'] for m in mm)); total+=out['training']['instrumented_cpu_s']
    out.update(total_instrumented_cpu_s=total,actual_rows_primary_reference_background_pilot=actual,nominal_main_rows=658243584,accounting='Instrumented fitting/task/diagnostic CPU; excludes installation, source retrieval, process startup, analysis, TeX. Parallel wall not sum of CPU. No claim these are uncached deployment costs.')
    out['peak_worker_rss_kb']=max(int(np.load(f)['peak_rss_kb']) for f in (OUT/'main').glob('*.npz'))
    out['workspace_bytes']=sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())
    (A/'resource_summary.json').write_text(json.dumps(out,indent=2)); return out

if __name__=='__main__':
    t=time.process_time(); df=summarize_records(); summarize_cells(df); summarize_diagnostics(); resource_summary(); (A/'analysis_cpu_s.txt').write_text(str(time.process_time()-t)+'\n')
