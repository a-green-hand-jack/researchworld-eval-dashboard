"""Direct-only source retrieval; no discovery, references, or related-paper calls."""
import datetime, hashlib, json, pathlib, time, urllib.request, urllib.error
from html.parser import HTMLParser
ROOT=pathlib.Path('/work'); (ROOT/'sources').mkdir(parents=True,exist_ok=True)
class Meta(HTMLParser):
    def __init__(self): super().__init__(); self.meta={}; self.in_abs=False; self.depth=0; self.abstract=[]; self.in_history=False; self.history=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='meta': self.meta.setdefault(a.get('name',a.get('property','')),[]).append(a.get('content',''))
        if tag=='blockquote' and 'abstract' in a.get('class',''): self.in_abs=True
        if tag=='div' and 'submission-history' in a.get('class',''): self.in_history=True
    def handle_endtag(self,tag):
        if tag=='blockquote': self.in_abs=False
        if tag=='div': self.in_history=False
    def handle_data(self,data):
        if self.in_abs:self.abstract.append(data)
        if self.in_history:self.history.append(data)
def fetch(url,path):
    rec={'requested_url':url,'accessed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'SourceVerification/1.0 (direct allowlisted retrieval)'})
        with urllib.request.urlopen(req,timeout=45) as r:
            data=r.read();rec.update(status=r.status,final_url=r.url,content_type=r.headers.get('Content-Type'),headers=dict(r.headers))
        path.write_bytes(data); rec.update(path=str(path),bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
        if 'html' in (rec['content_type'] or ''):
            p=Meta();p.feed(data.decode('utf-8','replace'));rec.update(metadata=p.meta,abstract=' '.join(' '.join(p.abstract).split()),history=' '.join(' '.join(p.history).split()))
    except Exception as e:rec['error']=str(e)
    return rec
if __name__=='__main__':
    ids=['2406.01574','2405.17202','2402.09723','1411.2664','1502.04585','1212.6906','2310.11324']
    records=[]
    for ident in ids:
        r=fetch('https://arxiv.org/abs/'+ident,ROOT/'sources'/f'{ident}.html'); records.append(r)
        if 'error' in r:
            time.sleep(3);records.append(fetch('https://arxiv.org/pdf/'+ident,ROOT/'sources'/f'{ident}.pdf'))
        (ROOT/'retrieval.json').write_text(json.dumps(records,indent=2))
        print(json.dumps({k:v for k,v in r.items() if k in ['requested_url','error','status','metadata','abstract','history']},ensure_ascii=False),flush=True)
        time.sleep(3)
    r=fetch('https://doi.org/10.1214/12-AOS1077',ROOT/'sources'/'12-AOS1077.html');records.append(r)
    (ROOT/'retrieval.json').write_text(json.dumps(records,indent=2))
    print(json.dumps({k:v for k,v in r.items() if k in ['requested_url','final_url','error','status','metadata','abstract']},ensure_ascii=False),flush=True)
