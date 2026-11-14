"""Package all deliverables, excluding runtime infrastructure and TeX scratch files."""
import hashlib,json,pathlib,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
    exclude={'research_deliverable.zip','research_deliverable.sha256','deliverable_manifest.json'}
    scratch={'.aux','.blg','.log','.out'}
    files=[]
    for p in ROOT.rglob('*'):
      if not p.is_file():continue
      rel=p.relative_to(ROOT)
      if any(part.startswith('.') or part=='__pycache__' for part in rel.parts):continue
      if p.name in exclude:continue
      if len(rel.parts)==1 and p.suffix in scratch:continue
      files.append(p)
    files.sort()
    manifest={str(p.relative_to(ROOT)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files}
    mp=ROOT/'deliverable_manifest.json';mp.write_text(json.dumps(manifest,indent=2,ensure_ascii=False));files.append(mp)
    zp=ROOT/'research_deliverable.zip'
    with zipfile.ZipFile(zp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
      for p in files:z.write(p,p.relative_to(ROOT))
    with zipfile.ZipFile(zp) as z:
      assert z.testzip() is None
      for name,meta in manifest.items():assert hashlib.sha256(z.read(name)).hexdigest()==meta['sha256']
    digest=hashlib.sha256(zp.read_bytes()).hexdigest();(ROOT/'research_deliverable.sha256').write_text(digest+'  research_deliverable.zip\n')
    print(json.dumps({'files':len(files),'archive_bytes':zp.stat().st_size,'sha256':digest,'all_archived_hashes_verified':True},indent=2))
if __name__=='__main__':main()
