"""Build paper with official style; verify content page cap and checklist."""
from pathlib import Path
import subprocess,sys,json,hashlib,re
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parent

def main():
    commands=[[sys.executable,'prepare_checklist.py'],[sys.executable,'render_paper_tables.py'],[sys.executable,'make_failure_example.py'],
              ['pdflatex','-interaction=nonstopmode','-halt-on-error','paper.tex'],['bibtex','paper'],
              ['pdflatex','-interaction=nonstopmode','-halt-on-error','paper.tex'],['pdflatex','-interaction=nonstopmode','-halt-on-error','paper.tex']]
    with (ROOT/'build.log').open('w') as log:
        for cmd in commands:
            log.write('$ '+' '.join(cmd)+'\n');log.flush()
            done=subprocess.run(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
            if done.returncode: raise RuntimeError(f'Build failed: {cmd}; see build.log')
    reader=PdfReader(ROOT/'paper.pdf');texts=[p.extract_text() or '' for p in reader.pages]
    # Bibliography starts on its own page immediately after main content.
    refs=[i+1 for i,t in enumerate(texts) if re.search(r'(?:^|\n)References\d*(?:\s*\n|$)',t)]
    if not refs: raise RuntimeError('Cannot locate References page')
    main_pages=refs[0]-1
    check_pages=[i+1 for i,t in enumerate(texts) if 'NeurIPS Paper Checklist' in t]
    logtext=(ROOT/'paper.log').read_text(errors='replace')
    unresolved=('There were undefined references' in logtext or 'undefined citations' in logtext)
    stylehash=hashlib.sha256((ROOT/'template/neurips_2026.sty').read_bytes()).hexdigest()
    report={'pdf':'paper.pdf','pdf_bytes':(ROOT/'paper.pdf').stat().st_size,'total_pages':len(reader.pages),'main_content_pages':main_pages,
            'main_page_limit':9,'references_start_page':refs[0],'checklist_start_pages':check_pages,'official_style_sha256':stylehash,
            'style_matches_official':stylehash=='c3fc2894e83d2517ca18b66741d6c595986d97957dc08ec08bb2125a7ec4555a',
            'undefined_references':unresolved,'overfull_boxes':logtext.count('Overfull \\hbox'),
            'checklist_answers':len(re.findall(r'Answer: \\answer(?:Yes|No|NA)\{\}',(ROOT/'checklist_filled.tex').read_text()))}
    assert main_pages<=9 and check_pages and not unresolved and report['style_matches_official'] and report['checklist_answers']==16 and report['pdf_bytes']<50_000_000,report
    (ROOT/'build_validation.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
