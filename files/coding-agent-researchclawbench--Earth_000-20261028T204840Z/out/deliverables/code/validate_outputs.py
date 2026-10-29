#!/usr/bin/env python3
"""Scientific and deliverable validation; raises on any inconsistency."""
from pathlib import Path
import hashlib,json,re
import numpy as np
import pandas as pd
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];O=ROOT/'outputs';results=[]
def check(name,condition):
 assert bool(condition),name
 results.append({'check':name,'passed':True})
a=pd.read_csv(O/'annual_mass_change_2000_2023.csv')
check('480 unique calendar region-year records',len(a)==480 and not a.duplicated(['region_id','year']).any())
check('19 regions plus globe, each with 24 years',set(a.region_id)==set(range(20)) and a.groupby('region_id').size().eq(24).all())
check('Calendar bounds and requested years',set(a.year)==set(range(2000,2024)) and np.allclose(a.start_dates,a.year) and np.allclose(a.end_dates,a.year+1))
for p in (ROOT/'data/glambie/results/calendar_years').glob('*.csv'):
 rid=int(p.stem.split('_')[0]);src=pd.read_csv(p);dst=a[a.region_id==rid].sort_values('year')
 for source,target in [('combined_gt','mass_change_gt'),('combined_gt_errors','mass_change_gt_ci95'),('combined_mwe','specific_change_mwe'),('combined_mwe_errors','specific_change_mwe_ci95')]:
  check(f'Faithful export: region {rid}, {source}',np.allclose(src[source],dst[target],rtol=1e-10,atol=1e-10))
check('Standard-density conversion',np.allclose(a.specific_change_mwe_density1000,a.mass_change_gt*1000/a.glacier_area_km2,rtol=1e-10))
check('Source density conversion',np.allclose(a.mass_change_gt,a.specific_change_mwe*a.glacier_area_km2*.000997,rtol=1e-10))
check('95% to sigma convention',np.allclose(a.mass_change_gt_ci95,a.mass_change_gt_sigma*1.96,rtol=1e-10))
g=a[a.region_id==0].sort_values('year');r=a[a.region_id>0]
check('Global mass conservation',np.allclose(r.groupby('year').mass_change_gt.sum(),g.mass_change_gt,rtol=1e-10))
check('Global uncertainty quadrature',np.allclose(r.groupby('year').mass_change_gt_ci95.apply(lambda x:np.linalg.norm(x)),g.mass_change_gt_ci95,rtol=1e-10))
cum=pd.read_csv(O/'cumulative_mass_change.csv');s=pd.read_csv(O/'regional_period_summary.csv')
check('Cumulative endpoint equals period totals',np.allclose(cum[cum.end_year==2024].sort_values('region_id').cumulative_gt,s.sort_values('region_id').total_gt))
inv=pd.read_csv(O/'input_inventory.csv')
check('Inventory includes every raw file',len(inv)==len(list((ROOT/'data/glambie/input').glob('*/*.csv')))==257)
for row in pd.read_csv(O/'input_checksums.csv').itertuples():
 check('Input unchanged: '+row.path,hashlib.sha256((ROOT/row.path).read_bytes()).hexdigest()==row.sha256)
matrices=np.load(O/'global_covariance_scenarios.npz')
for key in matrices.files:
 c=matrices[key]
 check('Covariance shape/symmetry: '+key,c.shape==(24,24) and np.allclose(c,c.T))
 check('Covariance positive semidefinite: '+key,np.linalg.eigvalsh(c).min()>-1e-7)
check('Independent covariance recovers released global errors',np.allclose(np.diag(matrices['Independent']),g.mass_change_gt_sigma.to_numpy()**2))
sc=pd.read_csv(O/'covariance_sensitivity.csv')
for row in sc.itertuples():
 c=matrices[row.scenario.replace(' ','_')]
 check('Mean interval matches covariance: '+row.scenario,np.isclose(row.mean_gt_ci95,1.96*np.sqrt(c.sum())/24))
 # Each reported Fieller endpoint must solve its defining quadratic.
 we=np.r_[np.ones(12)/12,np.zeros(12)];wl=np.r_[np.zeros(12),np.ones(12)/12]
 early=-float(we@g.mass_change_gt);late=-float(wl@g.mass_change_gt)
 for pct in [row.increase_percent_ci95_fieller_lower,row.increase_percent_ci95_fieller_upper]:
  rat=1+pct/100;w=wl-rat*we
  check('Fieller endpoint satisfies equation: '+row.scenario,np.isclose((late-rat*early)**2,1.96**2*(w@c@w),rtol=1e-8,atol=1e-6))
text=(ROOT/'report/report.md').read_text()
check('Report contains substantive methods/results/discussion',all(s in text for s in ['## 3. Methods','## 4. Results','## 5. Discussion']))
check('No unresolved template placeholders','{{' not in text)
links=re.findall(r'!\[[^\]]*\]\(([^)]+)\)',text)
check('Seven linked PNG figures',len(links)==7 and all(x.endswith('.png') for x in links))
for name in links:
 p=ROOT/'report'/name
 with Image.open(p) as im:
  check('Valid PNG '+name,im.format=='PNG' and min(im.size)>500)
  im.verify()
required=['code/README.md','code/requirements.lock.txt','outputs/README.md','outputs/literature/provenance.json','outputs/endpoint_sensitivity.csv','outputs/findings.json']
for p in required:check('Deliverable exists: '+p,(ROOT/p).is_file())
check('Only PNG figure artifacts',all(p.suffix=='.png' for p in (ROOT/'report/images').iterdir() if p.is_file()))
(O/'validation_results.json').write_text(json.dumps({'n_checks':len(results),'all_passed':True,'checks':results},indent=2)+'\n')
print(f'All {len(results)} validation checks passed.')
