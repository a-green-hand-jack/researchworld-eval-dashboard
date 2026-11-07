import urllib.request,json,pathlib
from html.parser import HTMLParser
class Links(HTMLParser):
    def __init__(self):super().__init__();self.stop=False;self.link=None;self.text=[];self.out=[]
    def handle_starttag(self,t,a):
        a=dict(a)
        if t=='section' and 'ltx_bibliography' in a.get('class',''):self.stop=True
        if t=='a' and not self.stop:self.link=a.get('href','');self.text=[]
    def handle_data(self,d):
        if self.link is not None:self.text.append(d)
    def handle_endtag(self,t):
        if t=='a' and self.link is not None:
            text=''.join(self.text)
            if any(s in self.link.lower() for s in ['github','scaling','stanford.edu/~']) or any(s in text.lower() for s in ['code','project','website']):self.out.append({'text':text,'url':self.link})
            self.link=None
url='https://arxiv.org/html/2405.10938v3'
with urllib.request.urlopen(url,timeout=60) as r:h=r.read().decode()
p=Links();p.feed(h);print(json.dumps(p.out,indent=2));pathlib.Path('/work/artifacts/sources/2405.10938.resource_links.json').write_text(json.dumps({'source_url':url,'links_not_followed':p.out},indent=2))
