"""Local, dependency-light PDF body-text extraction; no networking. Equations need manual caution."""
import re,zlib,json
from pathlib import Path
from fontTools.agl import toUnicode

def parse_objects(data):
 return {int(m[1]):m[2] for m in re.finditer(rb'(\d+)\s+\d+\s+obj\b(.*?)endobj',data,re.S)}
def stream(obj):
 m=re.search(rb'stream\r?\n(.*?)\r?\n?endstream',obj,re.S)
 if not m:return b''
 try:return zlib.decompress(m[1]) if b'FlateDecode' in obj else m[1]
 except:return b''
def lit(s):
 out=bytearray();i=1
 while i<len(s)-1:
  c=s[i];i+=1
  if c==92:
   if i>=len(s)-1:break
   c=s[i];i+=1
   if 48<=c<=55:
    digits=bytes([c])
    for _ in range(2):
     if i<len(s)-1 and 48<=s[i]<=55:digits+=s[i:i+1];i+=1
     else:break
    out.append(int(digits,8)%256)
   elif c in b'nrtbf':out.append({110:10,114:13,116:9,98:8,102:12}[c])
   elif c in [10,13]:
    if c==13 and s[i:i+1]==b'\n':i+=1
   else:out.append(c)
  else:out.append(c)
 return bytes(out)
def tokens(s):
 i=0
 while i<len(s):
  if s[i] in b' \r\n\t\x00':i+=1;continue
  if s[i]==37:
   j=s.find(b'\n',i);i=len(s) if j<0 else j+1;continue
  if s[i]==40:
   j=i+1;depth=1
   while j<len(s) and depth:
    if s[j]==92:j+=2;continue
    if s[j]==40:depth+=1
    if s[j]==41:depth-=1
    j+=1
   yield ('str',lit(s[i:j]));i=j;continue
  if s[i] in b'[]':yield ('symbol',chr(s[i]));i+=1;continue
  if s[i]==60 and s[i:i+2]!=b'<<':
   j=s.find(b'>',i);v=re.sub(rb'\s',b'',s[i+1:j]);
   if len(v)%2:v+=b'0'
   try:yield ('str',bytes.fromhex(v.decode()))
   except:pass
   i=j+1;continue
  j=i+1
  while j<len(s) and s[j] not in b' \t\n\r()[]<>/':j+=1
  yield ('tok',s[i:j].decode('latin1'));i=j

def extract(p):
 objs=parse_objects(p.read_bytes()); fontmaps={};names={}
 for k,v in objs.items():
  if not re.search(rb'/Type\s*/Font\b',v):continue
  cmap={i:chr(i) for i in range(256)}
  # Common TeX text ligatures; math fonts are not reliably reconstructed.
  cmap.update({11:'ff',12:'fi',13:'fl',14:'ffi',15:'ffl',27:'ff',28:'fi',29:'fl',30:'ffi',31:'ffl'})
  enc=re.search(rb'/Encoding\s+(\d+)\s+0\s+R',v)
  ed=objs.get(int(enc[1]),b'') if enc else v
  dif=re.search(rb'/Differences\s*\[(.*?)\]',ed,re.S)
  if dif:
   idx=0
   for t in re.findall(rb'/[^\s/\[\]]+|\d+',dif[1]):
    if t.startswith(b'/'):
     name=t[1:].decode('latin1');uni=toUnicode(name)
     if uni:cmap[idx]=uni
     idx+=1
    else:idx=int(t)
  u=re.search(rb'/ToUnicode\s+(\d+)\s+0\s+R',v)
  if u:
   us=stream(objs.get(int(u[1]),b''))
   for block in re.findall(rb'beginbfchar(.*?)endbfchar',us,re.S):
    for a,b in re.findall(rb'<([0-9a-fA-F]+)>\s*<([0-9a-fA-F]+)>',block):
     try:cmap[int(a,16)]=bytes.fromhex(b.decode()).decode('utf-16-be')
     except:pass
   for block in re.findall(rb'beginbfrange(.*?)endbfrange',us,re.S):
    for a,b,c in re.findall(rb'<([0-9a-fA-F]+)>\s*<([0-9a-fA-F]+)>\s*<([0-9a-fA-F]+)>',block):
     for n in range(int(a,16),int(b,16)+1):
      try:cmap[n]=chr(int(c,16)+n-int(a,16))
      except:pass
  fontmaps[k]=cmap
 for v in objs.values():
  for name,n in re.findall(rb'/([FR]\d+)\s+(\d+)\s+0\s+R',v):
   if int(n) in fontmaps:names[name.decode()]=fontmaps[int(n)]
 pages=[]; root=None
 for k,v in objs.items():
  if re.search(rb'/Type\s*/Catalog\b',v):
   m=re.search(rb'/Pages\s+(\d+)\s+0\s+R',v)
   if m:root=int(m[1])
 def visit(k):
  v=objs[k]
  if re.search(rb'/Type\s*/Page\b',v):pages.append((k,v));return
  m=re.search(rb'/Kids\s*\[(.*?)\]',v,re.S)
  if m:
   for n in re.findall(rb'(\d+)\s+0\s+R',m[1]):visit(int(n))
 if root:visit(root)
 if not pages:pages=[(k,v) for k,v in objs.items() if re.search(rb'/Type\s*/Page\b',v)]
 out=[];meta=[]
 for page,(k,v) in enumerate(pages,1):
  m=re.search(rb'/Contents\s*(\[.*?\]|\d+\s+0\s+R)',v,re.S)
  if not m:continue
  refs=[int(n) for n in re.findall(rb'(\d+)\s+0\s+R',m[1])]
  parts=[];font={i:chr(i) for i in range(256)};stack=[];in_text=False
  for ref in refs:
   for kind,val in tokens(stream(objs.get(ref,b''))):
    if kind=='tok' and val=='BT':in_text=True;stack=[];continue
    if kind=='tok' and val=='ET':in_text=False;parts.append('\n');stack=[];continue
    if not in_text:continue
    if kind=='tok' and val=='Tf':
     if len(stack)>=2:font=names.get(str(stack[-2][1]).lstrip('/'),font)
     stack=[];continue
    if kind=='tok' and val in ['Td','TD','Tm','T*']:
     if val in ['Td','TD'] and len(stack)>=2:
      try:
       if float(stack[-1][1]) < -4:parts.append('\n')
      except:pass
     elif val in ['Tm','T*']:parts.append('\n')
     stack=[];continue
    if kind=='tok' and val in ['Tj','TJ',"'",'"']:
     for typ,item in stack:
      if typ=='str':parts.append(''.join(font.get(b,chr(b)) for b in item))
      elif typ=='tok':
       try:
        if float(item)<-100:parts.append(' ')
       except:pass
     stack=[];continue
    if kind=='tok' and re.match(r'^[A-Za-z]+$',val):stack=[];continue
    stack.append((kind,val))
  text=''.join(parts);text=re.sub('[ \t]+',' ',text);text=re.sub(r'\n{3,}','\n\n',text)
  out.append(f'\n===== PDF PAGE {page} =====\n'+text)
  meta.append({'page':page,'object':k,'chars':len(text)})
 p.with_suffix('.txt').write_text(''.join(out))
 p.with_suffix('.extraction.json').write_text(json.dumps({'method':'Local PDF stream text extraction, equations/glyphs may be lossy','pages':meta},indent=2))
 print(p.name,'pages',len(pages),'textchars',sum(m['chars'] for m in meta))
for p in Path('/work/artifacts/sources').glob('*.pdf'):extract(p)
