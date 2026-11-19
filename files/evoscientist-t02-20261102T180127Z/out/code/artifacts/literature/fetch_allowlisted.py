"""Fetch only explicitly allowlisted source documents; never traverse links."""
import concurrent.futures
import datetime as dt
import hashlib
import json
from pathlib import Path
import urllib.request
import urllib.error

ROOT = Path('/work/artifacts/literature')
IDS = ['2201.02177','2301.05217','2210.01117','2309.02390','2310.06110','2303.06173','1711.05101']

def fetch(item):
    ident, kind = item
    url = f'https://arxiv.org/{kind}/{ident}'
    path = ROOT / f'{ident}.{ "pdf" if kind == "pdf" else "abs.html"}'
    record = {'requested_url': url, 'download_started_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'path': str(path)}
    try:
        req = urllib.request.Request(url, headers={'User-Agent':'IndependentResearchSupport/1.0 (direct allowlisted documents only)'})
        with urllib.request.urlopen(req, timeout=90) as response:
            data = response.read()
            record.update(final_url=response.url, status=response.status, headers=dict(response.headers))
        path.write_bytes(data)
        record.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), download_completed_utc=dt.datetime.now(dt.timezone.utc).isoformat())
        if kind == 'pdf':
            if not data.startswith(b'%PDF'):
                raise ValueError('Response is not PDF')
            from pypdf import PdfReader
            reader = PdfReader(path)
            text_path = ROOT / f'{ident}.txt'
            text_path.write_text('\n\n'.join(f'===== PAGE {i+1} =====\n'+page.extract_text() for i,page in enumerate(reader.pages)))
            record.update(pages=len(reader.pages), text_path=str(text_path))
    except Exception as e:
        record['error'] = repr(e)
    return record

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    records = list(pool.map(fetch, [(i,k) for i in IDS for k in ['abs','pdf']]))
(ROOT / 'download_manifest.json').write_text(json.dumps(records, indent=2))
for r in records:
    print(r['requested_url'], r.get('status'), r.get('bytes'), r.get('pages'), r.get('error',''))
