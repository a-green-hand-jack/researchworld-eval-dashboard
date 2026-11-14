"""Validate the released artifact and independently replay first 3 draws/cell.
Does NOT rerun all 64k repetitions or claim missing sample-ID logs exist.
"""
from pathlib import Path
import hashlib,json,zipfile
import numpy as np
import pandas as pd
from pypdf import PdfReader
from methods import all_intervals
from exact_stratified import stratified_interval
from run_experiments import BASE_SEED,SCENARIOS,conditional_mean
ROOT=Path(__file__).resolve().parent

def main():
    for f in ['paper.pdf','paper.tex','references.bib','README.md','final_report.md','requirements.txt',
              'methods.py','exact_stratified.py','run_experiments.py','run_stratified.py','analyze.py','plot.py']:
        assert (ROOT/f).is_file(),f
    s=pd.read_csv(ROOT/'results'/'all_summary.csv',keep_default_na=False,
                  dtype={'under_p_scientific':str,'under_holm_scientific':str})
    assert len(s)==442 and len(s[s.scenario=='null'])>0
    assert s.groupby(['scenario','n','ratio']).ngroups==32
    assert np.isfinite(s.under_log10p).all()
    config=json.loads((ROOT/'results'/'config.json').read_text())
    replay_count=0; maxerr=0.
    for name,n,ratio,reps,tag in config['cells']:
        rng=np.random.default_rng(np.random.SeedSequence([BASE_SEED,SCENARIOS.index(name),n,ratio]));N=n*ratio
        path=f'{name}_n{n}_r{ratio}.csv.gz'
        a=pd.read_csv(ROOT/'results'/'raw'/path,keep_default_na=False)
        b=pd.read_csv(ROOT/'results'/'supplement_raw'/path,keep_default_na=False)
        real=name in ['galaxies','forest'];d=np.load(ROOT/'data'/f'{name}.npz') if real else None
        for rep in range(3):
            if real:
                il=rng.integers(0,len(d['Y']),n);iu=rng.integers(0,len(d['Y']),N)
                y=d['Y'][il];sl=d['Yhat'][il];su=d['Yhat'][iu]
                out,_=all_intervals(y,sl,su)
            else:
                sl=rng.uniform(size=n);su=rng.uniform(size=N)
                ml=conditional_mean(name,sl);mu=conditional_mean(name,su);y=rng.binomial(1,ml)
                out,_=all_intervals(y,sl,su,ml,mu)
            out['cp_strat2']=stratified_interval(y,sl,su)
            for method,triple in out.items():
                frame=b if method=='cp_strat2' else a
                q=frame[(frame.rep==rep)&(frame.method==method)].iloc[0]
                actual=np.array([q.lower,q.upper,q.raw_width]);expected=np.array(triple)
                error=float(np.max(np.abs(actual-expected)));maxerr=max(maxerr,error)
                np.testing.assert_allclose(actual,expected,atol=1e-10,rtol=1e-10)
                replay_count+=1
    files=json.loads((ROOT/'artifacts'/'prerun_sha256.json').read_text())
    freeze={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h for f,h in files.items()}
    assert all(freeze.values()),freeze
    archive=zipfile.ZipFile(ROOT/'artifacts'/'icml2026.zip')
    style_match={f:(ROOT/f).read_bytes()==archive.read(f) for f in ['icml2026.sty','icml2026.bst','algorithm.sty','algorithmic.sty','fancyhdr.sty']}
    assert all(style_match.values())
    pdf=PdfReader(ROOT/'paper.pdf');texts=[p.extract_text() for p in pdf.pages]
    refs=next(i+1 for i,t in enumerate(texts) if 'References' in t)
    appendix=next(i+1 for i,t in enumerate(texts) if 'A. Proof Details' in t)
    assert refs<=8 and appendix>refs
    assert 'AUTHORERR' not in ''.join(texts) and '??' not in ''.join(texts)
    fonts={};seen=set()
    def scan(res):
        res=res.get_object()
        fd=res.get('/Font',{});fd=fd.get_object() if hasattr(fd,'get_object') else fd
        for f in fd.values():
            o=f.get_object();desc=o.get('/FontDescriptor',{});desc=desc.get_object() if hasattr(desc,'get_object') else desc
            fonts[str(o.get('/BaseFont'))]={'type':str(o.get('/Subtype')),'embedded':any(k in desc for k in ['/FontFile','/FontFile2','/FontFile3'])}
        xo=res.get('/XObject',{});xo=xo.get_object() if hasattr(xo,'get_object') else xo
        for x in xo.values():
            o=x.get_object();key=str(x)
            if key not in seen and o.get('/Resources'):
                seen.add(key);scan(o['/Resources'])
    for page in pdf.pages:scan(page['/Resources'])
    assert all(v['type']=='/Type1' and v['embedded'] for v in fonts.values()),fonts
    result={'files_present':True,'summary_rows':len(s),'cells':32,'replayed_datasets':96,
            'endpoint_triples_replayed':replay_count,'maximum_export_error':maxerr,
            'frozen_statistical_files_match':freeze,'official_template_files_match':style_match,
            'pdf_pages':len(pdf.pages),'references_start_page':refs,'appendix_start_page':appendix,
            'main_body_at_most_pages':refs,'all_fonts_embedded_type1':True,'font_count':len(fonts),
            'limitations':'sampled replay only; local freeze records not independently timestamped; no acceptance-readiness assertion'}
    (ROOT/'artifacts'/'final_validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
