"""Read-only analysis of completed results; never imports or runs experiment code."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
from scipy.stats import beta, binom, norm, t

ROOT = Path('/work')
OUT = ROOT/'artifacts'  # Host path; file-tool/public artifact prefix is /artifacts/.
OUT.mkdir(exist_ok=True)
FILES = ['summary.csv', 'paired.csv', 'seed_summary.csv', 'integrity_audit.json',
         'multiplicity_manifest.json', 'data_eda.json', 'design_addendum.md']
hashes = {f: hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in FILES}
s = pd.read_csv(ROOT/'summary.csv')
p = pd.read_csv(ROOT/'paired.csv')
z = pd.read_csv(ROOT/'seed_summary.csv')
s['summary_line'] = s.index + 2
p['paired_line'] = p.index + 2
z['seed_summary_line'] = z.index + 2
manifest = json.loads((ROOT/'multiplicity_manifest.json').read_text())

def holm(values):
    values = np.asarray(values, dtype=float)
    order = np.argsort(values)
    result = np.empty(len(values))
    result[order] = np.minimum(1, np.maximum.accumulate(
        (len(values)-np.arange(len(values))) * values[order]))
    return result

def discrepancy(a, b):
    a, b = np.asarray(a), np.asarray(b)
    finite = np.isfinite(a) & np.isfinite(b)
    assert np.array_equal(np.isnan(a), np.isnan(b))
    return float(np.max(np.abs(a[finite]-b[finite])))

assert s.shape[0] == 624 and p.shape[0] == 1248 and z.shape[0] == 1872
assert not s.duplicated(['cell_id', 'method']).any()
assert not p.duplicated(['cell_id', 'method', 'reference']).any()
assert not z.duplicated(['cell_id', 'method', 'seed']).any()
assert (s.groupby('cell_id').size() == 16).all()
assert (z.groupby(['cell_id', 'method']).size() == 3).all()
exact = (s.scenario != 'shift') & s.method.isin(manifest['exact_coverage_methods'])
under = (s.scenario != 'shift') & s.method.isin(manifest['undercoverage_methods'])
confirm = (p.scenario != 'shift') & (((p.method == 'safe_cp') & (p.reference == 'ppi_pp')) |
                                               ((p.method == 'cp_tails') & (p.reference == 'label_cp')))
assert exact.sum() == 180 and under.sum() == 252 and confirm.sum() == 72
assert np.array_equal(s.exact_family_member, exact)
assert np.array_equal(p.p_holm_width.notna(), confirm)
assert np.array_equal(s.p_holm_undercoverage.notna(), under)
assert np.array_equal(s.exact_sim_lower.notna(), exact)
R, h = s.reps.to_numpy(), s.hits.to_numpy()
ph = h/R
q = norm.ppf(.975)
c = (ph + q*q/(2*R))/(1+q*q/R)
r = q*np.sqrt(ph*(1-ph)/R+q*q/(4*R*R))/(1+q*q/R)
checks = {'coverage': discrepancy(s.coverage, ph),
          'wilson_low': discrepancy(s.cov_low, c-r),
          'wilson_high': discrepancy(s.cov_high, c+r),
          'exact_sim_lower': discrepancy(s.loc[exact, 'exact_sim_lower'],
                                         beta.ppf(.05/180, h[exact], R[exact]-h[exact]+1)),
          'undercoverage_p': discrepancy(s.undercoverage_p, binom.cdf(h, R, .95)),
          'holm_undercoverage': discrepancy(s.loc[under, 'p_holm_undercoverage'],
                                            holm(binom.cdf(h[under], R[under], .95)))}
merged = p.merge(s[['cell_id','method','width','reps']].rename(columns={'width':'width_A'}),
                 on=['cell_id','method']).merge(
                 s[['cell_id','method','width']].rename(columns={'method':'reference','width':'width_B'}),
                 on=['cell_id','reference'])
expected_ratio = np.divide(merged.width_A, merged.width_B,
                           out=np.full(len(merged), np.nan), where=merged.width_B != 0)
checks.update({'width_ratio': discrepancy(merged.ratio, expected_ratio),
               'width_difference': discrepancy(merged.difference, merged.width_A-merged.width_B),
               'ratio_low': discrepancy(p.ratio_low, p.ratio-1.96*p.ratio_mcse),
               'ratio_high': discrepancy(p.ratio_high, p.ratio+1.96*p.ratio_mcse)})
stat = np.divide(merged.difference, merged.difference_mcse,
                 out=np.zeros(len(merged)), where=merged.difference_mcse != 0)
pp = np.where(merged.difference_mcse != 0, t.cdf(stat, merged.reps-1),
              (merged.difference >= 0).astype(float))
checks['paired_t_p'] = discrepancy(merged.p_one_sided, pp)
# Merges preserve row order, but use explicit keys to avoid relying on that property.
merged['recomputed_p'] = pp
cf = (merged.scenario != 'shift') & (((merged.method == 'safe_cp') & (merged.reference == 'ppi_pp')) |
                                   ((merged.method == 'cp_tails') & (merged.reference == 'label_cp')))
checks['holm_width'] = discrepancy(merged.loc[cf,'p_holm_width'], holm(merged.loc[cf,'recomputed_p']))
z['recovered_hits'] = z.coverage*z.reps
assert np.allclose(z.recovered_hits, np.rint(z.recovered_hits), atol=1e-7)
z['weighted_width'] = z.width*z.reps
agg = z.groupby(['cell_id','method']).agg(seed_reps=('reps','sum'), seed_hits=('recovered_hits','sum'),
                                         width_sum=('weighted_width','sum')).reset_index()
a = s.merge(agg, on=['cell_id','method'])
checks['seed_reps'] = discrepancy(a.reps, a.seed_reps)
checks['seed_hits'] = discrepancy(a.hits, a.seed_hits)
checks['seed_width'] = discrepancy(a.width, a.width_sum/a.seed_reps)
assert max(checks.values()) < 2e-9

# Audit tables include physical CSV line locators and pointwise MC intervals.
w = p[confirm].copy()
w['difference_low_pointwise95'] = w.difference-1.96*w.difference_mcse
w['difference_high_pointwise95'] = w.difference+1.96*w.difference_mcse
w['fractional_width_reduction'] = 1-w.ratio
w.to_csv(OUT/'confirmatory_width_audit.csv', index=False)
s[exact].to_csv(OUT/'exact_coverage_audit.csv', index=False)
s[under].to_csv(OUT/'asymptotic_undercoverage_audit.csv', index=False)
zs = z.pivot(index=['cell_id','seed'], columns='method', values='width')
zs['safe_cp_over_ppi_pp'] = zs.safe_cp.div(zs.ppi_pp.replace(0,np.nan))
zs.reset_index().to_csv(OUT/'seed_width_audit.csv', index=False)

# Read existing outputs only, selected to diagnose the user's specific anomalies.
slugs = ['10_sharp_tails_n500_N10000','18_rare_tails_n100_N2000',
         '22_shift_n500_N10000','23_shift_n2000_N40000',
         '34_forest_n500_N10000','37_galaxies_n500_N10000']
raw_info = {}
for slug in slugs:
    raw = pd.read_csv(ROOT/'results'/(slug+'.csv.gz'))
    diag = pd.read_csv(ROOT/'results'/(slug+'_diagnostics.csv.gz'))
    cell = int(slug[:2])
    assert not raw.duplicated(['seed','rep','method']).any()
    assert np.array_equal(raw.covered, ((raw.low <= raw.truth)&(raw.truth <= raw.high)).astype(int))
    assert np.allclose(raw.width, raw.high-raw.low, atol=2e-14, rtol=0)
    pivot = raw.pivot(index=['seed','rep'], columns='method', values='width')
    errors = []
    for method,g in raw.groupby('method'):
        ss = s[(s.cell_id==cell)&(s.method==method)].iloc[0]
        assert len(g) == ss.reps and g.covered.sum() == ss.hits
        assert (g.width < 1e-14).sum() == ss.degenerate
        errors.extend([abs(g.width.mean()-ss.width), abs(g.width.std(ddof=1)/np.sqrt(len(g))-ss.width_mcse)])
        for ref in ['ppi_pp','label_cp']:
            row = p[(p.cell_id==cell)&(p.method==method)&(p.reference==ref)].iloc[0]
            A,B = pivot[method].to_numpy(), pivot[ref].to_numpy()
            diffse = np.std(A-B,ddof=1)/np.sqrt(len(A))
            errors.append(abs(diffse-row.difference_mcse))
            if B.mean():
                ratio = A.mean()/B.mean()
                ratiose = np.std(A-ratio*B,ddof=1)/(np.sqrt(len(A))*B.mean())
                errors.append(abs(ratiose-row.ratio_mcse))
    ppraw = raw[raw.method=='ppi_pp']
    raw_info[slug] = {'rows':len(raw),'max_checked_error':max(errors),
        'safe_choice_counts':{str(int(k)):int(v) for k,v in diag.safe_choice.value_counts().sort_index().items()},
        'lambda_mean':float(diag['lambda'].mean()),'lambda_sd':float(diag['lambda'].std(ddof=1)),
        'ppi_pp_at_0':int(((ppraw.low==0)&(ppraw.high==0)).sum()),
        'ppi_pp_at_1':int(((ppraw.low==1)&(ppraw.high==1)).sum()),
        'ppi_pp_nondegenerate_failures':int(((ppraw.width>=1e-14)&(ppraw.covered==0)).sum())}
    assert max(errors) < 1e-9

# Exact binomial summation, not generated trials or a new experiment.
truth = {'affine':.5,'reverse':.5,'smooth_u':.35,'sharp_tails':.5,'irrelevant':.35,
         'constant':.35,'rare_tails':.01,'forest':.15162907268170425,
         'galaxies':.2592725318043361}
analytic = []
for _,row in s[(s.method=='label_cp')&(s.scenario!='shift')].iterrows():
    n,mu = int(row.n),truth[row.scenario]
    k = np.arange(n+1)
    low = np.where(k==0,0,beta.ppf(.025,np.maximum(k,1),n-k+1))
    high = np.where(k==n,1,beta.ppf(.975,k+1,np.maximum(n-k,1)))
    cov = float(binom.pmf(k,n,mu)[(low<=mu)&(mu<=high)].sum())
    analytic.append({'cell_id':int(row.cell_id),'summary_line':int(row.summary_line),
                     'theoretical_label_cp_coverage':cov,
                     'exploratory_mc_lower_tail_p':float(binom.cdf(row.hits,row.reps,cov))})
analytic = pd.DataFrame(analytic)
analytic['exploratory_holm36'] = holm(analytic.exploratory_mc_lower_tail_p)
analytic.to_csv(OUT/'analytic_label_cp_diagnostic.csv',index=False)
report = {'input_sha256':hashes,'summary_shapes':{'summary':len(s),'paired':len(p),'seed_summary':len(z)},
          'max_absolute_formula_discrepancies':checks,
          'family_sizes':{'exact':int(exact.sum()),'width':int(confirm.sum()),'undercoverage':int(under.sum())},
          'width_rejections':p[confirm&(p.p_holm_width<.05)][['cell_id','method','reference','paired_line']].to_dict('records'),
          'undercoverage_rejections_by_method':s[s.p_holm_undercoverage<.05].groupby('method').size().to_dict(),
          'exact_min_coverage':float(s.loc[exact,'coverage'].min()),
          'exact_min_sim_lower':float(s.loc[exact,'exact_sim_lower'].min()),
          'exact_bounds_ge95':int((s.loc[exact,'exact_sim_lower']>=.95).sum()),
          'undefined_ratio_lines':p.loc[p.ratio.isna(),'paired_line'].tolist(),
          'selected_existing_raw_checks':raw_info,
          'new_trials_generated':0}
assert hashes == {f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in FILES}
(OUT/'analysis_audit_checks.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
