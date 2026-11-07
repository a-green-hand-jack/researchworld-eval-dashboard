"""Check page-limit compliance and final manuscript/build integrity."""
from pathlib import Path
import hashlib,json,re
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]

def main():
    paper=ROOT/'paper';r=PdfReader(paper/'main.pdf')
    pages=[p.extract_text() for p in r.pages]
    refs=next(i for i,t in enumerate(pages) if re.match(r'^References\s*\d*',t))
    assert refs<=9,f'Main text exceeds NeurIPS nine-page limit: {refs}'
    assert 'NeurIPS Paper Checklist' in '\n'.join(pages)
    checklist=(paper/'checklist_filled.tex').read_text()
    assert not re.search(r'\\(?:answer|justification)TODO',checklist)
    # Exactly the official questions and guidelines are retained.
    original=(paper/'vendor/checklist.tex').read_text()
    for question in re.findall(r'Question:(.*?)\\item\[\] Answer:',original,re.S):
        assert question in checklist
    assert (paper/'neurips_2026.sty').read_bytes()==(paper/'vendor/neurips_2026.sty').read_bytes()
    log=(paper/'main.log').read_text()
    assert 'undefined references' not in log
    assert 'undefined citations' not in log
    assert 'Overfull \\hbox' not in log
    assert 'Overfull \\vbox' not in log
    result=dict(pdf_pages=len(pages),main_text_pages=refs,main_limit=9,
        checklist_answers=len(re.findall(r'Answer: \\answer(?:Yes|No|NA)',checklist)),
        style_unmodified=True,pdf_sha256=hashlib.sha256((paper/'main.pdf').read_bytes()).hexdigest())
    assert result['checklist_answers']==16
    (ROOT/'results/pdf_check.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
