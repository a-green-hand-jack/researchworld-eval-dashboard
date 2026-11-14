"""Check a built manuscript; scientific completeness remains a review task."""
from pathlib import Path
import hashlib, json, re
import pymupdf

manifest = json.loads(Path('venue/provenance/source-manifest.json').read_text())
for item in manifest['official_extracted_files']:
    p = Path('venue')/item['path']
    assert hashlib.sha256(p.read_bytes()).hexdigest() == item['sha256'], p
log = Path('paper.log').read_text()
assert 'There were undefined references' not in log
assert 'There were undefined citations' not in log
assert 'Overfull \\hbox' not in log
assert 'Overfull \\vbox' not in log
aux = Path('paper.aux').read_text()
match = re.search(r'\\newlabel\{post-main-start\}\{\{[^}]*\}\{(\d+)\}', aux)
assert match, 'Main-text boundary must be recorded'
# The marker follows clearpage, which flushes all main-text floats.
# It records the first excluded page, so deferred figures count toward the limit.
main_pages = int(match.group(1)) - 1
assert main_pages >= 1
assert main_pages <= 9, f'{main_pages} main-text pages exceed limit 9'
pdf = pymupdf.open('paper.pdf')
for page in pdf:
    assert abs(page.rect.width - 612) < 1 and abs(page.rect.height - 792) < 1
text = '\n'.join(page.get_text() for page in pdf)
for heading in ['AI use statement', 'Ethics statement', 'Reproducibility statement']:
    assert heading.casefold() in text.casefold(), heading
print(json.dumps({'pages':len(pdf),'main_text_end_page':main_pages,'official_assets':'hashes verified','undefined_references':False,'overfull_boxes':False,'paper_size':'US Letter','scientific_completeness':'not certified by this check'},indent=2))
