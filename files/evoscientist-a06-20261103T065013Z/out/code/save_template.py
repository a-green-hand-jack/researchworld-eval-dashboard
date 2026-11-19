import sys,json,pathlib,hashlib
sys.path.insert(0,'/work');from retrieve import fetch
root=pathlib.Path('/work');records=json.loads((root/'official_retrieval.json').read_text())
commit=json.loads((root/'official'/'template_commit.json').read_text())['sha']
items=json.loads((root/'official'/'iclr2027_contents.json').read_text())
for x in items:
 url=f"https://raw.githubusercontent.com/ICLR/Master-Template/{commit}/{x['path']}"
 path=root/'template'/x['name'];r=fetch(url,path)
 if path.exists():
  data=path.read_bytes();actual=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest();r.update(expected_git_blob_sha=x['sha'],actual_git_blob_sha=actual,git_blob_matches=(actual==x['sha']))
 records.append(r);print(json.dumps({k:v for k,v in r.items() if k not in ['headers','metadata','abstract','history']}),flush=True)
for url,name in [
 ('https://iclr.cc/Conferences/2027/AuthorGuidelines','iclr2027_authors.html'),
 (f'https://raw.githubusercontent.com/ICLR/Master-Template/{commit}/README.md','template_README.md')]:
 r=fetch(url,root/'official'/name);records.append(r);print(json.dumps({k:v for k,v in r.items() if k not in ['headers','metadata','abstract','history']}),flush=True)
(root/'official_retrieval.json').write_text(json.dumps(records,indent=2))
