"""Generate every paper table, figure, numeric macro, and auditable summary."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.stats import binom,norm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from study import ROOT

plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,
                     'pdf.fonttype':42,'ps.fonttype':42,'savefig.bbox':'tight'})
FIG=ROOT/'figures';TEX=ROOT/'paper/generated';FIG.mkdir(exist_ok=True);TEX.mkdir(exist_ok=True)
COLORS={'OLS-L':'#1965b0','OLS-Q':'#4eb265','OLS-C':'#dc050c','OLS-2H':'#7b2e8e',
        'Ridge-C':'#eea236','DM':'#666666','RF':'#9c5100','CV-select':'#882e72'}
NAMES={'reg1600k8':'Regular 8','reg1600k32':'Regular 32','reg1600k128':'Regular 128',
       'SBM':'SBM','BA':'BA','Facebook':'Facebook'}

def wilson(success,total):
    z=norm.ppf(.975);p=success/total;den=1+z*z/total
    center=(p+z*z/(2*total))/den
    radius=z*np.sqrt(p*(1-p)/total+z*z/(4*total*total))/den
    return max(0.,center-radius),min(1.,center+radius)

def summarize(df,keys):
    rows=[]
    for key,g in df.groupby(keys,sort=False):
        if not isinstance(key,tuple):key=(key,)
        row=dict(zip(keys,key));ok=g[g.valid] if 'valid' in g else g
        e=ok.error.dropna().to_numpy();r=len(e)
        row.update(reps=len(g),valid_reps=r)
        if not r:
            rows.append(row);continue
        mse=np.mean(e**2);rmse=np.sqrt(mse)
        row.update(bias=float(np.mean(e)),bias_mcse=float(np.std(e,ddof=1)/np.sqrt(r)),
            rmse=float(rmse),rmse_mcse=float(np.std(e**2,ddof=1)/(2*rmse*np.sqrt(r))),
            mse=float(mse))
        for col in ['conditional_bias','noise_var','iid_var','norm2','l1','exposure_sd',
                    'cover_iid','cover_oracle','fully_exposed','tail_fraction','prediction_mse']:
            if col in ok:
                row[col]=float(ok[col].mean());row[col+'_mcse']=float(ok[col].std()/np.sqrt(r))
                if col.startswith('cover_'):
                    row[col+'_wilson_lo'],row[col+'_wilson_hi']=wilson(int(ok[col].sum()),r)
        if 'conditional_bias' in ok and 'noise_var' in ok:
            theory=ok.conditional_bias**2+ok.noise_var
            discrepancy=e**2-theory.to_numpy()
            row.update(predicted_mse=float(theory.mean()),
                mse_identity_gap=float(discrepancy.mean()),
                mse_identity_mcse=float(discrepancy.std(ddof=1)/np.sqrt(r)))
        rows.append(row)
    return pd.DataFrame(rows)

def savefig(fig,name):
    fig.savefig(FIG/(name+'.pdf'));fig.savefig(FIG/(name+'.png'),dpi=180);plt.close(fig)

def cell(row):
    if row.valid_reps==0:return '---'
    return f'${row.rmse:.3f}\\,({row.rmse_mcse:.3f})$'

def main():
    raw={name:pd.read_csv(ROOT/f'results/{name}_raw.csv.gz') for name in
         ['main','noise','scaling','validation','saturation','sensitivity','threshold_oracle','support']}
    sm={}
    for name in ['main','noise','scaling']:
        sm[name]=summarize(raw[name],['graph','design','dgm','model'])
        sm[name].to_csv(ROOT/f'results/{name}_summary.csv',index=False)
    for name,keys in [('validation',['k','model']),('saturation',['p','model']),
                      ('threshold_oracle',['graph','design']),('support',['cutoff','selection'])]:
        sm[name]=summarize(raw[name],keys)
        sm[name].to_csv(ROOT/f'results/{name}_summary.csv',index=False)
    m=sm['main'];sens=raw['sensitivity']
    srows=[]
    for (graph,design,dgm),a in sens.groupby(['graph','design','dgm']):
        half=a.sharp+1.96*a.noise_se
        lo,hi=wilson(int(a.cover_sensitivity.sum()),len(a))
        srows.append(dict(graph=graph,design=design,dgm=dgm,reps=len(a),sharp=a.sharp.mean(),
            sharp_mcse=a.sharp.sem(),loose=a.loose.mean(),loose_mcse=a.loose.sem(),
            halfwidth=half.mean(),halfwidth_mcse=half.sem(),coverage=a.cover_sensitivity.mean(),
            coverage_wilson_lo=lo,coverage_wilson_hi=hi,gaussian_coverage=a.cover_gaussian.mean(),
            noise_se=a.noise_se.mean()))
    sens_summary=pd.DataFrame(srows)
    sens_summary.to_csv(ROOT/'results/sensitivity_summary.csv',index=False)
    # Numeric macros: every empirically reported main-text number has a provenance.
    macros={};provenance={}
    def macro(name,value,source,fmt='.3f'):
        macros[name]=format(value,fmt);provenance[name]={'value':float(value),'source':source}
    def pick(graph,dgm,model,design='bernoulli',suite='main'):
        a=sm[suite];return a[(a.graph==graph)&(a.dgm==dgm)&(a.model==model)&(a.design==design)].iloc[0]
    for k in [8,32,128]:
        for model,tag in [('OLS-L','L'),('OLS-C','C')]:
            r=pick(f'reg1600k{k}','cubic',model)
            word=['Low','Mid','High'][[8,32,128].index(k)]
            macro(f'R{tag}{word}',r.rmse,f'main regular {k}, cubic, {model}')
            macro(f'S{tag}{word}',r.rmse_mcse,f'main regular {k}, cubic, {model}, MCSE')
    for name,g,d,model,design in [('FBc','Facebook','cubic','OLS-C','bernoulli'),
           ('SBMc','SBM','cubic','OLS-C','bernoulli'),('SBMcc','SBM','cubic','OLS-C','cluster'),
           ('FBl','Facebook','cubic','OLS-L','bernoulli'),('FBcl','Facebook','cubic','OLS-L','cluster'),
           ('Reglcluster','reg1600k32','cubic','OLS-L','cluster')]:
        r=pick(g,d,model,design);macro(name,r.rmse,f'main {g},{d},{model},{design}');macro(name+'se',r.rmse_mcse,f'{name} MCSE')
    for k in [8,32,128]:
        tag=['Low','Mid','High'][[8,32,128].index(k)]
        r=sm['validation'].query("k==@k and model=='CV-select'").iloc[0]
        macro('CV'+tag,r.rmse,f'validation CV-select k={k}');macro('CV'+tag+'se',r.rmse_mcse,f'validation CV-select k={k} MCSE')
        z=raw['validation'].query("k==@k and model=='CV-select'")
        macro('ChooseC'+tag,float(z.selected.eq('OLS-C').mean()*100),f'validation cubic selection percent k={k}', '.1f')
    for p,tag in [(.2,'Low'),(.5,'Mid'),(.8,'High')]:
        r=sm['saturation'].query("p==@p and model=='OLS-L'").iloc[0]
        macro('QuadBias'+tag,r.bias,f'saturation p={p} OLS-L bias');macro('QuadBias'+tag+'se',r.bias_mcse,f'saturation p={p} OLS-L bias MCSE')
    for design,tag in [('bernoulli','B'),('cluster','C')]:
        r=pick('Facebook','linear','OLS-L',design,'noise')
        macro('CoverIID'+tag,r.cover_iid*100,f'noise Facebook linear OLS-L {design} iid coverage','.1f')
        macro('CoverOracle'+tag,r.cover_oracle*100,f'noise Facebook linear OLS-L {design} oracle coverage','.1f')
    for k,tag in [(8,'Low'),(32,'Mid'),(128,'High')]:
        ss=sens.query("graph==@('reg1600k'+str(k)) and design=='bernoulli' and dgm=='cubic'") if False else sens[(sens.graph==f'reg1600k{k}')&(sens.design=='bernoulli')&(sens.dgm=='cubic')]
        macro('Sharp'+tag,ss.sharp.mean(),f'sensitivity regular{k} cubic sharp mean')
        macro('Loose'+tag,ss.loose.mean(),f'sensitivity regular{k} cubic loose mean')
    high=raw['threshold_oracle'].query("graph=='reg1600k128' and design=='bernoulli'")
    macro('ThresholdHighValid',high.valid.sum(),'threshold oracle regular128 Bernoulli estimable counts','.0f')
    mid=raw['threshold_oracle'].query("graph=='reg1600k32' and design=='bernoulli'")
    macro('ThresholdMidValid',100*mid.valid.mean(),'threshold oracle regular32 Bernoulli estimable percent','.1f')
    ub=1600*binom.sf(int(np.ceil(.8*128))-1,128,.5)
    macro('ThresholdUB',ub,'exact n times Binomial(128,.5) tail from scipy.stats.binom.sf','.2e')
    for cutoff,tag in [(1,'All'),(20,'Twenty'),(100,'Hundred')]:
        r=sm['support'].query("cutoff==@cutoff and selection=='degree'").iloc[0]
        macro('Trim'+tag,r.rmse,f'support cutoff={cutoff} RMSE');macro('Trim'+tag+'se',r.rmse_mcse,f'support cutoff={cutoff} MCSE')
        macro('Kept'+tag,raw['support'].query('cutoff==@cutoff').n_kept.iloc[0],f'support cutoff={cutoff} nodes','.0f')
        rr=sm['support'].query("cutoff==@cutoff and selection=='random'").iloc[0]
        macro('Random'+tag,rr.rmse,f'support random matched to cutoff={cutoff} RMSE')
        macro('Random'+tag+'se',rr.rmse_mcse,f'support random matched to cutoff={cutoff} MCSE')
    total=len(raw['main'])//35+len(raw['noise'])//35+len(raw['scaling'])//10
    macro('BaseAssignments',total,'main + noise + scaling assignment count','.0f')
    # Conditional mean MSE identity check across all non-HT main cells.
    subset=m[m.model.ne('HT')]
    macro('IdentityMaxZ',np.max(abs(subset.mse_identity_gap/subset.mse_identity_mcse)),
          'main, maximum standardized empirical MSE minus conditional prediction gap')
    (TEX/'numbers.tex').write_text('\n'.join('\\newcommand{\\'+k+'}{'+v+'}' for k,v in macros.items())+'\n')
    (ROOT/'results/number_provenance.json').write_text(json.dumps(provenance,indent=2))
    # Figure 1: degree and sample size, plus exact population-information proxies.
    fig,axs=plt.subplots(1,2,figsize=(6.7,2.4))
    for model in ['OLS-L','OLS-C']:
        for n,style in [(800,':'),(1600,'-'),(3200,'--')]:
            rows=[]
            for k in [8,32,128]:
                source=m if n==1600 else sm['scaling']
                rows.append(source[(source.graph==f'reg{n}k{k}')&source.dgm.eq('cubic')&source.model.eq(model)&source.design.eq('bernoulli')].iloc[0])
            axs[0].errorbar([8,32,128],[r.rmse for r in rows],yerr=[1.96*r.rmse_mcse for r in rows],
                color=COLORS[model],ls=style,marker='o',ms=3,label=f'{model}, n={n}')
    axs[0].set(xscale='log',yscale='log',xlabel='Regular degree k',ylabel='GATE RMSE (cubic response)')
    axs[0].set_xticks([8,32,128],['8','32','128']);axs[0].legend(fontsize=6.3,ncol=2,loc='upper left')
    for model in ['OLS-L','OLS-C']:
        v=[pick(f'reg1600k{k}','linear',model) for k in [8,32,128]]
        axs[1].plot([8,32,128],[np.sqrt(r.noise_var) for r in v],'-o',color=COLORS[model],label=model+' exact conditional SD')
        k=np.array([8,32,128],float)
        proxy=np.sqrt(.25*(4+4*k+(2/3*k*(k-1)*(k-2) if model=='OLS-C' else 0))/1600)
        axs[1].plot(k,proxy,':',color=COLORS[model],label=model+' population proxy')
    axs[1].set(xscale='log',yscale='log',xlabel='Regular degree k',ylabel='Noise SD, n=1600')
    axs[1].set_xticks([8,32,128],['8','32','128']);axs[1].legend(fontsize=6.1)
    fig.tight_layout();savefig(fig,'degree_scaling')
    # Figure 2: design interaction, visible uncertainty, no HT rare-tail misranking.
    fig,axs=plt.subplots(1,2,figsize=(6.7,2.35),gridspec_kw={'width_ratios':[1.45,1]})
    for model in ['DM','OLS-L','OLS-C']:
        for design,marker,off in [('bernoulli','o',-.09),('cluster','s',.09)]:
            rows=[pick(g,'cubic',model,design) for g in NAMES]
            axs[0].errorbar(np.arange(6)+off,[r.rmse for r in rows],yerr=[1.96*r.rmse_mcse for r in rows],
                marker=marker,ls='-' if design=='bernoulli' else '--',ms=3,color=COLORS[model],label=f'{model}, {design}')
    axs[0].set(yscale='log',ylim=(.01,160),ylabel='Cubic GATE RMSE');axs[0].set_xticks(np.arange(6),['R8','R32','R128','SBM','BA','FB'])
    axs[0].legend(fontsize=5.9,ncol=2)
    for sel,col,label in [('degree',COLORS['OLS-C'],'Remove low degree'),('random',COLORS['OLS-L'],'Random, same count')]:
        su=sm['support'].query('selection==@sel').sort_values('cutoff')
        axs[1].errorbar(su.cutoff,su.rmse,yerr=1.96*su.rmse_mcse,marker='o',color=col,label=label)
    axs[1].legend(fontsize=6.0)
    axs[1].set(xlabel='Degree cutoff (matched sample count)',ylabel='Facebook cubic OLS-C RMSE',yscale='log')
    fig.tight_layout();savefig(fig,'design_support')
    # Figure 3: prediction-risk comparison on identical validation experiments.
    fig,axs=plt.subplots(1,2,figsize=(6.7,2.35))
    for model in ['OLS-L','OLS-Q','OLS-C','CV-select','RF']:
        rows=sm['validation'].query('model==@model').sort_values('k')
        pred=raw['validation'].query('model==@model').groupby('k').mse.agg(['mean','sem'])
        axs[0].errorbar(pred.index,pred['mean'],yerr=1.96*pred['sem'],marker='o',ms=3,color=COLORS[model],label=model)
        axs[1].errorbar(rows.k,rows.rmse,yerr=1.96*rows.rmse_mcse,marker='o',ms=3,color=COLORS[model],label=model)
    for ax in axs:
        ax.set_xscale('log');ax.set_xticks([8,32,128],['8','32','128']);ax.set_xlabel('Regular degree k')
    axs[0].set_ylabel('Held-out outcome MSE');axs[1].set(ylabel='GATE RMSE',yscale='log')
    axs[0].legend(fontsize=6.1,ncol=2);fig.tight_layout();savefig(fig,'prediction')
    # Figure 4: sensitivity kernel and sharp vs triangle bounds.
    fig,axs=plt.subplots(1,2,figsize=(6.7,2.3))
    kernels=pd.read_csv(ROOT/'results/kernels.csv')
    for g in ['reg1600k8','reg1600k32','reg1600k128']:
        a=kernels[kernels.graph.eq(g)];axs[0].plot(a.t,a.K,label=NAMES[g])
    axs[0].axhline(0,color='grey',lw=.5);axs[0].set(xlabel='Exposure threshold t',ylabel='Peano kernel K(t)')
    axs[0].legend(fontsize=7)
    a=sens.query("design=='bernoulli' and dgm=='cubic'")
    for col,label,style in [('sharp','Sharp curvature bound','-'),('loose','Triangle bound','--')]:
        v=a.groupby('graph')[col].agg(['mean','sem']).reindex(NAMES)
        axs[1].errorbar(np.arange(6),v['mean'],yerr=1.96*v['sem'],marker='o',ls=style,label=label)
    axs[1].set(yscale='log',ylabel='Bias bound, M=12');axs[1].set_xticks(np.arange(6),['R8','R32','R128','SBM','BA','FB']);axs[1].legend(fontsize=6.5)
    fig.tight_layout();savefig(fig,'sensitivity')
    # Figure 5 (appendix): quadratic symmetry and covariance coverage.
    fig,axs=plt.subplots(1,2,figsize=(6.7,2.4))
    for model in ['OLS-L','OLS-Q']:
        a=sm['saturation'].query('model==@model')
        axs[0].errorbar(a.p,a.bias,yerr=1.96*a.bias_mcse,marker='o',label=model,color=COLORS[model])
    axs[0].plot([.2,.5,.8],2*(2*np.array([.2,.5,.8])-1)*31/32,':',color='grey',label='Population projection')
    axs[0].set(xlabel='Treatment probability p',ylabel='Quadratic GATE bias');axs[0].legend(fontsize=7)
    no=sm['noise'].query("dgm=='linear' and model=='OLS-L' and design=='cluster'").set_index('graph').reindex(NAMES)
    for i,(col,label) in enumerate([('cover_iid','IID covariance'),('cover_oracle','True covariance')]):
        axs[1].errorbar(np.arange(6)+(i-.5)*.12,no[col],yerr=1.96*no[col+'_mcse'],marker='o',ls='',label=label)
    axs[1].axhline(.95,color='grey',ls='--');axs[1].set(ylim=(0,1.02),ylabel='Nominal 95% coverage')
    axs[1].set_xticks(np.arange(6),['R8','R32','R128','SBM','BA','FB']);axs[1].legend(fontsize=6.5)
    fig.tight_layout();savefig(fig,'symmetry_coverage')
    # Main results table: cubic RMSE with MCSE, both designs.
    models=['DM','OLS-L','OLS-Q','OLS-C','OLS-2H','Ridge-C']
    lines=['\\begin{tabular}{ll'+('c'*len(models))+'}','\\toprule',
           'Graph & Assignment & '+' & '.join(models)+' \\\\','\\midrule']
    for graph in NAMES:
        for design in ['bernoulli','cluster']:
            lines.append(NAMES[graph]+' & '+('Bern.' if design=='bernoulli' else 'Cluster')+' & '+
                         ' & '.join(cell(pick(graph,'cubic',model,design)) for model in models)+' \\\\')
    lines+=['\\bottomrule','\\end{tabular}'];(TEX/'main_table.tex').write_text('\n'.join(lines))
    # Detailed results: all response laws. HT separately because its Monte Carlo is not reliable.
    lines=[]
    for dgm in ['linear','quadratic','cubic','threshold','twohop']:
        lines += ['\\begin{table*}[t]','\\centering\\scriptsize',
                  '\\caption{'+dgm.capitalize()+' response: RMSE (Monte Carlo SE), 400 repetitions.}',
                  '\\begin{tabular}{ll'+'c'*len(models)+'}','\\toprule',
                  'Graph & Assignment & '+' & '.join(models)+' \\\\','\\midrule']
        for graph in NAMES:
            for design in ['bernoulli','cluster']:
                lines.append(NAMES[graph]+' & '+('Bern.' if design=='bernoulli' else 'Cluster')+' & '+
                    ' & '.join(cell(pick(graph,dgm,model,design)) for model in models)+' \\\\')
        lines+=['\\bottomrule','\\end{tabular}','\\end{table*}']
    (TEX/'full_tables.tex').write_text('\n'.join(lines))
    # Graph table, all values read from measured artifacts.
    gs=pd.read_csv(ROOT/'results/main_graphs.csv')
    lines=['\\begin{tabular}{lrrrrrr}','\\toprule','Graph & $n$ & $|E|$ & Mean $d$ & Min/max $d$ & Groups & Within \\\\','\\midrule']
    for r in gs.itertuples():
        lines.append(f'{NAMES[r.graph]} & {r.n} & {r.edges} & {r.mean_degree:.2f} & {r.min_degree}/{r.max_degree} & {r.clusters} & {r.within_edge_fraction:.3f} \\\\')
    lines+=['\\bottomrule','\\end{tabular}'];(TEX/'graph_table.tex').write_text('\n'.join(lines))
    # Threshold oracle rates + conditional-on-estimability error, without hiding failures.
    lines=['\\begin{tabular}{llrrr}','\\toprule','Graph & Design & Estimable/400 & RMSE if estimable & MCSE \\\\','\\midrule']
    for r in sm['threshold_oracle'].itertuples():
        lines.append(f'{NAMES[r.graph]} & {r.design} & {r.valid_reps} & '+
            (f'{r.rmse:.3f} & {r.rmse_mcse:.3f}' if r.valid_reps else '--- & ---')+' \\\\')
    lines+=['\\bottomrule','\\end{tabular}'];(TEX/'oracle_table.tex').write_text('\n'.join(lines))
    # HT is never ranked with stable regressions: show exposure support, not misleading precision.
    ht=m.query("model=='HT' and dgm=='cubic'")
    htr=raw['main'].query("model=='HT' and dgm=='cubic'")
    lines=['\\begin{tabular}{llrrrr}','\\toprule','Graph & Design & No exposures/400 & Mean estimate & Empirical RMSE & MCSE \\\\','\\midrule']
    for r in ht.itertuples():
        zz=int((htr.query('graph==@r.graph and design==@r.design').fully_exposed==0).sum())
        lines.append(f'{NAMES[r.graph]} & {r.design} & {zz} & {3+r.bias:.3f} & {r.rmse:.3f} & {r.rmse_mcse:.3f} \\\\')
    lines+=['\\bottomrule','\\end{tabular}'];(TEX/'ht_table.tex').write_text('\n'.join(lines))
    lines=['\\begin{tabular}{llrrrr}','\\toprule','Graph & Design & Gaussian coverage & Sensitivity coverage [95\\% Wilson CI] & Half-width & MCSE \\\\','\\midrule']
    for r in sens_summary.query("dgm=='cubic'").itertuples():
        lines.append(f'{NAMES[r.graph]} & {r.design} & {100*r.gaussian_coverage:.1f}\\% & '+
            f'{100*r.coverage:.2f}\\% [{100*r.coverage_wilson_lo:.2f}, {100*r.coverage_wilson_hi:.2f}] & '+
            f'{r.halfwidth:.3f} & {r.halfwidth_mcse:.3f} \\\\')
    lines+=['\\bottomrule','\\end{tabular}'];(TEX/'sensitivity_table.tex').write_text('\n'.join(lines))
    # Paired uncertainty for design comparisons is inappropriate (independent designs).
    # Paired within-assignment squared-loss differences between C and L are valid.
    comp=[]
    for (graph,design),a in raw['main'].query("dgm=='cubic' and model in ['OLS-C','OLS-L']").groupby(['graph','design']):
        b=a.pivot(index='rep',columns='model',values='error')
        d=b['OLS-C']**2-b['OLS-L']**2
        comp.append(dict(graph=graph,design=design,mean_C_minus_L_squared_loss=d.mean(),mcse=d.std()/np.sqrt(len(d))))
    pd.DataFrame(comp).to_csv(ROOT/'results/paired_comparisons.csv',index=False)
    print('All figures, tables, summaries, and numeric provenance generated.')

if __name__=='__main__':main()
