"""Regenerate all paper figures, tables, and numeric macros from executed results."""
import json,pathlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=pathlib.Path(__file__).resolve().parents[1];A=ROOT/'artifacts';F=A/'figures';T=A/'tables';F.mkdir(exist_ok=True);T.mkdir(exist_ok=True)
METHODS=['Naive-Wilson','Simult-Hoeffding','Multiplier','Guarded-multiplier','Audit-Wilson','Audit-exact']
SHORT=['Naive','Hoeffding','Multiplier','Guarded','Audit Wilson','Audit exact']
COLORS=['#d55e00','#555555','#0072b2','#cc79a7','#e69f00','#009e73']
plt.rcParams.update({'font.family':'serif','font.size':9,'axes.titlesize':10,'axes.labelsize':9,'legend.fontsize':8,'xtick.labelsize':8,'ytick.labelsize':8,'axes.spines.top':False,'axes.spines.right':False,'axes.titlepad':9,'savefig.dpi':300})

def save(fig,name):
    fig.savefig(F/(name+'.pdf'),bbox_inches='tight');fig.savefig(F/(name+'.png'),dpi=300,bbox_inches='tight');plt.close(fig)
def primary(d,real=False):
    return d[(d.kind=='n_grid')&(d.n==64)] if real else d[(d.kind=='core')&(d.n==64)&(d.rho==.5)&(d.gap==0)]
def pcf(v):return f'{100*v:.2f}'
def make():
    syn=pd.read_csv(A/'synthetic_summary.csv');real=pd.read_csv(A/'real_summary.csv');sp=primary(syn);rp=primary(real,True)
    fig,ax=plt.subplots(1,2,figsize=(6.65,2.5),layout='constrained')
    for rho,c in zip([0,.5,.9],['#d55e00','#0072b2','#009e73']):
      q=syn[(syn.kind=='core')&(syn.rho==rho)&(syn.gap==0)&(syn.method=='Naive-Wilson')].sort_values('n')
      ax[0].errorbar(q.n,100*q.optimism,yerr=196*q.optimism_mcse,marker='o',capsize=2,color=c,label=f'latent rho={rho}')
    q=real[(real.kind=='n_grid')&(real.method=='Naive-Wilson')].sort_values('n')
    ax[1].errorbar(q.n,100*q.optimism,yerr=196*q.optimism_mcse,marker='o',capsize=2,label='Full cohort',color='#0072b2')
    ax[1].errorbar(q.n,100*q.remainder_optimism,yerr=196*q.optimism_mcse*600/(600-q.n),marker='s',capsize=2,label='Unselected remainder',color='#d55e00')
    for a,title in zip(ax,['(a) Known iid population, equal quality','(b) Real LLM cache, fixed finite cohort']):
      a.set_title(title);a.set_xlabel('Selection questions n');a.set_ylabel('Mean optimism (pp)');a.set_xticks([16,32,64,128]);a.grid(axis='y',alpha=.2);a.legend(frameon=False)
    save(fig,'optimism')
    fig,ax=plt.subplots(1,2,figsize=(6.65,2.6),layout='constrained',sharex=True,sharey=True)
    for a,d,title in zip(ax,[sp,rp],['(a) iid population','(b) Real finite cohort']):
      for i,(method,short,color) in enumerate(zip(METHODS,SHORT,COLORS)):
       r=d[d.method==method].iloc[0];a.errorbar(100*r.mean_width,100*r.coverage,yerr=196*r.coverage_mcse,color=color,marker='s' if i in [1,5] else 'o',capsize=2,label=short,linestyle='none')
      a.axhline(95,color='black',linestyle='--',linewidth=.7);a.set_title(title);a.set_xlabel('Mean interval width (pp)');a.set_ylabel('Coverage (%)');a.set_ylim(75,101.8);a.grid(alpha=.15)
    ax[1].legend(frameon=False,loc='lower right',ncol=2,columnspacing=.7,handletextpad=.4)
    save(fig,'coverage_width')
    fig,ax=plt.subplots(1,3,figsize=(6.65,2.35),layout='constrained')
    for i,(method,short,color) in enumerate(zip(METHODS,SHORT,COLORS)):
      q=syn[(syn.kind=='boundary')&(syn.p0==.95)&(syn.method==method)].sort_values('rho')
      ax[0].errorbar(q.rho+(i-2.5)*.012,100*q.coverage,yerr=196*q.coverage_mcse,marker='o',markersize=3,linestyle='-',linewidth=.6,color=color,label=short,capsize=1)
    ax[0].set_title('(a) Boundary stress: n=16');ax[0].set_xlabel('Latent correlation');ax[0].set_ylabel('Coverage (%)');ax[0].axhline(95,color='black',ls='--',lw=.7);ax[0].set_xticks([0,.9]);ax[0].set_ylim(75,102)
    q=real[((real.kind=='audit_size')|((real.kind=='n_grid')&(real.n==64)))&(real.method=='Audit-exact')].sort_values('m')
    ax[1].errorbar(q.m,100*q.mean_width,yerr=196*q.width_mcse,marker='s',color=COLORS[-1],capsize=2);ax[1].set_ylabel('Mean interval width (pp)');ax[1].set_title('(b) Real exact-audit width')
    ax[2].errorbar(q.m,100*q.coverage,yerr=196*q.coverage_mcse,marker='s',color=COLORS[-1],capsize=2);ax[2].axhline(95,color='black',ls='--',lw=.7);ax[2].set_ylabel('Coverage (%)');ax[2].set_ylim(90,101);ax[2].set_title('(c) Real exact-audit coverage')
    for a in ax[1:]:a.set_xlabel('Audit questions m');a.set_xticks([32,64,128])
    for a in ax:a.grid(axis='y',alpha=.2)
    handles,labels=ax[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='outside lower center',ncol=6,fontsize=7,frameon=False)
    save(fig,'failure_precision')
    C=pd.read_csv(A/'prompt_correlation.csv').to_numpy();fig,a=plt.subplots(figsize=(3.6,3.0),layout='constrained');im=a.imshow(C,vmin=-1,vmax=1,cmap='coolwarm');a.set_xticks(range(8),['P'+str(i) for i in range(8)]);a.set_yticks(range(8),['P'+str(i) for i in range(8)]);fig.colorbar(im,ax=a,label='Binary correctness correlation');save(fig,'correlation')
    # Primary result table includes uncertainties, preventing false precision.
    lines=['\\begin{tabular}{lrrrr}','\\toprule','& \\multicolumn{2}{c}{Iid population} & \\multicolumn{2}{c}{Real finite cohort} \\\\','Method & Coverage & Width & Coverage & Width \\\\','\\midrule']
    for method,short in zip(METHODS,SHORT):
      x=sp[sp.method==method].iloc[0];y=rp[rp.method==method].iloc[0]
      lines.append(f"{short} & {pcf(x.coverage)} $\\pm$ {pcf(x.coverage_mcse)} & {pcf(x.mean_width)} & {pcf(y.coverage)} $\\pm$ {pcf(y.coverage_mcse)} & {pcf(y.mean_width)} \\\\")
    lines+=['\\bottomrule','\\end{tabular}'];(T/'primary.tex').write_text('\n'.join(lines))
    # Complete core compact table, all rho/gap/n cells, not outcome-selected.
    lines=['\\begin{longtable}{rrrrrrrr}','\\caption{Complete core synthetic grid; optimism in pp, coverage and false promotion in percent.}\\label{tab:core}\\\\','\\toprule','$n$ & $\\rho$ & $\\delta$ & Optimism & Naive & Mult. & Exact & False prom. \\\\','\\midrule\\endhead']
    q=syn[(syn.kind=='core')&(syn.method=='Naive-Wilson')].sort_values(['n','rho','gap'])
    for _,r in q.iterrows():
      c=syn[syn.cell==r.cell].set_index('method');lines.append(f"{int(r.n)} & {r.rho:g} & {r.gap:g} & {pcf(r.optimism)} & {pcf(r.coverage)} & {pcf(c.loc['Multiplier','coverage'])} & {pcf(c.loc['Audit-exact','coverage'])} & {pcf(r.naive_false_promotion)} \\\\")
    lines+=['\\bottomrule','\\end{longtable}'];(T/'core_grid.tex').write_text('\n'.join(lines))
    # Real prompt summary and precommitted ablations.
    prompts=pd.read_csv(A/'prompt_summary.csv');lines=['\\begin{tabular}{rrrrr}','\\toprule','Prompt & Correct / 600 & Accuracy (\\%) & Parse failures & Mean reported comp. tokens \\\\','\\midrule']
    for _,r in prompts.iterrows():lines.append(f"P{int(r.prompt_id)} & {int(r.correct)} & {pcf(r.accuracy)} & {int(r.format_failures)} & {r.mean_completion_tokens:.1f} \\\\")
    lines+=['\\bottomrule','\\end{tabular}'];(T/'prompts.tex').write_text('\n'.join(lines))
    lines=['\\begin{tabular}{lrrrr}','\\toprule','Setting & Optimism (pp) & Naive cov. & Mult. cov. & Exact width \\\\','\\midrule']
    for kind,k,n,m,label in [('K_grid',1,64,128,'K=1'),('K_grid',2,64,128,'K=2'),('K_grid',4,64,128,'K=4'),('n_grid',8,64,128,'K=8 (primary)'),('audit_size',8,64,32,'m=32'),('audit_size',8,64,64,'m=64'),('independent_multiplier',8,64,128,'Independent multipliers'),('no_FPC_multiplier',8,64,128,'Multiplier without FPC')]:
      sub=real[(real.kind==kind)&(real.K==k)&(real.n==n)&(real.m==m)].set_index('method');r=sub.loc['Naive-Wilson'];lines.append(f"{label} & {pcf(r.optimism)} & {pcf(r.coverage)} & {pcf(sub.loc['Multiplier','coverage'])} & {pcf(sub.loc['Audit-exact','mean_width'])} \\\\")
    lines+=['\\bottomrule','\\end{tabular}'];(T/'ablations.tex').write_text('\n'.join(lines))
    # Machine generated macros: every displayed empirical number has one source.
    sx=sp.set_index('method');rx=rp.set_index('method');s=sx.loc['Naive-Wilson'];r=rx.loc['Naive-Wilson'];card=json.loads((A/'report_card.json').read_text());usage=json.loads((A/'inference_usage.json').read_text());rt=json.loads((A/'real_runtime.json').read_text())
    vals={'OptSyn':pcf(s.optimism),'OptSynSE':pcf(s.optimism_mcse),'OptReal':pcf(r.optimism),'OptRealSE':pcf(r.optimism_mcse),'SynNaiveCov':pcf(s.coverage),'SynAuditCov':pcf(sx.loc['Audit-exact','coverage']),'RealNaiveCov':pcf(r.coverage),'RealAuditCov':pcf(rx.loc['Audit-exact','coverage']),'SynFalseNaive':pcf(s.naive_false_promotion),'SynFalseAudit':pcf(s.honest_false_promotion),'RealFalseNaive':pcf(r.naive_false_promotion),'RealFalseAudit':pcf(r.honest_false_promotion),'MeanCorr':f"{rt['mean_offdiag_binary_correlation']:.3f}",'RawMinAcc':pcf(prompts.accuracy.min()),'RawMaxAcc':pcf(prompts.accuracy.max()),'FormatFailures':str(int(prompts.format_failures.sum())),'PromptTokens':f"{usage['prompt_tokens']:,}",'CompletionTokens':f"{usage['completion_tokens']:,}",'InferenceMinutes':f"{usage['wall_s_this_invocation']/60:.1f}",'Winner':str(card['winner']),'CardSelection':pcf(card['selection_score']),'CardAudit':pcf(card['audit_score']),'CardTruth':pcf(card['finite_pool_truth']),'CardLower':pcf(card['pool_accuracy_interval_joint95'][0]),'CardUpper':pcf(card['pool_accuracy_interval_joint95'][1]),'CardDeltaLower':pcf(card['pool_baseline_difference_interval_joint95'][0]),'CardDeltaUpper':pcf(card['pool_baseline_difference_interval_joint95'][1]),'CardDelta':pcf(card['pool_difference']),'CardPlus':str(card['audit_discordant_plus']),'CardMinus':str(card['audit_discordant_minus'])}
    (T/'numbers.tex').write_text('\n'.join('\\newcommand{\\'+k+'}{'+v+'}' for k,v in vals.items())+'\n')
    (A/'paper_numbers.json').write_text(json.dumps(vals,indent=2));pd.concat([sp,rp]).to_csv(F/'primary_plotted.csv',index=False)
    (A/'figure-audit.md').write_text('# Figure audit\n\n- Executed plot script: yes.\n- All numerical panels load executed CSV summaries, same parameter filters as tables.\n- Scales: linear; optimism/width percentage points, coverage percent.\n- Error bars: conditional Monte Carlo uncertainty only.\n- Full synthetic grids are supplementary CSV, not silently omitted from claims.\n- Exact and approximate methods distinguished by labels/markers.\n- Boundary/real-coverage ranges include all displayed means and error bars.\n- PNG and PDF files emitted at 300 dpi / vector.\n- Status: PASSED_WITH_WARNINGS until final visual PDF inspection.\n')
if __name__=='__main__':make()
