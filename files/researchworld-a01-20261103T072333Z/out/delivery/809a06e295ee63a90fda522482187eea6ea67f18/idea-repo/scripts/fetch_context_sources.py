"""Re-download consulted documents and check their recorded bytes; no search APIs."""
import argparse, hashlib, json, pathlib, urllib.request
parser=argparse.ArgumentParser();parser.add_argument('--out-dir',default='retrieved-context');args=parser.parse_args()
root=pathlib.Path(__file__).resolve().parents[1];out=pathlib.Path(args.out_dir);out.mkdir(parents=True,exist_ok=True)
rows=json.loads((root/'sources/starter_downloads.json').read_text())+json.loads((root/'sources/foundation_downloads.json').read_text())
failed=[]
for row in rows:
 if 'error' in row: continue
 name=row.get('id',row.get('name'));url=row.get('reproducible_url',row['url'])
 try:
  with urllib.request.urlopen(url,timeout=45) as response: data=response.read()
  (out/name).write_bytes(data);digest=hashlib.sha256(data).hexdigest()
  ok=digest==row['sha256'];print(name,'MATCH' if ok else 'CHANGED',digest)
  if not ok:failed.append(name)
 except Exception as error:print(name,'ERROR',str(error));failed.append(name)
if failed:raise SystemExit('Review changed/unavailable documents: '+', '.join(failed))
