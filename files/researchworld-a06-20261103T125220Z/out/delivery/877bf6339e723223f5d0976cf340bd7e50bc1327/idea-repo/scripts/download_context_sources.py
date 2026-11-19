from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import urllib.request, hashlib, json, subprocess
import argparse
parser=argparse.ArgumentParser(description='Download only the explicitly listed context sources; no searches or link traversal.')
parser.add_argument('--output-dir',type=Path,required=True)
parser.add_argument('--verify-manifest',type=Path,help='Compare downloaded bytes with a recorded primary-sources.json')
args=parser.parse_args()
root=args.output_dir
root.mkdir(parents=True,exist_ok=True)
sources={
'mmlu_pro':'https://arxiv.org/pdf/2406.01574v1',
'dspy':'https://arxiv.org/pdf/2310.03714v1',
'mipro':'https://arxiv.org/pdf/2406.11695v1',
'multiprompt':'https://arxiv.org/pdf/2405.17202v1',
'best_arm':'https://arxiv.org/pdf/2402.09723v1',
'format_sensitivity':'https://arxiv.org/pdf/2310.11324v1',
'adaptive_validity':'https://arxiv.org/pdf/1411.2664v1',
'ladder':'https://arxiv.org/pdf/1502.04585v1',
'inference_winners':'https://www.nber.org/system/files/working_papers/w25456/w25456.pdf',
'gaussian_maxima':'https://arxiv.org/pdf/1212.6906v1',
'posi':'https://arxiv.org/pdf/1306.1059v1',
'posi_metadata':'https://api.crossref.org/works/10.1214/12-AOS1077',
'mmlu_card':'https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro/raw/b189ec765aa7ed75c8acfea42df31fdae71f97be/README.md',
'cawley_talbot':'https://www.jmlr.org/papers/volume11/cawley10a/cawley10a.pdf',
}
def get(kv):
 k,u=kv
 try:
  r=urllib.request.urlopen(u,timeout=50);b=r.read()
  suffix='.pdf' if b.startswith(b'%PDF') else '.json' if k.endswith('metadata') else '.md'
  p=root/(k+suffix);p.write_bytes(b)
  if suffix=='.pdf': subprocess.run(['pdftotext','-layout',str(p),str(root/(k+'.txt'))],check=True)
  return dict(key=k,url=u,final_url=r.geturl(),bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),file=str(p),status='ok')
 except Exception as e:return dict(key=k,url=u,status='failed',error=str(e))
with ThreadPoolExecutor(max_workers=4) as pool: results=list(pool.map(get,sources.items()))
(root/'download-manifest.json').write_text(json.dumps(results,indent=2)+'\n')
for r in results: print(r['key'],r['status'],r.get('bytes',r.get('error')))

if any(r['status'] != 'ok' for r in results):
 raise SystemExit('At least one context source failed; see download-manifest.json')
if args.verify_manifest:
 expected={r['key']:r['sha256'] for r in json.loads(args.verify_manifest.read_text()) if r['status']=='ok'}
 mismatch=[r['key'] for r in results if expected.get(r['key']) != r['sha256']]
 if mismatch:
  raise SystemExit('Downloaded content differs from recorded source hashes: '+', '.join(mismatch))
 print('All downloaded bytes match the recorded source manifest.')
