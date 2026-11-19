import concurrent.futures, hashlib, json, pathlib, urllib.request, datetime
ids=['2009.03300','2210.09261','2211.09110','2107.07002','2312.03121','2504.20879','2311.01964','2311.04850','2603.08371']
root=pathlib.Path('sources'); root.mkdir(exist_ok=True)
def fetch(a):
 u='https://arxiv.org/pdf/'+a
 try:
  with urllib.request.urlopen(u,timeout=45) as r: b=r.read(); final=r.url
  p=root/(a+'.pdf'); p.write_bytes(b)
  return dict(id=a,url=u,final_url=final,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),accessed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
 except Exception as e: return dict(id=a,url=u,error=str(e))
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex: rows=list(ex.map(fetch,ids))
(root/'starter_downloads.json').write_text(json.dumps(rows,indent=2)+'\n')
for x in rows: print(x)
