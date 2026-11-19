"""Parse HELM MMLU v1.13.0 per-subject tables into a models x subjects EM matrix (CSV)."""
import json, glob, os, sys
import pandas as pd
src, out = sys.argv[1], sys.argv[2]
cols = {}
for f in sorted(glob.glob(os.path.join(src, 'groups__json__mmlu_mmlu_subject:*.json'))):
    d = json.load(open(f))
    subj = d['name'].split(':', 1)[1]
    hdr = [h['value'] for h in d['header']]
    j = hdr.index('EM')
    s = {}
    for r in d['rows']:
        v = r[j].get('value')
        if v is not None:
            s[r[0]['value']] = v
    cols[subj] = pd.Series(s)
df = pd.DataFrame(cols)
df.index.name = 'model'
df.to_csv(out)
print(df.shape, 'missing cells:', int(df.isna().sum().sum()))
print(df.isna().sum(axis=1).value_counts().to_dict())
