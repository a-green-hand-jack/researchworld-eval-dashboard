#!/usr/bin/env python3
"""Render measured real-model main summaries; no model or statistical experiment runs."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import tempfile
import numpy as np
import pandas as pd
from scipy.stats import beta
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT=Path(__file__).resolve().parents[1]
INPUT=ROOT/'presentation/inputs/real'
PROV=json.loads((ROOT/'presentation/real-provenance.json').read_text())
for name,record in PROV['inputs'].items():
    assert hashlib.sha256((INPUT/name).read_bytes()).hexdigest()==record['sha256'],name

def js(name): return json.loads((INPUT/name).read_text())
def csv(name): return pd.read_csv(INPUT/name)
P=js('primary-result.json'); G=js('primary-gap-decomposition.json')
C=csv('cache-calibration.csv'); D=csv('conditional-selection.csv')
F=csv('selection-frequencies.csv'); A=csv('candidate-audit.csv').set_index('candidate_id')
B=csv('cache-protocol-budgets.csv'); BOOT=csv('bootstrap-main.summary.csv')
NS=[16,32,64,128,256]; KS=[1,2,4]; IDS=[0,10,14,13]
METHODS={
 'naive':('Reused CP','#D55E00','o','-'),
 'simultaneous':('Simultaneous CP','#0072B2','s','--'),
 'independent_audit':('Extra audit','#009E73','^','-.'),
 'split_question_budget':('Question split','#CC79A7','D',':'),
 'split_call_budget':('Call split','#6B5B00','v',(0,(5,1))),
}
KSTYLE={1:('#777777','o','-'),2:('#9970AB','s','--'),4:('#762A83','^','-')}
IDCOL={0:'#777777',10:'#0072B2',14:'#009E73',13:'#CC79A7'}
plt.rcParams.update({'font.size':9,'axes.titlesize':9,'axes.labelsize':9,
 'xtick.labelsize':8,'ytick.labelsize':8,'legend.fontsize':8,
 'font.family':'DejaVu Sans','pdf.fonttype':42,'ps.fonttype':42,
 'axes.spines.top':False,'axes.spines.right':False,'axes.axisbelow':True,
 'savefig.dpi':180,'lines.linewidth':1.25,'lines.markersize':3.5})

# Validate the presentation's selected main grids/identity contracts, not the analysis anew.
assert js('validation.json')['status']=='PASS'
assert P['candidate_id']==10 and P['n_search']==256 and P['k']==4
assert P['design_count']==2 and P['per_design_alpha']==.025
assert js('disjoint-summary.json')['unseen_benchmark_population_questions']==11776
assert not C.duplicated(['n','k','metric']).any() and len(C)==375
assert not D.duplicated(['n','k','metric']).any() and len(D)==270
assert set(C.n)==set(NS) and set(C.k)==set(KS) and set(C.reps)=={20000}
assert set(C.population_questions)=={768} and set(F.candidate_id)==set(IDS)
assert set(A.audit_population_questions)=={11776} and set(A.audit_questions)=={512}
assert BOOT.bootstraps.eq(1000).all() and BOOT.inner_reps.eq(2000).all()

def select(frame,metric,**kw):
    q=frame[frame.metric.eq(metric)]
    for k,v in kw.items():q=q[q[k].eq(v)]
    return q.sort_values('n')

def mc(q,event=False):
    mu=q['mean'].to_numpy();se=q.mcse.to_numpy()
    if not event:return mu-1.96*se,mu+1.96*se
    r=q.reps.to_numpy();count=np.rint(mu*r).astype(int)
    assert np.max(np.abs(count-mu*r))<1e-6
    lo=np.zeros(len(q));hi=np.ones(len(q));a=count>0
    lo[a]=beta.ppf(.025,count[a],r[a]-count[a]+1)
    a=count<r;hi[a]=beta.ppf(.975,count[a]+1,r[a]-count[a])
    return lo,hi

def line(ax,q,label,col,mark,ls,event=False,scale=100):
    lo,hi=mc(q,event);ax.plot(q.n,scale*q['mean'],label=label,color=col,marker=mark,ls=ls)
    ax.fill_between(q.n,scale*lo,scale*hi,color=col,alpha=.15,lw=0)

def xaxis(ax,draws=False):
    ax.set_xscale('log',base=2);ax.set_xticks(NS,labels=[str(n) for n in NS]);ax.set_xlim(14,290)
    ax.set_xlabel('Search question draws n' if draws else 'Search questions n');ax.grid(axis='y',color='#e4e4e4',lw=.5)

def save(fig,name):
    for ext in ['pdf','png']:fig.savefig(ROOT/f'figures/{name}.{ext}',facecolor='white')
    plt.close(fig)

def bars(ax,mean,lo,hi,y,color,marker='o',label=None):
    ax.errorbar(100*mean,y,xerr=[[100*(mean-lo)],[100*(hi-mean)]],fmt=marker,
                color=color,ms=4,capsize=2,lw=1.2,label=label)

def primary():
    fig,axs=plt.subplots(2,1,figsize=(5.5,3.65),height_ratios=[.85,1.15])
    fig.subplots_adjust(left=.32,right=.97,bottom=.14,top=.85,hspace=.95)
    ax=axs[0]
    for y,cid in [(1,0),(0,10)]:
        r=A.loc[cid]
        ax.plot(100*r.search_accuracy,y+.11,'s',color='#D55E00',ms=4,label='Search reuse' if y==1 else None)
        bars(ax,r.audit_accuracy,r.audit_ci_lower,r.audit_ci_upper,y-.11,'#009E73',label='Disjoint audit' if y==1 else None)
    ax.set_yticks([1,0],labels=['Default 0','Winner 10']);ax.set_ylim(-.45,1.45);ax.set_xlim(8,44)
    ax.set_xticks([10,20,30,40]);ax.set_xlabel('Accuracy (%)');ax.grid(axis='x',color='#e4e4e4',lw=.5)
    ax.set_title('(a) Search and audit scores',loc='left',pad=10)
    fig.legend(*ax.get_legend_handles_labels(),loc='upper center',bbox_to_anchor=(.64,.995),ncol=2,frameon=False)
    ax=axs[1]
    quantities=[('Winner gap',P['reused_minus_audit'],*P['exact_gap_interval'],'#762A83'),
     ('Default gap',G['default_search_minus_audit'],A.loc[0].search_accuracy-A.loc[0].audit_ci_upper,A.loc[0].search_accuracy-A.loc[0].audit_ci_lower,'#777777'),
     ('Excess gap',G['excess_gap_beyond_default'],*G['excess_gap_interval_from_paired_audit'],'#D55E00'),
     ('Paired audit gain',P['paired_audit_contrast_to_default'],*P['exact_paired_contrast_interval'],'#0072B2')]
    for y,(_,mu,lo,hi,col) in enumerate(quantities):bars(ax,mu,lo,hi,3-y,col)
    ax.set_yticks([3,2,1,0],labels=[q[0] for q in quantities]);ax.set_ylim(-.5,3.5)
    ax.axvline(0,color='.4',ls='--',lw=.8);ax.set_xlim(-5,20);ax.set_xticks([-5,0,5,10,15,20]);ax.grid(axis='x',color='#e4e4e4',lw=.5)
    ax.set_xlabel('Difference (percentage points)');ax.set_title('(b) Gaps and paired comparison',loc='left',pad=10)
    save(fig,'real-primary')

def handles(keys):
    return [Line2D([],[],label=METHODS[k][0],color=METHODS[k][1],marker=METHODS[k][2],ls=METHODS[k][3]) for k in keys]

def calibration():
    fig,axs=plt.subplots(2,2,figsize=(5.5,4.9))
    fig.subplots_adjust(left=.13,right=.98,bottom=.11,top=.80,wspace=.36,hspace=.67)
    ax=axs[0,0]
    for k in KS:
        col,mark,ls=KSTYLE[k];line(ax,select(C,'optimism_reused',k=k),f'K = {k}',col,mark,ls)
    ax.axhline(0,color='.4',lw=.8);ax.set_ylabel('Reuse optimism (pp)');ax.set_title('(a) Point optimism');ax.legend(frameon=False,loc='upper right',fontsize=8)
    ax=axs[0,1]
    for key in ['naive','simultaneous','independent_audit']:
        label,col,mark,ls=METHODS[key];line(ax,select(C,'coverage_'+key,k=4),label,col,mark,ls,event=True)
    ax.axhline(95,color='.35',ls='--',lw=.8);ax.set_ylim(93,100.5);ax.set_yticks([94,95,97,99]);ax.set_ylabel('Coverage (%)');ax.set_title('(b) K = 4; nominal 95%')
    ax=axs[1,0]
    for key in METHODS:
        label,col,mark,ls=METHODS[key];line(ax,select(C,'width_'+key,k=4),label,col,mark,ls)
    ax.set_ylabel('Interval width (pp)');ax.set_title('(c) K = 4; reporting width');ax.set_ylim(0,65)
    ax=axs[1,1]
    for key,metric in [('naive','selected_quality'),('split_question_budget','quality_split_question_budget'),('split_call_budget','quality_split_call_budget')]:
        label,col,mark,ls=METHODS[key]
        if key=='naive':label='Full search';col='#333333'
        line(ax,select(C,metric,k=4),label,col,mark,ls)
    ax.set_ylabel('Selected cache quality (%)');ax.set_title('(d) K = 4; selection quality');ax.set_ylim(24,30)
    ax.text(.98,.04,'Black: full search',transform=ax.transAxes,ha='right',fontsize=8,color='#333333')
    for ax in axs.flat:xaxis(ax,draws=True)
    fig.legend(handles=handles(list(METHODS)),loc='upper center',bbox_to_anchor=(.5,1.),ncol=3,frameon=False)
    save(fig,'real-cache')

def calibration_main():
    """Compact main-text evidence: bias and calibration are distinct outcomes."""
    fig,axs=plt.subplots(1,2,figsize=(5.5,2.65))
    fig.subplots_adjust(left=.12,right=.98,bottom=.22,top=.75,wspace=.36)
    ax=axs[0]
    for k in KS:
        col,mark,ls=KSTYLE[k]
        line(ax,select(C,'optimism_reused',k=k),f'K = {k}',col,mark,ls)
    ax.axhline(0,color='.4',lw=.8)
    ax.set_ylabel('Reuse optimism (pp)');ax.set_title('(a) Positive point bias')
    ax.legend(frameon=False,loc='upper right',handlelength=1.7,labelspacing=.25)
    ax=axs[1]
    keys=['naive','simultaneous','independent_audit']
    for key in keys:
        label,col,mark,ls=METHODS[key]
        line(ax,select(C,'coverage_'+key,k=4),label,col,mark,ls,event=True)
    ax.axhline(95,color='.35',ls='--',lw=.8)
    ax.set_ylim(93,100.5);ax.set_yticks([94,95,97,99])
    ax.set_ylabel('Coverage (%)');ax.set_title('(b) K = 4; nominal 95%')
    for ax in axs:xaxis(ax,draws=True)
    fig.legend(handles=handles(keys),loc='upper center',bbox_to_anchor=(.5,1.),ncol=3,frameon=False)
    save(fig,'real-cache-main')

def conditional():
    fig,axs=plt.subplots(2,3,figsize=(5.5,4.6),sharex=True)
    fig.subplots_adjust(left=.12,right=.98,bottom=.13,top=.87,wspace=.30,hspace=.62)
    for j,k in enumerate(KS):
        ax=axs[0,j];q=select(D,'reused_minus_audit',k=k);col,mark,ls=KSTYLE[k]
        ax.fill_between(q.n,100*q.audit_simultaneous_gap_lower,100*q.audit_simultaneous_gap_upper,color='#0072B2',alpha=.15,lw=0)
        line(ax,q,'Mean gap',col,mark,ls);ax.axhline(0,color='.4',lw=.8);ax.set_ylim(0,26);ax.set_yticks([0,10,20]);ax.set_title(f'({chr(97+j)}) K = {k}')
        if j==0:ax.set_ylabel('Search minus audit (pp)')
        ax=axs[1,j]
        q=F[F.k.eq(k)].pivot(index='n',columns='candidate_id',values='full_selection_frequency').reindex(index=NS,columns=IDS)
        assert np.allclose(q.sum(axis=1),1)
        ax.stackplot(NS,*[100*q[c] for c in IDS],colors=[IDCOL[c] for c in IDS],alpha=.85)
        ax.set_ylim(0,100);ax.set_yticks([0,50,100]);ax.set_title(f'({chr(100+j)}) Selected identity')
        if j==0:ax.set_ylabel('Selection frequency (%)')
    for ax in axs.flat:xaxis(ax)
    for ax in axs[0]:ax.set_xlabel('')
    hs=[Line2D([],[],color='#762A83',marker='o',label='Mean ± MC uncertainty'),Line2D([],[],color='#0072B2',lw=6,alpha=.25,label='Protected audit uncertainty')]
    fig.legend(handles=hs,loc='upper center',bbox_to_anchor=(.5,1.),ncol=2,frameon=False)
    fig.legend(handles=[Line2D([],[],color=IDCOL[c],lw=5,label=f'ID {c}') for c in IDS],loc='lower center',bbox_to_anchor=(.5,-.005),ncol=4,frameon=False)
    save(fig,'real-conditional')

def coverage_grid():
    keys=list(METHODS);fig,axs=plt.subplots(3,1,figsize=(5.5,5.0))
    fig.subplots_adjust(left=.25,right=.85,bottom=.11,top=.94,hspace=.50)
    for j,(ax,k) in enumerate(zip(axs,KS)):
        arr=np.array([select(C,'coverage_'+key,k=k)['mean'].to_numpy()*100 for key in keys])
        im=ax.imshow(arr,aspect='auto',cmap='viridis',vmin=90,vmax=100)
        for y in range(5):
            for x in range(5):ax.text(x,y,f'{arr[y,x]:.1f}',ha='center',va='center',fontsize=8,color='black' if arr[y,x]>96 else 'white')
        ax.set_title(f'K = {k}');ax.set_xticks(range(5),labels=[str(n) for n in NS] if j==2 else ['']*5)
        if j==2:ax.set_xlabel('Search question draws n')
        ax.set_yticks(range(5),labels=[METHODS[key][0] for key in keys])
    ca=fig.add_axes([.90,.16,.02,.70]);fig.colorbar(im,cax=ca,ticks=[90,95,100]).ax.set_title('Coverage\n(%)',fontsize=8,pad=8)
    save(fig,'real-cache-coverage-grid')

def mse():
    fig,axs=plt.subplots(1,3,figsize=(5.5,2.8),sharey=True)
    fig.subplots_adjust(left=.13,right=.98,bottom=.25,top=.69,wspace=.26)
    for ax,k in zip(axs,KS):
        for key,metric in [('naive','mse_reused'),('independent_audit','mse_independent_audit'),('split_question_budget','mse_split_question_budget'),('split_call_budget','mse_split_call_budget')]:
            label,col,mark,ls=METHODS[key];line(ax,select(C,metric,k=k),label,col,mark,ls,scale=10000)
        ax.set_yscale('log');ax.set_yticks([10,100],labels=['10','100']);ax.set_title(f'K = {k}');xaxis(ax,draws=True)
    axs[0].set_ylabel('Score MSE (pp²)')
    fig.legend(handles=handles(['naive','independent_audit','split_question_budget','split_call_budget']),loc='upper center',bbox_to_anchor=(.5,1.),ncol=2,frameon=False)
    save(fig,'real-cache-mse')


def diagnostics():
    fig,axs=plt.subplots(1,2,figsize=(5.5,2.9));fig.subplots_adjust(left=.12,right=.85,bottom=.22,top=.83,wspace=.52)
    fmt=csv('format-diagnostics.csv').groupby('candidate_id').sum(numeric_only=True).loc[IDS]
    ax=axs[0];rates=100*fmt.invalid_format/fmt.responses
    ax.bar(range(4),rates,color=[IDCOL[c] for c in IDS],width=.6)
    for j,cid in enumerate(IDS):ax.text(j,rates.iloc[j]+1,f'{int(fmt.loc[cid,"invalid_format"])}',ha='center',fontsize=8)
    ax.set_xticks(range(4),labels=[str(c) for c in IDS]);ax.set_xlabel('Candidate ID');ax.set_ylabel('Malformed responses (%)');ax.set_ylim(0,37);ax.set_title('(a) Counts above bars')
    ax=axs[1];q=csv('candidate-correlation.csv').set_index('candidate_id').loc[IDS,[str(c) for c in IDS]]
    im=ax.imshow(q,cmap='Blues',vmin=0,vmax=1)
    for y in range(4):
        for x in range(4):ax.text(x,y,f'{q.iloc[y,x]:.2f}',ha='center',va='center',fontsize=8,color='white' if q.iloc[y,x]>.75 else 'black')
    ax.set_xticks(range(4),labels=[str(c) for c in IDS]);ax.set_yticks(range(4),labels=[str(c) for c in IDS]);ax.set_xlabel('Candidate ID');ax.set_ylabel('Candidate ID');ax.set_title('(b) Correctness correlation')
    ca=fig.add_axes([.90,.24,.02,.53]);fig.colorbar(im,cax=ca,ticks=[0,.5,1])
    save(fig,'real-diagnostics')

def latex_table(name,header,rows,align):
    text='\\begin{tabular}{'+align+'}\n\\toprule\n'+header+' \\\\\n\\midrule\n'
    text+='\n'.join(' & '.join(row)+' \\\\' for row in rows)+'\n\\bottomrule\n\\end{tabular}\n'
    (ROOT/f'tables/{name}.tex').write_text(text)

def previews(names):
    for name,height in names:
        tex=('\\documentclass{article}\n\\usepackage[paperwidth=6.5in,paperheight='+str(height)+'in,margin=.5in]{geometry}\n'
        '\\usepackage{booktabs}\n\\pagestyle{empty}\n\\begin{document}\n\\centering\\fontsize{8}{10}\\selectfont\n\\input{tables/'+name+'.tex}\n\\end{document}\n')
        (ROOT/f'presentation/{name}-preview.tex').write_text(tex)
        with tempfile.TemporaryDirectory(prefix='real-table-') as td:
            run=subprocess.run(['pdflatex','-interaction=nonstopmode','-halt-on-error','-output-directory',td,str(ROOT/f'presentation/{name}-preview.tex')],cwd=ROOT,capture_output=True,text=True)
            if run.returncode:raise RuntimeError(run.stdout[-3000:])
            assert 'Overfull' not in run.stdout,run.stdout[-3000:]
            pdf=ROOT/f'tables/{name}-preview.pdf';shutil.copyfile(Path(td)/(name+'-preview.pdf'),pdf)
            subprocess.run(['pdftoppm','-singlefile','-png','-scale-to','1600',str(pdf),str(ROOT/f'tables/{name}-preview')],check=True,capture_output=True)

def tables():
    rows=[];data=[]
    specifications=[('Reused CP',P['reused_score'],P['naive_binomial_interval'],P['naive_reused_nonoverlap_claim'],1024,'accuracy_percent'),
      ('Exact search',P['reused_score'],P['exact_simultaneous_remaining_interval'],P['exact_simultaneous_search_nonoverlap_claim'],1024,'accuracy_percent'),
      ('Disjoint audit',P['audit_accuracy'],P['exact_audit_interval'],P['independent_audit_nonoverlap_claim'],2048,'accuracy_percent'),
      ('Paired audit gain (pp)',P['paired_audit_contrast_to_default'],P['exact_paired_contrast_interval'],P['paired_audit_positive_claim'],2048,'contrast_pp')]
    for label,mu,ci,claim,calls,target in specifications:
        rows.append([label,f'{100*mu:.2f}',f'[{100*ci[0]:.2f}, {100*ci[1]:.2f}]','Yes' if claim else 'No','---' if target=='contrast_pp' else ('1,536' if label=='Disjoint audit' else '1,024'),f'{calls:,}'])
        data.append({'report':label,'mean':mu,'interval_lower':ci[0],'interval_upper':ci[1],'target_unit':target,'positive_comparison':claim,'logical_calls_for_comparison':calls,'logical_calls_selected_accuracy':1536 if label=='Disjoint audit' else (None if target=='contrast_pp' else 1024),'logical_calls_paired_comparison':calls})
    latex_table('real-reporting','Report & Estimate & Interval & Improvement & Calls (s) & Calls (p)',rows,'lrrrrr')
    pd.DataFrame(data).to_csv(ROOT/'tables/real-reporting.csv',index=False)
    methods=[('naive','naive_reuse','optimism_reused','selected_quality'),('simultaneous','simultaneous_reuse','optimism_reused','selected_quality'),('independent_audit','independent_audit','bias_independent_audit','selected_quality'),('split_question_budget','split_question_budget','bias_split_question_budget','quality_split_question_budget'),('split_call_budget','split_call_budget','bias_split_call_budget','quality_split_call_budget')]
    rows=[];data=[]
    for key,budgetkey,bias,quality in methods:
        def metric(m):return select(C,m,n=256,k=4).iloc[0]
        b=metric(bias);cov=metric('coverage_'+key);w=metric('width_'+key);q=metric(quality)
        budget=B[B.n.eq(256)&B.k.eq(4)&B.method.eq(budgetkey)].iloc[0]
        rows.append([METHODS[key][0],f'{100*b["mean"]:.2f} ({100*b.mcse:.3f})',f'{100*cov["mean"]:.2f} ({100*cov.mcse:.3f})',f'{100*w["mean"]:.2f}',f'{100*q["mean"]:.2f}',f'{int(budget.logical_total_model_calls):,}'])
        data.append({'method':key,'n':256,'k':4,'bias':b['mean'],'bias_mcse':b.mcse,'coverage':cov['mean'],'coverage_mcse':cov.mcse,'width':w['mean'],'width_mcse':w.mcse,'quality':q['mean'],'quality_mcse':q.mcse,**budget.to_dict()})
    latex_table('real-cache-methods','Report & Bias (pp) & Coverage (\\%) & Width (pp) & Quality (\\%) & Calls',rows,'lrrrrr')
    pd.DataFrame(data).to_csv(ROOT/'tables/real-cache-methods.csv',index=False)
    rows=[];data=[]
    for n in [64,256]:
        for metric,label in [('reused_minus_audit','Search minus audit'),('audit_contrast_to_default','Paired audit gain')]:
            row=BOOT[BOOT.n.eq(n)&BOOT.metric.eq(metric)].iloc[0]
            obs=select(D,'reused_minus_audit' if metric=='reused_minus_audit' else 'full_audit_contrast_to_default',n=n,k=4).iloc[0]['mean']
            rows.append([str(n),label,f'{100*obs:.2f}',f'[{100*row.percentile_lower:.2f}, {100*row.percentile_upper:.2f}]'])
            data.append({**row.to_dict(),'original_conditional_mean':obs})
    latex_table('real-bootstrap','Search n & Quantity (pp) & Original mean & Bootstrap 95\\% range',rows,'rlrr')
    pd.DataFrame(data).to_csv(ROOT/'tables/real-bootstrap.csv',index=False)
    rows=[];data=[]
    for n in NS:
        reuse=[];sim=[]
        for k in KS:
            for metric,out in [('false_superiority_naive',reuse),('false_superiority_simultaneous',sim)]:
                q=select(C,metric,n=n,k=k);r=q.iloc[0];count=int(round(r['mean']*r.reps));out.append(str(count))
                lo,hi=mc(q,event=True)
                data.append({'n':n,'k':k,'metric':metric,'events':count,'reps':int(r.reps),'rate':r['mean'],'mcse':r.mcse,'mc_lower':lo[0],'mc_upper':hi[0]})
        rows.append([str(n),*reuse,', '.join(sim)])
    latex_table('real-cache-decisions','Search n & Reuse K=1 & Reuse K=2 & Reuse K=4 & Sim K=1,2,4',rows,'rrrrr')
    pd.DataFrame(data).to_csv(ROOT/'tables/real-cache-decisions.csv',index=False)
    previews([('real-reporting',2.2),('real-cache-methods',2.4),('real-bootstrap',2.2),('real-cache-decisions',2.4)])

if __name__=='__main__':
    for f in [primary,calibration_main,calibration,conditional,coverage_grid,mse,diagnostics,tables]:f()
    print('Rendered seven measured-real figures, four numerical tables and actual-source table previews.')
