"""Offline integrity, result-contract and paper checks; no experiment rerun."""
from pathlib import Path
import hashlib
import json
import re
import zipfile
import numpy as np
import pandas as pd
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]

def main():
    manifest=json.loads((ROOT/'data/manifest.json').read_text())
    for f in manifest['files']:
        p=ROOT/f['path']
        assert hashlib.sha256(p.read_bytes()).hexdigest()==f['sha256'],f['path']
        assert p.stat().st_size==f['bytes']
    archive=ROOT/'paper/vendor/iclr-2027-official.zip'
    with zipfile.ZipFile(archive) as z:
        for filename in ['iclr2027_conference.sty','iclr2027_conference.bst']:
            key=next(k for k in z.namelist() if k.endswith('/'+filename))
            assert (ROOT/'paper'/filename).read_bytes()==z.read(key)
    s=pd.read_csv(ROOT/'artifacts/support.csv')
    expected=0
    for ds in ['helm','oll','oll_raw','oll_all_entries']:
        fr=pd.read_csv(ROOT/f'data/processed/{ds}.csv',index_col=0)
        expected+=len(fr)*80
    assert len(s)==expected
    assert not s.duplicated(['dataset','model','rule','cap','rho','margin']).any()
    assert ((s.k>=0)&(s.k<=s.d+1)).all()
    by_rho=s.pivot(index=['dataset','model','rule','cap','margin'],columns='rho',values='k')
    assert (np.diff(by_rho.values,axis=1)<=0).all(),'More response cannot increase cost'
    by_cap=s.pivot(index=['dataset','model','rule','rho','margin'],columns='cap',values='k')
    assert (by_cap.observed>=by_cap.perfect).all(),'Smaller box cannot decrease cost'
    primary=s.query("dataset in ['helm','oll'] and rho==1 and margin==0 and common")
    assert (primary.k<=primary.d).all()
    for dataset in ['helm','oll']:
        for cap in ['perfect','observed']:
            p=primary.query('dataset==@dataset and cap==@cap').pivot(index='model',columns='rule',values='k')
            delta=(p['median']-p['mean']).mean()
            assert delta>0 if cap=='perfect' else delta<0
    aux=(ROOT/'paper/main.aux').read_text()
    m=re.search(r'\\newlabel\{endmain\}\{\{[^}]*\}\{(\d+)\}',aux)
    assert m,'Missing endmain label'
    endmain_label=int(m.group(1))
    pdf=PdfReader(ROOT/'paper/main.pdf')
    texts=[p.extract_text() for p in pdf.pages]
    ai_pages=[i for i,t in enumerate(texts) if 'AIUSESTATEMENT' in re.sub(r'\s','',t.upper())]
    assert ai_pages
    main_pages=ai_pages[0]
    assert endmain_label<=main_pages<=9,(endmain_label,main_pages)
    source_files=[ROOT/'paper/main.tex',ROOT/'paper/references.bib']
    source_files+=list((ROOT/'paper/generated').glob('*.tex'))+list((ROOT/'paper/figures').glob('*.pdf'))
    assert (ROOT/'paper/main.pdf').stat().st_mtime>=max(p.stat().st_mtime for p in source_files)
    all_text='\n'.join(texts)
    for token in ['AIUSESTATEMENT','ETHICSSTATEMENT','REPRODUCIBILITYSTATEMENT','REFERENCES']:
        assert token in re.sub(r'\s','',all_text.upper()),token
    assert 'not submitted' in texts[0]
    assert '??' not in all_text
    log=(ROOT/'paper/main.log').read_text()
    assert 'undefined' not in log.lower()
    assert 'Overfull' not in log
    tex=(ROOT/'paper/main.tex').read_text()
    assert not re.search(r'\b(TODO|TBD|FIXME)\b',tex)
    figures=sorted(p.name for p in (ROOT/'paper/figures').glob('*.pdf'))
    assert len(figures)==5,figures
    tests=(ROOT/'artifacts/tests.xml').read_text()
    assert 'failures="0"' in tests and 'errors="0"' in tests
    result=dict(raw_files_checked=len(manifest['files']),raw_sha256='all match',
                official_template='byte-identical sty and bst', support_rows=len(s),
                response_monotonicity='pass',ceiling_monotonicity='pass',
                main_reversal='pass on both primary snapshots',
                main_text_pages=main_pages,main_limit=9,pdf_total_pages=len(pdf.pages),
                figures=figures,unresolved_references=0,overfull_boxes=0,
                mandatory_ai_statement='present',test_xml='zero failures/errors')
    (ROOT/'artifacts/verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    main()
