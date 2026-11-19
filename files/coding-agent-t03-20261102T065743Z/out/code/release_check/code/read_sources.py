"""Re-fetch ONLY the explicitly permitted, pinned original literature sources.
No topic search, citation traversal, recommendation page, or third-party mirror.
Read RESEARCH_LOG.md before adding any source.
"""
from common import ROOT
import json,hashlib,requests
from pypdf import PdfReader
for row in json.loads((ROOT/'literature/manifest.json').read_text()):
 p=ROOT/row['file']
 if not p.exists():
  r=requests.get(row['url'],timeout=90);r.raise_for_status();p.write_bytes(r.content)
 assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'],f"Source changed: {row['url']}"
 p.with_suffix('.txt').write_text('\n'.join(page.extract_text() for page in PdfReader(p).pages))
 print(row['key'],row['url'])
