import re,zlib
from pathlib import Path
for p in Path('/work/artifacts/sources').glob('*.pdf'):
 data=p.read_bytes(); objs={int(m[1]):m[2] for m in re.finditer(rb'(\d+)\s+0\s+obj\b(.*?)endobj',data,re.S)}
 print('\nFILE',p.name,'objects',len(objs))
 for k,v in objs.items():
  if b'/Type /Font' in v or b'/Type/Font' in v:
   print('FONT',k,v[:700])
   break
 for k,v in objs.items():
  if b'stream' not in v:continue
  raw=re.search(rb'stream\r?\n(.*?)\r?\n?endstream',v,re.S)
  if not raw:continue
  try:s=zlib.decompress(raw[1]) if b'FlateDecode' in v else raw[1]
  except:continue
  if b'BT' in s and b'Tj' in s or b'BT' in s and b'TJ' in s:
   print('STREAM',k,s[:3500]);break
