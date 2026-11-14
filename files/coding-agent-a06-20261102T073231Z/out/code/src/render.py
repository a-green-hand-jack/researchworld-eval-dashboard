"""Render every paper figure/table and data-derived TeX scalar from actual results."""
import json, pathlib, time
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'paper/generated';OUT.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,
 'text.usetex':True,'font.family':'serif','font.serif':['Times'],
 'figure.constrained_layout.use':True})

def save(fig,name):
    fig.savefig(OUT/(name+'.pdf'));plt.close(fig)
    import pymupdf
    doc=pymupdf.open(OUT/(name+'.pdf'));doc[0].get_pixmap(dpi=170).save(str(OUT/(name+'.png')))

def table(path,header,rows):
    col='l'+'r'*(len(header)-1)
    text='\\begin{tabular}{'+col+'}\n\\toprule\n'+' & '.join(header)+' \\\\\n\\midrule\n'
    text+='\n'.join(' & '.join(map(str,row))+' \\\\' for row in rows)
    text+='\n\\bottomrule\n\\end{tabular}\n';(OUT/path).write_text(text)

def pp(x):return f'{100*x:.1f}'
def meanse(row,key):return pp(row[key])+r' $\pm$ '+f"{100*row[key+'_se']:.2f}"

def main():
    syn=pd.read_csv(ROOT/'results/synthetic.csv')
    real=pd.read_csv(ROOT/'results/real_replay.csv')
    call=pd.read_csv(ROOT/'results/call_budget.csv')
    budget=pd.read_csv(ROOT/'results/budget.csv')
    dup=pd.read_csv(ROOT/'results/duplication.csv')
    hetero=pd.read_csv(ROOT/'results/heterogeneous.csv')
    paired_budget=pd.read_csv(ROOT/'results/paired_call_budget.csv')
    meta=json.loads((ROOT/'results/real_metadata.json').read_text());p=meta['primary']
    numbers={}
    def num(k,v):numbers[k]=str(v)
    s=syn.query('rho==0 and n==128 and k==64').iloc[0]
    for key in ['optimism','naive_cover','audit_cover','simultaneous_cover','naive_false_superiority','adjusted_false_superiority']:
        num('Syn'+''.join(x.title() for x in key.split('_')),pp(s[key]))
    r=real.query('n==128 and k==24').iloc[0]
    for key in ['optimism','naive_cover','audit_cover','simultaneous_cover','reported_gain','actual_gain','naive_false_superiority','adjusted_false_superiority','audit_referenced_optimism']:
        num('Real'+''.join(x.title() for x in key.split('_')),pp(r[key]))
    reps=np.load(ROOT/'results/real_repetitions.npz')['n128_k24_optimism']
    num('RealOptimismQFive',pp(np.quantile(reps,.05)))
    num('RealOptimismQNinetyFive',pp(np.quantile(reps,.95)))
    num('RealNegativeRate',pp(np.mean(reps<0)))
    hs=hetero.query('gap==.15').iloc[0]
    num('HeteroLargeOptimism',pp(hs.optimism));num('HeteroLargeOptimal',pp(hs.optimal_selection))
    num('RealMeanReportedAccuracy',pp(r.selected_target+r.optimism))
    num('RealWeightedAuditAccuracy',pp(r.weighted_audit_accuracy))
    num('RealAuditReferenceAuditSE',f'{100*r.audit_referenced_optimism_audit_se:.2f}')
    num('RealAuditReferenceMCSE',f'{100*r.audit_referenced_optimism_mcse:.2f}')
    matched=call.query('reuse_n==128').iloc[0]
    num('MatchedQualityDifference',f'{100*matched.quality_difference:+.2f}')
    num('MatchedQualitySE',f'{100*matched.quality_difference_se:.2f}')
    num('MatchedAuditWidth',pp(matched.audit_width));num('MatchedAuditCoverage',pp(matched.audit_cover))
    num('MatchedSimWidth',pp(r.simultaneous_width))
    for key in ['tune_score','baseline_tune','audit_score','baseline_audit','audit_gain']:
        num('Primary'+''.join(x.title() for x in key.split('_')),pp(p[key]))
    num('PrimaryCandidate',p['candidate']);num('PrimaryLo',pp(p['audit_ci'][0]));num('PrimaryHi',pp(p['audit_ci'][1]))
    num('PrimaryGainLo',pp(p['paired_gain_ci'][0]));num('PrimaryGainHi',pp(p['paired_gain_ci'][1]))
    num('PrimaryP',f"{p['paired_p']:.3f}");num('PrimaryWins',p['paired_wins']);num('PrimaryLosses',p['paired_losses'])
    num('MeanCorrelation',f"{meta['mean_pair_correlation']:.2f}")
    num('MinCorrelation',f"{meta['min_pair_correlation']:.2f}");num('MaxCorrelation',f"{meta['max_pair_correlation']:.2f}")
    num('MinDev',pp(meta['dev_accuracy_range'][0]));num('MaxDev',pp(meta['dev_accuracy_range'][1]))
    num('TotalResponses',f"{meta['responses']:,}");num('EvaluatedTokens',f"{meta['evaluated_tokens']:,}")
    # Main synthetic figure, all points directly from executed repetitions.
    fig,axs=plt.subplots(1,3,figsize=(7,2.15))
    for rho,color in zip([0,.5,.9],['#1565c0','#d66a00','#2e7d32']):
        ss=syn.query('n==128 and rho==@rho').sort_values('k')
        for ax,key in zip(axs,['optimism','naive_cover','naive_false_superiority']):
            ax.errorbar(ss.k,100*ss[key],yerr=196*ss[key+'_se'],marker='o',ms=3,color=color,label=rf'$\rho={rho}$')
    for ax in axs:ax.set_xscale('log',base=4);ax.set_xticks([1,4,16,64],['1','4','16','64']);ax.set_xlabel('Candidates K')
    axs[0].set_ylabel('Mean optimism (pp)');axs[1].set_ylabel(r'Naive 95\% coverage (\%)');axs[2].set_ylabel(r'False superiority (\%)')
    axs[1].axhline(95,color='grey',ls='--',lw=.7);axs[2].axhline(5,color='grey',ls='--',lw=.7)
    axs[0].legend(fontsize=7,frameon=False);save(fig,'synthetic')
    fig,axs=plt.subplots(2,1,figsize=(3.35,3.6))
    for k in [1,4,8,16,24]:
        rr=real.query('k==@k').sort_values('n')
        axs[0].errorbar(rr.n,100*rr.optimism,yerr=196*rr.optimism_se,marker='o',ms=3,label=f'K={k}')
    axs[0].set_ylabel('Mean optimism (pp)');axs[0].set_xlabel('Tuning questions n');axs[0].legend(fontsize=6,ncol=3,frameon=False)
    rr=real.query('k==24').sort_values('n')
    for key,label in [('naive_cover','Reuse, ordinary'),('simultaneous_cover','Reuse, simultaneous'),('audit_cover','Independent audit')]:
        axs[1].errorbar(rr.n,100*rr[key],yerr=196*rr[key+'_se'],marker='o',ms=3,label=label)
    axs[1].axhline(95,color='grey',ls='--',lw=.7);axs[1].set_ylabel(r'95\% interval coverage (\%)');axs[1].set_xlabel('Questions n');axs[1].legend(fontsize=6,frameon=False)
    save(fig,'real_replay')
    fig,axs=plt.subplots(1,2,figsize=(7,2.2))
    for key,label in [('reported_gain','Reported gain'),('actual_gain','Population gain')]:
        axs[0].errorbar(rr.n,100*rr[key],yerr=196*rr[key+'_se'],marker='o',label=label)
    axs[0].set_xlabel('Tuning questions n');axs[0].set_ylabel('Gain over fixed baseline (pp)');axs[0].legend(fontsize=8,frameon=False)
    # Equal call count comparison.
    axs[1].errorbar(rr.n,100*rr.selected_target,yerr=196*rr.selected_target_se,fmt='o-',capsize=2,label='Reuse: selected accuracy')
    axs[1].errorbar(call.reuse_n,100*call.selected_target,yerr=196*call.selected_target_se,fmt='s--',capsize=2,label='Lock: selected accuracy')
    axs[1].set_xlabel('Reuse-equivalent questions n');axs[1].set_ylabel(r'Selected population accuracy (\%)');axs[1].legend(fontsize=7,frameon=False)
    save(fig,'gains_budget')
    rows=[]
    for _,r in syn.query('n==128 and k==64').iterrows():
        rows.append([f"{r.rho:.1f}",meanse(r,'optimism'),meanse(r,'naive_cover'),meanse(r,'simultaneous_cover'),meanse(r,'audit_cover')])
    table('synthetic_table.tex',[r'$\rho$','Optimism','Naive cov.','Simult. cov.','Audit cov.'],rows)
    rows=[]
    for _,r in real.query('k==24').iterrows():
        rows.append([int(r.n),meanse(r,'optimism'),meanse(r,'naive_cover'),meanse(r,'simultaneous_cover'),meanse(r,'audit_cover')])
    table('real_table.tex',['n','Optimism','Naive cov.','Simult. cov.','Audit cov.'],rows)
    rows=[]
    for _,r in call.iterrows():
        full=real.query('k==24 and n==@r.reuse_n').iloc[0]
        quality=f"{100*r.quality_difference:+.2f}"+r' $\pm$ '+f"{100*r.quality_difference_se:.2f}"
        rows.append([int(r.total_calls),f"{int(r.tune_n)}/{int(r.audit_n)}",meanse(r,'audit_cover'),pp(full.simultaneous_width),pp(r.audit_width),quality])
    table('call_budget.tex',['Calls','Tune/audit','Audit cov.','Sim. width','Audit width',r'$\Delta$ quality'],rows)
    rows=[]
    for _,r in dup.iterrows():
        rows.append([int(r.k_penalty),meanse(r,'optimism'),meanse(r,'simultaneous_cover'),meanse(r,'simultaneous_width')])
    table('duplication.tex',['Charged K','Optimism','Coverage','Width'],rows)
    # Every configuration, including audit results; this table is descriptive only.
    cs=json.loads((ROOT/'data/candidates.json').read_text());rows=[]
    for c,dm,am in zip(cs,meta['development_means'],meta['audit_means']):
        rows.append([c['id'],c['id']//12,c['style'],c['rotation'],pp(dm),pp(am)])
    table('candidates.tex',['ID','Instruction','Style','Rotation',r'Dev. (\%)',r'Audit (\%)'],rows)
    # Full supplementary CSV-derived grids.
    for df,name,keys in [(syn,'full_synthetic.tex',['rho','n','k']), (real,'full_real.tex',['n','k'])]:
        rows=[]
        for _,r in df.iterrows():
            rows.append([f'{r[x]:g}' for x in keys]+[pp(r[x]) for x in ['optimism','naive_cover','simultaneous_cover','audit_cover','naive_false_superiority','adjusted_false_superiority']])
        table(name,keys+['Opt.','Naive','Simult.','Audit','False naive','False adj.'],rows)
    rows=[]
    for _,r in budget.iterrows():
        full=real.query('n==@r.total_n and k==24').iloc[0]
        quality=f"{100*r.quality_difference:+.2f}"+r' $\pm$ '+f"{100*r.quality_difference_se:.2f}"
        rows.append([int(r.total_n),int(r.tune_n),meanse(r,'audit_cover'),pp(r.audit_width),quality])
    table('question_budget.tex',['Total n','Tune n','Audit coverage','Audit width',r'$\Delta$ quality'],rows)
    rows=[]
    for _,r in hetero.iterrows():
        rows.append([pp(r.gap),meanse(r,'optimal_selection'),meanse(r,'optimism'),meanse(r,'oracle_regret'),meanse(r,'naive_cover'),meanse(r,'audit_cover')])
    table('heterogeneous.tex',['True gap',r'P(optimal) (\%)','Optimism','Oracle regret','Naive cov.','Audit cov.'],rows)
    rows=[]
    for _,r in paired_budget.iterrows():
        reuse=real.query('n==@r.reuse_n and k==24').iloc[0]
        rows.append([int(r.total_calls),int(r.tune_n),int(r.audit_n_per_configuration),
                     meanse(reuse,'naive_false_superiority'),meanse(r,'false_superiority'),meanse(r,'selected_target')])
    table('paired_call_budget.tex',['Calls','Tune n','Audit n each','Reuse false claims','Audit false claims','Selected accuracy'],rows)
    # Source all final compute statistics from measured JSONL records.
    records=[json.loads(x) for x in (ROOT/'data/responses.jsonl').open()]
    start=min(x['completed_utc'] for x in records);end=max(x['completed_utc'] for x in records)
    from datetime import datetime
    dt=lambda x:datetime.strptime(x,'%Y-%m-%dT%H:%M:%SZ')
    num('InferenceHours',f'{(dt(end)-dt(start)).total_seconds()/3600:.2f}')
    num('ComputedTokens',f"{sum(r['timings']['prompt_n'] for r in records):,}")
    num('MaxPrompt',max(r['tokens_evaluated'] for r in records))
    compute=json.loads((ROOT/'logs/compute.json').read_text())
    num('ServerCpuHours',f"{compute['main_server_cpu_seconds']/3600:.2f}")
    num('PeakMemoryGiB',f"{compute['main_server_peak_rss_kib']/(1024**2):.2f}")
    (OUT/'numbers.tex').write_text('\n'.join('\\newcommand{\\'+k+'}{'+v+'}' for k,v in numbers.items())+'\n')
    (OUT/'numbers.json').write_text(json.dumps(numbers,indent=2))

if __name__=='__main__':
    start=time.time();main()
    (ROOT/'logs/render_run.json').write_text(json.dumps(dict(elapsed_seconds=time.time()-start),indent=2))
