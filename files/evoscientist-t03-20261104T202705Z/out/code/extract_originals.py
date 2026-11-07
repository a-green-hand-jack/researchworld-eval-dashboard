from pypdf import PdfReader
from pathlib import Path
import re,json
root=Path('/work/originals')
summary=[]
for id in ['1705.07874','2006.16234','2410.01917','17-514','2108.04884']:
    r=PdfReader(root/(id+'.pdf'))
    kept=[]
    m=None
    for i,p in enumerate(r.pages):
        t=p.extract_text()
        m=re.search(r'(?mi)^\s*(?:[0-9]+[. ]+)?References\s*$',t)
        kept.append('\n=== PDF PAGE '+str(i+1)+' ===\n'+(t[:m.start()] if m else t))
        if m: break
    (root/(id+'.main.txt')).write_text('\n'.join(kept))
    summary.append({'id':id,'pdf_pages':len(r.pages),'main_pages_extracted':len(kept),'bibliography_removed':bool(m),'metadata':str(r.metadata)})
print(json.dumps(summary,indent=2))
