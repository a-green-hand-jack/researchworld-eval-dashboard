#!/usr/bin/env python3
"""Independent exact-revision PDF repair check; no network requests."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit
import pymupdf
from pypdf import PdfReader

p = argparse.ArgumentParser()
p.add_argument('directory', type=Path)
p.add_argument('output', type=Path)
p.add_argument('--head', required=True)
a = p.parse_args()
root = a.directory
old = pymupdf.open(root / 'previous.pdf')
new = pymupdf.open(root / 'delivered.pdf')
rebuilt = pymupdf.open(root / 'rebuilt.pdf')
assert len(old) == len(new) == len(rebuilt) == 36
same = []
rebuilt_same = []
for i in range(36):
    assert old[i].get_text() == new[i].get_text()
    assert old[i].get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5)).samples == new[i].get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5)).samples
    assert rebuilt[i].get_text() == new[i].get_text()
    assert rebuilt[i].get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5)).samples == new[i].get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5)).samples
    same.append(i+1)
    rebuilt_same.append(i+1)
reader = PdfReader(root / 'delivered.pdf')
counts = collections.Counter()
uris = []
for page in reader.pages:
    for ref in page.get('/Annots', []):
        item = ref.get_object()
        if item.get('/Subtype') != '/Link':
            continue
        action = item['/A'].get_object()
        kind = str(action['/S'])
        counts[kind] += 1
        assert kind in ('/GoTo', '/URI'), action
        if kind == '/GoTo':
            dest = action['/D']
            assert str(dest) in reader.named_destinations
            dest_page = reader.get_destination_page_number(reader.named_destinations[str(dest)])
            assert 0 <= dest_page < len(reader.pages)
        else:
            uri = str(action['/URI'])
            parsed = urlsplit(uri)
            assert parsed.scheme == 'https' and parsed.hostname
            uris.append(uri)
assert dict(counts) == {'/GoTo': 40, '/URI': 5}
assert len([link for page in new for link in page.get_links()]) == 45
old_launch = [dict(page=i+1, **link) for i,page in enumerate(old) for link in page.get_links() if link['kind'] == pymupdf.LINK_LAUNCH]
assert len(old_launch) == 1 and old_launch[0]['file'] == 'paperswithcode.com/datasets'
assert not [link for page in new for link in page.get_links() if link['kind'] in (pymupdf.LINK_LAUNCH, pymupdf.LINK_GOTOR)]
report = dict(status='pass', inspected_head=a.head, pdf_sha256=hashlib.sha256((root / 'delivered.pdf').read_bytes()).hexdigest(), unchanged_page_text_and_pixels=same, independent_rebuild_page_text_and_pixels=rebuilt_same, raster_scale=1.5, raw_link_action_counts=dict(counts), all_internal_named_destinations_resolve=True, external_uris=uris, external_validation='HTTPS syntax/hostname only; no network request', launch_or_gotor_actions=0)
a.output.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('unchanged_page_text_and_pixels', 'independent_rebuild_page_text_and_pixels')}, indent=2))
for f in sorted((root/'figures').glob('*.pdf')):
    doc=pymupdf.open(f)
    doc[0].get_pixmap(matrix=pymupdf.Matrix(1.8,1.8)).save(root/(f.stem+'-check.png'))
new[34].get_pixmap(matrix=pymupdf.Matrix(1.6,1.6)).save(root/'page35-check.png')
