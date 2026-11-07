"""Final artifact/measurement checks, without raw data or model evaluation."""
from pathlib import Path
import hashlib,json,re,zipfile
import numpy as np
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parent

def main():
    required=['paper.pdf','paper.tex','references.bib','checklist_filled.tex','README.md','requirements.txt','final_report.md','ARTIFACT_MAP.md','experiment.py','analyze.py','submission.zip','build_validation.json','review_resolution.md']
    assert all((ROOT/p).is_file() for p in required)
    original=(ROOT/'template/checklist.tex').read_text();filled=(ROOT/'checklist_filled.tex').read_text()
    q=lambda s:re.findall(r'Question: (.*)',s)
    assert len(q(original))==16 and q(original)==q(filled)
    assert len(re.findall(r'Answer: \\answer(?:Yes|No|NA)\{\}',filled))==16
    macros=[]
    for ds in ('pima','acs'):
        for model in ('lr','rf','mlp'):
            per=[]
            for seed in (11,23,47):
                with np.load(ROOT/f'results120/{ds}_{model}_{seed}.npz') as z:
                    a=z['phi'];ref=z['reference'];assert a.shape[:3]==(120,20,4)
                    ix=np.sort(np.argsort(-abs(a),axis=-1,kind='stable')[...,:3],axis=-1)
                    tar=np.sort(np.argsort(-abs(ref),axis=-1,kind='stable')[:,:3],axis=-1)
                    per.append(np.all(ix==tar[:,None,None,:],axis=-1).mean(axis=(0,1)))
            macros.append(np.mean(per,axis=0))
    macro=np.mean(macros,axis=0)
    summary=json.loads((ROOT/'analysis120/summary.json').read_text())
    reported=[r['top3_match'] for r in summary['exact_macro'] if r['method']=='antithetic']
    assert np.allclose(macro,reported,atol=1e-14)
    font_types=set(); seen=set()
    def scan_resources(resources):
        if hasattr(resources,'get_object'): resources=resources.get_object()
        if id(resources) in seen: return
        seen.add(id(resources))
        fonts=resources.get('/Font',{})
        if hasattr(fonts,'get_object'):fonts=fonts.get_object()
        for font in fonts.values():font_types.add(str(font.get_object().get('/Subtype')))
        xobjects=resources.get('/XObject',{})
        if hasattr(xobjects,'get_object'):xobjects=xobjects.get_object()
        for obj in xobjects.values():
            child=obj.get_object()
            if '/Resources' in child:scan_resources(child['/Resources'])
    for page in PdfReader(ROOT/'paper.pdf').pages:scan_resources(page.get('/Resources',{}))
    assert '/Type3' not in font_types
    with zipfile.ZipFile(ROOT/'submission.zip') as z:
        assert z.testzip() is None
        names=z.namelist()
        assert not any(n.endswith('.joblib') or n.startswith('originals/') or (n.startswith('data/') and n!='data/manifest.json') for n in names)
        manifest=json.loads(z.read('RELEASE_MANIFEST.json'))
        for n,r in manifest['files'].items():
            data=z.read(n);assert len(data)==r['bytes'] and hashlib.sha256(data).hexdigest()==r['sha256'],n
    report={'status':'passed','required_files_present':required,'official_checklist_questions_preserved':16,'independent_exact_macro_points':macro.tolist(),
            'pdf_font_types':sorted(font_types),'archive_crc_and_all_manifest_hashes':'passed','archive_bytes':(ROOT/'submission.zip').stat().st_size,
            'raw_data_models_original_pdfs_excluded':True,'build':json.loads((ROOT/'build_validation.json').read_text()),
            'note':'Independent array reduction and archive/PDF checks only; not a human peer review or deployment guarantee.'}
    (ROOT/'final_verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
