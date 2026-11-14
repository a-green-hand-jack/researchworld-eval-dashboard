"""Generate all paper statistics/tables from completed independent seed runs."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from experiment import METHODS, ROOT

OUT=ROOT/'artifacts'/'analysis'
METRICS=['coverage','coverage_G0','coverage_G1','coverage_B0','coverage_B1','V','A_K','A_mean','E_Q','E_rho25','E_rho75','ESS','MSE_G0','MSE_G1','MC_block_delta_Q','MC_block_delta_AK','infinite_threshold_rate','coordinate_coverage_mean','coordinate_coverage_min']

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    cfg=json.loads((ROOT/'config.json').read_text()); d=pd.read_csv(ROOT/'artifacts/main/metrics.csv')
    runs=pd.read_csv(ROOT/'artifacts/main/runs.csv')
    assert len(runs)==len(cfg['seeds'])*len(cfg['dimensions'])*len(cfg['laws'])
    assert set(runs.seed)==set(cfg['seeds']) and not runs.duplicated(['seed','K','law']).any()
    assert len(d)==len(runs)*21
    assert d[['coverage','V','A_K','E_Q']].notna().all().all()
    r=np.random.default_rng(cfg['bootstrap_seed']); n=len(cfg['seeds']); B=cfg['bootstrap_resamples']
    ix=r.integers(0,n,(B,n)); weights=np.stack([(ix==i).sum(1) for i in range(n)],axis=1)/n
    seeds=cfg['seeds']
    def stats(v):
        v=np.asarray(v,float); assert len(v)==n and np.isfinite(v).all()
        boot=weights@v
        return v.mean(),*np.quantile(boot,[.025,.975,.0025,.9975])
    def summarise(frame,group):
        rows=[]
        for key,sub in frame.groupby(group,sort=True):
            key=key if isinstance(key,tuple) else (key,)
            for met in METRICS:
                vec=sub.groupby('seed')[met].mean().reindex(seeds)
                if vec.notna().sum()==0: continue
                assert vec.notna().all(), (key,met)
                mean,lo,hi,_,_=stats(vec)
                rows.append(dict(zip(group,key),metric=met,mean=mean,lo=lo,hi=hi,n_seeds=n))
        return pd.DataFrame(rows)
    full=summarise(d,['K','law','regime','method']); full.to_csv(OUT/'summary_cells.csv',index=False)
    agg=summarise(d,['law','regime','method']); agg.to_csv(OUT/'summary_by_law.csv',index=False)
    overall=summarise(d,['regime','method']); overall.to_csv(OUT/'summary_overall.csv',index=False)
    def vector(method,metric,regime='source',law=None):
        z=d[(d.method==method)&(d.regime==regime)]
        if law is not None: z=z[z.law==law]
        return z.groupby('seed')[metric].mean().reindex(seeds).to_numpy()
    specs=[('P1','L2 easy minus difficult coverage',vector('L2','coverage_G0',law='zeros')-vector('L2','coverage_G1',law='zeros')),
           ('P2','L2 interior minus boundary coverage',vector('L2','coverage_B0',law='zeros')-vector('L2','coverage_B1',law='zeros')),
           ('P3','L2 shifted minus source coverage',vector('L2','coverage','shift')-vector('L2','coverage')),
           ('P4','Weighted minus L2 shifted coverage',vector('WeightedL2','coverage','shift')-vector('L2','coverage','shift')),
           ('P5','Mondrian minus L2 shifted difficult coverage',vector('MondrianL2','coverage_G1','shift')-vector('L2','coverage_G1','shift')),
           ('P6','Scaled minus L2 source difficult coverage',vector('ScaledL2','coverage_G1')-vector('L2','coverage_G1')),
           ('P7','CLR6 minus CLR2 source supported face mass',vector('CLR-6','A_K',law='zeros')-vector('CLR-2','A_K',law='zeros')),
           ('P8','Bonferroni minus coordinate source coverage',vector('Bonferroni','coverage')-vector('Coord','coverage')),
           ('P9','Scaled minus L2 source mixed mass',vector('ScaledL2','E_Q')-vector('L2','E_Q')),
           ('P10','Mondrian minus L2 shifted mixed mass',vector('MondrianL2','E_Q','shift')-vector('L2','E_Q','shift'))]
    contrasts=[]; cv=[]
    for pid,desc,v in specs:
        mean,lo,hi,al,ah=stats(v)
        contrasts.append({'ID':pid,'contrast':desc,'mean':mean,'lo95':lo,'hi95':hi,'lo995':al,'hi995':ah})
        cv.extend([{'ID':pid,'seed':s,'difference':float(vv)} for s,vv in zip(seeds,v)])
    c=pd.DataFrame(contrasts); c.to_csv(OUT/'contrasts.csv',index=False); pd.DataFrame(cv).to_csv(OUT/'contrast_seed_values.csv',index=False)
    controls=pd.read_csv(ROOT/'artifacts/main/controls.csv'); control_rows=[]
    for k,sub in controls[controls.law=='zeros'].groupby('K'):
        vec=sub.groupby('seed').coverage_difference.mean().reindex(seeds)
        mean,lo,hi,_,_=stats(vec)
        control_rows.append({'K':int(k),'coverage_difference':mean,'lo':lo,'hi':hi,'analytic_difference':.35,'ambient_mass_difference':0,'face_mass_difference':1,'mixed_mass_difference':1/(2*k)})
    control=pd.DataFrame(control_rows); control.to_csv(OUT/'control_summary.csv',index=False)
    def fmt(t,method,metric):
        z=t[(t.method==method)&(t.metric==metric)].iloc[0]
        precision=3
        values=[float(z['mean']),float(z.lo),float(z.hi)]
        while precision<8 and (any(0<v<1 and round(v,precision) in (0.,1.) for v in values)
                               or (z.lo<z.hi and round(float(z.lo),precision)==round(float(z.hi),precision))):
            precision+=1
        return f"{z['mean']:.{precision}f} [{z.lo:.{precision}f}, {z.hi:.{precision}f}]"
    names={'CLR-6':r'CLR $10^{-6}$','CLR-2':r'CLR $10^{-2}$','Coord':'Coordinate','Bonferroni':'Bonferroni','ScaledL2':'Scaled L2','MondrianL2':'Mondrian L2','WeightedL2':'Weighted L2'}
    def tex_table(filename,header,rows):
        text='\\begin{tabular}{'+'l'+'c'*(len(header)-1)+'}\n\\toprule\n'+' & '.join(header)+' \\\\\n\\midrule\n'
        text+='\n'.join(' & '.join(map(str,row))+' \\\\' for row in rows)
        text+='\n\\bottomrule\n\\end{tabular}\n'; (OUT/filename).write_text(text)
    t=agg[(agg.law=='zeros')&(agg.regime=='source')]
    tex_table('source_coverage.tex',['Method','Marginal','Easy $G=0$','Difficult $G=1$','Boundary $B=1$'],[[names.get(m,m)]+[fmt(t,m,v) for v in ['coverage','coverage_G0','coverage_G1','coverage_B1']] for m in METHODS if m!='WeightedL2'])
    tex_table('source_size.tex',['Method','$V$','$A_K$','$E_Q$'],[[names.get(m,m)]+[fmt(t,m,v) for v in ['V','A_K','E_Q']] for m in METHODS if m!='WeightedL2'])
    t=overall[overall.regime=='shift']
    tex_table('shift.tex',['Method','Marginal','Easy','Difficult','$E_Q$'],[[names.get(m,m)]+[fmt(t,m,v) for v in ['coverage','coverage_G0','coverage_G1','E_Q']] for m in ['L2','ScaledL2','MondrianL2','WeightedL2']])
    short={'P1':('L2 easy--difficult','S,Z'),'P2':('L2 interior--boundary','S,Z'),'P3':('L2 shifted--source','Both'),'P4':('Weighted--L2 coverage','T,Both'),'P5':('Mondrian--L2 difficult','T,Both'),'P6':('Scaled--L2 difficult','S,Both'),'P7':('CLR6--CLR2 face mass','S,Z'),'P8':('Bonf.--coordinate coverage','S,Both'),'P9':('Scaled--L2 mixed mass','S,Both'),'P10':('Mondrian--L2 mixed mass','T,Both')}
    tex_table('contrasts.tex',['ID','Effect','Cells','Estimate','95\\% interval','99.5\\% interval'],[[z.ID,*short[z.ID],f'{z["mean"]:.3f}',f'[{z.lo95:.3f}, {z.hi95:.3f}]',f'[{z.lo995:.3f}, {z.hi995:.3f}]'] for _,z in c.iterrows()])
    tex_table('controls.tex',['$K$','Measured coverage gain','Exact coverage gain','$\\Delta V$','$\\Delta A_K$','$\\Delta E_Q$'],[[int(z.K),f'{z.coverage_difference:.3f} [{z.lo:.3f}, {z.hi:.3f}]','0.350','0','1',f'{z.mixed_mass_difference:.4f}'] for _,z in control.iterrows()])
    # Full six-cell tables preserve all geometries and regimes, with no winner selection.
    for regime in ['source','shift']:
        lines=[]
        for law in cfg['laws']:
            for k in cfg['dimensions']:
                z=full[(full.K==k)&(full.law==law)&(full.regime==regime)]
                lines.append(r'\subsection{'+f'{regime.title()}, {law}, $K={k}$'+'}\n')
                header=['Method','$C$','$C_{G=1}$','$C_{B=1}$','$V$','$A_K$','$E_Q$']
                rows=[]
                for m in METHODS:
                    if regime=='source' and m=='WeightedL2': continue
                    vals=[fmt(z,m,v) if not (v=='coverage_B1' and law=='interior') else '--' for v in ['coverage','coverage_G1','coverage_B1','V','A_K','E_Q']]
                    rows.append([names.get(m,m)]+vals)
                temp=OUT/'_temp.tex'; tex_table('_temp.tex',header,rows)
                lines.append('\\begin{center}\\scriptsize\\resizebox{\\textwidth}{!}{%\n'+temp.read_text()+'}\\end{center}\n')
        (OUT/f'full_{regime}.tex').write_text('\n'.join(lines))
    (OUT/'_temp.tex').unlink(missing_ok=True)
    # Resource measurements and resolution flags, all generated from actual runs.
    mainlog=(ROOT/'main.log').read_text().strip().splitlines()
    manifest={'n_cells':len(runs),'n_rows':len(d),'seeds':n,'cell_seconds_sum':float(runs.seconds.sum()),'cell_seconds_max':float(runs.seconds.max()),'cell_seconds_median':float(runs.seconds.median()),'max_worker_rss_kb':int(runs.max_rss_kb.max()),'main_wall_seconds':json.loads(mainlog[-1])['wall_seconds'],'ESS_mean':float(runs.ESS.mean()),'ESS_min':float(runs.ESS.min()),'ESS_max':float(runs.ESS.max()),'zero_volume_rows':int(d.probe_zero_V.sum()),'zero_face_rows':int(d.probe_zero_AK.sum()),'max_infinity_rate':float(d.infinite_threshold_rate.max()),'cal_difficult_min':int(d.n_cal_G1.min()),'cal_difficult_max':int(d.n_cal_G1.max())}
    (OUT/'run_summary.json').write_text(json.dumps(manifest,indent=2))
    tex_table('resources.tex',['Field','Recorded value'],[
        ['Completed cells / method-regime rows',f'{len(runs)} / {len(d):,}'],
        ['Main-run wall time',f'{manifest["main_wall_seconds"]:.3f} seconds'],
        ['Sum of cell elapsed times',f'{manifest["cell_seconds_sum"]:.3f} seconds'],
        ['Median / maximum cell elapsed time',f'{manifest["cell_seconds_median"]:.3f} / {manifest["cell_seconds_max"]:.3f} seconds'],
        ['Maximum reported worker peak RSS',f'{manifest["max_worker_rss_kb"]:,} KB'],
        ['Mean weighted calibration ESS',f'{manifest["ESS_mean"]:.3f}'],
        ['Minimum / maximum ESS',f'{manifest["ESS_min"]:.3f} / {manifest["ESS_max"]:.3f}'],
        [r'Minimum / maximum calibration $G=1$ count',f'{manifest["cal_difficult_min"]} / {manifest["cal_difficult_max"]}'],
        ['Maximum observed infinity rate',str(manifest['max_infinity_rate'])]])
    print(c.to_string(index=False)); print(json.dumps(manifest,indent=2))

if __name__=='__main__': run()
