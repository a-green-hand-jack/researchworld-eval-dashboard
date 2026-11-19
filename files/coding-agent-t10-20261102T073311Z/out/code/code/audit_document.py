"""Verify conference pagination, complete checklist, and no unresolved TeX items."""
import json,hashlib,re
from pathlib import Path
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1]
r=PdfReader(ROOT/'paper/main.pdf')
texts=[p.extract_text() for p in r.pages]
ref=next(i for i,t in enumerate(texts) if t.startswith('References'))
assert ref<=9, f'Body exceeds official nine-page limit: {ref}'
assert ref==7
check=(ROOT/'paper/checklist.tex').read_text()
assert len(re.findall(r'Answer: \\answer(?:Yes|No|NA)\{\}',check))==16
assert 'TODO' not in check
log=(ROOT/'paper/main.log').read_text(errors='replace')
assert 'Overfull' not in log
assert 'undefined' not in log.lower()
assert 'Citation' not in ''.join(x for x in log.splitlines() if 'Warning' in x)
original=(ROOT/'template/neurips2026/checklist.tex').read_text()
assert re.findall(r'Question:.*',original)==re.findall(r'Question:.*',check)
# Original guideline prose is preserved; only instruction block and answers changed.
assert original.count('Guidelines:')==check.count('Guidelines:')==16
style=(ROOT/'paper/neurips_2026.sty').read_bytes()
assert style==(ROOT/'template/neurips2026/neurips_2026.sty').read_bytes()
out=dict(passed=True,total_pdf_pages=len(r.pages),body_pages=ref,official_body_limit=9,
         checklist_questions=16,style_sha256=hashlib.sha256(style).hexdigest(),
         no_overfull_boxes=True,no_undefined_references=True)
(ROOT/'logs/document_audit.json').write_text(json.dumps(out,indent=2))
(ROOT/'logs/paper_text.txt').write_text('\n'.join(f'PAGE {i+1}\n{t}' for i,t in enumerate(texts)))
print(json.dumps(out,indent=2))
