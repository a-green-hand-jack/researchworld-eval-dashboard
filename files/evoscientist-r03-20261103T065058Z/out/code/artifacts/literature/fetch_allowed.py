#!/usr/bin/env python3
"""Direct exact-ID acquisition only: no discovery APIs, search, or link traversal."""
import datetime, hashlib, json, re, time
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse, urljoin
import requests
from pypdf import PdfReader

ROOT = Path('/work/artifacts/literature')
ROOT.mkdir(parents=True, exist_ok=True)
IDS = ['2210.07316','2402.14992','2407.12844','2407.13696','2405.10938','2412.06540']
class Meta(HTMLParser):
    def __init__(self): super().__init__(); self.meta={}
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=='meta' and a.get('name','').startswith('citation_'):
            self.meta.setdefault(a['name'],[]).append(a.get('content',''))

def fetch(url, out):
    original=url
    for _ in range(4):
        parsed=urlparse(url)
        assert parsed.hostname in {'arxiv.org','export.arxiv.org'}
        assert re.fullmatch(r'/(abs|pdf)/('+'|'.join(re.escape(i) for i in IDS)+r')v1(?:\.pdf)?', parsed.path)
        assert not parsed.query
        t=datetime.datetime.now(datetime.timezone.utc).isoformat()
        try:
            r=requests.get(url, timeout=90, allow_redirects=False, headers={'User-Agent':'RestrictedLiteratureReader/1.0 (exact arXiv IDs only)'})
            row={'utc':t,'requested_url':url,'original_url':original,'status':r.status_code,'content_type':r.headers.get('content-type'),'location':r.headers.get('location')}
            if r.status_code==200:
                out.write_bytes(r.content)
                row.update(file=str(out),bytes=len(r.content),sha256=hashlib.sha256(r.content).hexdigest())
            with (ROOT/'access_log.jsonl').open('a') as f: f.write(json.dumps(row)+'\n')
            if r.is_redirect:
                url=urljoin(url,r.headers['location']); time.sleep(3); continue
            r.raise_for_status(); return r
        except Exception as e:
            with (ROOT/'access_log.jsonl').open('a') as f: f.write(json.dumps({'utc':t,'requested_url':url,'error':str(e)})+'\n')
            raise
    raise RuntimeError('Too many redirects')

for aid in IDS:
    d=ROOT/'sources'/aid; d.mkdir(parents=True,exist_ok=True)
    # Freeze original version to avoid silently using later revisions.
    abstract=f'https://arxiv.org/abs/{aid}v1'
    pdf=f'https://arxiv.org/pdf/{aid}v1'
    h=fetch(abstract,d/'abstract_v1.html'); parser=Meta(); parser.feed(h.text)
    (d/'metadata.json').write_text(json.dumps({'arxiv_id':aid,'version':'v1','abstract_url':abstract,'pdf_url':pdf,'citation_meta':parser.meta},ensure_ascii=False,indent=2))
    time.sleep(3)
    fetch(pdf,d/'paper_v1.pdf')
    pages=[]; plain_pages=[]
    for n,p in enumerate(PdfReader(str(d/'paper_v1.pdf')).pages,1):
        marker=f'\n\n===== PDF PAGE {n} =====\n'
        pages.append(marker+(p.extract_text(extraction_mode='layout') or ''))
        plain_pages.append(marker+(p.extract_text() or ''))
    text=''.join(pages); plain=''.join(plain_pages)
    (d/'full_text_v1.txt').write_text(text)
    (d/'plain_text_v1.txt').write_text(plain)
    # Use plain extraction: multi-column layout can hide the reference heading.
    body=re.split(r'(?im)^\s*(?:References|Bibliography)\s*$',plain,maxsplit=1)[0]
    (d/'body_before_references_v1.txt').write_text(body)
    print(aid, json.dumps(parser.meta,ensure_ascii=False), 'pages',len(pages),'body_chars',len(body),flush=True)
    time.sleep(3)
