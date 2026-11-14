"""Build score matrices (models x tasks) from the raw public data -> data/processed/*.csv"""
import json, glob, os, re
import numpy as np, pandas as pd
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
D = os.path.join(ROOT, 'data'); P = os.path.join(D, 'processed'); os.makedirs(P, exist_ok=True)

# ---- HELM MMLU v1.13.0: 57 subjects, metric EM; n_eval per subject
files = sorted(glob.glob(os.path.join(D, 'helm_v1.13.0/groups/json/mmlu_*_mmlu_*_subject:*.json')))
em, ne = {}, {}
for f in files:
    subj = re.search(r'_subject:(.+)\.json$', f).group(1)
    d = json.load(open(f))
    hdr = [h['value'] for h in d['header']]
    iem, ine = hdr.index('EM'), hdr.index('# eval')
    for r in d['rows']:
        m = r[0]['value']
        v = r[iem].get('value'); n = r[ine].get('value')
        em.setdefault(subj, {})[m] = np.nan if v is None else float(v) * 100
        ne.setdefault(subj, {})[m] = np.nan if n is None else float(n)
EM = pd.DataFrame(em); NE = pd.DataFrame(ne)
print('HELM raw shape', EM.shape, 'subjects', len(files))
print('models with any missing:', int(EM.isna().any(axis=1).sum()))
EM.to_csv(os.path.join(P, 'helm_mmlu_raw.csv'))
NE.to_csv(os.path.join(P, 'helm_mmlu_neval_raw.csv'))
keep = EM.dropna(axis=0, how='any')
print('HELM complete-case models', keep.shape, ' n_eval per subject (median over models):', NE.loc[keep.index].median().describe().to_dict())
keep.to_csv(os.path.join(P, 'helm_mmlu.csv')); NE.loc[keep.index].to_csv(os.path.join(P, 'helm_mmlu_neval.csv'))

# ---- Open LLM Leaderboard contents (v2 tasks, normalised columns used by the official average)
df = pd.read_parquet(os.path.join(D, 'ollb_contents/train-00000-of-00001.parquet'))
print('OLLB columns', list(df.columns)); print('OLLB shape', df.shape)
df.to_csv(os.path.join(P, 'ollb_contents_full.csv'), index=False)
