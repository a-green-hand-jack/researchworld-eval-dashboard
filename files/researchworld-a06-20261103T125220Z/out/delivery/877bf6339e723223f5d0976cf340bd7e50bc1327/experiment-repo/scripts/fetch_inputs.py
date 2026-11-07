"""Fetch only the exact pinned inputs in the delivered provenance manifest."""
import argparse, hashlib, json, pathlib, subprocess

def selected_records(records, model):
 # CLI labels have uppercase B; the pinned filenames use lowercase b.
 return [item for item in records if not item['path'].startswith('models/')
         or model=='all'
         or (model!='none' and model.lower() in pathlib.Path(item['path']).name.lower())]

def sha(file):
 h=hashlib.sha256()
 with file.open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()

def main():
 p=argparse.ArgumentParser();p.add_argument('--model',choices=['none','0.5B','1.5B','all'],default='1.5B');p.add_argument('--list',action='store_true',help='List selected pinned paths without downloading or reading model files');a=p.parse_args()
 records=selected_records(json.loads(pathlib.Path('provenance/downloads.json').read_text()),a.model)
 if a.list:
  print(json.dumps([item['path'] for item in records]));return
 for item in records:
  target=pathlib.Path(item['path']);target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists() and target.stat().st_size==item['bytes']:
   assert sha(target)==item['sha256'],f'Existing file has wrong hash: {target}'
   print(f'Already verified {target}',flush=True);continue
  subprocess.run(['curl','-fL','--retry','3','-C','-','-o',str(target),item['url']],check=True)
  assert target.stat().st_size==item['bytes'],f'Incomplete download: {target}'
  assert sha(target)==item['sha256'],f'Hash mismatch: {target}'
  print(f'Verified {target}',flush=True)

if __name__=='__main__':main()
