"""Measure how accepted NeurIPS main-track papers are laid out.
usage: python3 -I analyze.py PDF_DIR > stats.json
Per PDF: page where the main text ends (first of References/Acknowledgements),
abstract words, introduction words, distinct figure/table captions in the main
text and the number of words of the main text. Heuristic text extraction;
checked by reading three of the papers. Reference counts are not taken from
the PDF text: see refcount.py."""
import pymupdf, re, sys, json, glob, os

END = re.compile(r'^\s*(References|REFERENCES|Acknowledg\w+|ACKNOWLEDG\w+)\s*$', re.M)

def analyze(f):
    doc = pymupdf.open(f)
    pages = [p.get_text() for p in doc]
    end_pg = end_off = None
    for i, t in enumerate(pages):
        m = END.search(t)
        if m:
            end_pg, end_off = i, m.start()
            break
    main = '\n'.join(pages[:end_pg]) + '\n' + pages[end_pg][:end_off]
    flat = re.sub(r'[ \t]*\n[ \t]*', '\n', main)
    ab = re.search(r'Abstract\s*\n(.*?)\n\s*1\s*\n\s*Introduction', flat, re.S | re.I)
    if not ab:
        ab = re.search(r'Abstract\s*\n(.*?)\n\s*1\s+Introduction', flat, re.S | re.I)
    abs_txt = None
    if ab:
        lines = []
        for ln in ab.group(1).split('\n'):
            if len(ln.strip()) <= 3:   # figure debris or the section number
                break
            lines.append(ln)
        abs_txt = ' '.join(lines)
    intro = re.search(r'\n\s*1\s*\n\s*Introduction\s*\n(.*?)\n\s*2\s*\n\s*[A-Z]', flat, re.S)
    if not intro:
        intro = re.search(r'\n\s*1\s+Introduction\s*\n(.*?)\n\s*2\s+[A-Z]', flat, re.S)
    figs = {int(x) for x in re.findall(r'^(?:Figure|Fig\.)\s*(\d+)\s*[:.]', flat, re.M)}
    tabs = {int(x) for x in re.findall(r'^Table\s*(\d+)\s*[:.]', flat, re.M)}
    # page of the end of the main text, counted from the title page
    return dict(file=os.path.basename(f),
                title=' '.join(pages[0].strip().split('\n')[:2]),
                total_pages=len(pages),
                main_text_ends_on_page=end_pg + 1,
                abstract_words=len(abs_txt.split()) if abs_txt else None,
                intro_words=len(intro.group(1).split()) if intro else None,
                n_figures_main=len(figs), n_tables_main=len(tabs))

if __name__ == '__main__':
    print(json.dumps([analyze(f) for f in sorted(glob.glob(os.path.join(sys.argv[1], '*.pdf')))], indent=1, ensure_ascii=False))
