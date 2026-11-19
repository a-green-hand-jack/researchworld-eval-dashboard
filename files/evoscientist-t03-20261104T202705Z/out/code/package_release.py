"""Compact, anonymous supplemental archive (<100 MB); raw data/models excluded."""
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parent
DIRS=('results','results120','analysis','analysis30','analysis90','analysis120','paper_tables','template')
ROOT_SUFFIXES={'.py','.md','.json','.jsonl','.bib','.tex','.sh','.txt','.patch','.log'}
OMIT_NAMES={'analysis_inputs.npz'} # duplicated source arrays; deterministic rebuild

def select():
    files=[];omitted=[]
    for p in ROOT.iterdir():
        if p.is_file() and (p.suffix in ROOT_SUFFIXES or p.name in {'paper.pdf','paper.bbl'}):
            if p.name.startswith('paper_preview') or p.name in {'RELEASE_MANIFEST.json','final_verification.json'}: continue
            files.append(p)
    for d in DIRS:
        for p in (ROOT/d).rglob('*'):
            if not p.is_file() or '__pycache__' in p.parts:continue
            if p.suffix=='.joblib':continue
            if p.name in OMIT_NAMES:
                omitted.append(str(p.relative_to(ROOT)));continue
            files.append(p)
    # The raw-data checksum manifest is provenance, not raw data.
    files.append(ROOT/'data/manifest.json')
    return sorted(set(files)),sorted(omitted)

def main():
    files,omitted=select()
    manifest={'archive':'submission.zip','format':'root-relative files','raw_data_included':False,'fitted_models_included':False,
              'original_research_pdfs_included':False,'redundant_inputs_omitted':omitted,
              'regenerate_omitted':'Run analyze.py canonical analyses as instructed in README before test_precision_analysis.py. Source result NPZs, seeds, and code are included.',
              'files':{str(p.relative_to(ROOT)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files}}
    (ROOT/'RELEASE_MANIFEST.json').write_text(json.dumps(manifest,indent=2))
    with zipfile.ZipFile(ROOT/'submission.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in files: z.write(p,p.relative_to(ROOT))
        z.write(ROOT/'RELEASE_MANIFEST.json','RELEASE_MANIFEST.json')
    size=(ROOT/'submission.zip').stat().st_size
    assert size<100_000_000,f'Archive exceeds official 100MB supplement cap: {size}'
    print(json.dumps({'archive':'submission.zip','bytes':size,'files':len(files)+1,'omitted_redundant_caches':omitted},indent=2))
if __name__=='__main__':main()
