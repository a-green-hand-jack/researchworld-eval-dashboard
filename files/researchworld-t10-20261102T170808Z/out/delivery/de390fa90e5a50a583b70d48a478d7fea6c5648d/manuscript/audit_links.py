#!/usr/bin/env python3
"""Audit report link destinations locally; does not request external URLs."""
import collections
import hashlib
import json
import importlib.metadata
from pathlib import Path
from urllib.parse import urlsplit
import pymupdf
from pypdf import PdfReader

path = Path('paper.pdf')
doc = pymupdf.open(path)
reader = PdfReader(path)
counts = collections.Counter()
records = []
for i, page in enumerate(doc):
    for link in page.get_links():
        kind = link['kind']
        record = {'source_page': i + 1}
        if kind in (pymupdf.LINK_GOTO, pymupdf.LINK_NAMED):
            assert 0 <= link['page'] < len(doc), link
            if link.get('nameddest'):
                assert link['nameddest'] in reader.named_destinations, link
            record.update(type='internal', destination_page=link['page'] + 1,
                          named_destination=link.get('nameddest'))
        elif kind == pymupdf.LINK_URI:
            uri = urlsplit(link['uri'])
            assert uri.scheme == 'https' and uri.hostname, link
            record.update(type='external_uri', uri=link['uri'])
        elif kind in (pymupdf.LINK_LAUNCH, pymupdf.LINK_GOTOR):
            raise AssertionError(f'Unexpected local/remote file action: {link}')
        else:
            raise AssertionError(f'Unknown link action: {link}')
        counts[record['type']] += 1
        records.append(record)
# Check every raw PDF annotation as well, including actions the renderer may omit.
raw_counts = collections.Counter()
for page in reader.pages:
    for ref in page.get('/Annots', []):
        annot = ref.get_object()
        if annot.get('/Subtype') != '/Link':
            continue
        action = annot.get('/A')
        if action:
            action = action.get_object()
            raw_counts[str(action['/S'])] += 1
            assert action['/S'] in ('/GoTo', '/URI'), action
        else:
            assert '/Dest' in annot, annot
            raw_counts['/Dest'] += 1
assert sum(raw_counts.values()) == len(records)
report = {'tool_versions': {name: importlib.metadata.version(name) for name in ('PyMuPDF', 'pypdf')}, 'pdf': str(path), 'pdf_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'pages': len(doc), 'counts': dict(counts),
          'raw_action_counts': dict(raw_counts), 'launch_or_gotor_actions': 0,
          'external_uri_check': 'HTTPS syntax and hostname only; no network access or availability claim',
          'links': records}
Path('manuscript/link-audit.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: v for k, v in report.items() if k != 'links'}, indent=2))
