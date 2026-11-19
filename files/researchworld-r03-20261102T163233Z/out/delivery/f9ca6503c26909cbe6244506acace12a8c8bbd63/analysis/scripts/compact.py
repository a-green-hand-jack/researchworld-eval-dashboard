"""Losslessly compact completed numerical artifacts for the code delivery."""
import gzip,pathlib,shutil,json
ROOT=pathlib.Path(__file__).resolve().parents[1]
for p in (ROOT/'results').glob('*/*'):
 if p.name not in ('model_losses.csv','designs.json'):continue
 with p.open('rb') as src,p.with_suffix(p.suffix+'.gz').open('wb') as dst:
  with gzip.GzipFile(fileobj=dst,mode='wb',mtime=0) as packed:shutil.copyfileobj(src,packed)
 p.unlink()
meta=ROOT/'results/uncertainty.json'
if meta.exists():
 info=json.loads(meta.read_text())
 info['sources']=[str(p)+'.gz' if not (ROOT/p).exists() and (ROOT/(str(p)+'.gz')).exists() else p for p in info['sources']]
 meta.write_text(json.dumps(info,indent=2)+'\n')
print('Losses and query designs compacted losslessly.')
