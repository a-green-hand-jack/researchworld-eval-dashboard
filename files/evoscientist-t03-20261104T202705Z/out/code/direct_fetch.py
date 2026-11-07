"""Direct URL retrieval only; no search, crawling, recommendations, or experiments."""
import sys, os, json, hashlib, datetime, urllib.request, urllib.error
from html.parser import HTMLParser
ROOT='/work'
class Parser(HTMLParser):
    def __init__(self): super().__init__(); self.skip=0; self.text=[]; self.links=[]
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if tag in ('script','style'): self.skip+=1
        if tag=='a' and 'href' in d: self.links.append(d['href'])
        if tag in ('p','div','br','h1','h2','h3','li','tr','section'): self.text.append('\n')
    def handle_endtag(self,tag):
        if tag in ('script','style') and self.skip: self.skip-=1
    def handle_data(self,s):
        if not self.skip: self.text.append(s)
def fetch(url, dest):
    os.makedirs(os.path.dirname(dest),exist_ok=True)
    record={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'requested_url':url,'local_path':dest}
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'DirectSourceAcquisition/1.0'})
        with urllib.request.urlopen(req,timeout=55) as r:
            data=r.read(); record.update(status=r.status,final_url=r.url,content_type=r.headers.get('Content-Type',''))
        open(dest,'wb').write(data)
        record.update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
        if 'html' in record['content_type'] or dest.endswith('.html'):
            p=Parser(); p.feed(data.decode('utf-8',errors='replace'))
            lines=[s.strip() for s in ''.join(p.text).splitlines() if s.strip()]
            open(dest+'.txt','w').write('\n'.join(lines))
            open(dest+'.links.json','w').write(json.dumps(p.links,indent=2))
    except Exception as e:
        record.update(error=str(e),status=getattr(e,'code',None))
    with open(ROOT+'/access_log.jsonl','a') as f: f.write(json.dumps(record)+'\n')
    print(json.dumps(record))
if __name__=='__main__': fetch(sys.argv[1],sys.argv[2])
