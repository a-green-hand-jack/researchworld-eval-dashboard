from pathlib import Path
import concurrent.futures, hashlib, json, urllib.request
urls={
'neurips2026_call':'https://neurips.cc/Conferences/2026/CallForPapers',
'neurips2026_style':'https://media.neurips.cc/Conferences/NeurIPS2026/Styles/neurips_2026.zip',
'icml2026_author':'https://icml.cc/Conferences/2026/AuthorInstructions',
'icml2026_style':'https://media.icml.cc/Conferences/ICML2026/Styles/icml2026.zip',
}
def fetch(item):
 key,url=item
 try:
  with urllib.request.urlopen(url,timeout=45) as r:
   body=r.read(); status=r.status; final=r.url; ct=r.headers.get('Content-Type')
  name=key+('.zip' if key.endswith('style') else '.html')
  Path('sources',name).write_bytes(body)
  return {'key':key,'url':url,'final_url':final,'status':status,'content_type':ct,'path':'sources/'+name,'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()}
 except Exception as e:return {'key':key,'url':url,'error':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as p: results=list(p.map(fetch,urls.items()))
Path('sources/fetch-log.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
