"""Local, offline PDF text extraction aid (not an experiment implementation).
Approximate layout; used only on the five allowlisted PDFs. No networking.
"""
import re, zlib, sys
from pathlib import Path

TOK = re.compile(rb'\s+|%[^\r\n]*|/[A-Za-z0-9_.+\-]+|[+-]?(?:\d+\.\d*|\.\d+|\d+)|[A-Za-z*\'"]+|\[|\]|<[^<>]*>|\((?:\\.|[^()\\]|\((?:\\.|[^()\\])*\))*\)', re.S)

def stream(obj):
    m = re.search(rb'stream\r?\n',obj)
    if not m: return b''
    data=obj[m.end():obj.rfind(b'endstream')]
    return zlib.decompress(data) if b'/FlateDecode' in obj[:m.start()] else data

def unstring(t):
    if t[:1]==b'<':
        h=re.sub(rb'\s',b'',t[1:-1]); return bytes.fromhex((h+b'0'*(len(h)%2)).decode())
    t=t[1:-1]; out=bytearray(); i=0
    while i<len(t):
        if t[i]!=92: out.append(t[i]); i+=1; continue
        i+=1
        if i>=len(t):break
        if 48<=t[i]<=55:
            m=re.match(rb'[0-7]{1,3}',t[i:]); out.append(int(m[0],8)); i+=len(m[0])
        elif t[i] in (10,13):
            if t[i]==13 and i+1<len(t) and t[i+1]==10:i+=1
            i+=1
        else:
            out.append({110:10,114:13,116:9,98:8,102:12}.get(t[i],t[i])); i+=1
    return bytes(out)

class PDF:
    def __init__(self,path):
        data=Path(path).read_bytes()
        self.o={int(m[1]):m[2] for m in re.finditer(rb'(\d+)\s+\d+\s+obj\b(.*?)endobj',data,re.S)}
        for obj in list(self.o.values()):
            if re.search(rb'/Type\s*/ObjStm\b',obj):
                s=stream(obj); first=int(re.search(rb'/First\s+(\d+)',obj)[1]); n=int(re.search(rb'/N\s+(\d+)',obj)[1]); idx=list(map(int,s[:first].split()))
                for i in range(n):self.o[idx[2*i]]=s[first+idx[2*i+1]:first+(idx[2*i+3] if i+1<n else len(s)-first)]
        self.maps={}
        for k,obj in self.o.items():
            m=re.search(rb'/ToUnicode\s+(\d+)\s+\d+\s+R',obj)
            if not m:continue
            s=stream(self.o[int(m[1])]); mp={}
            for block in re.findall(rb'beginbfchar(.*?)endbfchar',s,re.S):
                for a,b in re.findall(rb'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>',block):
                    mp[bytes.fromhex(a.decode())]=bytes.fromhex(b.decode()).decode('utf-16-be',errors='replace')
            for block in re.findall(rb'beginbfrange(.*?)endbfrange',s,re.S):
                for a,b,c in re.findall(rb'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*(<[^>]+>|\[[^\]]+\])',block):
                    start,end=int(a,16),int(b,16); width=len(a)//2
                    dest=re.findall(rb'<([0-9A-Fa-f]+)>',c)
                    for j,key in enumerate(range(start,end+1)):
                        v=dest[j] if c.startswith(b'[') else format(int(dest[0],16)+j,'0%dx'%len(dest[0])).encode()
                        mp[key.to_bytes(width,'big')]=bytes.fromhex(v.decode()).decode('utf-16-be',errors='replace')
            self.maps[k]=mp
        catalog=next((v for v in self.o.values() if re.search(rb'/Type\s*/Catalog\b',v)),b'')
        root=int(re.search(rb'/Pages\s+(\d+)\s+\d+\s+R',catalog)[1]); self.pages=[]
        def walk(k,resources=b''):
            obj=self.o[k]; rm=re.search(rb'/Resources\s+(\d+)\s+\d+\s+R',obj)
            if rm: resources=self.o[int(rm[1])]
            elif b'/Resources' in obj:resources=obj[obj.index(b'/Resources'):]
            if re.search(rb'/Type\s*/Page\b',obj):self.pages.append((obj,resources));return
            kids=re.search(rb'/Kids\s*\[(.*?)\]',obj,re.S)
            for ref in re.findall(rb'(\d+)\s+\d+\s+R',kids[1]):walk(int(ref),resources)
        walk(root)
    def page(self,n):
        obj,res=self.pages[n-1]
        fm=re.search(rb'/Font\s+(\d+)\s+\d+\s+R',res)
        fonts=self.o[int(fm[1])] if fm else (re.search(rb'/Font\s*<<(.*?)>>',res,re.S)[1] if re.search(rb'/Font\s*<<(.*?)>>',res,re.S) else b'')
        fdict={name:int(ref) for name,ref in re.findall(rb'/([^\s/]+)\s+(\d+)\s+\d+\s+R',fonts)}
        cm=re.search(rb'/Contents\s*(\[[^\]]*\]|\d+\s+\d+\s+R)',obj,re.S)
        if not cm:return ''
        content=b'\n'.join(stream(self.o[int(k)]) for k in re.findall(rb'(\d+)\s+\d+\s+R',cm[1]))
        args=[]; out=[]; font=None; text=False
        def show(token):
            b=unstring(token); mp=self.maps.get(fdict.get(font),{})
            if mp:
                widths=sorted({len(k) for k in mp},reverse=True); parts=[]; i=0
                while i<len(b):
                    for w in widths:
                        if b[i:i+w] in mp:parts.append(mp[b[i:i+w]]);i+=w;break
                    else:parts.append(chr(b[i]));i+=1
                s=''.join(parts)
            else:s=b.decode('cp1252',errors='replace')
            out.append(s)
        for m in TOK.finditer(content):
            t=m[0]
            if t.isspace() or t.startswith(b'%'):continue
            if t[:1] in (b'/',b'(',b'<',b'[') or t==b']' or re.fullmatch(rb'[+\-\d.]+',t):args.append(t);continue
            if t==b'BT':text=True;out.append('\n')
            elif t==b'ET':text=False;out.append('\n')
            elif t==b'Tf' and len(args)>=2:font=args[-2][1:]
            elif text and t in (b'Tj',b"'",b'"'):
                if t!=b'Tj':out.append('\n')
                for a in args:
                    if a[:1] in (b'(',b'<'):show(a)
            elif text and t==b'TJ':
                for a in args:
                    if a[:1] in (b'(',b'<'):show(a)
                    elif re.fullmatch(rb'-?\d+(?:\.\d+)?',a) and float(a)<-100:out.append(' ')
            elif text and t in (b'Td',b'TD') and len(args)>=2:
                if float(args[-1])!=0:out.append('\n')
            elif text and t in (b'Tm',b'T*'):out.append('\n')
            args=[]
        s=''.join(out)
        return re.sub(r'\n{3,}','\n\n',s)

if __name__=='__main__':
    pdf=PDF(sys.argv[1]); pages=list(map(int,sys.argv[2:])) or [1]
    for p in pages:print(f'\n=== PDF PAGE {p}/{len(pdf.pages)} ===\n'+pdf.page(p))
