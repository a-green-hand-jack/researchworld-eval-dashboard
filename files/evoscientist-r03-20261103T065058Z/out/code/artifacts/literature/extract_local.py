"""Local-only extraction of permitted-paper bodies; omit bibliography subtrees."""
from html.parser import HTMLParser
import pathlib, re, json, datetime
R=pathlib.Path('/work/artifacts/literature')
IDS=['2210.07316','2402.14992','2407.12844','2407.13696','2405.10938','2412.06540']
VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
class Extract(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.stack=[]; self.out=[]; self.meta=[]; self.headings=[]; self.h=None
    def handle_starttag(self,t,attrs):
        a=dict(attrs); parent=self.stack[-1] if self.stack else {'active':False,'skip':False}
        active=parent['active'] or t=='article'
        skip=parent['skip'] or t in ['script','style','nav','footer'] or 'ltx_bibliography' in a.get('class','') or a.get('id','') in ['bib','bibliography','references']
        state={'active':active,'skip':skip,'tag':t}
        if t=='meta': self.meta.append(a)
        if t=='link' and a.get('rel')=='canonical': self.meta.append(a)
        if active and not skip and t in ['p','div','section','h1','h2','h3','h4','li','tr','br']: self.out.append('\n')
        if active and not skip and t in ['h1','h2','h3','h4']: self.h=[]
        if t not in VOID: self.stack.append(state)
    def handle_endtag(self,t):
        s=self.stack[-1] if self.stack else {'active':False,'skip':True}
        if s['active'] and not s['skip']:
            if t in ['p','div','section','h1','h2','h3','h4','li','tr']: self.out.append('\n')
            if t in ['h1','h2','h3','h4'] and self.h is not None: self.headings.append(''.join(self.h)); self.h=None
        for i in range(len(self.stack)-1,-1,-1):
            if self.stack[i]['tag']==t: self.stack=self.stack[:i]; break
    def handle_data(self,s):
        state=self.stack[-1] if self.stack else {'active':False,'skip':True}
        if state['active'] and not state['skip']:
            self.out.append(s)
            if self.h is not None: self.h.append(s)
class History(HTMLParser):
    def __init__(self): super().__init__(); self.depth=0; self.out=[]
    def handle_starttag(self,t,attrs):
        a=dict(attrs)
        if t=='div' and ('submission-history' in a.get('class','') or self.depth): self.depth+=1
    def handle_endtag(self,t):
        if t=='div' and self.depth:self.depth-=1
    def handle_data(self,s):
        if self.depth:self.out.append(s)
for ident in IDS:
    p=Extract(); p.feed((R/f'{ident}.html.html').read_text())
    text=re.sub(r'\n[ \t]*\n(?:[ \t]*\n)+','\n\n',''.join(p.out))
    out=R/f'{ident}.fullbody_no_references.txt'; out.write_text(text)
    h=History(); h.feed((R/f'{ident}.abs.html').read_text())
    info={'id':ident,'html_document_metadata':p.meta,'headings':p.headings,'arxiv_submission_history':''.join(h.out).strip()}
    (R/f'{ident}.structure.json').write_text(json.dumps(info,ensure_ascii=False,indent=2))
    with (R/'access_log.jsonl').open('a') as f:f.write(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'event':'local_extraction','source':str(R/f'{ident}.html.html'),'path':str(out),'bibliography_subtrees_excluded':True,'characters':len(text)})+'\n')
    print(json.dumps(info,ensure_ascii=False))
