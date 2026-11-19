"""Strip saved official HTML to local text without loading links or assets."""
from html.parser import HTMLParser
from pathlib import Path
import re,sys
class Text(HTMLParser):
    def __init__(self): super().__init__(); self.out=[]; self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style'):self.skip+=1
        if tag in ('p','div','li','h1','h2','h3','h4','br','tr'):self.out.append('\n')
    def handle_endtag(self,tag):
        if tag in ('script','style'):self.skip=max(0,self.skip-1)
        if tag in ('p','div','li','h1','h2','h3','h4','tr'):self.out.append('\n')
    def handle_data(self,data):
        if not self.skip:self.out.append(data)
for arg in sys.argv[1:]:
    p=Path(arg); t=Text();t.feed(p.read_text());s=''.join(t.out);s='\n'.join(' '.join(line.split()) for line in s.splitlines());s=re.sub(r'\n\n+','\n',s);dest=p.with_suffix('.txt');dest.write_text(s);print(dest)
