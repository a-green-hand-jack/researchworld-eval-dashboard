"""Offline artifact integrity validation; no network access."""
from pathlib import Path
import hashlib
import json
import re
import zipfile

work=Path('/work')
lit=work/'artifacts/literature'
off=work/'official_template'
ids={'2201.02177','2301.05217','2210.01117','2309.02390','2310.06110','2303.06173','1711.05101'}
records=json.loads((lit/'download_manifest.json').read_text())
assert len(records)==14
for record in records:
    assert record['status']==200 and 'error' not in record
    assert record['requested_url'].split('/')[-1] in ids
    path=Path(record['path'])
    assert path.exists(), str(path)
    assert hashlib.sha256(path.read_bytes()).hexdigest()==record['sha256']
for ident in ids:
    for suffix in ['pdf','txt','reading.txt','abs.html']:
        assert (lit/f'{ident}.{suffix}').stat().st_size>0
    assert (lit/f'{ident}.pdf').read_bytes().startswith(b'%PDF')
    assert '[BIBLIOGRAPHY OMITTED: independence guard]' in (lit/f'{ident}.reading.txt').read_text()

orecords=json.loads((off/'download_manifest.json').read_text())
for record in orecords:
    if record.get('status')==200:
        assert hashlib.sha256(Path(record['path']).read_bytes()).hexdigest()==record['sha256']
    else:
        assert record['status']==404 and record['requested_url'].endswith('/2026/PaperInformation/StyleFiles')
archive=off/'Formatting_Instructions_For_NeurIPS_2026.zip'
with zipfile.ZipFile(archive) as package:
    assert set(package.namelist())=={'neurips_2026.tex','neurips_2026.sty','checklist.tex'}
    for name in package.namelist():
        assert package.read(name)==(off/'original_package'/name).read_bytes()
report=work/'artifacts/research_support.md'
assert report.exists()
report_text=report.read_text()
for ident in ids:
    assert f'https://arxiv.org/pdf/{ident}' in report_text
    rec=next(r for r in records if r['requested_url']==f'https://arxiv.org/pdf/{ident}')
    assert rec['sha256'] in report_text
for path in [lit/'reading_notes.md',lit/'independence_audit.md',off/'requirements.md',off/'package_inventory.json']:
    assert path.stat().st_size>0
style=(off/'original_package/neurips_2026.sty').read_text()
checklist=(off/'original_package/checklist.tex').read_text()
assert '2026-01-29' in style
assert len(re.findall(r'^\s*\\item \{\\bf [^}]+\}\s*$',checklist,re.MULTILINE))==16
assert 'desk rejected' in checklist
files=[]
for root in [lit,off]:
    files.extend(p for p in root.rglob('*') if p.is_file())
files.append(report)
inventory=[{'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(set(files))]
(work/'artifacts/artifact_checksums.json').write_text(json.dumps(inventory,indent=2))
result={'validation':'PASS','literature_documents':7,'literature_source_downloads':14,'official_package_members':3,'checklist_questions':16,'original_package_members_byte_equal':True,'integrity_inventory':'/work/artifacts/artifact_checksums.json','network_used_for_validation':False}
(work/'artifacts/validation_result.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
