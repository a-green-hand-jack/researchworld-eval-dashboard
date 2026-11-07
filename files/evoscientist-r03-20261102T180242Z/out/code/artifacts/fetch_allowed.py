import urllib.request, urllib.error, json, pathlib, time
from html.parser import HTMLParser
ROOT=pathlib.Path('/work/artifacts/sources')
IDS=['2210.07316','2402.14992','2407.12844','2405.10938','2412.06540']
class MainParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.stack=[]; self.out=[]; self.stopped=False; self.stop_reason=None; self.meta=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs); cls=a.get('class',''); ident=a.get('id','')
        if tag=='meta' and a.get('name','').startswith('citation_'): self.meta.append(a)
        if tag=='section' and ('ltx_bibliography' in cls or ident.lower() in ['bib','references']):
            self.stopped=True; self.stop_reason='bibliography boundary: '+ident
        suppressed=(self.stack[-1][1] if self.stack else False) or tag in ['script','style','nav','footer'] or 'ltx_bib' in cls or 'ltx_ref' in cls or 'ltx_note' in cls
        if tag not in ['meta','link','img','br','hr','input','source','wbr']: self.stack.append((tag,suppressed))
        if not self.stopped and not suppressed and tag in ['p','div','section','h1','h2','h3','h4','table','tr','li','figure','figcaption']: self.out.append('\n')
    def handle_endtag(self,tag):
        for i in range(len(self.stack)-1,-1,-1):
            if self.stack[i][0]==tag:
                self.stack=self.stack[:i]; break
        if not self.stopped and tag in ['p','h1','h2','h3','h4','tr','li','figcaption']: self.out.append('\n')
    def handle_data(self,data):
        if not self.stopped and not (self.stack and self.stack[-1][1]): self.out.append(data)

def fetch(url):
    req=urllib.request.Request(url, headers={'User-Agent':'Allowed-source-reader/1.0'})
    opener=urllib.request.build_opener(NoRedirect)
    with opener.open(req,timeout=55) as r: return r.read().decode('utf-8'),r.geturl(),r.status
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl): return None
ledger=[]
for ident in IDS:
    url='https://arxiv.org/html/'+ident
    try:
        text,final,status=fetch(url); p=MainParser(); p.feed(text)
        out='\n'.join(line.strip() for line in ''.join(p.out).splitlines() if line.strip())
        (ROOT/(ident+'.main.txt')).write_text(out)
        item={'id':ident,'url':url,'status':status,'final_url':final,'chars':len(out),'boundary':p.stop_reason,'metadata':p.meta,'main_text_file':str(ROOT/(ident+'.main.txt'))}
        print(ident,status,len(out),'boundary',p.stop_reason)
    except Exception as e:
        item={'id':ident,'url':url,'error':str(e)}; print(ident,str(e))
    ledger.append(item); (ROOT/'paper_access.json').write_text(json.dumps(ledger,indent=2)); time.sleep(3)
