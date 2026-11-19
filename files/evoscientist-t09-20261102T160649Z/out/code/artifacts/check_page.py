from pathlib import Path
import re,zlib
p=Path('/work/artifacts/sources/1808.08683.pdf');d=p.read_bytes();objs={int(m[1]):m[2] for m in re.finditer(rb'(\d+)\s+0\s+obj\b(.*?)endobj',d,re.S)}
for k,v in objs.items():
 if re.search(rb'/Type\s*/Page\b',v):
  m=re.search(rb'/Contents\s+(\d+)\s+0\s+R',v)
  if m:
   raw=objs[int(m[1])];b=re.search(rb'stream\r?\n(.*?)\r?\n?endstream',raw,re.S)[1]
   s=zlib.decompress(b) if b'FlateDecode' in raw else b
   if b'This)-' in s or b'Regression' in s:print(k,s[:11000]);break
