#!/usr/bin/env python3
"""Offline provenance audit; performs no network requests or reference discovery."""
import datetime, hashlib, importlib.metadata, json, platform, re
from pathlib import Path
from urllib.parse import urlparse
from pypdf import PdfReader
ROOT=Path('/work/artifacts/literature')
IDS={'2210.07316','2402.14992','2407.12844','2407.13696','2405.10938','2412.06540'}
rows=[json.loads(x) for x in (ROOT/'access_log.jsonl').read_text().splitlines() if x.strip()]
requests=[x for x in rows if 'requested_url' in x]
assert len(requests)==12, len(requests)
for x in requests:
    p=urlparse(x['requested_url'])
    assert p.hostname=='arxiv.org'
    assert re.fullmatch(r'/(abs|pdf)/('+'|'.join(re.escape(i) for i in IDS)+r')v1',p.path)
    assert x['status']==200
    f=Path(x['file'])
    assert hashlib.sha256(f.read_bytes()).hexdigest()==x['sha256']
assert {x['requested_url'] for x in requests}=={f'https://arxiv.org/{kind}/{aid}v1' for kind in ['abs','pdf'] for aid in IDS}
papers=[]
for aid in sorted(IDS):
    d=ROOT/'sources'/aid
    reader=PdfReader(str(d/'paper_v1.pdf'))
    front=reader.pages[0].extract_text() or ''
    assert f'arXiv:{aid}v1' in front
    plain=(d/'plain_text_v1.txt').read_text()
    # Repair initial layout-based reading-copy boundaries without more requests.
    match=re.search(r'(?im)^\s*(?:References|Bibliography)\s*$',plain)
    assert match, aid
    body=plain[:match.start()]
    (d/'body_before_references_v1.txt').write_text(body)
    assert not re.search(r'(?im)^\s*(?:References|Bibliography)\s*$',body)
    meta=json.loads((d/'metadata.json').read_text())
    papers.append({'arxiv_id':aid,'version':'v1','pdf_stamp_verified':True,'pages':len(reader.pages),'title':meta['citation_meta']['citation_title'][0],'abstract_url':meta['abstract_url'],'pdf_url':meta['pdf_url'],'reference_heading_plain_line_1based':plain[:match.start()].count('\n')+1})
bib=(ROOT/'references.bib').read_text()
assert set(re.findall(r'eprint\s*=\s*\{([^}]+)\}',bib))==IDS
assert len(re.findall(r'@misc\{',bib))==6
for aid in IDS:
    assert f'https://arxiv.org/abs/{aid}v1' in bib
    assert f'https://arxiv.org/pdf/{aid}v1' in (ROOT/'allowed_literature.md').read_text()
files=[]
for f in sorted(ROOT.rglob('*')):
    if f.is_file() and f.name!='manifest.json':
        files.append({'path':str(f.relative_to(ROOT)),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
manifest={'audit_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'network_requests':len(requests),'all_requests_allowed_exact_v1':True,'papers':papers,'environment':{'python':platform.python_version(),'requests':importlib.metadata.version('requests'),'pypdf':importlib.metadata.version('pypdf')},'files':files}
(ROOT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'requests':len(requests),'papers':len(papers),'bib_entries':6,'total_bytes':sum(x['bytes'] for x in files),'all_allowed':True,'pdf_versions_verified':True,'reference_free_copies_verified':True,'environment':manifest['environment']},indent=2))
