"""Final offline deliverable checks; no experiments and no network."""
from pathlib import Path
import hashlib
import json
import re
import zipfile
import numpy as np
import pandas as pd
from experiment import ROOT

def main():
    required=['paper.pdf','paper.tex','references.bib','README.md','final_report.md','experiment.py','analyze.py','plot.py','qa.py','test_experiment.py','reproduce.py','verify.py','config.json','requirements.txt','theory.md','template_provenance.md','literature_access_log.md']
    for name in required: assert (ROOT/name).is_file(),name
    with zipfile.ZipFile(ROOT/'template/icml2026.zip') as z:
        for n in z.namelist(): assert (ROOT/'template'/n).read_bytes()==z.read(n)
    original=(ROOT/'preregistration/experiment.py').read_text(); current=(ROOT/'experiment.py').read_text()
    expected=original.replace('def weighted_quantile(scores,weights,test_weight,alpha=.1):\n','def weighted_quantile(scores,weights,test_weight,alpha=.1):\n    if len(scores)==0:\n        return np.inf  # Only the test atom remains.\n')
    assert current==expected,'Unexpected post-freeze runner change'
    frozen=json.loads((ROOT/'preregistration/manifest.json').read_text())
    for name in ['config.json','plan.md']:
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==frozen[name]
    log=(ROOT/'latex_pass3.log').read_text(); assert 'Overfull' not in log
    assert 'undefined references' not in log and 'undefined citations' not in log
    pdf_pages=int(re.search(r'Output written on paper.pdf \((\d+) pages',log).group(1))
    aux=(ROOT/'paper.aux').read_text(); mainlabels=['main-end','fig:audit','fig:shift','tab:source-coverage','tab:source-size','tab:contrasts','tab:shift']
    pages={}
    for lab in mainlabels:
        m=re.search(r'\\newlabel\{'+re.escape(lab)+r'\}\{\{[^}]*\}\{(\d+)\}',aux); assert m,lab
        pages[lab]=int(m.group(1))
    assert max(pages.values())<=8
    assert r'\usepackage[preprint]{template/icml2026}' in (ROOT/'paper.tex').read_text()
    assert 'Ran 7 tests' in (ROOT/'final_tests.log').read_text() and '\nOK\n' in (ROOT/'final_tests.log').read_text()
    assert json.loads((ROOT/'artifacts/verification.json').read_text())['max_absolute_metric_difference']==0
    # Check the precision repair, including strictly subunit and nondegenerate near-unit intervals.
    tex=(ROOT/'artifacts/analysis/full_source.tex').read_text()
    assert '0.999991 [0.999987, 0.999995]' in tex
    assert '1.0000 [1.0000, 1.0000]' not in tex
    clean=ROOT/'clean_reproduction'
    pairs=['artifacts/main/metrics.csv','artifacts/main/controls.csv','artifacts/analysis/summary_cells.csv','artifacts/analysis/summary_by_law.csv','artifacts/analysis/summary_overall.csv','artifacts/analysis/contrasts.csv','artifacts/analysis/contrast_seed_values.csv']
    maxima={}
    for name in pairs:
        a=pd.read_csv(ROOT/name); b=pd.read_csv(clean/name)
        pd.testing.assert_frame_equal(a,b,check_exact=False,atol=1e-13,rtol=0)
        num=a.select_dtypes(include='number'); num2=b.select_dtypes(include='number')
        maxima[name]=float(np.nanmax(np.abs(num.to_numpy()-num2.to_numpy())))
    assert (clean/'paper.pdf').is_file()
    assert (clean/'paper.tex').read_bytes()==(ROOT/'paper.tex').read_bytes()
    report={'status':'PASS','paper_pages':pdf_pages,'main_pages_including_floats':max(pages.values()),'label_pages':pages,'clean_reproduction_all_numeric_max_differences':maxima,'all_300_fresh_replay_exact':True,'seven_tests_pass':True,'official_template_unchanged':True,'precision_blocker_resolved':True,'complete_all_page_visual_check':False,'official_online_format_checker_run':False,'source_files_sha256':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in required if n.endswith(('.py','.tex','.bib','.json'))}}
    (ROOT/'artifacts/delivery_checks.json').write_text(json.dumps(report,indent=2)); print(json.dumps(report,indent=2))

if __name__=='__main__': main()
