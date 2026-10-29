"""Optional artifact checks; install requirements-validation.txt first."""
import csv
import hashlib
import json
import zipfile
from pathlib import Path

import numpy as np
import pymupdf

root=Path(__file__).resolve().parent
out=root/'results'
summary=json.loads((out/'summary.json').read_text())
raw=np.loadtxt(out/'cover_times.txt',dtype=np.int64)
assert raw.shape==(133,4000)
assert summary['graphs']==133 and summary['train_graphs']==76
rows=list(csv.DictReader((out/'estimates.csv').open()))
assert len(rows)==133
assert np.allclose([float(x['mean']) for x in rows],raw.mean(axis=1))
with zipfile.ZipFile(root/'icml2025.zip') as archive:
    for path in (root/'template').iterdir():
        assert path.read_bytes()==archive.read('icml2025/'+path.name)
digest=hashlib.sha256((out/'cover_times.txt').read_bytes()).hexdigest()
reference=(out/'raw_before.sha256').read_text().split()[0]
assert digest==reference, 'Raw samples differ from the recorded first run.'
pdf=pymupdf.open(root/'paper.pdf')
assert len(pdf)<=4
text=''.join(page.get_text() for page in pdf)
assert 'AUTHORERR' not in text and '20.1' in text and '31.3' in text
for i,page in enumerate(pdf):
    page.get_pixmap(matrix=pymupdf.Matrix(1.2,1.2)).save(out/f'page-{i+1}.png')
(out/'paper_extracted.txt').write_text(text)
report=dict(pdf_pages=len(pdf),graphs=133,trajectories=int(raw.size),
    raw_sha256=digest,identical_full_rerun=True,official_styles_unmodified=True,
    max_analytic_standardized_discrepancy=max(abs(v['z']) for v in summary['exact_checks']),
    analytic_checks=len(summary['exact_checks']),
    analytic_95_coverage=sum(abs(v['z'])<1.96056 for v in summary['exact_checks']),
    full_experiment_seconds=summary['analysis_and_simulation_seconds'],
    simulation_seconds=summary['simulation_seconds'],runtime='CPU only',
    pdf_tooling='PyMuPDF 1.26.7 used for independent rendering and text inspection')
(out/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
