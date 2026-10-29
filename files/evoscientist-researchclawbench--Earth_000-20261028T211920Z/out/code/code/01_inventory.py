"""Build an inventory of all GlaMBIE input datasets (region, method, group, unit, resolution, coverage)."""
import pandas as pd, numpy as np, glob, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IN = os.path.join(ROOT, 'data/glambie/input')
METHODS = ['glaciological', 'demdiff', 'altimetry', 'gravimetry', 'combined']
rows = []
for f in sorted(glob.glob(os.path.join(IN, '*', '*.csv'))):
    regdir = os.path.basename(os.path.dirname(f))
    rid = int(regdir.split('_')[0]); rname = regdir.split('_', 1)[1]
    base = os.path.basename(f)[:-4]
    rest = base[len(rname) + 1:]
    method = rest.split('_')[0]
    assert method in METHODS, (f, method)
    d = pd.read_csv(f)
    dur = (d.end_dates - d.start_dates).values
    rows.append(dict(region_id=rid, region=rname, method=method, dataset=rest[len(method) + 1:],
                     author=d.author.iloc[0], unit=str(d.unit.iloc[0]).lower(), n=len(d),
                     start=d.start_dates.min(), end=d.end_dates.max(),
                     median_dt=np.median(dur), max_dt=dur.max(),
                     contiguous=bool(np.allclose(d.start_dates.values[1:], d.end_dates.values[:-1], atol=1e-3)),
                     overlapping=bool((d.start_dates.values[1:] < d.end_dates.values[:-1] - 1e-3).any()),
                     med_change=np.median(d.changes), med_err=np.median(d.errors), file=os.path.relpath(f, ROOT)))
inv = pd.DataFrame(rows).sort_values(['region_id', 'method', 'dataset'])
inv.to_csv(os.path.join(ROOT, 'outputs/inventory.csv'), index=False)
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 400); pd.set_option('display.max_colwidth', 40)
print(inv.drop(columns=['file', 'region']).to_string())
print(inv.groupby('method').size()); print(inv.unit.value_counts()); print(len(inv))
