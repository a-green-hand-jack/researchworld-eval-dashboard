#!/usr/bin/env python3
"""Render every actual paper page for manual inspection; validate link targets."""
import hashlib
import json
from pathlib import Path
import argparse
import pymupdf
from PIL import Image, ImageDraw

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--pdf', default='paper.pdf')
p.add_argument('--output', required=True)
p.add_argument('--dpi', type=int, default=96)
a = p.parse_args()
out = Path(a.output)
out.mkdir(parents=True, exist_ok=True)
def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
doc = pymupdf.open(a.pdf)
links, bad, pages = [], [], []
for n, page in enumerate(doc, 1):
    path = out / f'page-{n:02d}.png'
    page.get_pixmap(dpi=a.dpi, alpha=False).save(path)
    pages.append(dict(page=n, proof_sha256=sha(path)))
    for link in page.get_links():
        item = dict(page=n, kind=link['kind'], uri=link.get('uri'),
                    target_page=link.get('page'))
        links.append(item)
        if link['kind'] == pymupdf.LINK_GOTO and not 0 <= link.get('page', -1) < len(doc):
            bad.append(item)
for start in range(0, len(doc), 4):
    sheet = Image.new('RGB', (1224, 1644), 'white')
    draw = ImageDraw.Draw(sheet)
    for j, n in enumerate(range(start, min(start + 4, len(doc)))):
        im = Image.open(out / f'page-{n + 1:02d}.png')
        im.thumbnail((612, 792))
        x, y = j % 2 * 612, j // 2 * 822
        sheet.paste(im, (x, y + 30))
        draw.text((x + 10, y + 8), f'PDF page {n + 1}', fill='black')
    sheet.save(out / f'contact-{start // 4 + 1}.png')
facts = dict(document=a.pdf, document_sha256=sha(a.pdf), dpi=a.dpi,
             page_count=len(doc), pages=pages, generator_sha256=sha(__file__),
             limitations='Rendering facts only; actual manual inspection is separate.')
(out / 'facts.json').write_text(json.dumps(facts, indent=2) + '\n')
report = dict(pdf_sha256=sha(a.pdf), pages=len(doc), link_count=len(links),
              uris=sorted({l['uri'] for l in links if l['uri']}),
              invalid_internal_destinations=bad, external_urls_requested=False)
Path('build/link-audit.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
if bad:
    raise SystemExit('Invalid internal PDF destinations')
