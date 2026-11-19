"""Fail loudly on missing results, incorrect inventory, or an overlength main paper."""
import hashlib,json,re
from pathlib import Path
import numpy as np
import pandas as pd
import pymupdf

ROOT=Path(__file__).resolve().parents[1]
d=pd.read_csv(ROOT/'results/runs.csv')
assert len(d)==5*3*100*15
assert not d.duplicated(['scenario','k','rep','method']).any()
assert d.groupby(['scenario','k','method']).size().eq(100).all()
assert d.groupby(['scenario','k','rep']).size().eq(15).all()
for metric in ['coverage','g0','g1','interior','clr_infinite']:
    assert d[metric].notna().all() and d[metric].between(0,1).all()
assert d[d.scenario.isin(['zeros','mixed','shift'])].boundary.notna().all()
assert d[d.scenario.isin(['dense','hetero'])].boundary.isna().all()
assert d[d.k==3][['v2','v1']].notna().all().all()
assert d[d.k>3][['v2','v1']].isna().all().all()
assert d[d.k==3][['v2','v1']].ge(0).all().all()
assert d[d.k==3][['v2','v1']].le(1).all().all()
sweep=pd.read_csv(ROOT/'results/boundary_sweep.csv')
assert len(sweep)==45 and sweep.repeats.eq(4000).all()
assert len(pd.read_csv(ROOT/'results/integration_check.csv'))==40*15*2
checks=json.loads((ROOT/'results/numerical_checks.json').read_text())
assert max(checks['initial_methods_max_absolute_difference'].values())==0
assert checks['max_absolute_mean_volume_difference']<.002
assert checks['max_analytic_sobol_difference']<.001
official=ROOT/'vendor/neurips2026/neurips_2026.sty'
assert official.read_bytes()==(ROOT/'paper/neurips_2026.sty').read_bytes()
official_check=(ROOT/'vendor/neurips2026/checklist.tex').read_text()
filled=(ROOT/'paper/checklist.tex').read_text()
questions=lambda s:re.findall(r'Question: (.*?)\n',s)
assert questions(official_check)==questions(filled) and len(questions(filled))==16
assert filled.count('Answer: \\answer')==16 and '\\answerTODO{}' not in filled
for name in ['transition','conditional','shift','smoothing','volume_weights']:
    assert (ROOT/'figures'/f'{name}.pdf').is_file()
doc=pymupdf.open(ROOT/'paper/main.pdf')
texts=[p.get_text() for p in doc]
refs=[i+1 for i,s in enumerate(texts) if re.search(r'(?m)^References\s*$',s)]
assert len(refs)==1
main_pages=refs[0]-1
assert main_pages<=9
whole='\n'.join(texts)
assert 'NeurIPS Paper Checklist' in whole and '[TODO]' not in whole
assert 'Preprint.' in whole
log=(ROOT/'paper/main.log').read_text()
assert 'undefined references' not in log and 'Citation `' not in log
assert 'Overfull \\hbox' not in log
assert (ROOT/'paper.pdf').read_bytes()==(ROOT/'paper/main.pdf').read_bytes()
result=dict(status='PASS',final_rows=len(d),methods=int(d.method.nunique()),
    independent_cells=int(d.groupby(['scenario','k','rep']).ngroups),
    repeats_per_cell=100,atom_sweep_configurations=len(sweep),
    atom_sweep_calibration_arrays=int(sweep.repeats.sum()),
    main_content_pages=main_pages,allowed_main_content_pages=9,
    references_begin_page=refs[0],total_pdf_pages=len(doc),
    official_style_unmodified=True,official_checklist_questions_preserved=16,
    pdf_sha256=hashlib.sha256((ROOT/'paper.pdf').read_bytes()).hexdigest(),
    note='Automated numerical/inventory/format checks; not human peer review.')
(ROOT/'results/artifact_validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
