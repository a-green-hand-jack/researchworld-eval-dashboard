"""helm_lite_ext: HELM Lite v1.13.0, 91 models x 28 benchmarks = the six core scenarios that are not themselves aggregates of subsets (NarrativeQA, NaturalQuestions open/closed-book,
OpenbookQA, GSM8K, MedQA) + the per-subset scores of MMLU (5 subjects), LegalBench (5 subsets), MATH (7 subjects) and WMT 2014 (5 language pairs).
usage: python build_helm_ext.py [DATA=/hutian/data] -> data/matrices/helm_lite_ext.npz (+ _benches.csv with the scenario family of every column)
"""
import json, os, re, sys
import numpy as np, pandas as pd

DATA = sys.argv[1] if len(sys.argv) > 1 else '/hutian/data'
HERE = os.path.dirname(__file__); out = os.path.join(HERE, '..', 'data', 'matrices')
num = lambda c: c.get('value') if isinstance(c.get('value'), (int, float)) else np.nan
core = json.load(open(os.path.join(DATA, 'helm', 'core_scenarios.json')))[0]
hn = [x['value'] for x in core['header']]
C = pd.DataFrame({r[0]['value']: [num(c) for c in r] for r in core['rows']}, index=hn).T
cols, fam = {}, {}
for c in ['NarrativeQA - F1', 'NaturalQuestions (open-book) - F1', 'NaturalQuestions (closed-book) - F1', 'OpenbookQA - EM', 'GSM8K - EM', 'MedQA - EM']:
    cols[c] = C[c]; fam[c] = c.split(' - ')[0]
for g, label in (('mmlu', 'MMLU'), ('legalbench', 'LegalBench'), ('math_chain_of_thought', 'MATH'), ('wmt_14', 'WMT14')):
    for t in json.load(open(os.path.join(DATA, 'helm', 'lite_groups', g + '.json')))[1:]:
        h = [x['value'] for x in t['header']]
        s = pd.Series({r[0]['value']: num(r[1]) for r in t['rows']})
        nm = label + ' / ' + re.sub(r', level: 1.*', '', t['title']).replace('subject: ', '').replace('subset: ', '').replace('source_language: ', '').replace(', target_language: en', '->en')
        cols[nm] = s; fam[nm] = label
M = pd.DataFrame(cols)
M = M.loc[:, M.notna().sum() > 0]
np.savez_compressed(os.path.join(out, 'helm_lite_ext.npz'), Y=M.values.astype(float), models=np.array(M.index.astype(str)), benches=np.array(M.columns.astype(str)))
pd.DataFrame({'task': M.columns, 'type': [fam[c] for c in M.columns], 'n_models': M.notna().sum().values}).set_index('task').to_csv(os.path.join(out, 'helm_lite_ext_benches.csv'))
print('helm_lite_ext', M.shape, 'observed fraction', M.notna().mean().mean(), 'range', np.nanmin(M.values), np.nanmax(M.values))
