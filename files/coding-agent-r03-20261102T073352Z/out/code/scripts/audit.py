"""Audit provenance/splits, recompute selected losses, and check the final paper."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
from pathlib import Path
import hashlib,json,re,zipfile
import numpy as np
import pandas as pd
from pypdf import PdfReader
from models import Gaussian,design
R=Path(__file__).resolve().parents[1];checks={};details={}
records_checked=0;recomputed=0;cache={};loss_cache={}
for p in sorted((R/'results').glob('*_designs.json')):
    records=json.loads(p.read_text())
    if not records or 'train_models' not in records[0]:continue
    for rec in records:
        ds=rec['dataset']
        if ds not in cache:
            xx=pd.read_csv(R/f'data/processed/{ds}.csv',index_col=0)
            mm=pd.read_csv(R/f'data/processed/{ds}_metadata.csv',index_col=0).loc[xx.index]
            cache[ds]=(xx,mm)
        x,meta=cache[ds]
        assert np.nanmin(x.to_numpy())>=(-1 if ds.startswith('mteb') else 0)
        assert np.nanmax(x.to_numpy())<=1
        train=rec['train_models'];test=rec['test_models']
        assert set(train).isdisjoint(test),(p,rec['seed'],rec['fold'])
        assert x.loc[test].notna().all().all()
        assert len(train)==len(set(train)) and len(test)==len(set(test))
        if rec['protocol']=='publisher':assert set(meta.loc[train].publisher).isdisjoint(meta.loc[test].publisher)
        for order in rec['orders']:
            for s in order['orders']:
                assert len(s)==len(set(s)) and all(0<=j<x.shape[1] for j in s)
                if rec['targets'] is not None:assert set(s).isdisjoint(rec['targets'])
        records_checked+=1
        # Recompute every main-cohort Schur fold at one preselected budget.
        if rec['audit']=='main':
            k=8 if x.shape[1]>6 else 2
            m=Gaussian(rec['alpha']).fit(x.loc[train].to_numpy())
            s=next(o['orders'][0][:k] for o in rec['orders'] if o['method']=='Schur')
            assert s==design(m.cov,k)
            u=[j for j in range(x.shape[1]) if j not in s]
            e=m.predict(x.loc[test].to_numpy(),s)[:,u]-x.loc[test].to_numpy()[:,u]
            lossfile=p.with_name(p.name.replace('_designs.json','_losses.csv.gz'))
            if lossfile not in loss_cache:loss_cache[lossfile]=pd.read_csv(lossfile)
            losses=loss_cache[lossfile]
            z=losses[(losses.seed==rec['seed'])&(losses.fold==rec['fold'])&(losses.method=='Schur')&(losses.k==k)].set_index('model').loc[test]
            np.testing.assert_allclose(z.smse,np.mean((e/m.std[u])**2,axis=1),rtol=1e-9,atol=1e-10)
            np.testing.assert_allclose(z.mse,np.mean((100*e)**2,axis=1),rtol=1e-9,atol=1e-10)
            recomputed+=len(test)
checks['split_and_query_integrity']=True;checks['main_loss_recomputation']=True
details.update(records_checked=records_checked,recomputed_model_predictions=recomputed)
for p in (R/'results').glob('*_losses.csv.gz'):
    x=pd.read_csv(p)
    assert np.isfinite(x[['smse','mse','mae']]).all().all()
    assert (x[['smse','mse','mae']]>=0).all().all()
checks['all_saved_losses_finite']=True
p=pd.read_csv(R/'data/processed/mteb_cell_provenance.csv')
x=pd.read_csv(R/'data/processed/mteb.csv',index_col=0)
assert len(p)==int(x.notna().sum().sum())
for row in p.itertuples():np.testing.assert_allclose(row.score,x.loc[row.model,row.task],rtol=1e-10,atol=1e-10)
checks['mteb_cell_provenance_complete']=True
t=pd.read_csv(R/'results/theory.csv');assert np.isfinite(t.select_dtypes('number')).all().all();assert (t.gap<=t.bound+1e-10).all()
details['max_theory_monte_carlo_z']=float((abs(t.mc_mse-t.true_risk)/t.mc_se).max())
checks['theory_bound']=True

r=PdfReader(R/'paper/main.pdf');texts=[p.extract_text() for p in r.pages]
reference_page=next(i for i,t in enumerate(texts) if t.lstrip().startswith('References'))
assert reference_page<=9
assert sum('NeurIPS Paper Checklist' in t for t in texts)==1
assert not re.search(r'undefined references|undefined citations|Overfull', (R/'paper/main.log').read_text())
assert 'Answer: \\answerTODO' not in (R/'paper/checklist.tex').read_text()
with zipfile.ZipFile(R/'paper/vendor/neurips2026.zip') as z:
    assert z.read('neurips_2026.sty')==(R/'paper/vendor/neurips_2026.sty').read_bytes()
checks['official_style_unchanged']=True;checks['paper_compiled_within_limit']=True
details.update(pdf_pages=len(r.pages),main_content_pages=reference_page,main_page_limit=9,checklist_items=16)

meta=pd.read_csv(R/'data/processed/openllm_metadata.csv');dates=pd.to_datetime(meta.submission_date,errors='coerce')
c1=dates.dropna().quantile(.6);c2=dates.dropna().quantile(.8)
details['temporal']={'missing_dates':int(dates.isna().sum()),'cut1':str(c1),'cut2':str(c2),
                     'train_rows':int((dates<c1).sum()),'validation_rows':int(((dates>=c1)&(dates<c2)).sum()),'test_rows':int((dates>=c2).sum())}
size=sum(p.stat().st_size for p in R.rglob('*') if p.is_file())
assert size<5_000_000_000;details['workspace_bytes_at_audit']=size;checks['under_5GB']=True
(R/'results/audit.json').write_text(json.dumps({'checks':checks,'details':details},indent=2))
print(json.dumps({'checks':checks,'details':details},indent=2))
