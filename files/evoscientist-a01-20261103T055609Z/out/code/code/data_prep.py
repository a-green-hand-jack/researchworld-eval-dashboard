"""Build processed score matrices from the raw public data (see README for download steps)."""
import json, glob, os, re, hashlib, sys
import numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, 'data'); OUT = os.path.join(ROOT, 'data', 'processed')
os.makedirs(OUT, exist_ok=True)

def sha(p):
    h = hashlib.sha256(); h.update(open(p, 'rb').read()); return h.hexdigest()

# ---------------- HELM MMLU v1.13.0 ----------------
rows = {}; neval = {}
for f in sorted(glob.glob(os.path.join(D, 'helm', 'mmlu_mmlu_subject_*.json'))):
    subj = os.path.basename(f)[len('mmlu_mmlu_subject_'):-5]
    d = json.load(open(f)); hdr = [h['value'] for h in d['header']]
    iem, ine = hdr.index('EM'), hdr.index('# eval')
    for r in d['rows']:
        m = r[0]['value']
        v = r[iem].get('value'); n = r[ine].get('value')
        rows.setdefault(m, {})[subj] = np.nan if v is None else v
        neval.setdefault(m, {})[subj] = np.nan if n is None else n
H = pd.DataFrame(rows).T.sort_index(axis=1); N = pd.DataFrame(neval).T.sort_index(axis=1)
print('HELM raw', H.shape, 'missing cells', int(H.isna().sum().sum()))
full = H.dropna(thresh=H.shape[1])  # models with all 57 subjects
print('HELM complete models', full.shape)
print('models dropped:', list(H.index.difference(full.index)))
full.to_csv(os.path.join(OUT, 'helm_mmlu_scores.csv'))
N.loc[full.index].iloc[0].to_frame('n_eval').to_csv(os.path.join(OUT, 'helm_mmlu_neval.csv'))
print('n_eval consistent across models:', bool((N.loc[full.index].nunique() == 1).all()))

# ---------------- Open LLM Leaderboard: contents (6 aggregate tasks) ----------------
C = pd.read_parquet(os.path.join(D, 'contents.parquet'))
raw_cols = ['IFEval Raw', 'BBH Raw', 'MATH Lvl 5 Raw', 'GPQA Raw', 'MUSR Raw', 'MMLU-PRO Raw']
nrm_cols = ['IFEval', 'BBH', 'MATH Lvl 5', 'GPQA', 'MUSR', 'MMLU-PRO']
print('OLL contents', C.shape, 'NaN in score cols', int(C[raw_cols+nrm_cols].isna().sum().sum()))
print('flagged', int(C['Flagged'].sum()), 'dup fullname', int(C['fullname'].duplicated().sum()), 'dup eval_name', int(C['eval_name'].duplicated().sum()))
meta = ['eval_name','fullname','Type','#Params (B)','Flagged','Official Providers','Merged','Submission Date','Average ⬆️']
keep = C[~C['Flagged']].copy()
o6 = keep[meta + nrm_cols + raw_cols].reset_index(drop=True)
o6.to_csv(os.path.join(OUT, 'oll6.csv'), index=False)
print('oll6 (non-flagged)', o6.shape)
chk = (o6[nrm_cols].mean(axis=1) - o6['Average ⬆️']).abs().max(); print('max |mean(normalized) - Average| =', chk)

# ---------------- Open LLM Leaderboard: results (leaf tasks) ----------------
R = os.path.join(D, 'results_repo')
leaf_keys = []
def leaf_vals(res):
    out = {}
    for k, v in res.items():
        if k.startswith('leaderboard_bbh_') or k.startswith('leaderboard_musr_') or k.startswith('leaderboard_gpqa_') or k.startswith('leaderboard_math_') and k.endswith('_hard') and k != 'leaderboard_math_hard':
            if 'acc_norm,none' in v: out[k] = v['acc_norm,none']
            elif 'exact_match,none' in v: out[k] = v['exact_match,none']
    if 'leaderboard_mmlu_pro' in res: out['leaderboard_mmlu_pro'] = res['leaderboard_mmlu_pro']['acc,none']
    if 'leaderboard_ifeval' in res:
        v = res['leaderboard_ifeval']
        out['leaderboard_ifeval'] = 0.5*(v['prompt_level_strict_acc,none'] + v['inst_level_strict_acc,none'])
    return out
recs = {}
files = sorted(glob.glob(os.path.join(R, '*', '*', 'results_*.json')))
print('result files', len(files))
for f in files:
    org, mod = f.split(os.sep)[-3:-1]
    try: d = json.load(open(f))
    except Exception as e: print('bad', f, e); continue
    lv = leaf_vals(d['results'])
    ts = os.path.basename(f)[len('results_'):-5]
    recs.setdefault(f'{org}/{mod}', []).append((ts, lv, d.get('n-samples', {})))
print('models with results', len(recs))
Lrows = {}; ns = None
for m, lst in recs.items():
    lst.sort(key=lambda x: x[0]); ts, lv, nsmp = lst[-1]   # latest file
    Lrows[m] = lv
    if ns is None and len(lv) >= 38: ns = {k: nsmp[k]['effective'] for k in lv if k in nsmp}
L = pd.DataFrame(Lrows).T
cnt = L.notna().sum().sort_values(); print(cnt.head(8)); print('n tasks', L.shape[1])
Lfull = L.dropna()
print('leaf complete models', Lfull.shape)
# cross-check vs contents: BBH Raw = mean over BBH subtasks? (unweighted)
bcols = [c for c in Lfull.columns if c.startswith('leaderboard_bbh_')]
cc = C.set_index('fullname')
common = Lfull.index.intersection(cc.index)
diff = (Lfull.loc[common, bcols].mean(axis=1) - cc.loc[common, 'BBH Raw'])
print('models in both', len(common), 'median abs diff BBH mean-of-subtasks vs contents BBH Raw:', float(diff.abs().median()), 'max', float(diff.abs().max()))
# restrict to non-flagged models in contents
nf = set(keep['fullname'])
Lfull = Lfull[Lfull.index.isin(nf)]
print('leaf complete non-flagged', Lfull.shape)
Lfull.to_csv(os.path.join(OUT, 'oll_leaf_scores.csv'))
pd.Series(ns).to_csv(os.path.join(OUT, 'oll_leaf_neval.csv'), header=['n_eval'])
# manifest
man = {os.path.relpath(p, ROOT): sha(p) for p in [os.path.join(D,'contents.parquet')] + sorted(glob.glob(os.path.join(OUT,'*.csv')))}
man['helm_groups_json_concat_sha256'] = hashlib.sha256(b''.join(open(f,'rb').read() for f in sorted(glob.glob(os.path.join(D,'helm','mmlu_mmlu_subject_*.json'))))).hexdigest()
json.dump(man, open(os.path.join(OUT, 'MANIFEST.json'), 'w'), indent=1)
print(json.dumps(man, indent=1))
