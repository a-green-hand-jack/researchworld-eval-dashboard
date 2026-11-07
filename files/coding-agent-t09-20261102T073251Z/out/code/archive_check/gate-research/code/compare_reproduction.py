"""Compare independently rerun raw/derived numbers, ignoring gzip/PDF timestamps."""
import gzip,hashlib,json
from pathlib import Path
import pandas as pd
from study import ROOT

other=ROOT/'reproduction_check'
records=[]
for original in sorted((ROOT/'results').glob('*_raw.csv.gz')):
    copy=other/'results'/original.name
    a=gzip.decompress(original.read_bytes());b=gzip.decompress(copy.read_bytes())
    assert a==b, f'Raw numerical mismatch: {original.name}'
    records.append(dict(file=original.name,bytes_uncompressed=len(a),sha256_uncompressed=hashlib.sha256(a).hexdigest(),exact_match=True))
for original in sorted((ROOT/'results').glob('*_summary.csv')):
    copy=other/'results'/original.name
    assert original.read_bytes()==copy.read_bytes(),f'Summary mismatch: {original.name}'
for filename in ['kernels.csv','paired_comparisons.csv','number_provenance.json']:
    assert (ROOT/'results'/filename).read_bytes()==(other/'results'/filename).read_bytes(),f'Derived mismatch: {filename}'
for original in sorted((ROOT/'paper/generated').glob('*.tex')):
    assert original.read_bytes()==(other/'paper/generated'/original.name).read_bytes(),f'LaTeX numeric mismatch: {original.name}'
result=dict(raw_files=records,summary_files=len(list((ROOT/'results').glob('*_summary.csv'))),
            latex_fragments=len(list((ROOT/'paper/generated').glob('*.tex'))),
            original_audit=json.loads((ROOT/'logs/audit.json').read_text()),
            reproduction_audit=json.loads((other/'logs/audit.json').read_text()),
            note='Raw decompressed CSVs, summary CSVs and generated LaTeX fragments match byte-for-byte. PDF hash can differ because of TeX timestamps and output paths.')
(ROOT/'logs/reproduction_comparison.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
