"""Check the deliverable's main-page limit, fonts, references, and template integrity."""
from pathlib import Path
import json,hashlib
import pymupdf
R=Path(__file__).resolve().parents[1]
def main():
 doc=pymupdf.open(R/'paper/paper.pdf');texts=[p.get_text() for p in doc]
 impact=[i for i,s in enumerate(texts) if 'Impact Statement' in s];assert len(impact)==1
 main_pages=impact[0];assert 1<=main_pages<=8,(main_pages,'ICML main body limit')
 fonts=sorted(set(f[2] for p in doc for f in p.get_fonts()));assert fonts==['Type1'],fonts
 assert all('??' not in s for s in texts)
 assert any('References' in s for s in texts);assert any('Completed Checklist' in s for s in texts)
 log=(R/'logs/latex-pass3.log').read_text();assert 'Overfull' not in log;assert 'undefined' not in log.lower()
 manifest=json.loads((R/'TEMPLATE_MANIFEST.json').read_text())
 for name,sha in manifest['files'].items():
  if name.endswith('.zip'):continue
  assert hashlib.sha256((R/'paper'/name).read_bytes()).hexdigest()==sha,name
 out={'total_pages':len(doc),'main_body_pages':main_pages,'impact_and_references_start_page':impact[0]+1,'font_types':fonts,'undefined_references':False,'overfull_boxes':False,'official_styles_unmodified':True,'pdf_bytes':(R/'paper/paper.pdf').stat().st_size}
 (R/'results/pdf_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
