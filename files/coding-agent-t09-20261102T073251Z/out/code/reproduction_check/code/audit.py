"""Audit artifact integrity, shared streams, numeric results, and the PDF page limit."""
import hashlib,json,re
from pathlib import Path
import numpy as np,pandas as pd,pymupdf
from study import ROOT

def main():
    m=pd.read_csv(ROOT/'results/main_raw.csv.gz')
    noise=pd.read_csv(ROOT/'results/noise_raw.csv.gz')
    scale=pd.read_csv(ROOT/'results/scaling_raw.csv.gz')
    s=pd.read_csv(ROOT/'results/sensitivity_raw.csv.gz')
    assert len(m)==168000 and m.valid.all()
    assert len(noise)==168000 and noise.valid.all()
    assert len(scale)==24000 and scale.valid.all()
    # Regenerated sensitivity trials must share exact errors with primary trials.
    a=m.query("model=='OLS-L' and dgm in ['linear','quadratic','cubic']")
    merged=a.merge(s,on=['graph','design','dgm','rep'],suffixes=('_main','_sensitivity'))
    assert len(merged)==14400
    assert np.max(abs(merged.error_main-merged.error_sensitivity))<1e-11
    assert (s.conditional_bias.abs()<=s.sharp+1e-10).all()
    assert (s.sharp<=s.loose+1e-10).all()
    su=pd.read_csv(ROOT/'results/support_raw.csv.gz')
    allnodes=su.query('cutoff==1')
    fb=m.query("graph=='Facebook' and design=='bernoulli' and dgm=='cubic' and model=='OLS-C'")
    for selection in ['degree','random']:
        dd=allnodes.query('selection==@selection').merge(fb,on='rep')
        assert np.max(abs(dd.error_x-dd.error_y))<1e-11
    assert hashlib.sha256((ROOT/'data/raw/facebook_combined.txt.gz').read_bytes()).hexdigest()== '125e84db872eeba443d270c70315c256b0af43a502fcfe51f50621166ad035d7'
    # Preserve the unmodified official style.
    official=ROOT/'sources/icml2026/icml2026.sty'
    if official.exists():assert official.read_bytes()==(ROOT/'paper/icml2026.sty').read_bytes()
    doc=pymupdf.open(ROOT/'paper/main.pdf')
    texts=[p.get_text() for p in doc]
    impact=next(i for i,t in enumerate(texts) if '\nImpact Statement\n' in t)
    assert impact<=8, f'Body has {impact} pages, over ICML submission limit.'
    assert 'Completed reproducibility checklist' in '\n'.join(texts)
    assert not re.search(r'Citation .+ undefined|Reference .+ undefined|Overfull \\hbox',
                         (ROOT/'paper/main.log').read_text())
    assert len(list((ROOT/'figures').glob('*.pdf')))==5
    result=dict(primary_rows=len(m),noise_rows=len(noise),scaling_rows=len(scale),
                shared_stream_max_error=float(np.max(abs(merged.error_main-merged.error_sensitivity))),
                curvature_bound_checks=len(s),pdf_pages=len(doc),body_pages=impact,
                main_contrasts_estimable=bool(m.valid.all()),
                figure_count=5,pdf_sha256=hashlib.sha256((ROOT/'paper/main.pdf').read_bytes()).hexdigest())
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
