"""Offline, limited PDF text reader for these downloaded PDFs, not a general parser.
Handles Flate streams, compressed objects, page-tree ordering, literal strings,
TJ word spacing, and common ToUnicode CMaps. Does not reconstruct figures/math.
No network access and no experimental code.
"""
from pathlib import Path
import re, zlib, sys

def stream(body):
    m = re.search(rb'stream\r?\n(.*?)\r?\n?endstream', body, re.S)
    if not m: return b''
    b = m[1]
    if b'/FlateDecode' in body[:m.start()]:
        try: b = zlib.decompress(b)
        except zlib.error: return b''
    return b

def objects(data):
    objs = {int(m[1]):m[2] for m in re.finditer(rb'(\d+)\s+\d+\s+obj\b(.*?)endobj',data,re.S)}
    for body in list(objs.values()):
        if not re.search(rb'/Type\s*/ObjStm',body): continue
        s=stream(body); first=int(re.search(rb'/First\s+(\d+)',body)[1]); n=int(re.search(rb'/N\s+(\d+)',body)[1])
        nums=list(map(int,s[:first].split()))
        for i in range(n):
            obj,off=nums[2*i:2*i+2]; end=nums[2*i+3] if i+1<n else len(s)-first
            objs[obj]=s[first+off:first+end]
    return objs

def literal(s):
    b=bytearray(); i=1
    while i<len(s)-1:
        c=s[i]; i+=1
        if c==92:
            c=s[i]; i+=1
            if 48<=c<=55:
                v=bytes([c])
                while i<len(s)-1 and len(v)<3 and 48<=s[i]<=55: v+=s[i:i+1]; i+=1
                b.append(int(v,8)%256)
            elif c in (10,13):
                if c==13 and s[i:i+1]==b'\n':i+=1
            else:b.extend({110:b'\n',114:b'\r',116:b'\t',98:b'\b',102:b'\f'}.get(c,bytes([c])))
        else:b.append(c)
    return bytes(b)

def cmap(s):
    out={}
    for block in re.findall(rb'beginbfchar(.*?)endbfchar',s,re.S):
        for a,b in re.findall(rb'<([0-9a-fA-F]+)>\s*<([0-9a-fA-F]+)>',block):
            try:out[bytes.fromhex(a.decode())]=bytes.fromhex(b.decode()).decode('utf-16-be')
            except (ValueError,UnicodeError):pass
    for block in re.findall(rb'beginbfrange(.*?)endbfrange',s,re.S):
        for a,b,c in re.findall(rb'<([0-9a-fA-F]+)>\s*<([0-9a-fA-F]+)>\s*<([0-9a-fA-F]+)>',block):
            start,end,dst=int(a,16),int(b,16),int(c,16)
            if end-start>4096:continue
            for i in range(end-start+1):
                try:out[(start+i).to_bytes(len(a)//2,'big')]=(dst+i).to_bytes(len(c)//2,'big').decode('utf-16-be')
                except (ValueError,UnicodeError,OverflowError):pass
    return out

TOKEN=re.compile(rb'\((?:\\(?:[0-7]{1,3}|\r\n|.)|[^\\()])*\)|<[0-9a-fA-F\s]+>|/[^\s\[\]<>/()]+|[-+]?(?:\d*\.\d+|\d+)|[A-Za-z*\x27\x22]+|[^\s]',re.S)
def read_content(s,maps):
    out=[]; stack=[]; font=None
    for m in TOKEN.finditer(s.replace(b'[',b' [ ').replace(b']',b' ] ')):
        t=m[0]
        if t==b'Tf':
            if len(stack)>=2:font=stack[-2].decode('latin1')
            stack=[]
        elif t in (b'TJ',b'Tj',b"'",b'"'):
            chunks=[]
            for q in stack:
                if q.startswith(b'(') or (q.startswith(b'<') and not q.startswith(b'<<')):
                    try:raw=literal(q) if q.startswith(b'(') else bytes.fromhex(q[1:-1].decode())
                    except ValueError:continue
                    mp=maps.get(font,{})
                    if mp:
                        widths=sorted({len(k) for k in mp},reverse=True); pos=0; text=''
                        while pos<len(raw):
                            for w in widths:
                                if raw[pos:pos+w] in mp:text+=mp[raw[pos:pos+w]];pos+=w;break
                            else:text+=raw[pos:pos+1].decode('cp1252',errors='replace');pos+=1
                    else:text=raw.decode('cp1252',errors='replace')
                    chunks.append(text)
                else:
                    try:
                        if float(q)<-100:chunks.append(' ')
                    except ValueError:pass
            out.append(''.join(chunks)); stack=[]
        elif t in (b'Td',b'TD',b'Tm',b'T*',b'ET'):
            if t in (b'Tm',b'T*',b'ET') or (len(stack)>=2 and abs(float(stack[-1]))>5):out.append('\n')
            stack=[]
        elif t[:1] in b'/([<' or re.fullmatch(rb'[-+]?(?:\d*\.\d+|\d+)',t) or t==b']':stack.append(t)
        else:stack=[]
    return re.sub(r'\n\s*\n+', '\n', ''.join(out)).strip()

def extract(path):
    objs=objects(path.read_bytes()); maps={}
    for body in objs.values():
        for name,ref in re.findall(rb'(/F\w+)\s+(\d+)\s+0\s+R',body):
            font=objs.get(int(ref),b''); uni=re.search(rb'/ToUnicode\s+(\d+)\s+0\s+R',font)
            if uni:maps[name.decode()]=cmap(stream(objs.get(int(uni[1]),b'')))
    pages=[]; seen=set()
    def walk(ref):
        if ref in seen:return
        seen.add(ref);body=objs.get(ref,b'')
        if re.search(rb'/Type\s*/Page\b',body):pages.append((ref,body));return
        kids=re.search(rb'/Kids\s*\[(.*?)\]',body,re.S)
        if kids:
            for r in re.findall(rb'(\d+)\s+0\s+R',kids[1]):walk(int(r))
    for body in objs.values():
        if re.search(rb'/Type\s*/Catalog\b',body):
            p=re.search(rb'/Pages\s+(\d+)\s+0\s+R',body)
            if p:walk(int(p[1]))
    if not pages:pages=[(r,b) for r,b in objs.items() if re.search(rb'/Type\s*/Page\b',b)]
    lines=[]
    for n,(ref,body) in enumerate(pages,1):
        c=re.search(rb'/Contents\s*(\[(.*?)\]|\d+\s+0\s+R)',body,re.S)
        refs=re.findall(rb'(\d+)\s+0\s+R',c[1]) if c else []
        text='\n'.join(read_content(stream(objs.get(int(r),b'')),maps) for r in refs)
        lines.append(f'\n===== PDF PAGE {n} (object {ref}) =====\n{text}\n')
    dest=path.with_suffix('.txt');dest.write_text(''.join(lines));print(path,'pages',len(pages),'text chars',sum(map(len,lines)),'->',dest)
for arg in sys.argv[1:]:extract(Path(arg))
