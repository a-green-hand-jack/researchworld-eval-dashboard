#!/usr/bin/env python3
"""Build root paper.pdf with unmodified official ICML styles and audit output."""
from pathlib import Path
import subprocess,json,re,shutil
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1]

def main():
    for style in ['icml2026.sty','fancyhdr.sty']:shutil.copyfile(ROOT/'paper/template'/style,ROOT/style)
    with (ROOT/'artifacts/latex_build.log').open('w') as log:
        subprocess.run(['latexmk','-pdf','-interaction=nonstopmode','-halt-on-error','paper.tex'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
    r=PdfReader(ROOT/'paper.pdf');text=[p.extract_text() for p in r.pages]
    (ROOT/'artifacts/paper_extracted.txt').write_text('\n\n'.join('PAGE '+str(i+1)+'\n'+t for i,t in enumerate(text)))
    first_impact=next(i+1 for i,t in enumerate(text) if 'Impact Statement' in t)
    assert first_impact-1<=8
    assert not any('AUTHORERR' in t or '??' in t for t in text)
    fonts={}
    def visit(resources):
        if resources is None:return
        for f in resources.get('/Font',{}).values():
            f=f.get_object();desc=f.get('/FontDescriptor');desc=desc.get_object() if desc else {}
            fonts[str(f.get('/BaseFont'))]={'subtype':str(f.get('/Subtype')),'embedded':any(k in desc for k in ['/FontFile','/FontFile2','/FontFile3'])}
        for obj in resources.get('/XObject',{}).values():
            obj=obj.get_object()
            if '/Resources' in obj:visit(obj['/Resources'])
    for page in r.pages:visit(page['/Resources'])
    assert all(f['subtype']=='/Type1' and f['embedded'] for f in fonts.values()),fonts
    log=(ROOT/'paper.log').read_text();undefined=[l for l in log.splitlines() if ('undefined' in l.lower() and 'warning' in l.lower())];assert not undefined,undefined
    overflow=[l for l in log.splitlines() if 'Overfull' in l]
    assert not overflow,overflow
    result={'pages':len(r.pages),'main_text_pages':first_impact-1,'impact_references_first_page':first_impact,'bytes':(ROOT/'paper.pdf').stat().st_size,'official_template':'ICML 2026, anonymous review, unmodified styles','main_limit':8,'all_fonts_embedded_type1':True,'fonts':fonts,'unresolved_refs_or_citations':False,'author_template_error':False,'overfull_boxes':overflow}
    (ROOT/'artifacts/pdf_audit.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='fonts'},indent=2))
if __name__=='__main__':main()
