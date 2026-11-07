from pathlib import Path
import re,zlib
for ident in ['1808.08683','1305.6156']:
 data=Path('/work/artifacts/sources/'+ident+'.pdf').read_bytes();objs={int(m[1]):m[2] for m in re.finditer(rb'(\d+)\s+0\s+obj\b(.*?)endobj',data,re.S)}
 forms=[]
 for k,v in objs.items():
  if re.search(rb'/Subtype\s*/Form',v):
   m=re.search(rb'stream\r?\n(.*?)\r?\n?endstream',v,re.S)
   if not m:continue
   try:s=zlib.decompress(m[1]) if b'FlateDecode' in v else m[1]
   except:continue
   if b'BT' in s:forms.append((k,s.decode('latin1')))
 Path('/work/artifacts/sources/'+ident+'.forms.json').write_text(__import__('json').dumps(forms,indent=2))
 print(ident,'forms',len(forms))
