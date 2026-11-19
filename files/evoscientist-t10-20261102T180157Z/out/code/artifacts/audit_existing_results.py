"""Output-only audit. Does not import or execute any study CI method."""
from pathlib import Path
import hashlib
import json
import platform
import numpy as np
import pandas as pd
import scipy
from scipy.stats import binom, norm
from scipy.special import logsumexp

def probability_sci(logp):
    if logp == 0:
        return '1'
    log10p = float(logp/np.log(10))
    exponent = int(np.floor(log10p))
    return f'{10**(log10p-exponent):.12g}e{exponent:+d}'

ROOT = Path('/work')
OUT = ROOT / 'artifacts'
CONFIG = json.loads((ROOT/'results/config.json').read_text())
SUMMARY = pd.read_csv(ROOT/'results/summary.csv', keep_default_na=False)
ORACLE = pd.read_csv(ROOT/'results/oracle.csv', keep_default_na=False)
FINITE = ['cp', 'eb_labeled', 'eb_ppi', 'eb_select']
ASYM = ['wald', 'ppi', 'ppipp', 'ppipp_pkg', 'cf_linear', 'cf_poly2', 'cf_rich', 'insample_rich']
Z = norm.ppf(.975)
METRICS, CELLS, ERRORS = [], [], []
HASHES = {}
DIFFS = {}
EXPECTED = set()
TRUTHS = {'linear': .5, 'quadratic': .34, 'step': .5, 'null': .5, 'rare': .01}
DATA = {}
for name in ['galaxies', 'forest']:
    p = ROOT/'data'/f'{name}.npz'
    d = np.load(p)
    TRUTHS[name] = float(d['Y'].mean())
    DATA[name] = dict(size=len(d['Y']), truth=TRUTHS[name], sha256=hashlib.sha256(p.read_bytes()).hexdigest(), hash_match=hashlib.sha256(p.read_bytes()).hexdigest()==CONFIG['data_sha256'][p.name], binary_y=bool(np.isin(d['Y'], [0, 1]).all()))

def wilson(k, r):
    p = k/r
    den = 1 + Z*Z/r
    mid = (p + Z*Z/(2*r))/den
    half = Z*np.sqrt(p*(1-p)/r + Z*Z/(4*r*r))/den
    return mid-half, mid+half

def se(x):
    return float(np.std(x, ddof=1)/np.sqrt(len(x)))

for scenario, n, ratio, reps, grid in CONFIG['cells']:
    N = n*ratio
    name = f'{scenario}_n{n}_r{ratio}.csv.gz'
    EXPECTED.add(name)
    f = ROOT/'results/raw'/name
    HASHES[str(f.relative_to(ROOT))] = hashlib.sha256(f.read_bytes()).hexdigest()
    d = pd.read_csv(f, keep_default_na=False)
    methods = ASYM + FINITE + ([] if scenario in ['galaxies', 'forest'] else ['oracle'])
    bad_meta = 0
    for key, val in dict(scenario=scenario, n=n, N=N, ratio=ratio, grid=grid).items():
        bad_meta += int((d[key] != val).sum())
    duplicate = int(d.duplicated(['method', 'rep']).sum())
    methods_ok = set(d.method) == set(methods)
    rep_ok = True
    order_ok = True
    for method in methods:
        g = d[d.method == method]
        rep_ok &= np.array_equal(np.sort(g.rep.to_numpy()), np.arange(reps))
        order_ok &= np.array_equal(g.rep.to_numpy(), np.arange(reps))
    truth_bad = int((np.abs(d.truth.to_numpy()-TRUTHS[scenario]) > 1e-12).sum())
    cell = dict(scenario=scenario,n=n,N=N,ratio=ratio,grid=grid,rows=len(d),expected_rows=reps*len(methods),method_count=d.method.nunique(),duplicate_method_rep=duplicate,rep_alignment_ok=bool(rep_ok),rep_order_ok=bool(order_ok),methods_ok=methods_ok,bad_metadata=bad_meta,bad_truth=truth_bad)
    CELLS.append(cell)
    if not (len(d)==reps*len(methods) and methods_ok and rep_ok and duplicate==0 and bad_meta==0 and truth_bad==0):
        ERRORS.append(cell)
    wpp = d[d.method=='ppipp'].sort_values('rep').width.to_numpy()
    cpp = d[d.method=='ppipp'].sort_values('rep').covered.to_numpy()
    cpw = d[d.method=='cp'].sort_values('rep').width.to_numpy()
    eblw = d[d.method=='eb_labeled'].sort_values('rep').width.to_numpy()
    for method in methods:
        g = d[d.method == method].sort_values('rep')
        lo, hi, saved_t = (g[c].to_numpy() for c in ['lower','upper','truth'])
        t = np.full(len(g), TRUTHS[scenario])
        w, rw = (g[c].to_numpy() for c in ['width','raw_width'])
        covered = (lo <= t) & (t <= hi)
        k, r = int(covered.sum()), len(g)
        p = k/r
        wl, wh = wilson(k, r)
        wr = w.mean()/wpp.mean()
        rd = w-wpp
        cd = covered.astype(float)-cpp
        tier = 'finite' if method in FINITE else ('oracle' if method=='oracle' else 'asymptotic')
        q = np.quantile(w, [.025,.25,.5,.75,.975])
        record = dict(scenario=scenario,n=n,N=N,ratio=ratio,grid=grid,method=method,tier=tier,negative_control=method=='insample_rich',reps=r,truth=TRUTHS[scenario],covered_count=k,miss_count=r-k,coverage=p,coverage_mcse=np.sqrt(p*(1-p)/r),cov_lo=wl,cov_hi=wh,undercoverage_gap=.95-p,p_undercoverage=float(binom.cdf(k,r,.95)),invalid_nonfinite=int((~np.isfinite(np.c_[lo,hi,w,rw])).any(axis=1).sum()),invalid_reversed=int((lo>hi).sum()),endpoints_outside_unit=int(((lo<0)|(hi>1)).sum()),negative_width=int((w<0).sum()),negative_raw_width=int((rw<0).sum()),width_endpoint_max_abs=float(np.max(np.abs(w-(hi-lo)))),covered_disagreement=int((covered!=g.covered.to_numpy()).sum()),stored_covered_invalid=int((~g.covered.isin([0,1])).sum()),zero_width=int((w==0).sum()),collapsed_at_zero=int(((lo==0)&(hi==0)).sum()),collapsed_at_one=int(((lo==1)&(hi==1)).sum()),touch_zero=int((lo==0).sum()),touch_one=int((hi==1).sum()),miss_below=int((hi<t).sum()),miss_above=int((lo>t).sum()),width=float(w.mean()),width_se=se(w),width_ci_lo=float(w.mean()-Z*se(w)),width_ci_hi=float(w.mean()+Z*se(w)),width_sd=float(w.std(ddof=1)),width_p025=q[0],width_p25=q[1],width_median=q[2],width_p75=q[3],width_p975=q[4],raw_width=float(rw.mean()),raw_width_se=se(rw),width_ratio_ppipp=wr,ratio_se=se((w-wr*wpp)/wpp.mean()),paired_diff=float(rd.mean()),paired_diff_se=se(rd),paired_coverage_diff=float(cd.mean()),paired_coverage_diff_se=se(cd),width_ratio_cp=float(w.mean()/cpw.mean()),width_ratio_eb_labeled=float(w.mean()/eblw.mean()),fraction_width_one=float((w==1).mean()),fraction_truncated=float((rw-w>1e-10).mean()),raw_minus_reported_min=float(np.min(rw-w)))
        record['zero_raw_width'] = int((rw==0).sum())
        record['near_zero_raw_width'] = int((rw<=1e-12).sum())
        record['zero_width_positive_raw_width'] = int(((w==0)&(rw>0)).sum())
        record['saved_truth_containment_disagreement'] = int((covered!=((lo<=saved_t)&(saved_t<=hi))).sum())
        record['ratio_cp_se'] = se((w-record['width_ratio_cp']*cpw)/cpw.mean())
        record['ratio_eb_labeled_se'] = se((w-record['width_ratio_eb_labeled']*eblw)/eblw.mean())
        logp = min(0., float(logsumexp(binom.logpmf(np.arange(k+1),r,.95))))
        record['log_p_undercoverage'] = logp
        record['log10_p_undercoverage'] = logp/np.log(10)
        record['p_undercoverage_sci'] = probability_sci(logp)
        record['ratio_ci_lo'] = wr-Z*record['ratio_se']
        record['ratio_ci_hi'] = wr+Z*record['ratio_se']
        record['paired_diff_ci_lo'] = record['paired_diff']-Z*record['paired_diff_se']
        record['paired_diff_ci_hi'] = record['paired_diff']+Z*record['paired_diff_se']
        record['coverage_diff_ci_lo'] = record['paired_coverage_diff']-Z*record['paired_coverage_diff_se']
        record['coverage_diff_ci_hi'] = record['paired_coverage_diff']+Z*record['paired_coverage_diff_se']
        if method=='eb_select':
            counts = g.selected.value_counts().sort_index()
            record.update({f'selected_{i}_count': int(counts.get(i,0)) for i in range(5)})
            record['selected_invalid'] = int((~g.selected.isin(range(5))).sum())
        else:
            record['selected_invalid'] = int((g.selected!=-1).sum())
        s = SUMMARY[(SUMMARY.scenario==scenario)&(SUMMARY.n==n)&(SUMMARY.ratio==ratio)&(SUMMARY.method==method)]
        if len(s)!=1:
            ERRORS.append(dict(summary_key=(scenario,n,ratio,method),matches=len(s)))
        else:
            for col in ['reps','truth','coverage','cov_lo','cov_hi','width','width_se','raw_width','width_ratio_ppipp','ratio_se','paired_diff','paired_diff_se']:
                delta = abs(float(s.iloc[0][col])-float(record[col]))
                DIFFS[col] = max(delta, DIFFS.get(col,0))
        METRICS.append(record)

M = pd.DataFrame(METRICS)
for tier, idx in M.groupby('tier').groups.items():
    indices = np.asarray(list(idx))
    logs = M.loc[indices,'log_p_undercoverage'].to_numpy()
    order = np.argsort(logs,kind='stable')
    adjusted_logs = np.minimum(0., np.maximum.accumulate(logs[order]+np.log(len(order)-np.arange(len(order)))))
    M.loc[indices[order], 'p_holm_tier'] = np.exp(adjusted_logs)
    M.loc[indices[order], 'log10_p_holm_tier'] = adjusted_logs/np.log(10)
    M.loc[indices[order], 'p_holm_tier_sci'] = [probability_sci(x) for x in adjusted_logs]
    M.loc[indices, 'holm_family_size'] = len(indices)
M['undercoverage_reject_holm05'] = M.p_holm_tier <= .05
M.to_csv(OUT/'results_audit_metrics.csv',index=False,float_format='%.17g')
pd.DataFrame(CELLS).to_csv(OUT/'results_audit_cells.csv',index=False)
REJECT = M[M.undercoverage_reject_holm05]
REJECT.to_csv(OUT/'results_audit_undercoverage.csv',index=False,float_format='%.17g')
CURRENT_HASHES = {}
for path, frozen in json.loads((OUT/'prerun_sha256.json').read_text()).items():
    current = hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
    CURRENT_HASHES[path] = dict(frozen=frozen,current=current,match=frozen==current)
for path in ['results/config.json','results/summary.csv','results/oracle.csv','run_experiments.py']:
    HASHES[path] = hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
# Cross-check analytic CSV arithmetic without refitting or running methods.
ORACLE['variance_gap'] = ORACLE.nvar_scalar-ORACLE.nvar_score_oracle
ORACLE['recomputed_ratio'] = np.sqrt(ORACLE.nvar_score_oracle/ORACLE.nvar_scalar)
ORACLE.to_csv(OUT/'results_audit_oracle.csv',index=False,float_format='%.17g')
PROVENANCE = dict(analysis_only=True,errors=ERRORS,raw_files_expected=sorted(EXPECTED),raw_files_unexpected=sorted({p.name for p in (ROOT/'results/raw').glob('*.csv.gz')}-EXPECTED),raw_files_missing=sorted(EXPECTED-{p.name for p in (ROOT/'results/raw').glob('*.csv.gz')}),cells=len(CELLS),replicates=sum(c[3] for c in CONFIG['cells']),intervals=len(M)*2000,method_cells=len(M),summary_rows=len(SUMMARY),summary_duplicate_keys=int(SUMMARY.duplicated(['scenario','n','ratio','method']).sum()),max_summary_absolute_differences=DIFFS,data=DATA,frozen_hash_checks=CURRENT_HASHES,input_sha256=HASHES,analysis_environment=dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,scipy=scipy.__version__),nominal=.95,holm_alpha=.05,holm_families={tier:int(len(g)) for tier,g in M.groupby('tier')},oracle_ratio_max_abs_difference=float(np.abs(ORACLE.recomputed_ratio-ORACLE.oracle_width_ratio).max()))
(OUT/'results_audit_provenance.json').write_text(json.dumps(PROVENANCE,indent=2)+'\n')
print('COMPLETENESS',len(CELLS),len(M),sum(c['rows'] for c in CELLS),'errors',ERRORS)
print('MAX SUMMARY DIFFS',DIFFS)
print('DATA',DATA)
print('FROZEN HASH MATCH',{p:d['match'] for p,d in CURRENT_HASHES.items()})
print('INVALID/INTEGRITY TOTALS',M[['invalid_nonfinite','invalid_reversed','endpoints_outside_unit','negative_width','negative_raw_width','covered_disagreement','stored_covered_invalid','selected_invalid']].sum().to_dict())
print('WIDTH PRECISION',M.width_endpoint_max_abs.max())
print('REJECTIONS',M.groupby('tier').agg(tests=('method','size'),rejections=('undercoverage_reject_holm05','sum')).to_string())
print('METHOD RANGES',M.groupby('method').agg(min_coverage=('coverage','min'),max_coverage=('coverage','max'),rejects=('undercoverage_reject_holm05','sum'),min_ratio=('width_ratio_ppipp','min'),max_ratio=('width_ratio_ppipp','max')).to_string())
print('REJECTED CELLS\n',REJECT[['scenario','n','ratio','method','covered_count','coverage','cov_lo','cov_hi','p_undercoverage','p_holm_tier']].to_string(index=False))
print('CF RICH\n',M[M.method=='cf_rich'][['scenario','n','ratio','coverage','cov_lo','cov_hi','p_undercoverage','p_holm_tier','width_ratio_ppipp','ratio_se','paired_coverage_diff','paired_coverage_diff_se']].to_string(index=False))
print('REAL\n',M[M.scenario.isin(['galaxies','forest']) & M.method.isin(['ppipp','cf_poly2','cf_rich','cp','eb_labeled','eb_select'])][['scenario','n','method','coverage','width','width_ratio_ppipp','ratio_se']].to_string(index=False))
