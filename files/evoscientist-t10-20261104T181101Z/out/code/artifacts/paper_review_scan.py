"""Read-only paper audit: no sampling, experiment imports, or manuscript writes.
Reproduce: python /work/artifacts/paper_review_scan.py
Output: /work/paper_review_mechanical.json
"""
from pathlib import Path
import hashlib, json, re, sys
import numpy as np
import pandas as pd
from scipy.stats import beta, binom, norm, t
from pypdf import PdfReader
R = Path('/work')
OUT = R/'paper_review_mechanical.json'
inputs = sorted(set([R/x for x in ['paper.tex','paper.pdf','references.bib','checklist_filled.tex','source_verification.md','summary.csv','paired.csv','seed_summary.csv','mass_ablation_summary.csv','mass_ablation_raw.csv.gz','analysis_audit.md','multiplicity_manifest.json','intervals.py','run_experiments.py','summarize.py','mass_ablation.py','supplement_baselines.py','test_intervals.py','integrity_audit.json','data_eda.json','template/neurips_2026.tex','results/design.json','results/run_metadata.json','results_supplement/metadata.json']] + list((R/'generated').glob('*')) + list((R/'results').glob('*.csv.gz')) + list((R/'results_supplement').glob('*.csv.gz'))))
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
hashes = {str(p.relative_to(R)):digest(p) for p in inputs}
report = {'reproduction_command':'python /work/artifacts/paper_review_scan.py','script_sha256':digest(Path(__file__)), 'scope':'Existing artifacts only; no new samples, no experiment code imports, no paper edits; all 78 main/supplement endpoint files and all 39 diagnostics read. Raw input score streams were not retained, so regenerated-stream pairing is verified by source inspection, not by direct input hashes.', 'input_sha256':hashes,'new_trials_generated':0,'python':sys.version.split()[0]}
s = pd.read_csv(R/'summary.csv'); p = pd.read_csv(R/'paired.csv'); z = pd.read_csv(R/'seed_summary.csv')
m = pd.read_csv(R/'mass_ablation_summary.csv'); mr = pd.read_csv(R/'mass_ablation_raw.csv.gz')
manifest = json.loads((R/'multiplicity_manifest.json').read_text())
checks = {}; errors = []
def difference(name, a, b, tol=2e-9):
    a,b = np.asarray(a,float),np.asarray(b,float)
    assert a.shape == b.shape, name
    assert np.array_equal(np.isnan(a),np.isnan(b)), name
    mask = np.isfinite(a)&np.isfinite(b)
    d = float(np.max(np.abs(a[mask]-b[mask]))) if mask.any() else 0.
    checks[name] = max(checks.get(name,0.),d)
    assert d < tol, (name,d)
def holm(vals):
    vals=np.asarray(vals,float); order=np.argsort(vals); a=np.empty(len(vals))
    a[order]=np.minimum(1,np.maximum.accumulate((len(vals)-np.arange(len(vals)))*vals[order])); return a
exact=(s.scenario!='shift')&s.method.isin(manifest['exact_coverage_methods'])
under=(s.scenario!='shift')&s.method.isin(manifest['undercoverage_methods'])
width=(p.scenario!='shift')&(((p.method=='safe_cp')&(p.reference=='ppi_pp'))|((p.method=='cp_tails')&(p.reference=='label_cp')))
assert (int(exact.sum()),int(under.sum()),int(width.sum()))==(180,252,72)
assert np.array_equal(s.exact_family_member,exact)
assert np.array_equal(s.p_holm_undercoverage.notna(),under)
assert np.array_equal(p.p_holm_width.notna(),width)
assert np.array_equal(s.exact_sim_lower.notna(),exact)
difference('coverage',s.coverage,s.hits/s.reps)
z975=norm.ppf(.975); q=s.hits/s.reps; den=1+z975*z975/s.reps
mid=(q+z975*z975/(2*s.reps))/den
rad=z975*np.sqrt(q*(1-q)/s.reps+z975*z975/(4*s.reps*s.reps))/den
difference('Wilson lower',s.cov_low,mid-rad); difference('Wilson upper',s.cov_high,mid+rad)
difference('exact lower',s.loc[exact,'exact_sim_lower'],beta.ppf(.05/180,s.loc[exact,'hits'],s.loc[exact,'reps']-s.loc[exact,'hits']+1))
difference('undercoverage p',s.undercoverage_p,binom.cdf(s.hits,s.reps,.95))
difference('undercoverage Holm',s.loc[under,'p_holm_undercoverage'],holm(s.loc[under,'undercoverage_p']))
difference('width Holm',p.loc[width,'p_holm_width'],holm(p.loc[width,'p_one_sided']))
ss=s.set_index(['cell_id','method']); pp=p.set_index(['cell_id','method','reference'])
raw_rows=0; main_rows=0; supplement_rows=0; trials=0; diagnostics={}; zero_denominator=0; cells=[]
for cid,g in s.groupby('cell_id',sort=True):
    first=g.iloc[0]; n,N=int(first.n),int(first.N); reps=int(first.reps)
    slug=f'{cid:02d}_{first.scenario}_n{n}_N{N}'
    main=pd.read_csv(R/'results'/(slug+'.csv.gz'))
    supplement=pd.read_csv(R/'results_supplement'/(slug+'.csv.gz'))
    raw=pd.concat([main,supplement],ignore_index=True)
    assert len(main)==14*reps and len(supplement)==2*reps
    assert not raw.duplicated(['seed','rep','method']).any()
    assert set(raw.seed)=={1729,2027,7919}
    assert np.isfinite(raw[['low','high','width','truth']]).all().all()
    assert ((raw.low>=0)&(raw.high<=1)&(raw.low<=raw.high)).all()
    difference('raw width endpoint identity',raw.width,raw.high-raw.low,3e-14)
    assert np.array_equal(raw.covered,((raw.low<=raw.truth)&(raw.truth<=raw.high)).astype(int))
    wide=raw.pivot(index=['seed','rep'],columns='method',values='width').sort_index()
    assert wide.shape==(reps,16) and not wide.isna().any().any()
    for method,gg in raw.groupby('method'):
        sr=ss.loc[(cid,method)]
        assert len(gg)==sr.reps and gg.covered.sum()==sr.hits
        assert int((gg.width<1e-14).sum())==int(sr.degenerate)
        difference('raw mean width',gg.width.mean(),sr.width)
        difference('raw width MCSE',gg.width.std(ddof=1)/np.sqrt(reps),sr.width_mcse)
        difference('raw width median',gg.width.median(),sr.width_median)
        for seed,sg in gg.groupby('seed'):
            zr=z[(z.cell_id==cid)&(z.method==method)&(z.seed==seed)].iloc[0]
            assert len(sg)==zr.reps
            difference('seed coverage',sg.covered.mean(),zr.coverage)
            difference('seed width',sg.width.mean(),zr.width)
        for ref in ['ppi_pp','label_cp']:
            a,b=wide[method].to_numpy(),wide[ref].to_numpy(); pr=pp.loc[(cid,method,ref)]
            diff=a-b; se=diff.std(ddof=1)/np.sqrt(reps)
            difference('paired difference',diff.mean(),pr.difference)
            difference('paired difference MCSE',se,pr.difference_mcse)
            pv=t.cdf(diff.mean()/se,reps-1) if se else float(diff.mean()>=0)
            difference('paired p',pv,pr.p_one_sided)
            if b.mean()==0:
                zero_denominator+=1
                assert np.isnan(pr[['ratio','ratio_mcse','ratio_low','ratio_high']].to_numpy(float)).all()
            else:
                ratio=a.mean()/b.mean(); rse=np.std(a-ratio*b,ddof=1)/(np.sqrt(reps)*b.mean())
                difference('paired ratio',ratio,pr.ratio)
                difference('paired ratio MCSE',rse,pr.ratio_mcse)
                difference('paired ratio lower',ratio-1.96*rse,pr.ratio_low)
                difference('paired ratio upper',ratio+1.96*rse,pr.ratio_high)
    dg=pd.read_csv(R/'results'/(slug+'_diagnostics.csv.gz'))
    assert len(dg)==reps and not dg.duplicated(['seed','rep']).any()
    assert set(dg.set_index(['seed','rep']).index)==set(wide.index)
    rp=raw[raw.method=='ppi_pp']
    diagnostics[str(cid)]={'safe_choices':{str(int(k)):int(v) for k,v in dg.safe_choice.value_counts().items()},'ppi_pp_00':int(((rp.low==0)&(rp.high==0)).sum()),'ppi_pp_11':int(((rp.low==1)&(rp.high==1)).sum()),'ppi_pp_nondegenerate_misses':int(((rp.width>=1e-14)&(rp.covered==0)).sum())}
    if cid in set(m.cell_id):
        ar=mr[mr.cell_id==cid].set_index(['seed','rep']).sort_index(); mm=m[m.cell_id==cid].iloc[0]
        assert len(ar)==reps and ar.index.equals(wide.index)
        assert np.array_equal(ar.covered,((ar.low<=.5)&(.5<=ar.high)).astype(int))
        difference('mass endpoints',ar.width,ar.high-ar.low,3e-14)
        difference('mass unknown',wide.cp_tails.mean(),mm.unknown_width)
        difference('mass matched',ar.width.mean(),mm.matched_width)
        difference('mass reallocated',wide.oracle_mass_cp.mean(),mm.reallocated_width)
        gap=wide.cp_tails-ar.width
        difference('mass gap',gap.mean(),mm.mass_gap)
        difference('mass gap MCSE',gap.std(ddof=1)/np.sqrt(reps),mm.mass_gap_mcse)
        difference('mass realloc gap',(ar.width-wide.oracle_mass_cp).mean(),mm.realloc_gap)
        difference('mass coverage',ar.covered.mean(),mm.coverage)
    raw_rows+=len(raw); main_rows+=len(main); supplement_rows+=len(supplement); trials+=reps
    cells.append({'cell_id':int(cid),'trials':reps,'methods':16,'rows':len(raw)})
report.update({'sizes':{'cells':len(cells),'summary_rows':len(s),'paired_rows':len(p),'seed_rows':len(z),'trial_inputs':trials,'main_rows':main_rows,'supplement_rows':supplement_rows,'total_method_rows':raw_rows,'mass_rows_separate':len(mr)},'maximum_absolute_discrepancies':checks,'raw_cells':cells,'diagnostics':diagnostics,'family_sizes':{'exact':int(exact.sum()),'width':int(width.sum()),'undercoverage':int(under.sum())},'width_rejections':p[width&(p.p_holm_width<.05)][['cell_id','scenario','method','reference','ratio']].to_dict('records'),'undercoverage_rejections':int((s.p_holm_undercoverage<.05).sum()),'exact_min_coverage':float(s.loc[exact,'coverage'].min()),'exact_min_sim_lower':float(s.loc[exact,'exact_sim_lower'].min()),'undefined_ratios':zero_denominator})
# TeX graph: inspect only files actually included by the manuscript.
seen={}
def load_tex(path):
    path=path.resolve()
    if path in seen:return
    text=path.read_text(); seen[path]=text
    for match in re.finditer(r'\\input\{([^}]+)\}',text):
        child=R/match.group(1)
        if not child.suffix:child=child.with_suffix('.tex')
        assert child.exists(),child
        load_tex(child)
load_tex(R/'paper.tex')
clean={path:re.sub(r'(?<!\\)%[^\n]*','',text) for path,text in seen.items()}
alltext='\n'.join(clean.values()); maintext=clean[(R/'paper.tex').resolve()]
labels=re.findall(r'\\label\{([^}]+)\}',alltext)
refs=re.findall(r'\\(?:eqref|ref|autoref|cref|Cref)\{([^}]+)\}',alltext)
cites=[]
for match in re.finditer(r'\\cite\w*\*?(?:\[[^]]*\])*\{([^}]+)\}',alltext):cites.extend(x.strip() for x in match.group(1).split(','))
bib=(R/'references.bib').read_text(); bibkeys=re.findall(r'@\w+\s*\{\s*([^,]+),',bib)
markers=[]
for path,text in clean.items():
    for no,line in enumerate(text.splitlines(),1):
        if re.search(r'\\todo\b|\bTODO\b|\bFIXME\b|\bTBD\b',line,re.I):markers.append({'file':str(path),'line':no,'text':line})
tables=[]
for match in re.finditer(r'\\begin\{table\}.*?\\end\{table\}',maintext,re.S):
    text=match.group(); cap=text.index('\\caption'); content=min([i for i in [text.find('\\input'),text.find('\\begin{tabular}')] if i>=0]); label=re.search(r'\\label\{([^}]+)\}',text).group(1)
    tables.append({'label':label,'paper_tex_line':maintext[:match.start()].count('\n')+1,'caption_above':cap<content,'referenced':label in refs})
figures=[]
for match in re.finditer(r'\\begin\{figure\}.*?\\end\{figure\}',maintext,re.S):
    text=match.group(); label=re.search(r'\\label\{([^}]+)\}',text).group(1); path=re.search(r'\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}',text).group(1)
    figures.append({'label':label,'paper_tex_line':maintext[:match.start()].count('\n')+1,'path':path,'exists':(R/path).exists(),'referenced':label in refs})
report['mechanical']={'included_tex_files':[str(x.relative_to(R)) for x in seen],'citation_keys':sorted(set(cites)),'bib_keys':bibkeys,'missing_bib_keys':sorted(set(cites)-set(bibkeys)),'uncited_bib_keys':sorted(set(bibkeys)-set(cites)),'missing_reference_labels':sorted(set(refs)-set(labels)),'duplicate_labels':sorted({x for x in labels if labels.count(x)>1}),'markers':markers,'tables':tables,'figures':figures,'unreferenced_table_labels':[x['label'] for x in tables if not x['referenced']],'unreferenced_figure_labels':[x['label'] for x in figures if not x['referenced']]}
# Every generated empirical table row is checked against its CSV source at printed precision.
names={'label_cp':'Label CP','label_wald':'Label Wald','ppi':'PPI','ppi_pp':'PPI++','wald_half':'Half Wald','wald_tails':'Tails Wald','wald_four':'Bin4 Wald','wald_eight':'Bin8 Wald','cp_half':'Half CP','cp_tails':'Tails CP','cp_four':'Bin4 CP','safe_cp':'Safe CP','unsafe_cp':'Unsafe selection','oracle_mass_cp':'Known-mass CP','label_hoeffding':'Label Hoeffding','ppi_hoeffding':'PPI Hoeffding'}
scenames={'affine':'Affine','reverse':'Reversed','smooth_u':'Smooth U','sharp_tails':'Sharp tails','irrelevant':'Irrelevant','constant':'Constant','rare_tails':'Rare tails','shift':'Shift','forest':'Forest','galaxies':'Galaxies'}
allres=(R/'generated/all_results.tex').read_text()
for _,row in s.iterrows():
    expected=f"{scenames[row.scenario]} {int(row.n)}/{int(row.N)} & {names[row.method]} & ${row.width:.5f}\\pm {row.width_mcse:.5f}$ & {row.coverage:.4f} & {row.cov_low:.4f} & {row.cov_high:.4f}"
    assert expected in allres,expected
methods=['label_cp','ppi_pp','wald_four','cp_tails','safe_cp']
for fname,subset,real in [('main_table.tex',s[(s.design=='main')&(s.n==500)&(s.scenario!='shift')],False),('real_table.tex',s[s.design=='empirical'],True)]:
    text=(R/'generated'/fname).read_text()
    for (sc,n),g in subset.groupby(['scenario','n']):
        vals=[f'{ss.loc[(int(g.iloc[0].cell_id),method)].width:.4f} / {100*ss.loc[(int(g.iloc[0].cell_id),method)].coverage:.1f}' for method in methods]
        expected=' & '.join([scenames[sc]]+([str(n)] if real else [])+vals)
        assert expected in text,expected
pairtext=(R/'generated/paired_table.tex').read_text()
for cid,method,ref in [(10,'cp_tails','label_cp'),(10,'safe_cp','ppi_pp'),(11,'safe_cp','ppi_pp'),(8,'wald_four','ppi_pp'),(13,'safe_cp','label_cp'),(37,'safe_cp','ppi_pp')]:
    a=ss.loc[(cid,method)]; b=pp.loc[(cid,method,ref)]
    expected=f'{scenames[a.scenario]} {int(a.n)} & {names[method]} & {b.ratio:.3f} & [{b.ratio_low:.3f},{b.ratio_high:.3f}] & {a.coverage:.3f} & [{a.cov_low:.3f},{a.cov_high:.3f}]'
    assert expected in pairtext,expected
for _,row in m.iterrows():
    expected=f'{row.N/500:.0f} & {row.unknown_width:.4f} & {row.matched_width:.4f} & {row.reallocated_width:.4f} & {row.mass_gap:.4f} & {row.mass_gap_mcse:.5f}'
    assert expected in (R/'generated/mass_ablation.tex').read_text()
report['generated_tables']={'all_results_rows_verified':len(s),'main_rows_verified':7,'real_rows_verified':6,'paired_rows_verified':6,'mass_rows_verified':4,'positive_mcse_printed_zero':int(((s.width_mcse>0)&(s.width_mcse<.000005)).sum()),'mass_positive_mcse_printed_zero':int((m.mass_gap_mcse<.000005).sum()),'status':'all printed values reproduced from CSVs at displayed precision'}
# Quote-critical headline numbers, preserving keys and physical CSV line locators.
headline=[]
for cid,method,ref in [(10,'safe_cp','ppi_pp'),(10,'cp_tails','label_cp'),(11,'safe_cp','ppi_pp'),(8,'wald_four','ppi_pp'),(34,'safe_cp','ppi_pp'),(37,'safe_cp','ppi_pp'),(27,'safe_cp','ppi_pp'),(28,'safe_cp','ppi_pp'),(29,'safe_cp','ppi_pp')]:
    pr=p[(p.cell_id==cid)&(p.method==method)&(p.reference==ref)].iloc[0]; sr=ss.loc[(cid,method)]
    headline.append({'cell_id':cid,'method':method,'reference':ref,'paired_csv_line':int(pr.name)+2,'summary_csv_line':int(s[(s.cell_id==cid)&(s.method==method)].index[0])+2,'ratio':float(pr.ratio),'gain_percent':100*(1-float(pr.ratio)),'gain_low_percent':100*(1-float(pr.ratio_high)),'gain_high_percent':100*(1-float(pr.ratio_low)),'coverage':float(sr.coverage)})
report['headline_claims']=headline
reader=PdfReader(R/'paper.pdf'); texts=[page.extract_text() or '' for page in reader.pages]
report['pdf']={'total_pages':len(texts),'references_pages':[i+1 for i,x in enumerate(texts) if re.search(r'^References\s*\d*\s*$',x,re.M)],'appendix_start_pages':[i+1 for i,x in enumerate(texts) if re.search(r'A\s+Complete proofs',x)],'checklist_start_pages':[i+1 for i,x in enumerate(texts) if 'NeurIPS Paper Checklist' in x],'page_size_points':[[float(x.mediabox.width),float(x.mediabox.height)] for x in reader.pages],'literal_double_question_mark_pages':[i+1 for i,x in enumerate(texts) if '??' in x]}
log=(R/'paper.log').read_text(errors='replace'); report['latex_warnings']=[x for x in log.splitlines() if re.search(r'undefined|Overfull|Underfull|Warning',x,re.I)]
# Analytic existing-output diagnostic, not a simulation.
k=np.arange(101); mu=.35
lo=np.where(k==0,0,beta.ppf(.025,np.maximum(k,1),101-k)); hi=np.where(k==100,1,beta.ppf(.975,k+1,np.maximum(100-k,1)))
true_cov=float(binom.pmf(k,100,mu)[(lo<=mu)&(mu<=hi)].sum())
report['analytic_label_cp_cell6']={'coverage':true_cov,'observed_hits':2830,'nominal_boundary_p':float(binom.cdf(2830,3000,.95)),'true_coverage_boundary_p':float(binom.cdf(2830,3000,true_cov))}
# Verify all generated numeric macros against artifacts, not just displayed tables.
values={}
def val(name,x,digits=3): values[name]=f'{x:.{digits}f}'
for cid,method,tag in [(10,'safe_cp','SharpSafe'),(10,'cp_tails','SharpCP'),(11,'safe_cp','SharpLarge'),(18,'ppi_pp','RarePP'),(18,'label_cp','RareLabel'),(22,'ppi_pp','ShiftPP'),(22,'cp_half','ShiftHalf'),(22,'safe_cp','ShiftSafe'),(37,'safe_cp','GalaxySafe'),(34,'safe_cp','ForestSafe'),(8,'wald_four','SmoothFour')]:
    row=ss.loc[(cid,method)]
    val(tag+'Cov',100*row.coverage,1); val(tag+'Width',row.width,4)
    for ref,rt in [('ppi_pp','PP'),('label_cp','Label')]:
        pr=pp.loc[(cid,method,ref)]
        val(tag+'Ratio'+rt,pr.ratio,3); val(tag+'Gain'+rt,100*(1-pr.ratio),1)
val('MinExactCoverage',100*s.loc[exact,'coverage'].min(),1)
val('MaxExactWidthSE',s.loc[exact,'width_mcse'].max(),5)
val('MinExactSimLower',100*s.loc[exact,'exact_sim_lower'].min(),1)
val('NumUndercoverage',(s.p_holm_undercoverage<.05).sum(),0); val('TotalTrialInputs',trials,0)
val('MainRuntime',json.loads((R/'results/run_metadata.json').read_text())['seconds'],1)
val('SupplementRuntime',json.loads((R/'results_supplement/metadata.json').read_text())['seconds'],1)
assert values==json.loads((R/'generated/numbers.json').read_text())
texvalues=dict(re.findall(r'\\newcommand\{\\(\w+)\}\{([^}]+)\}',(R/'generated/numbers.tex').read_text()))
assert values==texvalues
report['generated_number_macros_verified']=len(values)
report['empirical_input_checks']={}
for name,total,pos in [('forest',1596,242),('galaxies',16743,4341)]:
    with np.load(R/'data'/(name+'.npz')) as arr:
        y,score=arr['Y'],arr['Yhat']
        assert len(y)==total and np.sum(y)==pos and np.isin(y,[0,1]).all()
        assert np.isfinite(score).all() and ((score>=0)&(score<=1)).all()
        report['empirical_input_checks'][name]={'records':len(y),'successes':int(np.sum(y)),'target':float(np.mean(y)),'sha256':digest(R/'data'/(name+'.npz'))}
report['bib_leftover_markers']=re.findall(r'\\todo\b|\bTODO\b|\bFIXME\b|\bTBD\b',bib,re.I)
report['input_files_unchanged']=all(digest(R/path)==value for path,value in hashes.items())
assert report['input_files_unchanged']
report['overall_numerical_status']='passed: saved endpoints, summary/paired formulas, multiplicity families, mass ablation and printed empirical tables'
OUT.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
print(json.dumps({k:report[k] for k in ['sizes','family_sizes','undercoverage_rejections','exact_min_coverage','exact_min_sim_lower','undefined_ratios','generated_tables','overall_numerical_status','input_files_unchanged']},indent=2))
print('Mechanical:',json.dumps(report['mechanical'],indent=2)); print('LaTeX:',report['latex_warnings'])
