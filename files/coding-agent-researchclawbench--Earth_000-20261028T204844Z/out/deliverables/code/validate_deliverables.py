"""Check delivered scientific products, figures, provenance and report links."""
from pathlib import Path
import hashlib
import json
import re
import numpy as np
import pandas as pd
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs'


def main():
    results = {}
    annual = pd.read_csv(OUT / 'benchmark_annual_all.csv')
    assert len(annual) == 480
    assert not annual.duplicated(['region_id', 'year']).any()
    assert annual.groupby('region_id').year.apply(lambda s: set(s) == set(range(2000, 2024))).all()
    assert np.isfinite(annual.select_dtypes('number')).all().all()
    assert np.allclose(annual.end_dates - annual.start_dates, 1)
    for value, h in [('mass_change_gt', 'mass_change_gt_h95'),
                     ('specific_mass_change_mwe', 'specific_mass_change_mwe_h95')]:
        assert (annual[h] > 0).all()
        assert np.allclose(annual[value]-annual[h], annual[value+'_lower95'], atol=1e-8)
        assert np.allclose(annual[value]+annual[h], annual[value+'_upper95'], atol=1e-8)
    for p in (ROOT / 'data/glambie/results/calendar_years').glob('*.csv'):
        rid = int(p.stem.split('_')[0])
        source = pd.read_csv(p).sort_values('start_dates')
        export = annual[annual.region_id == rid].sort_values('start_dates')
        for dest, src in [('mass_change_gt','combined_gt'), ('mass_change_gt_h95','combined_gt_errors'),
                          ('specific_mass_change_mwe','combined_mwe'), ('specific_mass_change_mwe_h95','combined_mwe_errors')]:
            assert np.allclose(export[dest],source[src],rtol=1e-11,atol=1e-9), (rid,src)
    results['annual_product_rows'] = len(annual)
    results['source_value_preservation'] = 'passed for all regions, years and uncertainty fields'
    global_data=annual[annual.region_id==0].sort_values('year')
    regional_data=annual[annual.region_id>0]
    aggregated=regional_data.groupby('year').mass_change_gt.sum().values
    closure = np.max(np.abs(global_data.mass_change_gt.values-aggregated))
    assert closure<1e-7
    results['exported_gt_closure_max_abs'] = float(closure)
    cov = np.load(OUT/'global_annual_covariance_ar1_07_gt2.npy')
    assert cov.shape==(24,24)
    assert np.allclose(cov,cov.T)
    assert np.linalg.eigvalsh(cov).min()>0
    assert np.allclose(np.diag(cov),(global_data.mass_change_gt_h95/1.96)**2)
    results['covariance_matrix'] = 'symmetric positive definite; correct standard-deviation scale'
    manifest = pd.read_csv(OUT/'data_manifest_sha256.csv')
    for _, row in manifest.iterrows():
        assert hashlib.sha256((ROOT/row.path).read_bytes()).hexdigest()==row.sha256
    results['input_checksums_verified'] = len(manifest)
    report = ROOT/'report/report.md'
    text = report.read_text()
    assert len(text.split()) > 5000
    assert not any(ord(c)<32 and c not in '\n\t' for c in text), 'Invalid control character in report'
    for word in ['Methodology','Results','Discussion','References','2000–2023']:
        assert word in text
    links = re.findall(r'!\[[^\]]*\]\(([^)]+)\)',text)
    assert len(links)==8
    for link in links:
        path=(report.parent/link).resolve()
        assert path.is_relative_to(ROOT)
        assert path.suffix=='.png' and path.stat().st_size>10000
        with Image.open(path) as img:
            assert img.format=='PNG'
            img.verify()
        with Image.open(path) as img:
            assert min(img.size)>400
            assert np.asarray(img.convert('RGB')).std()>10
    for link in re.findall(r'(?<!!)\[[^\]]*\]\(([^)]+)\)',text):
        if '://' not in link:
            assert (report.parent/link).exists(), link
    results['report_words'] = len(text.split())
    results['referenced_pngs_verified'] = len(links)
    results['local_report_links'] = 'all resolve'
    results['status'] = 'passed'
    (OUT/'validation_results.json').write_text(json.dumps(results,indent=2))
    print(json.dumps(results,indent=2))


if __name__=='__main__':
    main()
