import sys,json,pathlib
sys.path.insert(0,'/work')
from retrieve import fetch
root=pathlib.Path('/work');(root/'official').mkdir(exist_ok=True);(root/'template').mkdir(exist_ok=True)
items=[
 ('https://api.github.com/repos/ICLR/Master-Template','repository.json'),
 ('https://api.github.com/repos/ICLR/Master-Template/contents','repository_contents.json'),
 ('https://iclr.cc/Conferences/2027/CallForPapers','iclr2027_call.html'),
 ('https://iclr.cc/Conferences/2027/AuthorGuide','iclr2027_authors.html'),
 ('https://iclr.cc/Conferences/2026/CallForPapers','iclr2026_call.html'),
 ('https://iclr.cc/Conferences/2026/AuthorGuide','iclr2026_authors.html'),
]
records=[]
for url,name in items:
 r=fetch(url,root/'official'/name);records.append(r)
 print(json.dumps({k:v for k,v in r.items() if k not in ['metadata','abstract','history','headers']},ensure_ascii=False),flush=True)
(root/'official_retrieval.json').write_text(json.dumps(records,indent=2))
