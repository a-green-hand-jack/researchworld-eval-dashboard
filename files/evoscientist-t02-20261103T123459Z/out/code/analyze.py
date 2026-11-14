"""Deterministic paired-seed analysis of the frozen protocol (no training).
All intervals are seed-cluster percentile bootstrap CIs, not point-level CIs.
"""
import itertools
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

SEED=20261103
B=10000
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'analysis'


def ci(x, statistic=np.mean):
    x=np.asarray(x,dtype=float)
    rng=np.random.default_rng(SEED)
    samples=x[rng.integers(0,len(x),size=(B,len(x)))]
    vals=statistic(samples,axis=1)
    return dict(mean=float(statistic(x)),lo=float(np.quantile(vals,.025)),hi=float(np.quantile(vals,.975)))


def signflip(x):
    x=np.asarray(x,float)
    signs=np.asarray(list(itertools.product([-1,1],repeat=len(x))))
    return float(np.mean(np.abs((signs*x).mean(axis=1))>=abs(x.mean())-1e-12))


def holm(ps):
    order=np.argsort(ps); adjusted=np.zeros(len(ps)); last=0
    for i,j in enumerate(order):
        last=max(last,(len(ps)-i)*ps[j]); adjusted[j]=min(last,1.)
    return adjusted.tolist()


def wilson(k,n):
    z=norm.ppf(.975); f=k/n; d=1+z*z/n
    center=(f+z*z/(2*n))/d
    half=z*np.sqrt(f*(1-f)/n+z*z/(4*n*n))/d
    return [float(center-half),float(center+half)]


def load():
    data=[]
    for f in sorted((ROOT/'results/confirm').glob('*.summary.json')):
        d=json.loads(f.read_text()); d['summary_path']=str(f.relative_to(ROOT)); data.append(d)
    expected=json.loads((ROOT/'confirm_jobs.json').read_text())
    if len(data)!=len(expected): raise RuntimeError(f'Need all {len(expected)} summaries, found {len(data)}')
    df=pd.DataFrame(data).sort_values(['tag','width','decay','seed'])
    # Validate exact ledger membership and pairing, not merely record count.
    cols=['tag','width','seed','p','fraction','steps','decay','normalization','task','frozen','shuffle']
    def key(d): return tuple(d.get(c,False) if c in ['frozen','shuffle'] else d.get(c) for c in cols)
    assert set(map(key,data))==set(map(key,expected))
    assert all(d['source_sha256']==json.loads((ROOT/'protocol.json').read_text())['train_sha256'] for d in data)
    assert not df[['seed','tag','width','decay']].duplicated().any()
    for _,g in df.groupby(['p','fraction','seed']): assert g['split_sha256'].nunique()==1
    return df


def times(g,key='t_eval'):
    tau=g['steps'].to_numpy()-2*g['eval_every'].to_numpy()
    x=g[key].to_numpy(float)
    return np.where(np.isfinite(x),x,tau)


def width_contrast(df,tag='main',suffix='',low_width=32,high_width=128):
    low=df[(df.tag==tag)&(df.width==low_width)].sort_values('seed')
    high=df[(df.tag==tag)&(df.width==high_width)].sort_values('seed')
    out=dict(tag=tag,threshold_suffix=suffix,low_width=low_width,high_width=high_width)
    yt_l=np.log1p(times(low,'t_train'+suffix)/50)
    yt_h=np.log1p(times(high,'t_train'+suffix)/50)
    ye_l=np.log1p(times(low,'t_eval'+suffix)/50)
    ye_h=np.log1p(times(high,'t_eval'+suffix)/50)
    d=yt_h-yt_l-(ye_h-ye_l)
    out.update(D=ci(d),train_log_effect=ci(yt_h-yt_l),eval_log_effect=ci(ye_h-ye_l),p=signflip(d),seed_values=d.tolist())
    out['relative_multiplier']={k:math.exp(v) for k,v in out['D'].items()}
    out['train_multiplier']={k:math.exp(v) for k,v in out['train_log_effect'].items()}
    out['eval_multiplier']={k:math.exp(v) for k,v in out['eval_log_effect'].items()}
    return out


def curve(row):
    p=Path(row['csv'])
    if not p.is_absolute():p=ROOT/p
    return pd.read_csv(p)


def clock_one(df,width,mode='next',landmark=0):
    low=df[(df.tag=='decay')&(df.width==width)&(df.decay==.05)].sort_values('seed')
    high=df[(df.tag=='decay')&(df.width==width)&(df.decay==.2)].sort_values('seed')
    rate=lambda wd:-math.log1p(-.01*wd)
    delta=rate(.2)*50
    horizon=rate(.05)*(20000-landmark)
    grid=np.arange(math.floor(horizon/delta)+1)*delta
    kappa=grid[-3]
    aa=[]; bb=[]; events=[]; allcurves=[]
    for (_,a),(_,b) in zip(low.iterrows(),high.iterrows()):
        per=[];ev=[];cc=[]
        for row in [a,b]:
            c=curve(row)
            target=landmark+grid/rate(row.decay)
            if mode=='next':idx=np.searchsorted(c.step.to_numpy(),target-1e-7,side='left')
            else:idx=np.searchsorted(c.step.to_numpy(),target+1e-7,side='right')-1
            idx=np.clip(idx,0,len(c)-1)
            accuracy=c.eval_acc.to_numpy()[idx]
            t=None
            for i in range(len(accuracy)-2):
                if np.all(accuracy[i:i+3]>=.99):t=grid[i];break
            per.append(kappa if t is None else t);ev.append(t is not None);cc.append(accuracy.tolist())
        aa.append(per[0]/kappa);bb.append(per[1]/kappa);events.append(ev);allcurves.append(cc)
    aa=np.asarray(aa);bb=np.asarray(bb)
    diff=bb-aa
    # Bootstrap ratio of restricted means, preserving seed pairs.
    rng=np.random.default_rng(SEED);ix=rng.integers(0,8,size=(B,8))
    ratios=bb[ix].mean(1)/np.maximum(aa[ix].mean(1),1e-12)
    return dict(width=width,mode=mode,landmark=landmark,kappa=float(kappa),deltaC=float(delta),
                K=ci(diff),p=signflip(diff),seed_values=diff.tolist(),half_values=aa.tolist(),double_values=bb.tolist(),
                half_events=sum(e[0] for e in events),double_events=sum(e[1] for e in events),
                ratio_of_restricted_means=dict(mean=float(bb.mean()/max(aa.mean(),1e-12)),lo=float(np.quantile(ratios,.025)),hi=float(np.quantile(ratios,.975))),
                clock_grid=grid.tolist(),accuracy=allcurves)


def main():
    OUT.mkdir(exist_ok=True)
    df=load();df.to_csv(OUT/'runs.csv',index=False)
    groups=[]
    for (tag,p,h,wd,f,task,normname),g in df.groupby(['tag','p','width','decay','fraction','task','normalization']):
        g=g.sort_values('seed'); n=len(g)
        s=dict(tag=tag,p=int(p),width=int(h),decay=float(wd),fraction=float(f),task=task,normalization=normname,n=n,n_params=int(g.n_params.iloc[0]),n_trainable=int(g.n_trainable.iloc[0]))
        for metric in ['final_train_acc','final_eval_acc','final_eval_loss','wall_seconds','cpu_seconds','initial_logit_rms']:
            for k,v in ci(g[metric]).items():s[metric+'_'+k]=v
        for metric in ['t_train','t_eval','t_train95','t_eval95','t_train90','t_eval90']:
            count=int(g[metric].notna().sum());s[metric+'_events']=count
            s[metric+'_wilson_lo'],s[metric+'_wilson_hi']=wilson(count,n)
            for k,v in ci(times(g,metric)).items():s[metric+'_restricted_'+k]=v
        # Difference/ratio is restricted endpoint, not uncensored delay.
        for k,v in ci(np.log((50+times(g,'t_eval'))/(50+times(g,'t_train')))).items():s['log_restricted_delay_'+k]=v
        groups.append(s)
    grouped=pd.DataFrame(groups);grouped.to_csv(OUT/'groups.csv',index=False)
    w=width_contrast(df)
    c32=clock_one(df,32);c128=clock_one(df,128)
    primary=[w,c32,c128]
    for obj,padj in zip(primary,holm([x['p'] for x in primary])):obj['p_holm']=padj
    contrasts=dict(width=w,clock32=c32,clock128=c128,
                   width95=width_contrast(df,suffix='95'),width90=width_contrast(df,suffix='90'),
                   normalizations={tag:width_contrast(df,tag) for tag in ['mean','matched']},
                   clock_previous={str(h):clock_one(df,h,'previous') for h in [32,128]},
                   clock_landmark={str(h):clock_one(df,h,landmark=5000) for h in [32,128]})
    # Observed-only contrasts explicitly reported only if ALL 8 pairs observed.
    for h in [32,128]:
        a=df[(df.tag=='decay')&(df.width==h)&(df.decay==.05)].sort_values('seed')
        b=df[(df.tag=='decay')&(df.width==h)&(df.decay==.2)].sort_values('seed')
        if a.t_eval.notna().all() and b.t_eval.notna().all():
            r=lambda wd:-math.log1p(-.01*wd)
            v=np.log(b.t_eval.to_numpy()*r(.2)/(a.t_eval.to_numpy()*r(.05)))
            contrasts['clock'+str(h)]['uncensored_log_clock_ratio']=ci(v)
        base=df[(df.tag=='main')&(df.width==h)].sort_values('seed')
        if base.t_eval.notna().all() and b.t_eval.notna().all():
            contrasts['clock'+str(h)]['double_base_log_time_ratio']=ci(np.log(b.t_eval.to_numpy()/base.t_eval.to_numpy()))
    contrasts['secondary_width_grid']=[width_contrast(df,low_width=lo,high_width=hi) for lo,hi in [(8,16),(16,32),(32,64),(64,128),(128,256),(64,256)]]
    # Adjacent-grid and completed-wide-range contrasts are exploratory, not new primary tests.
    secondary_rows=[]
    for obj in contrasts['secondary_width_grid']:
        q=obj['D']
        secondary_rows.append(f"{obj['low_width']} to {obj['high_width']} & {q['mean']:.3f} [{q['lo']:.3f}, {q['hi']:.3f}] \\\\")
    (OUT/'secondary_width_table.tex').write_text('\n'.join(secondary_rows)+'\n')
    (OUT/'contrasts.json').write_text(json.dumps(contrasts,indent=2))
    timing=dict(n_confirm=len(df),sum_run_wall_hours=float(df.wall_seconds.sum()/3600),
                sum_cpu_hours=float(df.cpu_seconds.sum()/3600),min_run_wall=float(df.wall_seconds.min()),
                max_run_wall=float(df.wall_seconds.max()),n_checkpoints=len(list((ROOT/'results/confirm').glob('*.pt'))),
                tags=df.groupby('tag').size().to_dict())
    (OUT/'timing.json').write_text(json.dumps(timing,indent=2))
    # Every row in the main width table is generated here, never typed manually.
    lines=[]
    for _,g in grouped[grouped.tag=='main'].sort_values('width').iterrows():
        lines.append(f"{g.width} & {g.n_params:,} & {int(g.t_train_events)}/8 & {g.t_train_restricted_mean:.0f} & {int(g.t_eval_events)}/8 & {g.t_eval_restricted_mean:.0f} [{g.t_eval_restricted_lo:.0f}, {g.t_eval_restricted_hi:.0f}] & {100*g.final_eval_acc_mean:.1f} \\\\")
    (OUT/'width_table.tex').write_text('\n'.join(lines)+'\n')
    lines=[]
    for tag in ['main','decay','frozen','shuffle','mean','matched','modulus','subtract','lowdata','middata','capacitytrain','capacityfrozen']:
        g=grouped[(grouped.tag==tag)&(grouped.width.isin([32,128,1024]))].sort_values(['decay','width'])
        for _,r in g.iterrows():
            lines.append(f"{tag} & {r.width} & {r.decay:g} & {int(r.t_train_events)}/8 & {int(r.t_eval_events)}/8 & {100*r.final_eval_acc_mean:.1f} [{100*r.final_eval_acc_lo:.1f}, {100*r.final_eval_acc_hi:.1f}] & {r.final_eval_loss_mean:.3g} \\\\")
    (OUT/'controls_table.tex').write_text('\n'.join(lines)+'\n')
    concise={k:{q:v for q,v in obj.items() if q in ['D','K','p','p_holm','relative_multiplier','train_multiplier','eval_multiplier','half_events','double_events','uncensored_log_clock_ratio']} for k,obj in contrasts.items() if k in ['width','clock32','clock128']}
    print(json.dumps(dict(primary=concise,timing=timing),indent=2))

if __name__=='__main__':main()
