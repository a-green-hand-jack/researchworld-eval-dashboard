"""Local-only PDF text extraction; standard library, no network or statistics."""
import re, zlib, pathlib, sys

def tokens(b):
    i=0
    while i<len(b):
        c=b[i]
        if c in b' \t\r\n\x00\x0c': i+=1; continue
        if c==37:
            j=b.find(b'\n',i); i=len(b) if j<0 else j+1; continue
        if b[i:i+2] in (b'<<',b'>>'):
            yield b[i:i+2].decode(); i+=2; continue
        if c==40:
            i+=1; depth=1; out=bytearray()
            while depth and i<len(b):
                c=b[i]; i+=1
                if c==92:
                    if i>=len(b): break
                    c=b[i]; i+=1
                    if c in b'01234567':
                        s=bytes([c])
                        while i<len(b) and len(s)<3 and b[i] in b'01234567': s+=b[i:i+1]; i+=1
                        out.append(int(s,8)); continue
                    if c in b'\r\n':
                        if c==13 and i<len(b) and b[i]==10:i+=1
                        continue
                    out.append({110:10,114:13,116:9,98:8,102:12}.get(c,c)); continue
                if c==40: depth+=1
                if c==41: depth-=1
                if depth:out.append(c)
            yield bytes(out); continue
        if c==60:
            j=b.find(b'>',i+1); h=re.sub(rb'\s',b'',b[i+1:j]); h+=b'0' if len(h)%2 else b''
            yield bytes.fromhex(h.decode()); i=j+1; continue
        if c in b'[]{}': yield chr(c); i+=1; continue
        j=i+1
        while j<len(b) and b[j] not in b' \t\r\n\x00\x0c()<>[]{}/%':j+=1
        s=b[i:j].decode('latin1');i=j
        if re.fullmatch(r'[+-]?(?:\d+\.?\d*|\.\d+)',s):yield float(s) if '.' in s else int(s)
        else:yield s

def parse(ts,i=0):
    x=ts[i]
    if x=='<<':
        d={};i+=1
        while ts[i]!='>>':
            k=ts[i];v,i=parse(ts,i+1);d[k]=v
        return d,i+1
    if x=='[':
        a=[];i+=1
        while ts[i]!=']':v,i=parse(ts,i);a.append(v)
        return a,i+1
    if isinstance(x,int) and i+2<len(ts) and isinstance(ts[i+1],int) and ts[i+2]=='R':return ('ref',x),i+3
    return x,i+1

class PDF:
    def __init__(self,path):
        self.obj={};self.stream={}
        for m in re.finditer(rb'(\d+)\s+\d+\s+obj\b(.*?)endobj',path.read_bytes(),re.S):
            n=int(m[1]); raw=m[2]; sm=re.search(rb'\bstream\r?\n(.*?)\r?\n?endstream',raw,re.S)
            try:self.obj[n]=parse(list(tokens(raw[:sm.start()] if sm else raw)))[0]
            except Exception:continue
            if sm:
                data=sm[1]
                if isinstance(self.obj[n],dict) and self.obj[n].get('/Filter')=='/FlateDecode':
                    try:data=zlib.decompress(data)
                    except zlib.error:continue
                self.stream[n]=data
        for n,d in list(self.obj.items()):
            if isinstance(d,dict) and d.get('/Type')=='/ObjStm':
                b=self.stream[n]; first=d['/First']; h=list(map(int,b[:first].split()))
                for j in range(0,len(h),2):
                    start=first+h[j+1]; end=first+h[j+3] if j+3<len(h) else len(b)
                    try:self.obj[h[j]]=parse(list(tokens(b[start:end])))[0]
                    except Exception:pass
        self.maps={}
    def resolve(self,x):
        return self.obj.get(x[1],{}) if isinstance(x,tuple) and x[0]=='ref' else x
    def cmap(self,font):
        if font in self.maps:return self.maps[font]
        d=self.obj[font]; ref=d.get('/ToUnicode'); mp={}
        if ref and ref[1] in self.stream:
            b=self.stream[ref[1]]
            for section in re.findall(rb'beginbfchar(.*?)endbfchar',b,re.S):
                for a,v in re.findall(rb'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>',section):
                    try:mp[bytes.fromhex(a.decode())]=bytes.fromhex(v.decode()).decode('utf-16-be')
                    except Exception:pass
            for section in re.findall(rb'beginbfrange(.*?)endbfrange',b,re.S):
                for a,e,v in re.findall(rb'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>',section):
                    start,end=int(a,16),int(e,16);base=int(v,16);width=len(a)//2
                    for k in range(end-start+1):
                        try:mp[(start+k).to_bytes(width,'big')]=(base+k).to_bytes(len(v)//2,'big').decode('utf-16-be')
                        except Exception:pass
        self.maps[font]=mp;return mp
    def text(self,b,fonts):
        ts=list(tokens(b));stack=[];out=[];font=None;last_y=None
        def dec(s):
            mp=self.cmap(font) if font in self.obj else {}
            if not mp:return s.decode('latin1')
            widths=sorted({len(k) for k in mp},reverse=True); parts=[];i=0
            while i<len(s):
                for w in widths:
                    if s[i:i+w] in mp:parts.append(mp[s[i:i+w]]);i+=w;break
                else:parts.append(chr(s[i]));i+=1
            return ''.join(parts)
        for t in ts:
            if isinstance(t,str) and not t.startswith('/') and t not in ('[',']'):
                if t=='Tf' and len(stack)>=2:
                    ref=fonts.get(stack[-2]);font=ref[1] if isinstance(ref,tuple) else None
                elif t=='Tj' and stack and isinstance(stack[-1],bytes):out.append(dec(stack[-1]))
                elif t=='TJ':
                    for s in stack:
                        if isinstance(s,bytes):out.append(dec(s))
                        elif isinstance(s,(int,float)) and s < -100:out.append(' ')
                elif t in ('Td','TD') and len(stack)>=2:
                    if abs(stack[-1])>1:out.append('\n')
                elif t=='Tm' and len(stack)>=6:
                    y=stack[-1]
                    if last_y is not None and abs(y-last_y)>3:out.append('\n')
                    last_y=y
                elif t in ('ET','T*'):out.append('\n')
                stack=[]
            else:stack.append(t)
        return ''.join(out)
    def pages(self):
        cats=[d for d in self.obj.values() if isinstance(d,dict) and d.get('/Type')=='/Catalog']
        def walk(ref,resources=None):
            d=self.resolve(ref);resources=d.get('/Resources',resources)
            if d.get('/Type')=='/Page':yield d,resources
            else:
                for k in d.get('/Kids',[]):yield from walk(k,resources)
        yield from walk(cats[0]['/Pages'])
    def extract(self):
        out=[]
        for p,(d,r) in enumerate(self.pages(),1):
            res=self.resolve(r) or {}; fonts=self.resolve(res.get('/Font',{}));cs=d.get('/Contents',[])
            if isinstance(cs,tuple):cs=[cs]
            body='\n'.join(self.text(self.stream.get(c[1],b''),fonts) for c in cs)
            out.append(f'\n\n===== PDF PAGE {p} =====\n'+body)
        return ''.join(out)

for arg in sys.argv[1:]:
    path=pathlib.Path(arg); pdf=PDF(path);text=pdf.extract();dest=path.with_suffix('.txt');dest.write_text(text)
    print(path.name,'pages',text.count('===== PDF PAGE'),'chars',len(text),'->',dest)
